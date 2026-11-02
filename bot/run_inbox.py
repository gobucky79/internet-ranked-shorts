"""Autopilot: Drive inbox -> finished Short -> YouTube.

Every run (GitHub Actions, hourly in the daytime):
  1. Look in the Google Drive folder "Internet Ranked Inbox" for downloaded clips.
     - Clips loose in the folder belong to the oldest plan in plans/ whose status is "clips sent".
     - Or put them in a subfolder named after the plan's slug (e.g. babies_lemon) to pick the plan yourself.
  2. Wait until the upload has settled (4+ clips and nothing new for 10 min, or 3 clips and nothing new for 1 hour).
  3. Auto-edit (bot/autoedit.py), write title/description/tags (bot/metadata.py).
  4. Upload to YouTube — PRIVATE by default, so the creator approves it in YouTube Studio with one tap.
     UPLOAD_MODE=schedule instead schedules it to go public at PUBLISH_TIME (Arizona time) unless stopped.
  5. Put the finished MP4 + thumbnail in Drive "Internet Ranked Done/<slug>" (easy to preview on a phone),
     move the source clips there too, mark the plan "uploaded" and log it in HISTORY.md.

Local test without Google:  python3 -m bot.run_inbox --local DIR --dry-run
"""
import argparse, datetime as dt, glob, json, os, shutil, sys, tempfile

from bot import autoedit, metadata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANS = os.path.join(ROOT, "plans")
INBOX, DONE = "Internet Ranked Inbox", "Internet Ranked Done"
AZ = dt.timezone(dt.timedelta(hours=-7))          # Arizona: no daylight saving
SETTLE_4, SETTLE_3 = 10 * 60, 60 * 60


def load_plans():
    plans = []
    for p in sorted(glob.glob(os.path.join(PLANS, "*.json"))):
        with open(p) as f:
            d = json.load(f)
        d["_path"] = p
        d.setdefault("slug", os.path.splitext(os.path.basename(p))[0])
        plans.append(d)
    return plans


def save_plan(plan):
    path = plan.pop("_path")
    with open(path, "w") as f:
        json.dump(plan, f, indent=2)
        f.write("\n")
    plan["_path"] = path


def fallback_plan(slug):
    topic = slug.replace("_", " ").replace("-", " ").title()
    p = {"slug": slug, "date": dt.datetime.now(AZ).strftime("%Y-%m-%d"), "title": f"Ranking Funniest {topic}",
         "topic": topic, "clips": [], "status": "clips sent", "_path": os.path.join(PLANS, f"{slug}.json")}
    return p


def pick_plan(plans, slug=None):
    if slug:
        for p in plans:
            if p["slug"] == slug:
                return p
        return fallback_plan(slug)
    pending = [p for p in plans if p.get("status") == "clips sent"]
    pending.sort(key=lambda p: p.get("date", ""))
    return pending[0] if pending else None


def next_publish_time(hhmm):
    h, m = map(int, hhmm.split(":"))
    now = dt.datetime.now(AZ)
    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if t < now + dt.timedelta(hours=1):
        t += dt.timedelta(days=1)
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_history(plan, meta, video_url):
    line = (f"- {plan.get('date', dt.datetime.now(AZ).strftime('%Y-%m-%d'))} – {plan['slug']} – "
            f"[slot {plan.get('slot', '?')}] – {meta['title'].replace(' #shorts', '')} – autopilot upload "
            f"({video_url}). Clips: {', '.join(meta['credits']) or 'see plan'}\n")
    with open(os.path.join(ROOT, "HISTORY.md"), "a") as f:
        f.write(line)


def settled(files, now):
    vids = [f for f in files if f["name"].lower().endswith(autoedit.VIDEO_EXT) or f["mimeType"].startswith("video/")]
    if not vids:
        return vids, False
    newest = max(dt.datetime.fromisoformat(f["modifiedTime"].replace("Z", "+00:00")) for f in vids)
    age = (now - newest).total_seconds()
    ok = (len(vids) >= 4 and age >= SETTLE_4) or (len(vids) >= 3 and age >= SETTLE_3)
    return vids, ok


def produce(plan, clip_paths, work):
    out = os.path.join(work, "out", plan["slug"])
    rep = autoedit.build_short(clip_paths, out, tease=plan.get("tease"))
    used = [os.path.basename(o["src"]) for o in rep["order"]]
    meta = metadata.build(plan, used)
    print(f"built {rep['video']} ({rep['duration']}s) — order #4→#1: {used}")
    if not rep["in_range"]:
        print(f"WARNING: length {rep['duration']}s is outside 28–32s (clips too short?) — check before publishing")
    return rep, meta


def run_local(folder, dry_run):
    plans = load_plans()
    plan = pick_plan(plans) or fallback_plan(os.path.basename(os.path.normpath(folder)))
    clips = sorted(glob.glob(os.path.join(folder, "*")))
    work = tempfile.mkdtemp(prefix="autopilot_")
    rep, meta = produce(plan, clips, work)
    print(json.dumps({"edit": rep, "metadata": meta}, indent=2))
    if not dry_run:
        print("local mode never uploads — use the GitHub workflow for that")


def run_drive(dry_run):
    from bot.google_api import Google
    g = Google()
    inbox = g.find_folder(INBOX)
    done_root = g.find_folder(DONE)
    now = dt.datetime.now(dt.timezone.utc)
    plans = load_plans()

    entries = g.list_files(inbox)
    batches = [(None, inbox, [e for e in entries if e["mimeType"] != "application/vnd.google-apps.folder"])]
    for sub in (e for e in entries if e["mimeType"] == "application/vnd.google-apps.folder"):
        batches.append((sub["name"], sub["id"], g.list_files(sub["id"])))

    did = False
    for slug, folder_id, files in batches:
        vids, ok = settled(files, now)
        if not vids:
            continue
        if not ok:
            print(f"{slug or 'inbox'}: {len(vids)} clip(s), waiting for the upload to finish")
            continue
        plan = pick_plan(plans, slug)
        if plan is None:
            print("clips are in the inbox but no plan has status 'clips sent' — put them in a subfolder named "
                  "after the topic (e.g. babies_lemon) or add a plan file")
            continue

        work = tempfile.mkdtemp(prefix="autopilot_")
        src_dir = os.path.join(work, "clips")
        os.makedirs(src_dir)
        paths = [g.download(f["id"], os.path.join(src_dir, f["name"].replace("/", "_"))) for f in vids]
        rep, meta = produce(plan, paths, work)

        done = g.find_folder(plan["slug"], parent=done_root)
        g.upload_file(rep["video"], done, "video/mp4")
        g.upload_file(rep["thumbnail"], done, "image/jpeg")

        if dry_run:
            print("DRY RUN: skipping YouTube upload")
            print(json.dumps(meta, indent=2))
            plan.update(status="built (dry run)")
        else:
            mode = os.environ.get("UPLOAD_MODE", "private").lower()
            publish_at = next_publish_time(os.environ.get("PUBLISH_TIME", "09:00")) if mode == "schedule" else None
            video = g.upload_video(rep["video"], meta["title"], meta["description"], meta["tags"],
                                   privacy="private", publish_at=publish_at)
            vid = video["id"]
            url = f"https://youtube.com/shorts/{vid}"
            ok_t, msg = g.set_thumbnail(vid, rep["thumbnail"])
            if not ok_t:
                print(f"thumbnail not set (needs a phone-verified channel?): {msg}")
            print(f"uploaded {url} ({'scheduled ' + publish_at if publish_at else 'private — approve in YouTube Studio'})")
            plan.update(status="uploaded", video_id=vid, video_url=url, publish_at=publish_at,
                        uploaded=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
            log_history(plan, meta, url)

        plan.update(title_final=meta["title"], credits=meta["credits"],
                    edit=[{k: o[k] for k in ("rank", "start", "end")} | {"file": os.path.basename(o["src"])}
                          for o in rep["order"]])
        save_plan(plan)
        clips_dir = g.find_folder("clips", parent=done)
        for f in vids:
            g.move(f["id"], clips_dir, folder_id)
        shutil.rmtree(work, ignore_errors=True)
        did = True
    if not did:
        print("nothing ready")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", help="build from a local folder of clips instead of Google Drive")
    ap.add_argument("--dry-run", action="store_true", default=os.environ.get("DRY_RUN") == "1")
    a = ap.parse_args()
    if a.local:
        run_local(a.local, a.dry_run)
    else:
        run_drive(a.dry_run)
