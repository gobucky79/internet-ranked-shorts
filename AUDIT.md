# YouTube API audit — the last step to hands-off

**Why this matters:** YouTube locks every video uploaded through an *unaudited* API project as private, and those
locked videos can't be published or appealed (YouTube Help › "Videos locked as private"). Until the Internet Ranked
Bot's Google Cloud project passes YouTube's API compliance audit, the Autopilot runs in `drive` mode: it builds the
Short and sends you a notification with the file and the text to paste, and you post it from the YouTube app.

After the audit passes, set the repo variable `UPLOAD_MODE` = `schedule` and the bot uploads and schedules each Short
itself. You get a "goes public at …" notification; doing nothing means it goes live.

## How to apply (about 15 minutes)

1. Make sure the project page and privacy policy are live on GitHub Pages: repo Settings › Pages › Deploy from branch
   `main`, folder `/docs`. They'll be at `https://gobucky79.github.io/internet-ranked-shorts/` and `…/privacy.html`.
   Add both URLs to the OAuth consent screen (Google Cloud › APIs & Services › OAuth consent screen › App domain).
2. Open the **YouTube API Services – Audit and Quota Extension Form**:
   https://support.google.com/youtube/contact/yt_api_form
3. Answers to use (edit anything that isn't true for you):
   - **Project:** your Google Cloud project number (Cloud console home page).
   - **What the app does:** "Private tool used only by the owner of the Internet Ranked YouTube channel. It edits
     the channel's daily Short, uploads it to the owner's own channel and schedules it, saves a copy to the owner's
     Google Drive, and reads the channel's own statistics for a weekly report. It is not offered to anyone else and
     never accesses other users' accounts."
   - **Users:** 1 (the channel owner). **Public?** No.
   - **API calls:** videos.insert (1 upload per day), thumbnails.set, videos.list, videos.update (only to set the
     owner's own video to private), channels.list, playlistItems.list, YouTube Analytics reports.query.
   - **Website / privacy policy:** the two GitHub Pages URLs from step 1.
   - **Quota:** the default 10,000 units/day is plenty (one upload ≈ 1,600 units), so don't ask for more.
4. Google may email follow-up questions or ask for a screen recording of the app; reply from the same account.

Reviews can take a few weeks. Nothing breaks while you wait — `drive` mode keeps the channel posting.

## When it's approved

GitHub › repo › Settings › Secrets and variables › Actions › Variables › New variable:
`UPLOAD_MODE` = `schedule`. Optional: `PUBLISH_TIME` = `09:00` (Arizona) and `VETO_HOURS` = `3` (the minimum heads-up
before a Short goes live).
