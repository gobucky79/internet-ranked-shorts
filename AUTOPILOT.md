# Internet Ranked Autopilot

Bots that run the channel day to day. Your whole job: **keep your PC on in the morning so the clip fetcher can
download the day's clips, and tap Publish in YouTube Studio.**

```
8 AM   daily package (Claude): topic + 5 numbered clip links + title/description/tags → plans/<date>_<slug>.json
8:20   clip fetcher (your PC, Task Scheduler): downloads the 5 clips with yt-dlp → Drive › "Internet Ranked Inbox/<slug>"
         (if a link fails, it logs it and you drop that one in by hand, named by its number)
hourly Autopilot (GitHub Actions, 7 AM–10 PM):
         finds each clip's laugh moment from its sound → trims → ranks #4→#1 (biggest reaction last)
         → 28–32 s Short with smooth crossfades, original audio, @InternetRanked-x4p watermark, matching thumbnail
         → uploads to YouTube as PRIVATE with title, description (credits each channel) and tags
         → finished MP4 + thumbnail in Drive › "Internet Ranked Done/<slug>" so you can watch it on your phone
you    YouTube Studio app › the new private Short › watch it › set to Public (or Schedule)   ← the one tap
Sunday weekly stats report → reports/<date>.md (views, % viewed, likes, subs gained per Short)
```

## Why it uploads as private

Two reasons:

1. **YouTube's rule:** videos uploaded through the API by an app that hasn't passed YouTube's API audit are locked to
   private. You can still publish them yourself in Studio. (If you pass the audit later, set the `UPLOAD_MODE`
   variable to `schedule` and they'll go public at `PUBLISH_TIME` on their own.)
2. **It protects the channel.** The editor picks the funny part from the *sound* (laughs, screams). Usually right, but
   not always. Every Short is built from other creators' clips, so a quick human check is what keeps you clear of
   reused-content demonetization and copyright strikes.

## One-time setup (about 20 minutes, on a computer)

1. **Google Cloud project.** Go to console.cloud.google.com, make a project ("Internet Ranked Bot"), and enable
   *YouTube Data API v3*, *YouTube Analytics API* and *Google Drive API* (APIs & Services › Library).
2. **OAuth client.**
   - APIs & Services › OAuth consent screen: choose External, fill in the app name and your email, and add yourself
     as a test user.
   - **Then click "Publish app" so it's "In production".** Otherwise Google expires the sign-in every 7 days and the
     bot stops. You'll see an "unverified app" warning when you sign in; click Advanced › Go to app. That's normal
     for a personal tool.
   - Credentials › Create credentials › OAuth client ID › **Desktop app**. Download the JSON file.
3. **Sign in once.** On your computer, run:
   `python3 bot/auth_setup.py ~/Downloads/client_secret_XXXX.json`
   Sign in with the Google account that owns Internet Ranked. It prints three values.
4. **GitHub secrets.** In the repo, go to Settings › Secrets and variables › Actions › New repository secret. Add
   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `GOOGLE_REFRESH_TOKEN`. Never commit them or the JSON file.
5. **Test.** Go to Actions › "Autopilot (edit + upload)" › Run workflow, with **dry_run** ticked. This creates the two
   Drive folders. Drop a few clips in the Inbox, wait 10 minutes, and run it again. The Short shows up in
   "Internet Ranked Done" without touching YouTube. Once you like it, run it without dry run.
6. **Thumbnails.** YouTube only allows custom thumbnails on phone-verified channels (youtube.com/verify).

Optional repo variables (Settings › Secrets and variables › Actions › Variables):
`UPLOAD_MODE` = `private` (default) or `schedule` · `PUBLISH_TIME` = `09:00` (Arizona) · `DRY_RUN` = `1` to pause uploads.

## Clip fetcher (your PC)

YouTube and TikTok block downloads from cloud servers, so the downloader runs on your Windows PC:
`bot/fetch_clips.py` reads today's plan from this repo, downloads each clip with yt-dlp as `1.mp4`…`5.mp4`, and uploads
them to Drive › Internet Ranked Inbox › `<slug>`. Setup, in a folder like `C:\Users\<you>\InternetRanked`:
download `fetch_clips.py`, `setup_fetcher.bat` and `run_fetcher.bat` from `bot/`, then double-click
`setup_fetcher.bat` (installs yt-dlp, asks once for the same three Google values as the GitHub secrets, and schedules a
daily 8:20 AM run that retries every 30 min until 12:20 PM). Log: `%USERPROFILE%\.internet-ranked\fetch.log`.
Manual run: `py fetch_clips.py` · test without uploading: `py fetch_clips.py --dry-run`.

## Daily use

- Clips loose in "Internet Ranked Inbox" go with the oldest plan marked `"status": "clips sent"`.
- Want a specific topic? Put the clips in a subfolder named after the plan's slug (e.g. `babies_lemon`). With no
  plan for that name, the title is made from the folder name ("Ranking Funniest Babies Lemon").
- Name files `1.mp4` … `5.mp4` (or `2 - baby face.mp4`) to match the numbered list. That's how the description
  credits the right channels. Unnumbered files still work, but then every channel in the plan gets credited.
- Send 4 clips + the backup. The bot keeps the 4 with the biggest reactions. It waits until nothing new has arrived
  for 10 minutes (4+ clips) or 1 hour (3 clips) before building.
- Not happy with a Short? Delete it in Studio, then re-trim by hand with `compilations/clean.py`, or drop different
  clips in a subfolder.

## Plan file format (plans/<date>_<slug>.json, written by the 8 AM package)

```json
{
  "slug": "babies_lemon", "date": "2026-11-02", "slot": 1,
  "title": "Ranking Funniest Babies Trying Lemon",
  "topic": "Babies Trying Lemon",
  "tease": "HE WASN'T READY",
  "description": "optional — default asks viewers for their #1 and adds a 'Clips:' credits line",
  "tags": ["funny babies", "babies trying lemon"],
  "clips": [{"n": 1, "channel": "Channel Name", "url": "https://youtube.com/shorts/…", "what": "one-line description"}],
  "status": "clips sent"
}
```
After upload the bot adds `status: "uploaded"`, `video_url`, the final title, credits and the trims it used.

## Files

`bot/autoedit.py` editor · `bot/metadata.py` title/description/tags · `bot/run_inbox.py` Drive → YouTube pipeline ·
`bot/weekly_stats.py` Sunday report · `bot/auth_setup.py` one-time sign-in · `.github/workflows/` the schedules.
Local test, no Google needed: `python3 -m bot.run_inbox --local path/to/clips --dry-run`.
