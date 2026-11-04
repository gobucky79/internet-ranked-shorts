"""Watchdog (GitHub Actions, twice a day): the safety net that lets the channel run without being watched.

Checks, newest Shorts first:
  - YouTube removed a Short for copyright / a claim / legal reasons  -> creates PAUSED (no more uploads), urgent alert.
    A copyright removal usually means a strike; three strikes ends the channel, so the pipeline stops until the
    creator reads it and deletes PAUSED.
  - A Short is blocked in some countries (that's how a Content ID block shows up in the API) -> set it to private
    (needs the youtube.force-ssl scope; otherwise just alerts) and alert.
  - A scheduled Short went live -> closes its "goes public" notification.
  - Evening check: no Short was built today -> alert (PC off? fetcher failed? no plan written?).
  - Bot sign-in broken -> alert, because otherwise everything just silently stops.

What it can't see: claims that only take the ad money (no block, no removal). YouTube emails those and lists them in
Studio › Content › Copyright; the API doesn't expose them to regular channels.
"""
import datetime as dt, glob, json, os, sys

from bot import notify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAUSED = os.path.join(ROOT, "PAUSED")
STATE = os.path.join(ROOT, "watchdog_state.json")
AZ = dt.timezone(dt.timedelta(hours=-7))
REMOVAL_REASONS = {"claim", "copyright", "trademark", "legal", "termsOfUse"}
DONE_STATUSES = {"uploaded", "ready to post", "built (dry run)"}


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"handled": []}


def save_state(st):
    st["handled"] = st["handled"][-200:]
    with open(STATE, "w") as f:
        json.dump(st, f, indent=2)
        f.write("\n")


def pause(reason):
    if not os.path.exists(PAUSED):
        with open(PAUSED, "w") as f:
            f.write(f"Paused by the watchdog on {dt.datetime.now(AZ):%Y-%m-%d %H:%M} Arizona time.\n{reason}\n"
                    "Delete this file to let the Autopilot upload again.\n")


def check_videos(g, st):
    for v in g.recent_uploads():
        vid, s = v["id"], v["status"]
        title = v["snippet"]["title"]
        url = f"https://youtube.com/shorts/{vid}"

        if s.get("uploadStatus") == "rejected" and s.get("rejectionReason") in REMOVAL_REASONS:
            key = f"removed:{vid}"
            if key not in st["handled"]:
                reason = s["rejectionReason"]
                pause(f"'{title}' ({url}) was removed by YouTube: {reason}.")
                notify.alert(key, f"YouTube removed a Short ({reason}) — uploads paused",
                             f"**{title}**\n{url}\n\nYouTube took this Short down for **{reason}**. A copyright "
                             "removal usually comes with a strike (3 strikes = channel deleted), so the Autopilot "
                             "is **paused** and won't upload anything else.\n\n**What to do:**\n"
                             "1. YouTube Studio › Content › Copyright (or the email from YouTube) — see who claimed it.\n"
                             "2. If it's a strike, take the copyright school course in Studio; add that channel to the "
                             "skip list in README.md so the Scout never picks it again.\n"
                             "3. Resume: delete the `PAUSED` file in the repo (GitHub app › Code › PAUSED › ⋯ › Delete).",
                             urgent=True)
                st["handled"].append(key)
            continue

        blocked = (v.get("contentDetails", {}).get("regionRestriction") or {}).get("blocked") or []
        if blocked and s.get("privacyStatus") != "private":
            key = f"blocked:{vid}"
            if key not in st["handled"]:
                ok, msg = g.set_private(vid)
                did = ("so the watchdog set it to **private**" if ok else
                       "the watchdog couldn't set it to private (re-run auth_setup.py to give it permission — "
                       "AUTOPILOT.md › Watchdog), so set it to Private in Studio yourself")
                notify.alert(key, "A Short got a copyright block",
                             f"**{title}**\n{url}\n\nIt's blocked in {len(blocked)} countries — that's a Content ID "
                             f"claim, {did}. Check Studio › Content › Copyright for who claimed it and keep their "
                             "clips out of future Shorts.", urgent=not ok)
                st["handled"].append(key)

        if s.get("privacyStatus") == "public":
            for p in plans():
                if p.get("video_id") == vid:
                    notify.resolve(f"short:{p['slug']}", f"Live now: {url}")


def plans():
    out = []
    for path in glob.glob(os.path.join(ROOT, "plans", "*.json")):
        try:
            with open(path) as f:
                d = json.load(f)
            d.setdefault("slug", os.path.splitext(os.path.basename(path))[0])
            out.append(d)
        except (OSError, ValueError):
            pass
    return out


def check_today():
    now = dt.datetime.now(AZ)
    if now.hour < 17:
        return
    today = now.strftime("%Y-%m-%d")
    todays = [p for p in plans() if p.get("date") == today]
    if any(p.get("status") in DONE_STATUSES for p in todays):
        notify.resolve(f"missing:{today}")
        return
    if os.path.exists(PAUSED):
        return                              # already alerted about the pause
    if not todays:
        why = ("No plan was written for today, so the 8 AM daily package didn't run (it needs your PC on and the "
               "Claude desktop app open).")
    else:
        p = todays[0]
        why = (f"Today's plan **{p.get('title', p['slug'])}** is still at *{p.get('status')}*. Usually that means "
               "the clip fetcher couldn't run (PC asleep/off) or couldn't download the clips — its log is "
               "`%USERPROFILE%\\.internet-ranked\\fetch.log`. Drop the clips in Drive › Internet Ranked Inbox to finish it.")
    notify.alert(f"missing:{today}", f"No Short built today ({today})",
                 f"{why}\n\nSkipping a day is fine — tomorrow runs as normal. This closes itself once a Short is built.")


def main():
    st = load_state()
    try:
        from bot.google_api import Google
        g = Google()
        g.token()
        notify.resolve("signin", "Sign-in works again.")
    except SystemExit as e:
        notify.alert("signin", "The bot can't sign in to Google — everything is stopped",
                     f"```\n{e}\n```\nRe-run `python3 bot/auth_setup.py client_secret.json` on your computer and "
                     "update the GOOGLE_REFRESH_TOKEN secret (AUTOPILOT.md setup steps 3–4).", urgent=True)
        check_today()
        return
    check_videos(g, st)
    check_today()
    save_state(st)


if __name__ == "__main__":
    sys.exit(main())
