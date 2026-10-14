"""Ranking Funniest Kids Fails - compilation builder.
# Run from a folder containing src/{easy,flip,candles,skate}.mp4 (the creator downloads the clips).
Usage: python3 build.py  -> out/kids_fails.mp4
"""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
BOLD = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
OUT = "out"
os.makedirs(OUT, exist_ok=True)
os.makedirs("tmp", exist_ok=True)

TITLE = ["RANKING FUNNIEST", "KIDS FAILS"]
# (rank, label, source, start, end)  -- played #4 first, #1 last
CLIPS = [
    (4, "Belly flop baby", "src/easy.mp4", 15.50, 20.25),
    (3, "The \"flip\"", "src/flip.mp4", 16.70, 19.95),
    (2, "Candle thief", "src/candles.mp4", 11.25, 15.20),
    (1, "Mega ramp drop", "src/skate.mp4", 36.50, 40.80),
]


def font(sz):
    return ImageFont.truetype(BOLD, sz)


def outlined(d, xy, text, f, fill, stroke=8, anchor="la"):
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill="black", anchor=anchor)


def overlay(stage):
    """stage = index into CLIPS currently playing; ranks revealed so far are shown."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # title banner
    d.rounded_rectangle((60, 90, W - 60, 330), radius=36, fill=(255, 255, 255, 245))
    ft = font(78)
    d.text((W // 2, 150), TITLE[0], font=ft, fill="black", anchor="mm")
    d.text((W // 2, 260), TITLE[1], font=font(96), fill=(230, 30, 40), anchor="mm")
    # ranking list, left side
    revealed = {c[0]: c[1] for c in CLIPS[: stage + 1]}
    current = CLIPS[stage][0]
    fn, fl = font(70), font(48)
    y0 = 560
    for i, rank in enumerate([1, 2, 3, 4]):
        y = y0 + i * 130
        col = (255, 214, 0) if rank == current else "white"
        outlined(d, (50, y), f"{rank}.", fn, col)
        if rank in revealed:
            outlined(d, (140, y + 14), revealed[rank], fl, col, stroke=7)
    return im


def run(cmd):
    subprocess.run(cmd, check=True)


# pop sound (short pitched blip)
run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
     "sine=frequency=900:duration=0.12", "-af",
     "afade=t=out:st=0.02:d=0.10,asetrate=44100*1.4,aresample=44100,volume=0.9",
     "tmp/pop.wav"])

segs = []
for i, (rank, label, src, ss, ee) in enumerate(CLIPS):
    png = f"tmp/ov{i}.png"
    overlay(i).save(png)
    seg = f"tmp/seg{i}.mp4"
    dur = ee - ss
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{dur}", "-i", src,
         "-loop", "1", "-t", f"{dur}", "-i", png, "-i", "tmp/pop.wav",
         "-filter_complex",
         f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,setsar=1[v];"
         f"[1:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1[o];"
         f"[v][o]overlay=0:0:shortest=1,format=yuv420p[vo];"
         f"[0:a]aresample=44100,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[a0];"
         f"[2:a]aformat=channel_layouts=stereo[p];"
         f"[a0][p]amix=inputs=2:duration=first:normalize=0[ao]",
         "-map", "[vo]", "-map", "[ao]", "-t", f"{dur}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
         "-ar", "44100", seg])
    segs.append(seg)

# slow-mo replay of the #1 fall
rs, re_ = 39.85, 40.80
im = overlay(len(CLIPS) - 1)
outlined(ImageDraw.Draw(im), (W // 2, 1600), "SLOW-MO", font(100), (255, 214, 0), stroke=10, anchor="mm")
im.save("tmp/ov_replay.png")
rdur = (re_ - rs) * 2.5
run(["ffmpeg", "-v", "error", "-y", "-ss", f"{rs}", "-t", f"{re_ - rs}", "-i", "src/skate.mp4",
     "-loop", "1", "-t", f"{rdur}", "-i", "tmp/ov_replay.png",
     "-filter_complex",
     f"[0:v]scale={W}:{H},fps=30,minterpolate=fps=30:mi_mode=blend,setpts=2.5*PTS,setsar=1[v];"
     f"[v][1:v]overlay=0:0,format=yuv420p[vo];"
     f"[0:a]aresample=44100,atempo=0.5,atempo=0.8,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[ao]",
     "-map", "[vo]", "-map", "[ao]", "-t", f"{rdur}",
     "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
     "-ar", "44100", "tmp/seg_replay.mp4"])
segs.append("tmp/seg_replay.mp4")

with open("tmp/list.txt", "w") as f:
    for s in segs:
        f.write(f"file '{os.path.abspath(s)}'\n")
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "tmp/list.txt",
     "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
     "-movflags", "+faststart", f"{OUT}/kids_fails.mp4"])

# thumbnail: #1 moment frame + title
run(["ffmpeg", "-v", "error", "-y", "-ss", "40.2", "-i", "src/skate.mp4", "-frames:v", "1",
     "-vf", f"scale={W}:{H}", "tmp/thumb_bg.png"])
bg = Image.open("tmp/thumb_bg.png").convert("RGBA")
t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(t)
d.rounded_rectangle((60, 90, W - 60, 330), radius=36, fill=(255, 255, 255, 245))
d.text((W // 2, 150), TITLE[0], font=font(78), fill="black", anchor="mm")
d.text((W // 2, 260), TITLE[1], font=font(96), fill=(230, 30, 40), anchor="mm")
outlined(d, (W // 2, 1650), "#1 IS BRUTAL", font(110), (255, 214, 0), stroke=10, anchor="mm")
Image.alpha_composite(bg, t).convert("RGB").save(f"{OUT}/kids_fails_thumb.png")
print("done")
