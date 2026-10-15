""""Vine Boom" format for "Ranking Funniest ____" Shorts.

Opens on a black card with a vine boom and big "FUNNY ___" text, then after every clip the same black boom card hits
again. During clips: title banner + "#N label" bar + @InternetRanked-x4p watermark. Ends on a boom card.

Usage: python3 vineboom.py <config.json>
Config keys:
  title2   second title line on the banner, e.g. "DOGS BEING DRAMATIC"
  card     text on the black boom cards (default "FUNNY " + title2), e.g. "FUNNY DOGS"
  clips    [[rank, label, src, start, end], ...] played in order (#4 first, #1 last); a clip may add a 6th element
           to override the card text shown after it
  replay   optional [src, start, end] slow-mo replay of the #1 moment, before the last card
  thumb    [src, time]   tease   thumbnail caption   out   output prefix
  boom     optional path to the card sound; default is sounds/mentality.mp3 (the creator's sound), falling back to a
           synthesized boom if that file is missing
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
YEL, RED = (255, 214, 0), (230, 30, 40)
CARD = 0.9
WATERMARK = "@InternetRanked-x4p"
VF = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "9M", "-bufsize", "18M",
       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]


def font(sz):
    return ImageFont.truetype(BOLD, sz)


def fit(text, start, maxw):
    sz = start
    while sz > 30 and font(sz).getlength(text) > maxw:
        sz -= 2
    return font(sz)


def run(cmd):
    subprocess.run(cmd, check=True)


def has_audio(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", src], capture_output=True, text=True)
    return bool(r.stdout.strip())


def watermark(d):
    d.text((72, 50), WATERMARK, font=font(36), fill=(255, 255, 255, 165), anchor="lm",
           stroke_width=3, stroke_fill=(0, 0, 0, 120))


def banner(d, title2):
    watermark(d)
    d.rounded_rectangle((60, 90, W - 60, 330), radius=36, fill=(255, 255, 255, 245))
    d.text((W // 2, 150), "RANKING FUNNIEST", font=fit("RANKING FUNNIEST", 78, 900), fill="black", anchor="mm")
    d.text((W // 2, 260), title2, font=fit(title2, 96, 900), fill=RED, anchor="mm")


def rank_bar(d, rank, label):
    text = f"#{rank}  {label}"
    f = fit(text, 54, 860)
    w = f.getlength(text) + 80
    x0 = (W - w) / 2
    d.rounded_rectangle((x0, 350, x0 + w, 446), radius=48, fill=(0, 0, 0, 215))
    d.text((W / 2, 398), text, font=f, fill=YEL, anchor="mm")


def wrap(text, maxw, start=150):
    """split card text into 1-3 lines that fit, biggest font possible"""
    words = text.split()
    for sz in range(start, 60, -4):
        f = font(sz)
        lines, cur = [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if f.getlength(t) <= maxw:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if len(lines) <= 3 and all(f.getlength(l) <= maxw for l in lines):
            return f, lines
    return font(60), [text]


def card_png(text, path):
    im = Image.new("RGB", (W, H), "black")
    d = ImageDraw.Draw(im)
    f, lines = wrap(text.upper(), 940)
    lh = f.size * 1.15
    y0 = H / 2 - lh * (len(lines) - 1) / 2
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + i * lh), l, font=f, fill="white", anchor="mm")
    watermark(d)
    im.save(path)


def make_boom(path):
    # deep pitch-dropping bass hit + click, saturated, with a short room tail
    expr = ("(0.95*sin(2*PI*(62-26*t)*t)*exp(-2.6*t)+0.45*sin(2*PI*(124-52*t)*t)*exp(-5*t)"
            "+0.25*sin(2*PI*31*t)*exp(-1.8*t))*min(1,t*400)")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d=1.4",
         "-af", "volume=2.2,asoftclip=type=tanh,aecho=0.8:0.6:45|90:0.35|0.2,volume=1.4,afade=t=out:st=1.0:d=0.4,"
                "aformat=channel_layouts=stereo",
         path])


def build(cfg):
    tmp = tempfile.mkdtemp(prefix="vineboom_")
    here = os.path.dirname(os.path.abspath(__file__))
    src_sound = cfg.get("boom") or os.path.join(here, "sounds", "mentality.mp3")
    boom = f"{tmp}/boom.wav"
    if os.path.exists(src_sound):
        # trim the leading silence so the sound hits exactly on the cut to black
        run(["ffmpeg", "-v", "error", "-y", "-i", src_sound, "-af",
             "silenceremove=start_periods=1:start_threshold=-45dB,aresample=44100,aformat=channel_layouts=stereo,"
             "loudnorm=I=-14:TP=-1:LRA=7", boom])
    else:
        make_boom(boom)
    title2 = cfg["title2"]
    default_card = cfg.get("card") or f"FUNNY {title2}"

    def card_seg(text, name):
        png, seg = f"{tmp}/card_{name}.png", f"{tmp}/seg_card_{name}.mp4"
        card_png(text, png)
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{CARD}", "-i", png, "-i", boom,
             "-filter_complex", f"[0:v]fps={FPS},format=yuv420p[v];[1:a]atrim=0:{CARD},asetpts=PTS-STARTPTS,"
                                f"aformat=channel_layouts=stereo[a]",
             "-map", "[v]", "-map", "[a]", "-t", f"{CARD}", *ENC, seg])
        return seg

    def clip_seg(src, ss, ee, rank, label, name, slow=1.0):
        png, seg = f"{tmp}/ov_{name}.png", f"{tmp}/seg_{name}.mp4"
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        banner(d, title2)
        rank_bar(d, rank, label)
        if slow != 1:
            d.text((W / 2, H - 300), "SLOW-MO", font=font(110), fill=YEL, anchor="mm", stroke_width=10,
                   stroke_fill="black")
        im.save(png)
        dur = ee - ss
        out_d = dur * slow
        ain, a = ([], "0:a") if has_audio(src) else (
            ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo"], "2:a")
        vf = VF + (f",minterpolate=fps={FPS}:mi_mode=blend,setpts={slow}*PTS" if slow != 1 else "")
        af = "aresample=44100" + (",atempo=0.5,atempo=0.8" if slow == 2.5 else "")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{dur}", "-i", src,
             "-loop", "1", "-t", f"{out_d}", "-i", png, *ain,
             "-filter_complex", f"[0:v]{vf}[v];[v][1:v]overlay=0:0,format=yuv420p[vo];"
                                f"[{a}]{af},loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[ao]",
             "-map", "[vo]", "-map", "[ao]", "-t", f"{out_d}", *ENC, seg])
        return seg

    segs = [card_seg(default_card, "open")]
    clips = cfg["clips"]
    for i, c in enumerate(clips):
        rank, label, src, ss, ee = c[:5]
        segs.append(clip_seg(src, ss, ee, rank, label, str(i)))
        last = i == len(clips) - 1
        if last and cfg.get("replay"):
            rs, rsrc = cfg["replay"][1:], cfg["replay"][0]
            segs.append(clip_seg(rsrc, rs[0], rs[1], rank, label, "replay", slow=2.5))
        segs.append(card_seg(c[5] if len(c) > 5 else default_card, f"after{i}"))

    lst = f"{tmp}/list.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    out = cfg["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, *ENC, "-movflags", "+faststart",
         f"{out}.mp4"])

    tsrc, tsec = cfg["thumb"]
    bgp = f"{tmp}/thumb_bg.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tsec}", "-i", tsrc, "-frames:v", "1", "-vf", VF, bgp])
    bg = Image.open(bgp).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    banner(d, title2)
    tease = cfg.get("tease", "WAIT FOR #1")
    d.text((W // 2, 1700), tease, font=fit(tease, 110, 980), fill=YEL, anchor="mm", stroke_width=10,
           stroke_fill="black")
    Image.alpha_composite(bg, lay).convert("RGB").save(f"{out}_thumb.png")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                f"{out}.mp4"], capture_output=True, text=True).stdout)
    print(f"{out}.mp4  ({dur:.1f}s)")


if __name__ == "__main__":
    build(json.load(open(sys.argv[1])))
