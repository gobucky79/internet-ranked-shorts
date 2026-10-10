# Internet Ranked – Shorts engine

Makes one ranking-style YouTube Short a day for the channel **Internet Ranked**: 1080×1920, a 4-slot ranking list that fills #4 → #1,
an animated flat illustration per item with a pulsing highlight, punchy captions, pop sounds on reveals, and a looping ending.
The creator records the voiceover; the engine times everything to the audio automatically.

```
python3 engine.py script  topics/<slug>.py                      # voiceover script + title/description/tags
python3 engine.py preview topics/<slug>.py out.png              # scene contact sheet (check drawings before audio exists)
python3 engine.py thumb   topics/<slug>.py out.png              # 1080x1920 thumbnail
python3 engine.py video   topics/<slug>.py voice.mp3 out.mp4    # final Short (prints the phrase timing it found)
python3 engine.py sheet   out.mp4 out.png                       # 10-frame contact sheet of a rendered video
```
Needs Python 3 + Pillow + ffmpeg, and the Poppins Bold font at `/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf`.
`topics/plane_features.py` is the complete reference topic — copy its structure.

## Daily routine (1 Short a day)

0. **vidIQ check (before any topic or script work)** — see "vidIQ" below. Read `INSIGHTS.md` either way.
1. **Pick 1 fresh topic** — the best one you can find — from the next category in the **Top 5 rotation** below
   (look at the last entry in HISTORY.md and take the category after it; after #5 go back to #1).
   Prefer topics backed by today's vidIQ breakouts or by what INSIGHTS.md says works.
2. **Research every claim** with web search before writing it. Only use items you can confirm from a reliable source.
   No myths, no "fun facts" that are actually false. If an item is disputed, drop it.
3. **Write `topics/<slug>.py`** (see rules below), then run `preview` and *look at the image*.
   Fix any drawing that is unclear, off-canvas, or doesn't read as the object at a glance.
4. **Run `thumb`**, look at it. It shows the #1 item big with its `focus` spot circled and arrowed — make sure that spot
   is the thing the #1 tease is about and that the drawing reads instantly at small size.
5. **Send the creator**: the voiceover script (from `script`), the title, description, tags, and the thumbnail PNG.
   Remind them: generate at ~1.1× speed and send back the MP3.
6. **Commit and push** the topic files and the HISTORY.md entries.
7. **When the MP3 arrives:** run `video`. Check the printed timing: each `num` line must be the "Number X:" phrase
   (short, ~0.6–0.9s). Run `sheet` and look at it. Then send the MP4.
   If the creator changed the wording when recording, update the topic text to match what they said before rendering.

## Top 5 rotation (the most-viewed Shorts niches, in our ranking format)

Chosen from Shorts view-share data (Oct 2026: entertainment ~17–32% of all Shorts views, gaming ~21%, tutorials/hacks ~18%;
the all-time top Shorts are dominated by food, transformations, skits and stunts; animals rate "very high" viral potential).
Every Short is still a fact-checked 4-item ranking. Record the category in HISTORY.md (`[cat N]`).

1. **Entertainment / relatable** — relatable moments, wildest world records, craziest stunts, "things everyone has done".
   e.g. "Ranking things everyone does but never admits", "Ranking the most insane world records".
2. **Gaming** — hidden tricks game developers used, gaming myths that were true, how classic games fooled you.
   Name games in the script if needed, but **never draw real game characters, logos or screenshots** — draw generic
   controllers, screens, pixel shapes.
3. **Life hacks / how-to** — hacks that actually work (test claims via reliable sources; no dangerous hacks),
   built-in features of everyday things people don't use.
4. **Food** — food facts, foods that aren't what you think, why foods are made/packaged the way they are.
5. **Animals** — animal abilities that sound fake, animals with secret superpowers, pet behaviors explained.

Format ideas that fit all five (vidIQ trend formats): Top X, Ranking Every, Tier List, Cheap vs Expensive,
Fake vs Real, Guess The…. Stay within the engine's 4-item ranking layout.

## Quality rules (from MrBeast's advice — apply every day)

1. **Give them why they clicked, immediately.** The first line names the exact thing the title/thumbnail promised.
   No intro, no setup, no "today we're going to". Every sentence must be about the topic — cut anything that isn't.
2. **Quality over quantity.** One great Short beats two average ones; average videos never get pushed. Before sending,
   rate each topic honestly: are all 4 items genuinely surprising, and is #1 a real "wait, what?" Would *you* stop scrolling?
   If the topic isn't clearly great, replace it with a better one. Never ship filler.
3. **Thumbnail = simple + one emotion + curiosity.** Understood in under a second while scrolling. One subject (the #1 item,
   drawn big), at most ~4 words of text, and a tease that makes them wonder "what happened / why?" if they don't click.
4. **Title = the same promise as the thumbnail**, and the video's first line pays it off.

## Topic file rules

- **Hook** (`HOOK`): starts with "Ranking …", promises a payoff for #1 ("…and number one will surprise you",
  "…and number one could save your life"). Vary the payoff wording across days.
- **4 items**, ordered #4 → #1 in `ITEMS`. Each has `what` (names the thing, short) and `why` (the payoff, one sentence).
  Spoken as "Number four: <what> <why>". #1 must be the strongest item.
- **Length:** 65–80 words total (check the count `script` prints). Over 85 words = too long; cut.
- **Outro** (`OUTRO`): one short line that flows back into the hook so the Short loops.
- `label`: 1–3 words for the ranking list. `VIDEO_TITLE`: 2 lines. `THUMB_TEXT`: (small line, BIG line) — 4 words max in total; a third element is ignored. `THUMB_BANNER`: the #1 tease.
- `KEYWORDS`: words to highlight yellow in captions (uppercase, letters only).
- `PALETTE`: pick a different one from the previous day (top/bottom gradient + glow color).

## Drawing rules

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
  and a `keyword` rotating by weekday: Mon "ranking", Tue "things you never noticed", Wed "did you know", Thu "facts about",
  Fri "secret features", Sat "hidden meaning". Pick topics inspired by the winners — never copy a video; make our own 4-item
  ranking on the same *theme*. Append the 5 most useful findings (title, views, outlier score, why it works) under
  "Breakouts" in INSIGHTS.md with the date; keep only the latest ~30 lines there.
- **Sunday — our own performance:** find the channel with `vidiq_user_channels` (the creator's channel is Internet Ranked,
  @InternetRanked-x4p), then one `vidiq_channel_analytics` call: last 7 days, `dimensions: ["video"]`,
  metrics views, engagedViews, averageViewPercentage, likes, subscribersGained, sort "-views", maxResults 25.
  Write plain takeaways under "What works for us" in INSIGHTS.md (which topics/hooks/categories held viewers best,
  which flopped) and apply them. If the channel isn't authorized in vidIQ, tell the creator in one line and skip.
- Commit INSIGHTS.md changes along with the topic files.

## Platform notes

- YouTube can demonetize "inauthentic"/mass-produced content. Keep topics varied, vary hooks and palettes, and keep facts solid.
- vidIQ cannot upload to YouTube. The creator uploads/schedules in YouTube Studio.
