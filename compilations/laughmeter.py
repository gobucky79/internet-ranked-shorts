""""Laugh meter" format for "Ranking Funniest Kids ____" Shorts.

A vertical meter on the right fills higher with each clip (#4 -> #1). On #1 it maxes out,
cracks, shakes and flashes MAXED OUT with a crash sound. Current rank + label sit in a pill
under the title banner.

Usage: python3 laughmeter.py <config.json>   (same config keys as kidscomp.py)
"""
import json, math, os, random, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
YEL, RED = (255, 214, 0), (230, 30, 40)
MX0, MX1, MY0, MY1 = 948, 1040, 560, 1400   # meter tube
RISE = 0.7                                   # seconds for the fill to rise


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


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def heat(t):
    """green -> yellow -> red for t in 0..1"""
    g, y, r = (60, 220, 90), YEL, RED
    return lerp(g, y, t / 0.5) if t < 0.5 else lerp(y, r, (t - 0.5) / 0.5)


# pre-render the gradient fill once
GRAD = Image.new("RGBA", (MX1 - MX0 - 16, MY1 - MY0 - 16))
for yy in range(GRAD.height):
    c = heat(1 - yy / GRAD.height)
    ImageDraw.Draw(GRAD).line([(0, yy), (GRAD.width, yy)], fill=c + (255,))


def banner(d, title2):
    d.rounded_rectangle((60, 90, W - 60, 330), radius=36, fill=(255, 255, 255, 245))
    d.text((W // 2, 150), "RANKING FUNNIEST", font=fit("RANKING FUNNIEST", 78, 900), fill="black", anchor="mm")
    d.text((W // 2, 260), title2, font=fit(title2, 96, 900), fill=RED, anchor="mm")


def pill(d, rank, label, scale=1.0):
    text = f"#{rank}  {label}"
    f = fit(text, int(58 * scale), 860)
    w = f.getlength(text) + 70
    x0, y0 = (W - w) / 2, 360
    d.rounded_rectangle((x0, y0, x0 + w, y0 + 96 * scale), radius=48, fill=(0, 0, 0, 210))
    d.text((W / 2, y0 + 48 * scale), text, font=f, fill=YEL, anchor="mm")


def meter(im, level, broken=False, t=0.0):
    d = ImageDraw.Draw(im)
    dx = int(random.uniform(-9, 9)) if broken else 0
    x0, x1, y0, y1 = MX0 + dx, MX1 + dx, MY0, MY1
    # label
    for i, word in enumerate(["LAUGH", "METER"]):
        d.text(((x0 + x1) / 2, y0 - 92 + i * 40), word, font=font(34), fill="white", anchor="mm",
               stroke_width=6, stroke_fill="black")
    # tube
    d.rounded_rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), radius=52, fill=(0, 0, 0, 255))
    d.rounded_rectangle((x0, y0, x1, y1), radius=46, fill=(40, 40, 40, 230))
    # fill
    lv = max(0.0, min(1.0, level))
    if lv > 0:
        h = int(GRAD.height * lv)
        part = GRAD.crop((0, GRAD.height - h, GRAD.width, GRAD.height))
        mask = Image.new("L", part.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, part.width - 1, part.height - 1), radius=38, fill=255)
        im.paste(part, (x0 + 8, y1 - 8 - h), mask)
    # ticks
    for k in range(1, 4):
        yy = y1 - (y1 - y0) * k / 4
        d.line([(x0 + 10, yy), (x0 + 34, yy)], fill=(255, 255, 255, 200), width=5)
    # bulb
    cx, cy, r = (x0 + x1) / 2, y1 + 50, 70
    d.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill=(0, 0, 0, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=heat(lv) + (255,) if lv > 0 else (40, 40, 40, 230))
    d.text((cx, cy), f"{int(round(lv * 100))}%", font=font(40), fill="white", anchor="mm",
           stroke_width=5, stroke_fill="black")
    if broken:
        # cracks
        rnd = random.Random(7)
        for _ in range(5):
            px, py = rnd.uniform(x0 + 10, x1 - 10), rnd.uniform(y0 + 40, y0 + 300)
            pts = [(px, py)]
            for _ in range(4):
                px += rnd.uniform(-30, 30)
                py += rnd.uniform(20, 60)
                pts.append((px + dx, py))
            d.line(pts, fill="white", width=4)
        # flashing MAXED OUT
        if int(t * 6) % 2 == 0:
            d.text((W / 2 - 60, H - 430), "MAXED", font=font(130), fill=RED, anchor="mm",
                   stroke_width=12, stroke_fill="white")
            d.text((W / 2 - 60, H - 290), "OUT!", font=font(130), fill=RED, anchor="mm",
                   stroke_width=12, stroke_fill="white")
        # sparks over the top of the tube
        for k in range(10):
            a = rnd.uniform(0, math.pi * 2) + t * 3
            rr = 40 + 60 * ((t * 2 + k / 10) % 1)
            sx, sy = (x0 + x1) / 2 + math.cos(a) * rr, y0 + math.sin(a) * rr * 0.6
            d.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=YEL)


def make_clip(src, ss, ee, tmp, i, slow=1.0):
    seg = f"{tmp}/seg{i}.mp4"
    d = ee - ss
    out_d = d * slow
    if has_audio(src):
        ain, a = [], "0:a"
    else:
        ain, a = ["-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=44100:cl=stereo"], "1:a"
    vf = VF + (f",minterpolate=fps={FPS}:mi_mode=blend,setpts={slow}*PTS" if slow != 1 else "")
    af = "aresample=44100" + (",atempo=0.5,atempo=0.8" if slow == 2.5 else "")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{d}", "-i", src, *ain,
         "-filter_complex", f"[0:v]{vf},format=yuv420p[v];[{a}]{af},loudnorm=I=-16:TP=-1.5:LRA=11,"
                            f"aformat=channel_layouts=stereo[ao]",
         "-map", "[v]", "-map", "[ao]", "-t", f"{out_d}", *ENC, seg])
    return seg


def build(cfg):
    random.seed(1)
    tmp = tempfile.mkdtemp(prefix="laugh_")
    clips = cfg["clips"]
    n = len(clips)
    segs, starts, t = [], [], 0.0
    for i, (rank, label, src, ss, ee) in enumerate(clips):
        s = make_clip(src, ss, ee, tmp, i)
        segs.append(s)
        starts.append(t)
        t += dur(s)
    replay_start = None
    if cfg.get("replay"):
        src, rs, re_ = cfg["replay"]
        s = make_clip(src, rs, re_, tmp, "r", slow=2.5)
        segs.append(s)
        replay_start = t
        t += dur(s)
    total = t
    break_t = starts[-1] + RISE

    lst = f"{tmp}/list.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    base = f"{tmp}/base.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    # sounds: pop at each clip start, crash when the meter breaks
    pop, crash = f"{tmp}/pop.wav", f"{tmp}/crash.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=900:duration=0.12", "-af",
         "afade=t=out:st=0.02:d=0.10,asetrate=44100*1.4,aresample=44100,volume=0.9", pop])
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.6:c=white:a=0.9", "-af",
         "highpass=f=1500,afade=t=out:st=0.03:d=0.55,volume=1.2", crash])

    # overlay frames piped straight into the final encode
    nfr = int(round(total * FPS))
    sfx_in, sfx_f, k = [], [], 2
    for i, st in enumerate(starts):
        sfx_in += ["-i", pop]
        sfx_f.append(f"[{k}:a]adelay={int(st * 1000)}|{int(st * 1000)},aformat=channel_layouts=stereo[s{k}]")
        k += 1
    sfx_in += ["-i", crash]
    sfx_f.append(f"[{k}:a]adelay={int(break_t * 1000)}|{int(break_t * 1000)},aformat=channel_layouts=stereo[s{k}]")
    k += 1
    mix = "".join(f"[s{j}]" for j in range(2, k))
    fc = (f"[0:v][1:v]overlay=0:0,format=yuv420p[vo];" + ";".join(sfx_f) +
          f";[0:a]{mix}amix=inputs={k - 1}:duration=first:normalize=0[ao]")
    out = cfg["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-i", base,
                          "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          *sfx_in, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", *ENC,
                          "-movflags", "+faststart", f"{out}.mp4"], stdin=subprocess.PIPE)
    static = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    banner(ImageDraw.Draw(static), cfg["title2"])
    for fr in range(nfr):
        tt = fr / FPS
        i = max(j for j, st in enumerate(starts) if st <= tt + 1e-6)
        prev = i / n
        target = (i + 1) / n
        prog = min(1.0, (tt - starts[i]) / RISE)
        ease = 1 - (1 - prog) ** 3
        level = prev + (target - prev) * ease
        im = static.copy()
        rank, label = clips[i][0], clips[i][1]
        pop_in = min(1.0, (tt - starts[i]) / 0.15)
        pill(ImageDraw.Draw(im), rank, label, scale=0.85 + 0.15 * pop_in)
        meter(im, level, broken=tt >= break_t, t=tt - break_t)
        p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()

    # thumbnail: #1 frame + maxed meter
    src, tsec = cfg["thumb"]
    bgp = f"{tmp}/thumb_bg.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tsec}", "-i", src, "-frames:v", "1", "-vf", VF, bgp])
    bg = Image.open(bgp).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    banner(ImageDraw.Draw(lay), cfg["title2"])
    meter(lay, 1.0, broken=True, t=0.2)  # t=0.2 -> flash frame off, tease takes the bottom
    tease = cfg.get("tease", "#1 BROKE THE METER")
    ImageDraw.Draw(lay).text((W // 2, 1700), tease, font=fit(tease, 110, 980), fill=YEL, anchor="mm",
                             stroke_width=10, stroke_fill="black")
    Image.alpha_composite(bg, lay).convert("RGB").save(f"{out}_thumb.png")
    print(f"{out}.mp4  ({total:.1f}s)")


if __name__ == "__main__":
    build(json.load(open(sys.argv[1])))
