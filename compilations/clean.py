"""Clean format for "Ranking Funniest ____" Shorts (default since 2026-10-15, audience: mostly middle-aged).

Straight cuts from clip to clip, #4 first and #1 last. No black cards, no added sound effects: the only audio is the
clips' own sound (loudness-matched so no clip is jarringly louder than the next). During clips: title banner,
"#N label" bar and the @InternetRanked-x4p watermark.

Usage: python3 clean.py <config.json>
Config keys (same as vineboom.py; `card` and `boom` are ignored):
  title2   second title line on the banner, e.g. "BABIES TRYING LEMON"
  clips    [[rank, label, src, start, end], ...] played in order (#4 first, #1 last)
  replay   optional [src, start, end] slow-mo replay of the #1 moment (silent slow-mo, no sound effect)
  thumb    [src, time]   tease   thumbnail caption   out   output prefix
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vineboom import W, H, FPS, YEL, VF, ENC, font, fit, run, has_audio, banner, rank_bar  # noqa: E402


def build(cfg):
    tmp = tempfile.mkdtemp(prefix="clean_")
    title2 = cfg["title2"]

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
            ["-f", "lavfi", "-t", f"{out_d}", "-i", "anullsrc=r=44100:cl=stereo"], "2:a")
        vf = VF + (f",minterpolate=fps={FPS}:mi_mode=blend,setpts={slow}*PTS" if slow != 1 else "")
        if slow != 1:   # slow-mo plays silent rather than with stretched audio
            ain, a = ["-f", "lavfi", "-t", f"{out_d}", "-i", "anullsrc=r=44100:cl=stereo"], "2:a"
            af = "aresample=44100"
        else:
            af = "aresample=44100,loudnorm=I=-16:TP=-1.5:LRA=11"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss}", "-t", f"{dur}", "-i", src,
             "-loop", "1", "-t", f"{out_d}", "-i", png, *ain,
             "-filter_complex", f"[0:v]{vf}[v];[v][1:v]overlay=0:0,format=yuv420p[vo];"
                                f"[{a}]{af},aformat=channel_layouts=stereo[ao]",
             "-map", "[vo]", "-map", "[ao]", "-t", f"{out_d}", *ENC, seg])
        return seg

    segs = []
    clips = cfg["clips"]
    for i, c in enumerate(clips):
        rank, label, src, ss, ee = c[:5]
        segs.append(clip_seg(src, ss, ee, rank, label, str(i)))
    if cfg.get("replay"):
        rank, label = clips[-1][:2]
        rsrc, rs, re_ = cfg["replay"]
        segs.append(clip_seg(rsrc, rs, re_, rank, label, "replay", slow=2.5))

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
