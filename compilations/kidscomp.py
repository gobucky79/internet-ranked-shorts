"""Reusable builder for "Ranking Funniest Kids ____" compilation Shorts.

Usage: python3 kidscomp.py <config.json>
Config keys:
  title2   second title line, e.g. "KIDS TRYING LEMON" (first line is always "RANKING FUNNIEST")
  clips    list of [rank, label, source_path, start, end], played in list order (#4 first, #1 last)
  replay   optional [source_path, start, end] slow-mo replay appended after the last clip
  thumb    [source_path, time] frame used for the thumbnail
  tease    thumbnail caption, e.g. "#1 IS BRUTAL"
  list_y   optional y of the ranking list (default 1300, lower third, away from faces)
  out      output path prefix (writes <out>.mp4 and <out>_thumb.png)
Needs Python 3 + Pillow + ffmpeg and Poppins Bold.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
YEL = (255, 214, 0)


def font(sz):
    return ImageFont.truetype(BOLD, sz)


def fit(text, start, maxw):
    sz = start
    while sz > 30 and font(sz).getlength(text) > maxw:
        sz -= 2
    return font(sz)


def outlined(d, xy, text, f, fill, stroke=8, anchor="la"):
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill="black", anchor=anchor)


def banner(d, title2):
    d.rounded_rectangle((60, 90, W - 60, 330), radius=36, fill=(255, 255, 255, 245))
    d.text((W // 2, 150), "RANKING FUNNIEST", font=fit("RANKING FUNNIEST", 78, 900), fill="black", anchor="mm")
    d.text((W // 2, 260), title2, font=fit(title2, 96, 900), fill=(230, 30, 40), anchor="mm")


def overlay(cfg, stage):
    clips = cfg["clips"]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    banner(d, cfg["title2"])
    revealed = {c[0]: c[1] for c in clips[: stage + 1]}
    current = clips[stage][0]
    n = len(clips)
    for i, rank in enumerate(range(1, n + 1)):
        y = cfg.get("list_y", 1300) + i * 120
        col = YEL if rank == current else "white"
        outlined(d, (50, y), f"{rank}.", font(70), col)
        if rank in revealed:
            outlined(d, (140, y + 14), revealed[rank], font(48), col, stroke=7)
    return im


def run(cmd):
    subprocess.run(cmd, check=True)


def has_audio(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                        "stream=index", "-of", "csv=p=0", src], capture_output=True, text=True)
    return bool(r.stdout.strip())


VF = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "44100"]


def audio_in(src, ss, dur):
    """Returns ffmpeg input args for the clip audio (real or silent)."""
    if has_audio(src):
        return []
    return ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo"]


def build(cfg):
    tmp = tempfile.mkdtemp(prefix="kidscomp_")
    pop = f"{tmp}/pop.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=900:duration=0.12", "-af",
         "afade=t=out:st=0.02:d=0.10,asetrate=44100*1.4,aresample=44100,volume=0.9", pop])
    segs = []
    for i, (rank, label, src, ss, ee) in enumerate(cfg["clips"]):
        png = f"{tmp}/ov{i}.png"
        overlay(cfg, i).save(png)
        dur = ee - ss
        extra = audio_in(src, ss, dur)
        a = "3:a" if extra else "0:a"
        seg = f"{tmp}/seg{i}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{dur}", "-i", src,
             "-loop", "1", "-t", f"{dur}", "-i", png, "-i", pop, *extra,
             "-filter_complex",
             f"[0:v]{VF}[v];[1:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1[o];"
             f"[v][o]overlay=0:0:shortest=1,format=yuv420p[vo];"
             f"[{a}]aresample=44100,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[a0];"
             f"[2:a]aformat=channel_layouts=stereo[p];[a0][p]amix=inputs=2:duration=first:normalize=0[ao]",
             "-map", "[vo]", "-map", "[ao]", "-t", f"{dur}", *ENC, seg])
        segs.append(seg)

    if cfg.get("replay"):
        src, rs, re_ = cfg["replay"]
        im = overlay(cfg, len(cfg["clips"]) - 1)
        outlined(ImageDraw.Draw(im), (W // 2, cfg.get("list_y", 1300) - 110), "SLOW-MO", font(100), YEL, stroke=10, anchor="mm")
        png = f"{tmp}/ov_replay.png"
        im.save(png)
        rdur = (re_ - rs) * 2.5
        extra = audio_in(src, rs, re_ - rs)
        a = "2:a" if extra else "0:a"
        seg = f"{tmp}/seg_replay.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{rs}", "-t", f"{re_ - rs}", "-i", src,
             "-loop", "1", "-t", f"{rdur}", "-i", png, *extra,
             "-filter_complex",
             f"[0:v]{VF},minterpolate=fps=30:mi_mode=blend,setpts=2.5*PTS[v];"
             f"[v][1:v]overlay=0:0,format=yuv420p[vo];"
             f"[{a}]aresample=44100,atempo=0.5,atempo=0.8,loudnorm=I=-16:TP=-1.5:LRA=11,"
             f"aformat=channel_layouts=stereo[ao]",
             "-map", "[vo]", "-map", "[ao]", "-t", f"{rdur}", *ENC, seg])
        segs.append(seg)

    lst = f"{tmp}/list.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    out = cfg["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, *ENC,
         "-movflags", "+faststart", f"{out}.mp4"])

    src, t = cfg["thumb"]
    bgp = f"{tmp}/thumb_bg.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", src, "-frames:v", "1", "-vf", VF, bgp])
    bg = Image.open(bgp).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    banner(d, cfg["title2"])
    outlined(d, (W // 2, 1650), cfg.get("tease", "#1 IS INSANE"), fit(cfg.get("tease", "#1 IS INSANE"), 110, 980),
             YEL, stroke=10, anchor="mm")
    Image.alpha_composite(bg, lay).convert("RGB").save(f"{out}_thumb.png")
    print(f"{out}.mp4")


if __name__ == "__main__":
    build(json.load(open(sys.argv[1])))
