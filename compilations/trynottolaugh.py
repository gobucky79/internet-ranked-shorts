""""Try Not To Laugh" lives format for "Ranking Funniest ____" Shorts.

Opens with a ~1s teaser of the #1 moment that freezes on "WAIT FOR #1", then counts down #4 -> #1.
Three hearts sit under the title ("LAUGHED? LOSE A LIFE"). #4 is the warm-up; a heart breaks at the end of
#3 and #2, and the last heart shatters on the #1 hit ("YOU LOST!") followed by an optional slow-mo replay.

Usage: python3 trynottolaugh.py <config.json>
Config keys: title2, clips [[rank, label, src, start, end], ...], replay, thumb, tease, out, plus:
  final_hit   seconds into the #1 clip where the big laugh lands (last heart breaks there). Default 1.0
  teaser      optional [src, start, end] for the opening teaser; defaults to 0.8s ending at the thumb frame
"""
import json, math, os, random, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
YEL, RED = (255, 214, 0), (230, 30, 40)
FREEZE = 0.75          # teaser freeze length
BREAK_ANIM = 0.35      # heart break animation length
HEART_Y, HEART_R = 398, 30


def font(sz):
    return ImageFont.truetype(BOLD, sz)


def fit(text, start, maxw):
    sz = start
    while sz > 30 and font(sz).getlength(text) > maxw:
        sz -= 2
    return font(sz)


def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def has_audio(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", src], capture_output=True, text=True)
    return bool(r.stdout.strip())


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 path], capture_output=True, text=True).stdout)


VF = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "9M", "-bufsize", "18M", "-c:a", "aac", "-b:a", "160k", "-ar", "44100"]


def outlined(d, xy, text, f, fill, stroke=8, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill="black", anchor=anchor)


WATERMARK = "@InternetRanked-x4p"


def watermark(d):
    """channel handle, top-left above the title banner (clear of YouTube's buttons, captions and faces)"""
    f = font(36)
    d.text((72, 50), WATERMARK, font=f, fill=(255, 255, 255, 165), anchor="lm",
           stroke_width=3, stroke_fill=(0, 0, 0, 120))


def banner(d, title2):
    watermark(d)
    d.rounded_rectangle((60, 90, W - 60, 330), radius=36, fill=(255, 255, 255, 245))
    d.text((W // 2, 150), "RANKING FUNNIEST", font=fit("RANKING FUNNIEST", 78, 900), fill="black", anchor="mm")
    d.text((W // 2, 260), title2, font=fit(title2, 96, 900), fill=RED, anchor="mm")


def bar_layout(rank, label, scale=1.0):
    text = f"#{rank}  {label}"
    f = fit(text, int(54 * scale), 640)
    tw = f.getlength(text)
    w = tw + 40 + 30 + 3 * 2 * HEART_R + 2 * 18 + 40
    x0 = (W - w) / 2
    hx = [x0 + 40 + tw + 30 + HEART_R + k * (2 * HEART_R + 18) for k in range(3)]
    return text, f, x0, w, hx


def bar(d, rank, label, scale=1.0):
    """dark bar under the title: '#N label' + 3 heart slots. Returns heart centre xs."""
    text, f, x0, w, hx = bar_layout(rank, label, scale)
    y0, h = 350, 96
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=48, fill=(0, 0, 0, 215))
    d.text((x0 + 40, y0 + h / 2), text, font=f, fill=YEL, anchor="lm")
    return hx


def heart_poly(cx, cy, r, n=60):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * r / 16, cy - y * r / 16))
    return pts


def heart(d, cx, cy, r, state, k=0.0):
    """state: 'full', 'breaking' (k 0..1), 'broken'"""
    if state == "breaking":
        s = 1 + 0.35 * math.sin(k * math.pi)          # pop
        r2 = r * s
        d.polygon(heart_poly(cx, cy, r2 + 6), fill=(0, 0, 0, 255))
        col = tuple(int(RED[i] + (90 - RED[i]) * k) for i in range(3))
        d.polygon(heart_poly(cx, cy, r2), fill=col + (255,))
        gap = 14 * k
        d.line([(cx, cy - r2 * 0.6), (cx - 8 - gap, cy - r2 * 0.1), (cx + 6 + gap, cy + r2 * 0.25),
                (cx, cy + r2 * 0.9)], fill="black", width=7)
        return
    d.polygon(heart_poly(cx, cy, r + 6), fill=(0, 0, 0, 255))
    if state == "full":
        d.polygon(heart_poly(cx, cy, r), fill=RED + (255,))
        d.ellipse((cx - r * 0.55, cy - r * 0.55, cx - r * 0.25, cy - r * 0.25), fill=(255, 255, 255, 170))
    else:
        d.polygon(heart_poly(cx, cy, r), fill=(90, 90, 90, 255))
        d.line([(cx, cy - r * 0.6), (cx - 22, cy - r * 0.1), (cx + 20, cy + r * 0.25), (cx, cy + r * 0.9)],
               fill="black", width=7)


def hearts(d, xs, lost_times, tt, shake=False):
    for i, x in enumerate(xs):
        lt = lost_times[i]
        dx = random.uniform(-6, 6) if shake else 0
        if tt < lt:
            heart(d, x + dx, HEART_Y, HEART_R, "full")
        elif tt < lt + BREAK_ANIM:
            heart(d, x + dx, HEART_Y, HEART_R, "breaking", (tt - lt) / BREAK_ANIM)
        else:
            heart(d, x + dx, HEART_Y, HEART_R, "broken")


def make_clip(src, ss, ee, tmp, name, slow=1.0, freeze=0.0):
    seg = f"{tmp}/seg_{name}.mp4"
    d = ee - ss
    out_d = d * slow + freeze
    ain, a = ([], "0:a") if has_audio(src) else (["-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=44100:cl=stereo"], "1:a")
    vf = VF
    if slow != 1:
        vf += f",minterpolate=fps={FPS}:mi_mode=blend,setpts={slow}*PTS"
    if freeze:
        vf += f",tpad=stop_mode=clone:stop_duration={freeze}"
    af = "aresample=44100"
    if slow == 2.5:
        af += ",atempo=0.5,atempo=0.8"
    af += ",loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo"
    if freeze:
        af += f",apad=pad_dur={freeze}"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{d}", "-i", src, *ain,
         "-filter_complex", f"[0:v]{vf},format=yuv420p[v];[{a}]{af}[ao]",
         "-map", "[v]", "-map", "[ao]", "-t", f"{out_d}", *ENC, seg])
    return seg


def tone(path, expr):
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", expr[0], "-af", expr[1], path])


def build(cfg):
    random.seed(3)
    tmp = tempfile.mkdtemp(prefix="tntl_")
    clips = cfg["clips"]
    tsrc, tt_ = cfg["thumb"]
    teaser = cfg.get("teaser") or [tsrc, max(0, tt_ - 0.6), tt_ + 0.2]

    segs, starts = [], []
    s = make_clip(*teaser, tmp, "teaser", freeze=FREEZE)
    segs.append(s)
    t = dur(s)
    teaser_end = t
    for i, (rank, label, src, ss, ee) in enumerate(clips):
        s = make_clip(src, ss, ee, tmp, str(i))
        segs.append(s)
        starts.append(t)
        t += dur(s)
    clip_ends = starts[1:] + [t]
    if cfg.get("replay"):
        s = make_clip(*cfg["replay"], tmp, "replay", slow=2.5)
        segs.append(s)
        t += dur(s)
    total = t
    final_hit = starts[-1] + cfg.get("final_hit", 1.0)
    n = len(clips)
    # hearts break at the end of the 2nd-to-last two clips before #1, then on the #1 hit
    lost = [clip_ends[n - 3] - BREAK_ANIM - 0.05, clip_ends[n - 2] - BREAK_ANIM - 0.05, final_hit]

    lst = f"{tmp}/list.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in segs)
    base = f"{tmp}/base.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    pop, crack, crash, whoosh = (f"{tmp}/{x}.wav" for x in ("pop", "crack", "crash", "whoosh"))
    tone(pop, ("sine=frequency=900:duration=0.12", "afade=t=out:st=0.02:d=0.10,asetrate=44100*1.4,aresample=44100,volume=0.9"))
    tone(crack, ("anoisesrc=d=0.25:c=pink:a=0.8", "highpass=f=800,afade=t=out:st=0.02:d=0.22,volume=1.4"))
    tone(crash, ("anoisesrc=d=0.6:c=white:a=0.9", "highpass=f=1500,afade=t=out:st=0.03:d=0.55,volume=1.2"))
    tone(whoosh, ("anoisesrc=d=0.4:c=brown:a=0.9", "bandpass=f=600:w=500,afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.2,volume=2"))
    events = [(whoosh, max(0, teaser_end - 0.35))] + [(pop, st) for st in starts] + \
             [(crack, x) for x in sorted(lost)[:2]] + [(crash, max(lost))]
    sfx_in, sfx_f = [], []
    for j, (wav, at) in enumerate(events):
        k = j + 2
        sfx_in += ["-i", wav]
        ms = int(at * 1000)
        sfx_f.append(f"[{k}:a]adelay={ms}|{ms},aformat=channel_layouts=stereo[s{k}]")
    mix = "".join(f"[s{j + 2}]" for j in range(len(events)))
    fc = ("[0:v][1:v]overlay=0:0,format=yuv420p[vo];" + ";".join(sfx_f) +
          f";[0:a]{mix}amix=inputs={len(events) + 1}:duration=first:normalize=0[ao]")
    out = cfg["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *sfx_in, "-filter_complex", fc,
                          "-map", "[vo]", "-map", "[ao]", *ENC, "-movflags", "+faststart", f"{out}.mp4"],
                         stdin=subprocess.PIPE)
    static = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    banner(ImageDraw.Draw(static), cfg["title2"])
    heart_times = sorted(lost, reverse=True)   # right heart breaks first, left heart lasts to #1
    for fr in range(int(round(total * FPS))):
        tt = fr / FPS
        im = static.copy()
        d = ImageDraw.Draw(im)
        if tt < teaser_end:
            if tt >= teaser_end - FREEZE:
                dim = Image.new("RGBA", (W, H), (0, 0, 0, 110))
                im = Image.alpha_composite(im, dim)
                d = ImageDraw.Draw(im)
                banner(d, cfg["title2"])
                k = min(1.0, (tt - (teaser_end - FREEZE)) / 0.15)
                outlined(d, (W / 2, H - 470), "WAIT FOR", font(int(90 + 30 * k)), "white", stroke=10)
                outlined(d, (W / 2, H - 330), "#1", font(int(150 + 60 * k)), YEL, stroke=12)
            p.stdin.write(im.tobytes())
            continue
        i = max(j for j, st in enumerate(starts) if st <= tt + 1e-6)
        rank, label = clips[i][0], clips[i][1]
        xs = bar(d, rank, label)
        over = tt >= max(lost)
        hearts(d, xs, heart_times, tt, shake=over and tt < max(lost) + 1.0)
        if tt < starts[0] + 2.0:
            outlined(d, (W / 2, H - 300), "LAUGHED?", font(84), "white", stroke=9)
            outlined(d, (W / 2, H - 200), "LOSE A LIFE", font(84), RED, stroke=9)
        if over and int((tt - max(lost)) * 6) % 2 == 0:
            outlined(d, (W / 2, H - 330), "YOU", font(140), RED, stroke=12)
            outlined(d, (W / 2, H - 190), "LOST!", font(140), RED, stroke=12)
        p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()

    bgp = f"{tmp}/thumb_bg.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tt_}", "-i", tsrc, "-frames:v", "1", "-vf", VF, bgp])
    bg = Image.open(bgp).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    banner(d, cfg["title2"])
    xs = bar(d, 1, cfg["clips"][-1][1])
    for x, st in zip(xs, ["full", "broken", "broken"]):
        heart(d, x, HEART_Y, HEART_R, st)
    tease = cfg.get("tease", "NOBODY SURVIVES #1")
    outlined(d, (W // 2, 1700), tease, fit(tease, 110, 980), YEL, stroke=10)
    Image.alpha_composite(bg, lay).convert("RGB").save(f"{out}_thumb.png")
    print(f"{out}.mp4  ({total:.1f}s)")


if __name__ == "__main__":
    build(json.load(open(sys.argv[1])))
