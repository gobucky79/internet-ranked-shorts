"""Reference topic: Secret Plane Features Nobody Tells You About (posted Oct 2026)."""
import math
from PIL import Image, ImageDraw
from engine import canvas, sc, fin, ease_back, ease_out, F, YEL

SLUG = "plane_features"
PALETTE = {"top": (20, 30, 70), "bottom": (30, 20, 50), "glow": (60, 110, 200)}
VIDEO_TITLE = ("Secret plane features", "nobody tells you about")
THUMB_TEXT = ("Secret plane", "features", "nobody tells you")
THUMB_BANNER = "#1 could save your life"
KEYWORDS = ["SECRET","PLANE","SAVE","LIFE","HIDDEN","BUTTON","ARMREST","TRIANGLE","STICKER","WINGS","ASHTRAYS",
            "BANNED","SAFE","DIM","LIGHTS","EVACUATE","NEXT","FLIGHT","RULEBREAKERS","EYES"]

HOOK = "Ranking secret plane features nobody tells you about, and number one could save your life."
OUTRO = "Now check for these on your next flight…"

# ---------------- drawings (800x800 canvas, use sc() for coordinates) ----------------
def draw_intro():
    im, d = canvas()
    d.polygon(sc(400,320,80,480,80,525,400,445,720,525,720,480), fill=(200,206,218))
    for ex in (225, 575): d.rounded_rectangle(sc(ex-20,400,ex+20,480), radius=16*2, fill=(150,158,175))
    d.polygon(sc(400,610,265,700,265,728,400,690,535,728,535,700), fill=(200,206,218))
    d.rounded_rectangle(sc(358,70,442,730), radius=42*2, fill=(240,243,250))
    d.polygon(sc(388,600,412,600,404,760,396,760), fill=(210,60,70))
    d.chord(sc(372,95,428,150), 180, 360, fill=(40,60,100))
    d.line(sc(400,160,400,580), fill=(210,60,70), width=8*2)
    return fin(im)

# #4 armrest
PIV = (262, 420)
def _rot(p, a):
    x, y = p[0]-PIV[0], p[1]-PIV[1]
    return (PIV[0] + x*math.cos(a) + y*math.sin(a), PIV[1] - x*math.sin(a) + y*math.cos(a))
def draw_armrest():
    im, d = canvas()
    d.polygon(sc(175,150,275,135,315,480,205,485), fill=(50,85,165))
    d.rounded_rectangle(sc(178,140,275,205), radius=40, fill=(235,235,240))
    d.rounded_rectangle(sc(195,465,610,560), radius=60, fill=(40,72,145))
    for x in (265, 505): d.rectangle(sc(x,560,x+30,700), fill=(150,155,165))
    d.rounded_rectangle(sc(235,690,575,712), radius=20, fill=(150,155,165))
    return fin(im)
def anim_armrest(img, d, lt, e):
    a = math.radians(78) * ease_back(e/0.5) if e >= 0 else 0.0
    d.polygon([_rot(p, a) for p in [(232,400),(565,400),(575,420),(565,442),(232,442)]], fill=(70,72,84,255))
    d.polygon([_rot(p, a) for p in [(240,392),(560,392),(560,408),(240,408)]], fill=(110,112,126,255))
    c = _rot(PIV, a); d.ellipse((c[0]-16, c[1]-16, c[0]+16, c[1]+16), fill=(150,155,165,255))
    b = _rot((300, 446), a); d.ellipse((b[0]-11, b[1]-9, b[0]+11, b[1]+9), fill=(200,205,215,255))
    return (None, b)

# #3 triangle sticker
WING = [(262,600),(545,488),(545,540),(300,640)]
def draw_triangle():
    im, d = canvas()
    d.rounded_rectangle(sc(90,60,710,740), radius=100, fill=(236,233,226))
    d.rounded_rectangle(sc(225,215,575,685), radius=280, fill=(212,207,198))
    sky = Image.new("RGBA", im.size, (0,0,0,0)); sd = ImageDraw.Draw(sky)
    sd.rectangle(sc(0,0,800,800), fill=(125,190,245)); sd.rectangle(sc(0,520,800,800), fill=(160,210,250))
    for cx, cy, r in [(330,330,40),(380,315,50),(430,335,38)]: sd.ellipse(sc(cx-r,cy-r,cx+r,cy+r), fill=(255,255,255))
    sd.polygon(sc(*sum(WING, ())), fill=(215,220,230)); sd.line(sc(262,600,545,488), fill=(180,185,200), width=12)
    mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).rounded_rectangle(sc(255,250,545,650), radius=230, fill=255)
    im.paste(sky, (0,0), mask); d = ImageDraw.Draw(im)
    d.polygon(sc(365,110,435,110,400,170), fill=(20,20,25))
    return fin(im)
def anim_triangle(img, d, lt, e):
    if e < 0: return
    p = ease_out(e/0.4)
    d.polygon(WING, outline=YEL+(int(255*p),), width=8)
    y1 = 180 + 260*p
    for k in range(int((y1-180)/30)):
        yy = 180 + k*30 + (lt*60 % 30)
        if yy < y1: d.line((400, yy, 400 + (yy-180)*0.05, yy+16), fill=YEL+(255,), width=8)
    if p > 0.95: d.polygon([(380,450),(420,450),(402,485)], fill=YEL+(255,))

# #2 ashtray
def draw_ashtray():
    im, d = canvas()
    d.rounded_rectangle(sc(170,50,630,770), radius=60, fill=(205,207,215)); d.line(sc(400,50,400,770), fill=(185,188,198), width=8)
    d.ellipse(sc(305,125,495,315), fill=(255,255,255), outline=(220,40,40), width=32)
    d.rectangle(sc(330,207,450,233), fill=(250,250,250), outline=(40,40,40), width=6)
    d.rectangle(sc(450,207,472,233), fill=(240,140,40), outline=(40,40,40), width=6)
    d.line(sc(338,150,462,290), fill=(220,40,40), width=32)
    d.rounded_rectangle(sc(315,430,485,570), radius=36, fill=(176,181,192), outline=(130,135,148), width=8)
    d.rounded_rectangle(sc(337,452,463,512), radius=20, fill=(118,124,136)); d.line(sc(352,482,448,482), fill=(60,64,74), width=12)
    return fin(im)
def anim_ashtray(img, d, lt, e):
    if e < 0: return
    for k in range(4):
        p = ((e*0.9 + k/4) % 1.0); a = int(170*(1-p) * min(1, e*3))
        x = 400 + 22*math.sin(p*6 + k*1.7); y = 440 - p*130; r = 10 + p*26
        d.ellipse((x-r, y-r, x+r, y+r), fill=(235,235,240,a))

# #1 dim lights
def draw_lights():
    im, d = canvas()
    d.polygon(sc(60,60,740,60,520,330,280,330), fill=(228,228,233))
    d.polygon(sc(60,60,280,330,280,520,60,760), fill=(212,212,218)); d.polygon(sc(740,60,520,330,520,520,740,760), fill=(212,212,218))
    d.polygon(sc(60,760,280,520,520,520,740,760), fill=(115,110,135)); d.polygon(sc(300,760,370,520,430,520,500,760), fill=(150,60,70))
    d.rectangle(sc(280,330,520,520), fill=(195,195,205))
    for dd in (0.85, 0.6, 0.35, 0.1):
        yb = 760 - dd*240; h = 270*(1-0.62*dd)
        for x0, x1 in ((60+220*dd+8, 300+70*dd-6), (500-70*dd+6, 740-220*dd-8)):
            d.rounded_rectangle(sc(x0, yb-h, x1, yb-10), radius=int(20*(1-dd*0.5))*2, fill=(45,75,150))
            d.rounded_rectangle(sc(x0+6, yb-h+6, x1-6, yb-h+0.22*h), radius=int(14*(1-dd*0.5))*2, fill=(235,235,240))
    return fin(im)
def anim_lights(img, d, lt, e):
    if e < 0:
        d.line((120,75,300,325), fill=(255,245,210,255), width=14); d.line((680,75,500,325), fill=(255,245,210,255), width=14); return
    p = ease_out(e/0.7)
    dark = Image.new("RGBA", img.size, (0,0,0,0)); ImageDraw.Draw(dark).rectangle((60,60,740,760), fill=(10,10,40,int(175*p)))
    img = Image.alpha_composite(img, dark); g = 1 - p
    col = (int(255*g + 90*p), int(245*g + 110*p), int(210*g + 220*p), 255)
    d.line((120,75,300,325), fill=col, width=14); d.line((680,75,500,325), fill=col, width=14)
    if e > 1.2:
        q = ease_out((e-1.2)/0.5)
        for side in (0, 1):
            for k in range(9):
                t = k/8; x0 = 300 + 70*t if side == 0 else 500 - 70*t; y = 760 - 240*t; r = 7 - 4*t
                d.ellipse((x0-r, y-r, x0+r, y+r), fill=(255,190,70,int(255*q)))
        d.rounded_rectangle((350,350,450,395), radius=8, fill=(30,170,80,int(255*q)))
        d.text((400,373), "EXIT", font=F(30), fill=(255,255,255,int(255*q)), anchor="mm")
    return img

# ITEMS in reveal order (#4 first). Spoken as: "Number four: <what> <why>"
ITEMS = [
    dict(rank=4, label="Armrest button", what="a hidden button under the aisle armrest", why="lifts it all the way up.",
         draw=draw_armrest, animate=anim_armrest, focus=(300, 446)),
    dict(rank=3, label="Triangle sticker", what="the little triangle sticker", why="marks the best window for the crew to check the wings.",
         draw=draw_triangle, animate=anim_triangle, focus=(400, 132)),
    dict(rank=2, label="Bathroom ashtray", what="bathroom ashtrays.", why="Smoking's banned, but rule-breakers still need somewhere safe to put it out.",
         draw=draw_ashtray, animate=anim_ashtray, focus=(400, 482)),
    dict(rank=1, label="Dim lights", what="they dim the lights for landing,", why="so your eyes are ready if you have to evacuate.",
         draw=draw_lights, animate=anim_lights, focus=(205, 195)),
]

META = {
    "title": "Secret Plane Features Nobody Tells You About ✈️ #shorts",
    "description": """Ranking secret plane features nobody tells you about, and #1 could actually save your life ✈️

#4 – Hidden armrest button
#3 – The triangle sticker above the window
#2 – Bathroom ashtrays (yes, still!)
#1 – Why they dim the lights for landing

Which one did you already know? Comment below 👇
Subscribe for more rankings and facts you didn't know you needed.

#shorts #airplane #travel #didyouknow #facts #ranking""",
    "tags": ["secret plane features", "airplane secrets", "hidden airplane features", "plane facts",
             "why do planes dim lights for landing", "airplane armrest button", "triangle sticker airplane window",
             "why do planes have ashtrays", "flight attendant secrets", "travel hacks", "flying tips",
             "things you never noticed", "did you know", "fun facts", "ranking", "internet ranked", "shorts", "aviation facts"],
}
