# Internet Ranked – Shorts engine

> **Autopilot (added 2026-11-01): see [AUTOPILOT.md](AUTOPILOT.md).** The creator drops the downloaded clips in Drive ›
> "Internet Ranked Inbox". A GitHub Action auto-edits them (`bot/autoedit.py`: 28–32 s, crossfades, original audio,
> watermark only, no on-screen title/ranking) and uploads the Short to YouTube as private for one-tap approval.
> The daily package's job now ends at step 3 plus writing the plan file. Step 5 below is the manual fallback.

**Audience (updated 2026-10-15): mostly middle-aged funny-video fans** (parents/grandparents age). Every Short is a
"Ranking Funniest ___" compilation in the **Clean format** (`compilations/clean.py`): straight cuts from #4 to #1 with
the title banner, a "#N label" bar and the @InternetRanked-x4p watermark. **No black screens and no added sound
effects** — the only audio is the clips' own sound (loudness-matched). Every Short and thumbnail carries the watermark.

```
python3 compilations/clean.py compilations/configs/<slug>.json   # builds <out>.mp4 + <out>_thumb.png
```
Config: `title2` (2nd title line, e.g. "BABIES TRYING LEMON"), `clips` [[rank, label, src, start, end], …] played
#4 → #1, `thumb` [src, time], `tease`, `out`. (`replay` exists but is not used.)

Retired formats, kept for reference only: `vineboom.py` (black boom cards + sound — dropped 2026-10-15 for the
middle-aged audience) and `trynottolaugh.py` (hearts game with sound effects). Needs Python 3 + Pillow + ffmpeg + Poppins Bold.

## Daily routine (1 Short a day)

0. **Research check** — see "Research (no vidIQ)" below. Read `INSIGHTS.md` either way.
1. **Pick today's topic** from the next slot in the **rotation** below (last entry in HISTORY.md → next slot; after #5 go
   back to #1). Never repeat a topic theme from HISTORY.md. Title is always `Ranking Funniest <Topic>`.
2. **Find 4 clips + 1 backup that haven't blown up yet.** Viral clips get swiped ("seen it") and look like reused
   content, so: **posted in the last ~60 days, about 5K–500K views, ideally from channels under ~500K subscribers.**
   Never use a clip over ~2M views. If the HQ's Scout already posted today's picks (`scout.json` on the Internet Ranked
   HQ page) for this topic, start from those. Otherwise search with the **video-searcher** skill: WebSearch plus the
   built-in browser on YouTube (Filters: Type = Shorts, Upload date = this month/year, sorted by view count, then by
   relevance), TikTok and Reddit, keeping only results inside the view range. Favor small-channel clips that are already
   outperforming (views several times the channel's subscriber count, high views per hour) — the best kind: proven
   funny, not yet everywhere. Every number must come from a page actually opened; never guess views or dates.
   If the video-watcher skill is available, watch the shortlist (captions on) to confirm each laugh before sending.
   Each clip: a single original moment (not someone else's compilation), clearly on-theme, a real laugh in ~8 seconds.
   **Skip channels that license/claim footage:** AFV, Jukin (FailArmy, The Pet Collective, Kyoot), ViralHog, BVIRAL,
   Storyful, Newsflare, MLB/NBA/NFL/league channels, House of Highlights, TV shows (Kimmel, Ellen, TODAY, GMA), Disney.
   **Real clips only — screen every pick for AI fakes (added 2026-11-03).** Baby and pet Shorts are flooded with
   AI-generated clips; on 2026-11-03 most in-range baby/dog and baby/food picks were fake. Before a clip makes the list,
   look at 3+ frames up close and drop it on any of these:
   - garbled or misspelled text on name tags, signs, packaging or clothing (the tell that exposed "Sheldon" — tag read "Sheeldon")
   - too-perfect "story" clips: studio-even lighting, staged showroom kitchens, a person frozen or staring in the
     background, every shot framed like a movie, a neat setup → twist → payoff in 15 s
   - templated channels: a pet + named baby duo posting near-identical 15 s clips daily with SEO titles
     ("Dog and Baby 😂 <Name> Nuzzles Giggling <Baby>"), or generic names (Giggle Paws, Tiny ___, ___ Paws, "AI" in the name)
   - third-person descriptions ("an adorable baby tries…") on a channel that isn't the parent's — usually a reupload farm
   - waxy skin, hair or fur that smears when moving, hands/fingers that merge, food that changes shape between frames
   Known AI (verified): Sheldon the Drama King, Bug The Bully, Golden Adventures, Dan Davies, Ornelaz Hornaday, LussBabe.
   Same template, treat as AI: Jake The Troublemaker. Real parent-filmed clips are easier to find on **TikTok** — check it
   first for baby themes. If you can't confirm a clip is real, it doesn't go in.
   **Getting the numbers:** in the built-in browser (or Claude in Chrome if the built-in one is down), YouTube search with
   Type = Shorts + Upload date = This month (`sp=CAMSBAgEEAk%3D` sorted by views, `sp=EgQIBRAJ` this year by relevance,
   `sp=CAISAhAJ` newest) gives views and age for every result; opening a Short gives exact views and publish date. Ignore
   the vidIQ overlay if the browser has the extension (no vidIQ, creator's call). Backup with no browser:
   `returnyoutubedislikeapi.com/votes?videoId=<id>` via WebFetch gives real view counts; its `dateCreated` is when that
   service first saw the clip, so it only proves a clip is *too old*, never that it's fresh. A `0` view count there means
   "not known yet", not zero.
3. **Send the creator**: the topic, the 4 clip links + backup (one line each: what happens, views, posted date), and the title,
   description (with a credits line naming each channel) and tags. They download the clips and upload them.
   **Number the clips 1–5 in the message** (backup = 5) and tell the creator to name the downloaded files to match.
   Also write `plans/<date>_<slug>.json` (format in AUTOPILOT.md: slug, date, slot, title, topic, tease, description,
   tags, clips [{n, channel, url, what}], `"status": "clips sent"`). The Autopilot uses it for the upload.
4. **Commit and push** the HISTORY.md entry (mark it "clips sent") and the plan file.
5. **When the clips arrive:** make 2-fps contact sheets of every clip and *look at them*. Find each clip's laugh moment,
   rank the four (#1 = biggest laugh), drop any clip with no real payoff (use the backup), trim each to its moment
   (~4–7s), pick a thumbnail frame at the #1 peak. No slow-mo replay (creator: not necessary) — leave `replay` out of configs. Write the config, build,
   then check a contact sheet of the output: faces must never sit under the title or rank bar, and there must
   be no stray frames from the next scene at a cut. Send the MP4 + thumbnail with the final title/description/tags.

## Rotation (5 slots)

Babies get 3 of 5 slots (switched from kids on 2026-10-15 — babies fit the middle-aged audience). Record the slot in
HISTORY.md (`[slot N]`).

1. **Babies** — babies and toddlers: e.g. Babies Trying Lemon, Babies Laughing, Babies vs Dogs, Babies First Food,
   Babies Getting Scared, Babies Meeting Twins, Babies Hearing Music, Babies Sneezing. Title: `Ranking Funniest Babies <Theme>`.
2. **Animals** — pets and animals doing dumb or dramatic things: Dogs Being Dramatic, Cats Knocking Things Over,
   Pets Getting Caught, Animal Jump Scares.
3. **Babies** (a different theme from slot 1).
4. **Fails & pranks** — everyday fails, gym fails, pool fails, prank reactions (no injuries that look serious).
5. **Babies** (a different theme again).

Keep it light: no real injuries, no babies in distress beyond a funny moment (no real crying meltdowns), nothing mean-spirited.

## Quality rules (from MrBeast's advice — apply every day)

1. **Give them why they clicked, immediately.** The first clip starts on the action — no slow lead-in.
   Trim every clip to its laugh; cut anything that isn't funny.
2. **Quality over quantity.** One great Short beats two average ones; average videos never get pushed. Before sending,
   rate it honestly: is every clip actually funny, and is #1 the biggest laugh? Would *you* stop scrolling?
   If the topic isn't clearly great, replace it with a better one. Never ship filler.
3. **Thumbnail = simple + one emotion + curiosity.** Understood in under a second while scrolling. One subject (the #1 moment,
   at its peak), at most ~4 words of text, and a tease that makes them wonder "what happened / why?" if they don't click.
4. **Title = the same promise as the thumbnail**, and the first clip pays it off.

## Research (no vidIQ)

**Never use vidIQ or any other paid research tool** (creator's call, 2026-11-02). All research is free: WebSearch, the
built-in browser on YouTube/TikTok/Reddit, and our own YouTube API stats.

- **Mon–Sat — breakout topics:** search YouTube Shorts in the built-in browser (Upload date = this month, sorted by view
  count) for a keyword rotating by weekday: Mon "funny babies", Tue "ranking funniest", Wed "funny animals", Thu "funny
  fails", Fri "try not to laugh", Sat "funny pranks". Open the top results and note views, upload date, channel
  subscribers, views per hour and outlier ratio (views ÷ subscribers). Pick themes inspired by the winners — never copy a
  video; build our own 4-clip ranking on the same *theme*. Append the 5 most useful findings (title, views, outlier
  ratio, why it works) under "Breakouts" in INSIGHTS.md with the date; keep only the latest ~30 lines there. If the
  browser isn't available, use WebSearch and say the numbers are partial.
- **Sunday — our own performance:** comes from `bot/weekly_stats.py` (YouTube Analytics through our own API access,
  free). Read its latest output and write plain takeaways under "What works for us" in INSIGHTS.md (which
  topics/hooks/categories held viewers best, which flopped) and apply them.
- Commit INSIGHTS.md changes along with the topic files.

## Platform notes

- YouTube can demonetize reused content. Every Short must be transformative: our ranking, trims, rank bars and text — never a straight reupload — and the description credits each source channel. Expect occasional Content ID claims on clips with music.
- The Autopilot uploads through the YouTube Data API (as private; the creator publishes in YouTube Studio). The Sunday
  stats come from `bot/weekly_stats.py`.
