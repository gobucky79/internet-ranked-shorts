"""Internet Ranked Shorts engine.

Usage:
  python3 engine.py script  topics/<slug>.py            # print voiceover script + metadata
  python3 engine.py video   topics/<slug>.py audio.mp3 out.mp4
  python3 engine.py thumb   topics/<slug>.py out.png
  python3 engine.py preview topics/<slug>.py out.png     # contact sheet of scenes (no audio needed)
  python3 engine.py sheet   out.mp4 out.png              # contact sheet of 10 frames from a rendered video

A topic file defines the ranking (4 items), the script lines, the drawings and the metadata.
See topics/plane_features.py for a complete example and README.md for the rules.
"""
import math, re, subprocess, sys, importlib.util, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
def F(sz): return ImageFont.truetype(FONT, sz)
YEL = (255, 214, 10); RED = (255, 59, 48); WHITE = (255, 255, 255)
NUMWORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}

# ---------------------------------------------------------------- helpers for topic drawings
S = 2  # supersample factor for base drawings
def canvas():
    im = Image.new("RGBA", (800*S, 800*S), (0,0,0,0)); return im, ImageDraw.Draw(im)
def sc(*v): return [x*S for x in v]
def fin(im): return im.resize((800, 800), Image.LANCZOS)
def ease_back(x):
    x = min(max(x, 0), 1); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def ease_out(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def load_topic(path):
    spec = importlib.util.spec_from_file_location("topic", path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

# ---------------------------------------------------------------- script
def phrases(T):
    """Ordered list of (kind, rank, text). Voiceover = these joined with spaces."""
    out = [("hook", None, T.HOOK)]
    for it in T.ITEMS:  # ITEMS ordered #4 -> #1
        num = ("And number " if it["rank"] == 1 else "Number ") + NUMWORD[it["rank"]] + ":"
        out += [("num", it["rank"], num), ("what", it["rank"], it["what"]), ("why", it["rank"], it["why"])]
    out.append(("outro", None, T.OUTRO))
    return out

def vo_script(T):
    ph = phrases(T); lines = [T.HOOK]
    for it in T.ITEMS:
        num = ("And number " if it["rank"] == 1 else "Number ") + NUMWORD[it["rank"]] + ":"
        lines.append(f"{num} {it['what']} {it['why']}")
    lines.append(T.OUTRO)
    return "\n\n".join(lines)

# ---------------------------------------------------------------- audio alignment
def silences(audio):
    r = subprocess.run(["ffmpeg", "-i", audio, "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    return list(zip(st, en))

def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())

NUM_W = 20
def syllables(text):
    n = 0
    for w in re.findall(r"[a-zA-Z']+", text.lower()):
        k = len(re.findall(r"[aeiouy]+", w))
        if w.endswith("e") and k > 1 and not w.endswith("le"): k -= 1
        n += max(1, k)
    return n

def align(T, audio):
    """Start/end of every phrase.
    1) Coarse units (hook, 'Number X:', item body, outro) are matched to pauses with a best-fit search:
       unit lengths should match their syllable share, and 'Number X:' units are short (~0.75s).
    2) Each body is split into what/why by syllable share, snapped to an internal pause if one is close."""
    ph = phrases(T); dur = duration(audio); raw = silences(audio)
    lead = raw[0][1] if raw and raw[0][0] <= 0.05 else 0.0
    tail = raw[-1][0] if raw and raw[-1][1] >= dur - 0.05 else dur
    inner = [s for s in raw if s[0] > 0.05 and s[1] < dur - 0.05]
    sil = [(lead, lead)] + inner + [(tail, tail)]
    units = []                                   # (kind, [phrase indexes])
    i = 0
    while i < len(ph):
        if ph[i][0] == "what": units.append(("body", [i, i+1])); i += 2
        else: units.append((ph[i][0], [i])); i += 1
    U = len(units); n = len(sil)
    wts = [sum(syllables(ph[k][2]) for k in idx) + 1.5 for _, idx in units]; rate = (tail - lead) / sum(wts)
    mid = [(a + b) / 2 for a, b in sil]; mid[0], mid[-1] = lead, tail
    def cost(u, j0, j1):
        span = mid[j1] - mid[j0]; exp = wts[u] * rate
        c = (span - exp) ** 2 / exp
        if units[u][0] == "num": c += NUM_W * ((sil[j1][0] - sil[j0][1]) - 0.75) ** 2
        return c
    INF = float("inf"); best = [[INF]*n for _ in range(U+1)]; prev = [[-1]*n for _ in range(U+1)]
    best[0][0] = 0.0
    for u in range(U):
        for j0 in range(n):
            if best[u][j0] == INF: continue
            for j1 in range(j0+1, n):
                if (j1 == n-1) != (u == U-1): continue
                c = best[u][j0] + cost(u, j0, j1)
                if c < best[u+1][j1]: best[u+1][j1] = c; prev[u+1][j1] = j0
    if best[U][n-1] == INF:
        cum = [0]
        for w in wts: cum.append(cum[-1] + w)
        us = [lead + (tail-lead) * cum[u] / cum[-1] for u in range(U)]; ue = us[1:] + [tail]
    else:
        path = [n-1]
        for u in range(U, 0, -1): path.append(prev[u][path[-1]])
        path = path[::-1]
        us = [sil[path[u]][1] for u in range(U)]; ue = [sil[path[u+1]][0] for u in range(U)]
    starts = [0.0]*len(ph); ends = [0.0]*len(ph)
    for (kind, idx), s0, e0 in zip(units, us, ue):
        if kind != "body":
            starts[idx[0]], ends[idx[0]] = s0, e0; continue
        sw, sy = syllables(ph[idx[0]][2]) + 0.5, syllables(ph[idx[1]][2]) + 0.5
        est = s0 + (e0 - s0) * sw / (sw + sy)
        near = [s for s in inner if s0 < s[0] and s[1] < e0 and abs((s[0]+s[1])/2 - est) < 0.8]
        if near:
            s = min(near, key=lambda s: abs((s[0]+s[1])/2 - est)); split_e, split_s = s[0], s[1]
        else:
            split_e = split_s = est
        starts[idx[0]], ends[idx[0]] = s0, split_e
        starts[idx[1]], ends[idx[1]] = split_s, e0
    return [(k, r, txt, s, e) for (k, r, txt), s, e in zip(ph, starts, ends)], dur

# ---------------------------------------------------------------- rendering pieces
def make_bg(T):
    top, bot, glowc = T.PALETTE["top"], T.PALETTE["bottom"], T.PALETTE["glow"]
    bg = Image.new("RGB", (W, H)); bd = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H; bd.line((0, y, W, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))
    glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse((140, 760, 940, 1560), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    return Image.composite(Image.new("RGB", (W, H), glowc), bg, glow)

def fit_font(text, max_w, start):
    sz = start
    while sz > 30 and F(sz).getlength(text) + 18 > max_w: sz -= 2
    return F(sz)

ROW_Y = {1: 400, 2: 505, 3: 610, 4: 715}
def draw_list(frame, T, t, reveal, hook_flash, recap=False):
    d = ImageDraw.Draw(frame, "RGBA"); active = None
    for rk, rt in reveal.items():
        if t >= rt and (active is None or rt >= reveal[active]): active = rk
    labels = {it["rank"]: it["label"].upper() for it in T.ITEMS}
    for rank in (1, 2, 3, 4):
        y = ROW_Y[rank]; is_active = rank == active and not recap
        d.rounded_rectangle((110, y, 970, y+88), radius=22, fill=(255,214,10,235) if is_active else (0,0,0,120), outline=(255,255,255,70), width=3)
        d.text((150, y+44), f"#{rank}", font=F(56), fill=(0,0,0) if is_active else YEL, anchor="lm")
        if t >= reveal[rank]:
            p = ease_out((t - reveal[rank]) / 0.25); col = (0,0,0) if is_active else WHITE
            d.text((260 + (1-p)*500, y+44), labels[rank], font=fit_font(labels[rank], 690, 56), fill=col+(int(255*p),), anchor="lm")
        else:
            col = (RED if int(t*6) % 2 == 0 else WHITE) if rank == 1 and hook_flash[0] <= t < hook_flash[1] else WHITE
            d.text((260, y+44), "???", font=F(56), fill=col, anchor="lm")
    if recap:
        pr = (math.sin(t*8)+1)/2
        d.rounded_rectangle((104, ROW_Y[1]-6, 976, ROW_Y[4]+94), radius=26, outline=(255,214,10,int(150+100*pr)), width=6)

FCAP = F(74)
def caption_img(words, key):
    lines, cur = [], []
    for w in words:
        if cur and FCAP.getlength(" ".join(cur+[w])) > 900: lines.append(cur); cur = [w]
        else: cur.append(w)
    lines.append(cur)
    im = Image.new("RGBA", (W, 110*len(lines)+40), (0,0,0,0)); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        x = (W - FCAP.getlength(" ".join(ln)))/2; y = 75 + i*110
        for w in ln:
            core = ''.join(c for c in w if c.isalpha())
            d.text((x, y), w, font=FCAP, fill=YEL if core in key else WHITE, stroke_width=10, stroke_fill=(0,0,0), anchor="lm")
            x += FCAP.getlength(w + " ")
    return im

def title_layer(T):
    im = Image.new("RGBA", (W, 330), (0,0,0,0)); d = ImageDraw.Draw(im)
    l1, l2 = T.VIDEO_TITLE
    d.text((540, 120), l1.upper(), font=fit_font(l1.upper(), 1000, 82), fill=WHITE, stroke_width=9, stroke_fill=(0,0,0), anchor="mm")
    d.text((540, 225), l2.upper(), font=fit_font(l2.upper(), 1000, 68), fill=YEL, stroke_width=9, stroke_fill=(0,0,0), anchor="mm")
    return im

class Scenes:
    """Base drawings + per-frame overlay (animation, pulse ring)."""
    def __init__(self, T):
        self.T = T
        self.base = {"intro": T.draw_intro()}
        for it in T.ITEMS: self.base[it["rank"]] = it["draw"]()
    def frame(self, key, lt, e, pulse=True):
        """key: 'intro' or rank. lt: seconds into scene. e: seconds since the 'why' phrase (negative = not yet)."""
        img = self.base[key].copy(); lay = Image.new("RGBA", img.size, (0,0,0,0)); d = ImageDraw.Draw(lay)
        it = None if key == "intro" else next(i for i in self.T.ITEMS if i["rank"] == key)
        anim = (self.T.animate_intro if key == "intro" and hasattr(self.T, "animate_intro") else (it.get("animate") if it else None))
        fp = (getattr(self.T, "INTRO_FOCUS", None) if key == "intro" else it.get("focus"))
        if anim:
            res = anim(img, d, lt, e)          # may return None, a new image, or (image_or_None, focus_or_None)
            if isinstance(res, Image.Image): img = res
            elif isinstance(res, tuple):
                if res[0] is not None: img = res[0]
                if len(res) > 1 and res[1] is not None: fp = res[1]
        if pulse and fp:
            hx, hy = fp
            for k in range(2):
                p = ((lt*1.25 + k*0.5) % 1.0); r = 24 + p*70; a = int(255*(1-p))
                d.ellipse((hx-r, hy-r, hx+r, hy+r), outline=YEL+(a,), width=7)
            d.ellipse((hx-26, hy-26, hx+26, hy+26), outline=RED+(255,), width=6)
        return Image.alpha_composite(img, lay)
    def icon(self, rank):
        return self.frame(rank, 0, -1, pulse=False)

def build_timeline(T, audio):
    al, dur = align(T, audio)
    reveal, why = {}, {}
    hook_flash = (al[0][3] + (al[0][4]-al[0][3])*0.5, None)
    for k, r, txt, s, e in al:
        if k == "num": reveal[r] = s
        if k == "why": why[r] = s
    outro = al[-1][3]
    hook_flash = (hook_flash[0], reveal[T.ITEMS[0]["rank"]])
    caps = []
    for k, r, txt, s, e in al:
        words = txt.upper().split()
        n = max(1, math.ceil(len(words)/5)); per = math.ceil(len(words)/n)
        pieces = [words[i:i+per] for i in range(0, len(words), per)]
        total = sum(len(" ".join(p)) for p in pieces); t = s
        for p in pieces: caps.append((t, p)); t += (e - s) * len(" ".join(p)) / total
    return dict(al=al, dur=dur, reveal=reveal, why=why, outro=outro, hook_flash=hook_flash, caps=caps)

def render_video(T, audio, out):
    tl = build_timeline(T, audio); sc_ = Scenes(T)
    for k, r, txt, s, e in tl["al"]: print(f"{s:6.2f}-{e:6.2f} {k:5} {txt}")
    bg = make_bg(T); tlay = title_layer(T); bg.paste(tlay, (0, 30), tlay)
    key = set(w.upper() for w in getattr(T, "KEYWORDS", [])) | {"NUMBER","ONE","TWO","THREE","FOUR"}
    capimgs = [caption_img(w, key) for _, w in tl["caps"]]
    order = [(0.0, "intro")] + [(tl["reveal"][it["rank"]], it["rank"]) for it in T.ITEMS] + [(tl["outro"], "outro")]
    icons = {it["rank"]: sc_.icon(it["rank"]) for it in T.ITEMS}
    icon_pos = [(330, 1000), (750, 1000), (330, 1330), (750, 1330)]
    pops = [int(tl["reveal"][it["rank"]]*1000) for it in T.ITEMS]
    fc = ("aevalsrc='0.5*sin(2*PI*(500+700*exp(-t*35))*t)*exp(-t*22)':d=0.25:s=44100,asplit=4[p1][p2][p3][p4];" +
          "".join(f"[p{i+1}]adelay={ms}|{ms}[a{i+1}];" for i, ms in enumerate(pops)) +
          "[1:a]aresample=44100[v];[v][a1][a2][a3][a4]amix=inputs=5:normalize=0:duration=first[aout]")
    ff = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
        "-i","-","-i",audio,"-filter_complex",fc,"-map","0:v","-map","[aout]","-c:v","libx264","-preset","medium","-crf","18",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",out], stdin=subprocess.PIPE)
    for i in range(int(tl["dur"]*FPS)):
        t = i / FPS; fr = bg.copy()
        st, name = [o for o in order if t >= o[0]][-1]; lt = t - st
        if name == "outro":
            draw_list(fr, T, t, tl["reveal"], tl["hook_flash"], recap=True)
            for k, it in enumerate(sorted(T.ITEMS, key=lambda x: -x["rank"])):
                cx, cy = icon_pos[k]; sz = int(340 * max(ease_back((lt - k*0.08)/0.35), 0.01))
                if sz > 4:
                    ic = icons[it["rank"]].resize((sz, sz), Image.LANCZOS); fr.paste(ic, (cx-sz//2, cy-sz//2), ic)
        else:
            draw_list(fr, T, t, tl["reveal"], tl["hook_flash"])
            e = (t - tl["why"][name]) if name != "intro" else -1
            s = 0.3 + 0.7*ease_back(lt/0.35) + 0.05*min(lt/6, 1)
            if name == "intro": s *= 1 + 0.02*math.sin(t*2.5)
            sz = int(680 * s); ill = sc_.frame(name, lt, e).resize((sz, sz), Image.LANCZOS)
            fr.paste(ill, (540 - sz//2, 1170 - sz//2), ill)
        ci = max(k for k, (ct, _) in enumerate(tl["caps"]) if ct <= t + 1e-6)
        cimg = capimgs[ci]; pop = 1.0 + 0.15*(1 - ease_out((t - tl["caps"][ci][0])/0.12))
        if pop > 1.001: cimg = cimg.resize((int(cimg.width*pop), int(cimg.height*pop)), Image.BILINEAR)
        fr.paste(cimg, (540 - cimg.width//2, 1560 - cimg.height//2), cimg)
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait()
    if ff.returncode: sys.exit("ffmpeg failed")
    print("wrote", out, f"{tl['dur']:.1f}s")

def render_thumb(T, out):
    """Simple, single-subject thumbnail (MrBeast rule: understood instantly, one emotion, curiosity):
    two short text lines, the #1 item drawn BIG with its key spot circled and an arrow, and the #1 tease banner."""
    sc_ = Scenes(T); im = make_bg(T); d = ImageDraw.Draw(im, "RGBA")
    l1, big = T.THUMB_TEXT[0], T.THUMB_TEXT[1]
    d.text((540, 215), l1.upper(), font=fit_font(l1.upper(), 1000, 130), fill=WHITE, stroke_width=14, stroke_fill=(0,0,0), anchor="mm")
    d.text((540, 385), big.upper(), font=fit_font(big.upper(), 1000, 190), fill=YEL, stroke_width=16, stroke_fill=(0,0,0), anchor="mm")
    top = next(it for it in T.ITEMS if it["rank"] == 1)
    ic = sc_.icon(1); dd = ImageDraw.Draw(ic); fp = top.get("focus")
    if fp: dd.ellipse((fp[0]-60, fp[1]-60, fp[0]+60, fp[1]+60), outline=RED+(255,), width=16)
    sz = 960; ic = ic.resize((sz, sz), Image.LANCZOS); x0, y0 = 540 - sz//2, 1080 - sz//2
    sh = Image.new("RGBA", ic.size, (0,0,0,0)); sh.putalpha(ic.getchannel("A").point(lambda a: int(a*0.55)))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.paste(Image.new("RGB", ic.size, (0,0,0)), (x0+12, y0+18), sh); im.paste(ic, (x0, y0), ic)
    d = ImageDraw.Draw(im, "RGBA")
    if fp:  # red arrow pointing at the circled spot, coming from the emptier side
        hx, hy = x0 + fp[0]*sz/800, y0 + fp[1]*sz/800
        sx = 1 if hx < 540 else -1
        tx, ty = hx + sx*230, hy + 170
        ang = math.atan2(hy - ty, hx - tx); ex, ey = hx - math.cos(ang)*95, hy - math.sin(ang)*95
        d.line((tx, ty, ex, ey), fill=(0,0,0), width=44); d.line((tx, ty, ex, ey), fill=RED, width=28)
        for col, w in (((0,0,0), 18), (RED, 0)):
            L = 70 + w; pts = [(ex + math.cos(ang)*L*0.6, ey + math.sin(ang)*L*0.6),
                   (ex + math.cos(ang+2.4)*L, ey + math.sin(ang+2.4)*L), (ex + math.cos(ang-2.4)*L, ey + math.sin(ang-2.4)*L)]
            d.polygon(pts, fill=col)
    d.rounded_rectangle((60, 1630, 1020, 1800), radius=36, fill=RED, outline=(0,0,0), width=8)
    d.text((540, 1715), T.THUMB_BANNER.upper(), font=fit_font(T.THUMB_BANNER.upper(), 920, 84), fill=WHITE, anchor="mm", stroke_width=6, stroke_fill=(0,0,0))
    im.save(out); print("wrote", out)

def render_preview(T, out):
    """Scene contact sheet without audio: intro, each item before/after its animation, outro icons."""
    sc_ = Scenes(T); tiles = [sc_.frame("intro", 0.4, -1)]
    for it in T.ITEMS: tiles += [sc_.frame(it["rank"], 0.4, -1), sc_.frame(it["rank"], 2.0, 1.5)]
    sheet = Image.new("RGB", (400*len(tiles), 400), T.PALETTE["top"])
    for i, t in enumerate(tiles):
        t = t.resize((400, 400), Image.LANCZOS); sheet.paste(t, (i*400, 0), t)
    sheet.save(out); print("wrote", out)

def contact_sheet(video, out):
    dur = duration(video); tmp = []
    for i in range(10):
        p = f"/tmp/_cs_{i}.png"; t = dur * (i + 0.5) / 10
        subprocess.run(["ffmpeg","-loglevel","error","-y","-ss",f"{t:.2f}","-i",video,"-frames:v","1","-vf","scale=360:-1",p]); tmp.append(p)
    ims = [Image.open(p) for p in tmp]; w, h = ims[0].size
    sheet = Image.new("RGB", (w*5, h*2))
    for i, im in enumerate(ims): sheet.paste(im, ((i % 5)*w, (i//5)*h))
    sheet.save(out); print("wrote", out)

def print_meta(T):
    print("=== VOICEOVER SCRIPT ===\n" + vo_script(T))
    words = len(vo_script(T).split()); print(f"\n({words} words, ~{words/2.4:.0f}s at a normal pace)")
    print("\n=== TITLE ===\n" + T.META["title"])
    print("\n=== DESCRIPTION ===\n" + T.META["description"])
    print("\n=== TAGS ===\n" + ", ".join(T.META["tags"]))

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet": contact_sheet(sys.argv[2], sys.argv[3]); sys.exit()
    T = load_topic(sys.argv[2])
    if mode == "script": print_meta(T)
    elif mode == "video": render_video(T, sys.argv[3], sys.argv[4])
    elif mode == "thumb": render_thumb(T, sys.argv[3])
    elif mode == "preview": render_preview(T, sys.argv[3])
    else: sys.exit(__doc__)
