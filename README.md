# Internet Ranked – Shorts engine

Makes ranking-style YouTube Shorts for the channel **Internet Ranked**: 1080×1920, a 4-slot ranking list that fills #4 → #1,
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

## Daily routine (2 Shorts a day)

1. **Pick 2 fresh topics.** Read `HISTORY.md` and never repeat a topic or reuse an item. Rotate categories
   (everyday objects, the human body, travel, food, animals, tech, history, money, school/work life, "relatable moments").
   The two topics of a day should be from different categories.
2. **Research every claim** with web search before writing it. Only use items you can confirm from a reliable source.
   No myths, no "fun facts" that are actually false. If an item is disputed, drop it.
3. **Write `topics/<slug>.py`** for each (see rules below), then run `preview` and *look at the image*.
   Fix any drawing that is unclear, off-canvas, or doesn't read as the object at a glance.
4. **Run `thumb`**, look at it, fix overflow or clutter.
5. **Send the creator**, for each Short: the voiceover script (from `script`), the title, description, tags, and the thumbnail PNG.
   Remind them: generate at ~1.1× speed, and send back the MP3s (one per Short; say which is which).
6. **Commit and push** the topic files and the HISTORY.md entries.
7. **When the MP3s arrive:** run `video`. Check the printed timing: each `num` line must be the "Number X:" phrase
   (short, ~0.6–0.9s). Run `sheet` and look at it. Then send the MP4.
   If the creator changed the wording when recording, update the topic text to match what they said before rendering.

## Topic file rules

- **Hook** (`HOOK`): starts with "Ranking …", promises a payoff for #1 ("…and number one will surprise you",
  "…and number one could save your life"). Vary the payoff wording across days.
- **4 items**, ordered #4 → #1 in `ITEMS`. Each has `what` (names the thing, short) and `why` (the payoff, one sentence).
  Spoken as "Number four: <what> <why>". #1 must be the strongest item.
- **Length:** 65–80 words total (check the count `script` prints). Over 85 words = too long; cut.
- **Outro** (`OUTRO`): one short line that flows back into the hook so the Short loops.
- `label`: 1–3 words for the ranking list. `VIDEO_TITLE`: 2 lines. `THUMB_TEXT`: (small, BIG, small). `THUMB_BANNER`: the #1 tease.
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

## Platform notes

- YouTube can demonetize "inauthentic"/mass-produced content. Keep topics varied, vary hooks and palettes, and keep facts solid.
- vidIQ cannot upload to YouTube. The creator uploads/schedules in YouTube Studio.
