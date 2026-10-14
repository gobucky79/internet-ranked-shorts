# Internet Ranked – Shorts engine

**Audience (decided 2026-10-14): funny-video fans** — teens and adults scrolling for laughs. Every Short is a
"Ranking Funniest ___" compilation in the **laugh-meter format** (`compilations/laughmeter.py`). The old illustrated
fact-ranking engine (`engine.py`, `topics/`) is retired; keep it for reference only.

```
python3 compilations/laughmeter.py compilations/configs/<slug>.json   # builds <out>.mp4 + <out>_thumb.png
```
Config: `title2` (2nd title line, e.g. "KIDS TRYING LEMON"), `clips` [[rank, label, src, start, end], …] played #4 → #1,
optional `replay` [src, start, end] (slow-mo of the #1 moment), `thumb` [src, time], `tease`, `out`.
See `compilations/configs/kids_lemon.json`. Needs Python 3 + Pillow + ffmpeg + Poppins Bold.

## Daily routine (1 Short a day)

0. **vidIQ check** — see "vidIQ" below. Read `INSIGHTS.md` either way.
1. **Pick today's topic** from the next slot in the **rotation** below (last entry in HISTORY.md → next slot; after #5 go
   back to #1). Never repeat a topic theme from HISTORY.md. Title is always `Ranking Funniest <Topic>`.
2. **Find 4 clips + 1 backup** with `vidiq_youtube_search` (type video, videoDuration short, order viewCount) — one search
   per angle if needed. Each clip: a single original moment (not someone else's compilation), clearly on-theme, ideally
   1M+ views, a real laugh in under ~8 seconds.
   **Skip channels that license/claim footage:** AFV, Jukin (FailArmy, The Pet Collective, Kyoot), ViralHog, BVIRAL,
   Storyful, Newsflare, MLB/NBA/NFL/league channels, House of Highlights, TV shows (Kimmel, Ellen, TODAY, GMA), Disney.
3. **Send the creator**: the topic, the 4 clip links + backup (one line each: what happens, views), and the title,
   description (with a credits line naming each channel) and tags. They download the clips and upload them.
4. **Commit and push** the HISTORY.md entry (mark it "clips sent").
5. **When the clips arrive:** make 2-fps contact sheets of every clip and *look at them*. Find each clip's laugh moment,
   rank the four (#1 = biggest laugh), drop any clip with no real payoff (use the backup), trim each to its moment
   (~4–7s), pick a 1–2.5s slow-mo replay of the #1 moment and a thumbnail frame at the #1 peak. Write the config, build,
   then check a contact sheet of the output: faces must never sit under the pill, meter or MAXED OUT text, and there must
   be no stray frames from the next scene at a cut. Send the MP4 + thumbnail with the final title/description/tags.

## Rotation (5 slots)

Kids topics broke out for us, so they get 3 of 5 slots. Record the slot in HISTORY.md (`[slot N]`).

1. **Kids** — e.g. Kids Fails, Kids Trying Lemon, Kids Halloween Moments, Kids Sibling Moments, Kids First Haircut,
   Kids Sports Fails, Kids Saying No, Kids Getting Scared, Kids vs Snow. Title: `Ranking Funniest Kids <Theme>`.
2. **Animals** — pets and animals doing dumb or dramatic things: Dogs Being Dramatic, Cats Knocking Things Over,
   Pets Getting Caught, Animal Jump Scares.
3. **Kids** (a different theme from slot 1).
4. **Fails & pranks** — everyday fails, gym fails, pool fails, prank reactions (no injuries that look serious).
5. **Kids** (a different theme again).

Keep it light: no real injuries, no kids in distress beyond a funny moment, nothing mean-spirited.

## Quality rules (from MrBeast's advice — apply every day)

1. **Give them why they clicked, immediately.** The first clip starts on the action — no slow lead-in.
   Trim every clip to its laugh; cut anything that isn't funny.
2. **Quality over quantity.** One great Short beats two average ones; average videos never get pushed. Before sending,
   rate it honestly: is every clip actually funny, and is #1 the biggest laugh? Would *you* stop scrolling?
   If the topic isn't clearly great, replace it with a better one. Never ship filler.
3. **Thumbnail = simple + one emotion + curiosity.** Understood in under a second while scrolling. One subject (the #1 moment,
   at its peak), at most ~4 words of text, and a tease that makes them wonder "what happened / why?" if they don't click.
4. **Title = the same promise as the thumbnail**, and the first clip pays it off.

## Legacy: fact-ranking engine (retired 2026-10-14)

`engine.py` still works (`script` / `preview` / `thumb` / `video` / `sheet` on a `topics/<slug>.py`), but the channel no
longer posts fact Shorts. The rules below apply only if the creator asks for one.

### Topic file rules

- **Hook** (`HOOK`): starts with "Ranking …", promises a payoff for #1 ("…and number one will surprise you",
  "…and number one could save your life"). Vary the payoff wording across days.
- **4 items**, ordered #4 → #1 in `ITEMS`. Each has `what` (names the thing, short) and `why` (the payoff, one sentence).
  Spoken as "Number four: <what> <why>". #1 must be the strongest item.
- **Length:** 65–80 words total (check the count `script` prints). Over 85 words = too long; cut.
- **Outro** (`OUTRO`): one short line that flows back into the hook so the Short loops.
- `label`: 1–3 words for the ranking list. `VIDEO_TITLE`: 2 lines. `THUMB_TEXT`: (small line, BIG line) — 4 words max in total; a third element is ignored. `THUMB_BANNER`: the #1 tease.
- `KEYWORDS`: words to highlight yellow in captions (uppercase, letters only).
- `PALETTE`: pick a different one from the previous day (top/bottom gradient + glow color).

### Drawing rules

- Each `draw_*()` draws on an 800×800 transparent canvas via `canvas()`, coordinates through `sc()`, returns `fin(im)`.
  Widths/radii must be multiplied by 2 (supersampling). Keep the subject within ~80–720.
- Flat, bold shapes, 3–5 colors, recognizable at thumbnail size. No text except tiny signage (e.g. "EXIT").
- **No brand logos, characters, or copyrighted designs.** Generic objects only.
- `focus=(x, y)`: the exact spot the item is about — the pulse ring goes there.
- `animate(img, d, lt, e)`: optional. `d` draws on a transparent overlay (use RGBA fills). `e` = seconds since the `why`
  phrase started (negative before it) — trigger the "payoff" animation when `e >= 0`. Return `None`, a new image, or
  `(image_or_None, new_focus)`. Keep animations simple: something moves, flows, lights up, or appears.

## vidIQ (one 5-credit call per day, max)

The free plan gives 150 credits/month (refills monthly); almost every vidIQ tool costs 5 credits. So: **at most ONE paid
vidIQ call per daily run.** First call `vidiq_balance`. If fewer than 5 credits remain, skip vidIQ and rely on INSIGHTS.md.
Never spend credits on title/thumbnail scoring, voiceovers or anything else unless the creator asks.

- **Mon–Sat — breakout topics:** `vidiq_outliers` with `contentType: "short"`, `publishedWithin: "thisMonth"`, `limit: 25`,
  and a `keyword` rotating by weekday: Mon "funny kids", Tue "ranking funniest", Wed "funny animals", Thu "funny fails",
  Fri "try not to laugh", Sat "funny pranks". Pick themes inspired by the winners — never copy a video; build our own
  4-clip ranking on the same *theme*. (Clip searches with `vidiq_youtube_search` are separate and also 5 credits each —
  keep the whole run to ~4 calls.) Append the 5 most useful findings (title, views, outlier score, why it works) under
  "Breakouts" in INSIGHTS.md with the date; keep only the latest ~30 lines there.
- **Sunday — our own performance:** find the channel with `vidiq_user_channels` (the creator's channel is Internet Ranked,
  @InternetRanked-x4p), then one `vidiq_channel_analytics` call: last 7 days, `dimensions: ["video"]`,
  metrics views, engagedViews, averageViewPercentage, likes, subscribersGained, sort "-views", maxResults 25.
  Write plain takeaways under "What works for us" in INSIGHTS.md (which topics/hooks/categories held viewers best,
  which flopped) and apply them. If the channel isn't authorized in vidIQ, tell the creator in one line and skip.
- Commit INSIGHTS.md changes along with the topic files.

## Platform notes

- YouTube can demonetize reused content. Every Short must be transformative: our ranking, laugh meter, trims, slow-mo, sound effects and text — never a straight reupload — and the description credits each source channel. Expect occasional Content ID claims on clips with music.
- vidIQ cannot upload to YouTube. The creator uploads/schedules in YouTube Studio.
