"""Clip fetcher: downloads today's clips and drops them in Drive for the Autopilot. Runs on YOUR PC.

Why on your PC: YouTube and TikTok block downloads from cloud servers (GitHub Actions), but a home connection works.

What it does each run:
  1. Reads the plan files in the GitHub repo (plans/*.json) and finds plans marked "clips sent".
  2. Downloads each plan's clips with yt-dlp as 1.mp4 ... 5.mp4 (numbered like the daily package).
  3. Uploads them to Google Drive > "Internet Ranked Inbox" / <plan slug>, which the Autopilot turns into a Short.
  4. Remembers which plans it finished so it never downloads the same clips twice.

One-time setup (setup_fetcher.bat does all of this):
  py -m pip install -U yt-dlp requests imageio-ffmpeg
  py fetch_clips.py --setup        # paste the 3 values auth_setup.py printed (same ones as the GitHub secrets)
Then Windows Task Scheduler runs it every morning.

Other options:
  py fetch_clips.py --dry-run      # download only, don't upload to Drive
  py fetch_clips.py --plan SLUG    # fetch one specific plan even if already done
"""
import argparse, datetime as dt, json, os, sys, tempfile, time

import requests

REPO = "gobucky79/internet-ranked-shorts"
INBOX = "Internet Ranked Inbox"
HOME = os.path.join(os.path.expanduser("~"), ".internet-ranked")
CREDS = os.path.join(HOME, "google.json")
STATE = os.path.join(HOME, "fetched.json")
LOG = os.path.join(HOME, "fetch.log")
DRIVE = "https://www.googleapis.com/drive/v3"
FOLDER = "application/vnd.google-apps.folder"


def log(msg):
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M} {msg}"
    print(line)
    os.makedirs(HOME, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    os.makedirs(HOME, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------- setup ----------
def setup():
    print("Paste the three values that auth_setup.py printed (the same ones you put in GitHub secrets).")
    print("They're saved only on this PC, in", CREDS, "\n")
    vals = {}
    for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"):
        v = input(f"{k}: ").strip()
        if "=" in v and v.split("=")[0].strip() == k:      # pasted the whole printed line
            v = v.split("=", 1)[1].strip()
        if not v:
            sys.exit(f"{k} was empty — run setup again.")
        vals[k] = v
    save_json(CREDS, vals)
    Drive(vals).token()                                       # proves the values work
    print("\nSaved and tested — Google accepted them.")


# ---------- Google Drive ----------
class Drive:
    def __init__(self, creds):
        self.c, self._tok, self._exp = creds, None, 0

    def token(self):
        if time.time() > self._exp - 60:
            r = requests.post("https://oauth2.googleapis.com/token", data={
                "client_id": self.c["GOOGLE_CLIENT_ID"], "client_secret": self.c["GOOGLE_CLIENT_SECRET"],
                "refresh_token": self.c["GOOGLE_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
            if r.status_code != 200:
                sys.exit(f"Google sign-in failed ({r.status_code}): {r.text[:200]}\n"
                         "Run auth_setup.py again, then: py fetch_clips.py --setup")
            j = r.json()
            self._tok, self._exp = j["access_token"], time.time() + j.get("expires_in", 3600)
        return self._tok

    def h(self, extra=None):
        return {"Authorization": f"Bearer {self.token()}", **(extra or {})}

    def folder(self, name, parent=None, create=True):
        q = f"name = '{name}' and mimeType = '{FOLDER}' and trashed = false"
        if parent:
            q += f" and '{parent}' in parents"
        r = requests.get(f"{DRIVE}/files", headers=self.h(), params={"q": q, "fields": "files(id)"}, timeout=30)
        r.raise_for_status()
        if r.json()["files"]:
            return r.json()["files"][0]["id"]
        if not create:
            return None
        meta = {"name": name, "mimeType": FOLDER, **({"parents": [parent]} if parent else {})}
        r = requests.post(f"{DRIVE}/files", headers=self.h(), json=meta, params={"fields": "id"}, timeout=30)
        r.raise_for_status()
        return r.json()["id"]

    def video_names(self, folder):
        r = requests.get(f"{DRIVE}/files", headers=self.h(), timeout=30, params={
            "q": f"'{folder}' in parents and trashed = false and mimeType contains 'video/'", "fields": "files(name)"})
        r.raise_for_status()
        return [f["name"] for f in r.json()["files"]]

    def upload(self, path, folder):
        size = os.path.getsize(path)
        meta = {"name": os.path.basename(path), "parents": [folder]}
        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
                          headers=self.h({"X-Upload-Content-Type": "video/mp4",
                                          "X-Upload-Content-Length": str(size)}), json=meta, timeout=60)
        r.raise_for_status()
        with open(path, "rb") as f:
            up = requests.put(r.headers["Location"], headers=self.h({"Content-Type": "video/mp4"}), data=f,
                              timeout=900)
        up.raise_for_status()


# ---------- plans from GitHub ----------
def pending_plans():
    r = requests.get(f"https://api.github.com/repos/{REPO}/contents/plans", timeout=30,
                     headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    plans = []
    for item in r.json():
        if not item["name"].endswith(".json"):
            continue
        p = requests.get(item["download_url"], timeout=30).json()
        p.setdefault("slug", item["name"][:-5])
        plans.append(p)
    return sorted(plans, key=lambda p: p.get("date", ""))


# ---------- downloading ----------
def download(url, n, out_dir):
    import yt_dlp
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = None
    opts = {
        "outtmpl": os.path.join(out_dir, f"{n}.%(ext)s"),
        "format": "bv*[height<=1920][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True, "quiet": True, "no_warnings": True, "retries": 3,
    }
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    path = os.path.join(out_dir, f"{n}.mp4")
    if not os.path.exists(path):                       # merged into another container
        cands = [f for f in os.listdir(out_dir) if f.startswith(f"{n}.")]
        if not cands:
            raise RuntimeError("download produced no file")
        path = os.path.join(out_dir, cands[0])
    return path, info.get("view_count")


def fetch(plan, drive, dry_run):
    clips = sorted(plan.get("clips", []), key=lambda c: c.get("n", 99))
    if not clips:
        log(f"{plan['slug']}: plan has no clip links — skipped")
        return False
    have = []
    if drive:
        inbox = drive.folder(INBOX)
        sub = drive.folder(plan["slug"], parent=inbox)
        have = drive.video_names(sub)
        if len(have) >= 4:
            log(f"{plan['slug']}: Drive already has {len(have)} clips — nothing to do")
            return True
    work = tempfile.mkdtemp(prefix=f"ir_{plan['slug']}_")
    got = []
    for c in clips:
        n, url = c.get("n"), c.get("url")
        if any(name.split(".")[0].split(" ")[0] == str(n) for name in have):
            got.append(None)                           # already in Drive from an earlier run
            continue
        try:
            path, views = download(url, n, work)
            got.append(path)
            log(f"{plan['slug']}: clip {n} downloaded ({c.get('channel', '?')}, {views or '?'} views)")
        except Exception as e:                         # one bad link shouldn't sink the rest
            log(f"{plan['slug']}: clip {n} FAILED ({url}): {str(e)[:200]}")
    if len(got) < 4:
        log(f"{plan['slug']}: only {len(got)} clips downloaded — need 4+. Download the rest by hand into "
            f"Drive > {INBOX} > {plan['slug']}, named by their number.")
    if dry_run:
        log(f"{plan['slug']}: dry run — files are in {work}")
        return len(got) >= 4
    for p in got:
        if p is None:
            continue
        drive.upload(p, sub)
        log(f"{plan['slug']}: uploaded {os.path.basename(p)} to Drive > {INBOX} > {plan['slug']}")
    return len(got) >= 4


def main():
    ap = argparse.ArgumentParser(description="Download the daily clips and put them in the Drive inbox.")
    ap.add_argument("--setup", action="store_true", help="save the Google sign-in values on this PC")
    ap.add_argument("--dry-run", action="store_true", help="download only, no Drive upload")
    ap.add_argument("--plan", help="fetch this plan slug even if it was already done")
    a = ap.parse_args()
    if a.setup:
        return setup()
    creds = load_json(CREDS, None)
    if not creds and not a.dry_run:
        sys.exit("Not set up yet — run:  py fetch_clips.py --setup")
    drive = None if a.dry_run else Drive(creds)
    done = load_json(STATE, [])
    plans = pending_plans()
    todo = [p for p in plans if (a.plan and p["slug"] == a.plan) or
            (not a.plan and p.get("status") == "clips sent" and p["slug"] not in done)]
    if not todo:
        log("no new plans waiting for clips")
        return
    for plan in todo:
        if fetch(plan, drive, a.dry_run) and not a.dry_run and plan["slug"] not in done:
            done.append(plan["slug"])
            save_json(STATE, done)


if __name__ == "__main__":
    main()
