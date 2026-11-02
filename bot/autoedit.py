"""Auto-editor: turns a folder of downloaded clips into a finished Internet Ranked Short.

Format (creator's current rules, Oct 2026):
  * 28-32 seconds total, vertical 1080x1920
  * clips play #4 -> #1 (biggest laugh last); NO on-screen title or ranking — the ranking lives in the YouTube title
  * smooth short crossfades between clips, slightly longer clips (~7-8 s each)
  * only the clips' own audio (loudness-matched), no added sound effects
  * @InternetRanked-x4p watermark on every frame and on the thumbnail
  * thumbnail = the #1 clip at its peak, matching the video (watermark + optional tease of up to ~4 words)

How it picks the funny part without a human: it measures each clip's loudness over time. The laugh / scream /
reaction is the loudest spike above the clip's normal level, and the payoff happens just before it, so each clip is
trimmed to end ~2.5 s after the reaction starts. The size of the spike also ranks the clips (#1 = biggest reaction).
Always glance at the result before it goes public — this is a heuristic, not taste.

Usage: python3 -m bot.autoedit <out_prefix> <clip1> <clip2> ... [--tease "HE WASN'T SCARED"]
"""
import argparse, json, os, subprocess, sys, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
WATERMARK = "@InternetRanked-x4p"
YEL = (255, 214, 0)
TARGET, MIN_LEN, MAX_LEN = 30.0, 28.0, 32.0
XFADE = 0.4                      # crossfade length between clips (seconds)
TAIL = 2.5                       # how long to let the laugh play after the reaction starts
MAX_CLIPS = 4
FONT_PATHS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Poppins-Bold.ttf"),
              "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"]
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "9M", "-bufsize", "18M",
       "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".3gp")


def font(sz):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def fit(text, start, maxw):
    sz = start
    while sz > 30 and font(sz).getlength(text) > maxw:
        sz -= 2
    return font(sz)


def run(cmd):
    subprocess.run(cmd, check=True)


def probe(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", src], capture_output=True, text=True, check=True)
    info = json.loads(r.stdout)
    dur = float(info["format"]["duration"])
    v = next((s for s in info["streams"] if s.get("codec_type") == "video"), None)
    a = any(s.get("codec_type") == "audio" for s in info["streams"])
    return dur, (v or {}).get("width", W), (v or {}).get("height", H), a


def loudness(src, hop=0.1):
    """dB loudness every `hop` seconds (mono, 8 kHz)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    n = int(8000 * hop)
    if len(x) < n * 5:
        return None
    frames = x[: len(x) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)
    k = 5                                                     # smooth over 0.5 s
    return np.convolve(db, np.ones(k) / k, mode="same")


def analyze(src):
    """Find the clip's reaction peak and score how big it is."""
    dur, w, h, has_a = probe(src)
    db = loudness(src) if has_a else None
    if db is None or db.max() < -55:                          # silent clip: assume payoff ~60% through
        return {"src": src, "dur": dur, "w": w, "h": h, "audio": has_a, "peak": dur * 0.6, "score": 0.0}
    skip = min(5, len(db) // 4)                               # ignore the first/last half second (pops, encoder clicks)
    i = skip + int(np.argmax(db[skip:len(db) - skip]))
    base = float(np.median(db))
    score = float(db[i] - base)                               # how far the reaction jumps above normal
    onset = i                                                 # walk back to where the reaction starts
    while onset > 0 and db[onset - 1] > base + 0.5 * score:
        onset -= 1
    return {"src": src, "dur": dur, "w": w, "h": h, "audio": has_a, "peak": round(onset * 0.1, 2),
            "score": round(score, 2)}


def windows(clips):
    """Give each clip a trim window so the finished Short lands at ~30 s."""
    n = len(clips)
    need = TARGET + (n - 1) * XFADE                           # crossfades eat time, so add it back
    lens = [0.0] * n
    left, todo = need, list(range(n))
    while todo:                                               # short clips use everything, the rest share the leftover
        share = left / len(todo)
        short = [j for j in todo if clips[j]["dur"] < share]
        if not short:
            for j in todo:
                lens[j] = share
            break
        for j in short:
            lens[j] = clips[j]["dur"]
            left -= clips[j]["dur"]
            todo.remove(j)
    out = []
    for c, L in zip(clips, lens):
        end = min(c["dur"], c["peak"] + TAIL)
        start = max(0.0, end - L)
        end = min(c["dur"], start + L)                        # if we hit the start, extend past the peak instead
        out.append((round(start, 2), round(end, 2)))
    return out


def overlay_png(path, tease=None):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((72, 70), WATERMARK, font=font(38), fill=(255, 255, 255, 170), anchor="lm",
           stroke_width=3, stroke_fill=(0, 0, 0, 130))
    if tease:
        t = tease.upper()
        d.text((W // 2, 1560), t, font=fit(t, 120, 980), fill=YEL, anchor="mm", stroke_width=11, stroke_fill="black")
    im.save(path)
    return path


def vfilter(c):
    """Vertical clips fill the frame; wide clips sit on a blurred copy of themselves instead of being cropped."""
    if c["w"] / max(c["h"], 1) > 0.7:
        return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,"
                f"eq=brightness=-0.08[bg];[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2,fps={FPS},setsar=1")
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1"


def segment(c, ss, ee, out):
    dur = ee - ss
    ain = [] if c["audio"] else ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo"]
    a = "0:a" if c["audio"] else "1:a"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{dur}", "-i", c["src"], *ain,
         "-filter_complex", f"[0:v]{vfilter(c)},format=yuv420p[v];"
                            f"[{a}]aresample=44100,loudnorm=I=-15:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur}", *ENC, out])


def build_short(srcs, out_prefix, tease=None, keep=MAX_CLIPS):
    srcs = [s for s in srcs if s.lower().endswith(VIDEO_EXT)]
    if len(srcs) < 3:
        raise SystemExit(f"need at least 3 clips, got {len(srcs)}")
    tmp = tempfile.mkdtemp(prefix="autoedit_")
    clips = [analyze(s) for s in srcs]
    clips.sort(key=lambda c: c["score"], reverse=True)
    dropped = clips[keep:]
    clips = clips[:keep][::-1]                                # play smallest reaction first, biggest (#1) last
    wins = windows(clips)

    segs = []
    for i, (c, (ss, ee)) in enumerate(zip(clips, wins)):
        seg = f"{tmp}/seg{i}.mp4"
        segment(c, ss, ee, seg)
        segs.append((seg, ee - ss))

    # chain crossfades: video xfade + audio acrossfade, then the watermark on top
    wm = overlay_png(f"{tmp}/wm.png")
    inputs, parts = [], []
    for s, _ in segs:
        inputs += ["-i", s]
    inputs += ["-loop", "1", "-i", wm]
    vprev, aprev, t = "[0:v]", "[0:a]", segs[0][1]
    for k in range(1, len(segs)):
        off = t - XFADE
        parts.append(f"{vprev}[{k}:v]xfade=transition=fade:duration={XFADE}:offset={off:.3f}[v{k}]")
        parts.append(f"{aprev}[{k}:a]acrossfade=d={XFADE}:c1=tri:c2=tri[a{k}]")
        vprev, aprev = f"[v{k}]", f"[a{k}]"
        t = off + segs[k][1]
    parts.append(f"{vprev}[{len(segs)}:v]overlay=0:0:shortest=1,format=yuv420p[vout]")
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts),
         "-map", "[vout]", "-map", aprev, "-t", f"{t:.3f}", *ENC, "-movflags", "+faststart", f"{out_prefix}.mp4"])

    # thumbnail: the #1 clip just before its peak (the payoff), same look as the video
    top = clips[-1]
    tsec = max(0.0, top["peak"] - 0.3)
    bg = f"{tmp}/thumb_bg.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tsec}", "-i", top["src"], "-frames:v", "1",
         "-filter_complex", vfilter(top), bg])
    lay = Image.open(overlay_png(f"{tmp}/thumb_ov.png", tease))
    thumb = Image.alpha_composite(Image.open(bg).convert("RGBA"), lay).convert("RGB")
    thumb.save(f"{out_prefix}_thumb.jpg", quality=90)

    total = probe(f"{out_prefix}.mp4")[0]
    order = [{"rank": len(clips) - i, "src": c["src"], "start": w[0], "end": w[1], "peak": c["peak"],
              "score": c["score"]} for i, (c, w) in enumerate(zip(clips, wins))]
    report = {"video": f"{out_prefix}.mp4", "thumbnail": f"{out_prefix}_thumb.jpg", "duration": round(total, 2),
              "in_range": MIN_LEN <= total <= MAX_LEN, "order": order, "dropped": [c["src"] for c in dropped]}
    with open(f"{out_prefix}_edit.json", "w") as f:
        json.dump(report, f, indent=2)
    return report


def contact_sheet(video, out, fps=1):
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},scale=216:384,tile=8x4", "-frames:v", "1", out])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--tease")
    a = ap.parse_args()
    print(json.dumps(build_short(a.clips, a.out, a.tease), indent=2))
