"""Hidden car features most drivers never use (Oct 2026)."""
import math
from PIL import Image, ImageDraw
from engine import canvas, sc, fin, ease_back, ease_out, F, YEL

SLUG = "hidden_car_features"
PALETTE = {"top": (62, 18, 26), "bottom": (22, 14, 30), "glow": (220, 80, 60)}
VIDEO_TITLE = ("Hidden car features", "most drivers never use")
THUMB_TEXT = ("Hidden car", "features")
THUMB_BANNER = "#1 could save a life"
KEYWORDS = ["HIDDEN","CAR","FEATURES","SAVE","LIFE","MIRROR","TAB","GLARE","DISAPPEARS","KEY","METAL","BATTERY",
            "UNLOCK","WINDOW","GLOWING","HANDLE","TRUNK","TRAPPED","ESCAPE"]

HOOK = "Ranking hidden car features most drivers miss, and number one could save a life."
OUTRO = "Go check your car…"

# ---------------- shared ----------------
RED = (200, 40, 50); DARKRED = (150, 28, 38); GLASS = (150, 200, 235); TIRE = (35, 35, 42); HUB = (180, 185, 195)

def _car_side(d, body=RED):
    d.rounded_rectangle(sc(70,380,730,560), radius=60*2, fill=body)
    d.polygon(sc(200,385,280,250,540,250,640,385), fill=body)
    d.polygon(sc(225,380,292,272,395,272,395,380), fill=GLASS)
    d.polygon(sc(415,380,415,272,528,272,610,380), fill=GLASS)
    for x in (210, 590):
        d.ellipse(sc(x-75,480,x+75,630), fill=TIRE); d.ellipse(sc(x-35,520,x+35,590), fill=HUB)
    d.rounded_rectangle(sc(690,410,730,450), radius=12*2, fill=(255,235,150))
    d.rounded_rectangle(sc(70,410,100,450), radius=10*2, fill=(255,90,80))

def draw_intro():
    im, d = canvas(); _car_side(d); return fin(im)

# #4 rearview mirror tab
def draw_mirror():
    im, d = canvas()
    d.rectangle(sc(370,60,430,240), fill=(60,60,70))
    d.rounded_rectangle(sc(80,220,720,540), radius=90*2, fill=(40,40,48))
    return fin(im)
def anim_mirror(img, d, lt, e):
    p = ease_back(e/0.4) if e >= 0 else 0.0
    q = min(1.0, max(0.0, p))
    # mirror glass: bright night glare -> dim
    d.rounded_rectangle((110,250,690,510), radius=150, fill=(int(70-40*q), int(80-45*q), int(110-60*q), 255))
    for cx in (300, 500):
        r = 70 - 40*q; a = int(255*(1-0.75*q))
        d.ellipse((cx-r-40, 380-r-40, cx+r+40, 380+r+40), fill=(255,250,200,int(a*0.35)))
        d.ellipse((cx-r, 380-r, cx+r, 380+r), fill=(255,252,225,a))
    # the tab under the mirror flips
    ang = math.radians(-35 + 70*p)
    tx, ty = 400, 545
    w, h = 80, 70
    dx = h*math.sin(ang); dy = h*math.cos(ang)
    d.polygon([(tx-w, ty), (tx+w, ty), (tx+w+dx, ty+dy), (tx-w+dx, ty+dy)], fill=(175,180,192,255), outline=(255,255,255,255), width=4)
    return (None, (tx + dx/2, ty + dy/2 + 6))

# #3 metal key hidden in the fob
def draw_fob():
    im, d = canvas()
    d.rounded_rectangle(sc(200,180,600,520), radius=130*2, fill=(30,30,36))
    for i, y in enumerate((260, 345, 430)):
        d.rounded_rectangle(sc(310,y-30,490,y+30), radius=30*2, fill=(70,72,82))
    d.polygon(sc(380,245,420,245,400,275), fill=(200,205,215))          # lock-ish arrow
    d.ellipse(sc(385,330,415,360), outline=(200,205,215), width=6*2)
    d.rectangle(sc(380,420,420,440), fill=(200,205,215))
    d.rounded_rectangle(sc(560,300,610,340), radius=10*2, fill=(170,175,185))   # release slider
    return fin(im)
def anim_fob(img, d, lt, e):
    p = ease_out(e/0.6) if e >= 0 else 0.0
    off = 170*p
    # blade slides out the bottom
    y0 = 470 + off*0.0
    d.rectangle((370, 470, 430, 520 + off), fill=(200,205,215,255))
    for k in range(int(off/40)):
        yy = 540 + k*40
        if yy < 500 + off: d.polygon([(430,yy),(452,yy+14),(430,yy+28)], fill=(200,205,215,255))
    d.rounded_rectangle((200,180,600,520), radius=130, fill=(30,30,36,255))
    for y in (260, 345, 430): d.rounded_rectangle((310,y-30,490,y+30), radius=30, fill=(70,72,82,255))
    d.polygon([(380,245),(420,245),(400,275)], fill=(200,205,215,255))
    d.ellipse((385,330,415,360), outline=(200,205,215,255), width=6)
    d.rectangle((380,420,420,440), fill=(200,205,215,255))
    sx = 585 - 20*p
    d.rounded_rectangle((sx-25,300,sx+25,340), radius=10, fill=(230,190,60,255) if e >= 0 else (170,175,185,255))
    return (None, (400, 520 + off*0.75) if e >= 0 else (sx, 320))

# #2 hold unlock -> all windows down
def draw_windows():
    im, d = canvas()
    d.rounded_rectangle(sc(70,380,730,560), radius=60*2, fill=(40,110,190))
    d.polygon(sc(200,385,280,250,540,250,640,385), fill=(40,110,190))
    d.polygon(sc(225,380,292,272,395,272,395,380), fill=(25,30,45))
    d.polygon(sc(415,380,415,272,528,272,610,380), fill=(25,30,45))
    for x in (210, 590):
        d.ellipse(sc(x-75,480,x+75,630), fill=TIRE); d.ellipse(sc(x-35,520,x+35,590), fill=HUB)
    d.line(sc(405,385,405,550), fill=(30,85,150), width=6*2)
    return fin(im)
def anim_windows(img, d, lt, e):
    p = ease_out(e/0.9) if e >= 0 else 0.0
    drop = 108*p
    glass = Image.new("RGBA", img.size, (0,0,0,0)); gd = ImageDraw.Draw(glass)
    gd.polygon([(225,380+drop),(292,272+drop),(395,272+drop),(395,380+drop)], fill=GLASS+(255,))
    gd.polygon([(415,380+drop),(415,272+drop),(528,272+drop),(610,380+drop)], fill=GLASS+(255,))
    mask = Image.new("L", img.size, 0); md = ImageDraw.Draw(mask)
    md.polygon([(225,380),(292,272),(395,272),(395,380)], fill=255); md.polygon([(415,380),(415,272),(528,272),(610,380)], fill=255)
    img = img.copy(); img.paste(glass, (0,0), Image.composite(glass.split()[3], Image.new("L", img.size, 0), mask))
    d2 = ImageDraw.Draw(img)
    # small fob with the unlock button held
    d2.rounded_rectangle((560,90,700,210), radius=45, fill=(45,45,55,255), outline=(235,235,240,255), width=6)
    on = e >= 0 and int(lt*4) % 2 == 0
    d2.ellipse((605,125,655,175), fill=(255,210,60,255) if on else (90,92,104,255))
    if e >= 0:
        for k in range(3):
            r = 40 + 18*k + (lt*40 % 18)
            d2.arc((630-r,150-r,630+r,150+r), 200, 260, fill=(255,210,60,200), width=6)
    return (img, (630, 150))

# #1 glowing trunk release
GLOW = (120, 255, 140)
def draw_trunk():
    im, d = canvas()
    # rear of a car seen from behind, trunk cut away so you see inside
    d.polygon(sc(190,90,610,90,690,260,110,260), fill=DARKRED)              # roof / rear pillar
    d.polygon(sc(220,115,580,115,640,240,160,240), fill=GLASS)               # rear window
    d.rounded_rectangle(sc(60,250,740,640), radius=50*2, fill=RED)          # body
    d.rounded_rectangle(sc(80,290,170,400), radius=20*2, fill=(255,90,80))  # tail lights
    d.rounded_rectangle(sc(630,290,720,400), radius=20*2, fill=(255,90,80))
    d.rounded_rectangle(sc(60,600,740,690), radius=30*2, fill=(60,60,70))    # bumper
    for x in (130, 670): d.rectangle(sc(x-60,690,x+60,740), fill=TIRE)
    d.rectangle(sc(190,280,610,590), fill=(14,14,22))                        # dark trunk space
    d.polygon(sc(190,280,610,280,570,320,230,320), fill=(34,34,46))
    d.polygon(sc(190,590,230,550,570,550,610,590), fill=(30,30,40))
    d.rounded_rectangle(sc(375,315,425,340), radius=8*2, fill=(80,82,95))   # latch
    return fin(im)
def anim_trunk(img, d, lt, e):
    pull = ease_back(e/0.5)*40 if e >= 0 else 0.0
    glow = 0.65 + 0.35*math.sin(lt*5)
    if e > 0.6:   # latch pops: daylight at the lid seam
        q = ease_out((e-0.6)/0.5)
        d.rectangle((190,272,610,272+16*q), fill=(255,240,190,int(255*q)))
    cy = 440 + pull
    for r, a in ((170, 45), (125, 80)):
        d.ellipse((400-r, cy-r*0.7, 400+r, cy+r*0.7), fill=GLOW+(int(a*glow),))
    d.line((400,340,400,cy-60), fill=(200,205,215,255), width=10)
    d.rounded_rectangle((378,cy-75,422,cy-10), radius=14, fill=GLOW+(255,))
    d.rounded_rectangle((280,cy-30,520,cy+30), radius=30, fill=GLOW+(255,))
    return (None, (400, cy))

# ITEMS in reveal order (#4 first). Spoken as: "Number four: <what> <why>"
ITEMS = [
    dict(rank=4, label="Mirror tab", what="the tab on your rearview mirror.",
         why="Flip it at night and headlight glare disappears.",
         draw=draw_mirror, animate=anim_mirror, focus=(400, 570)),
    dict(rank=3, label="Hidden key", what="your key fob hides a metal key",
         why="for when the battery dies.",
         draw=draw_fob, animate=anim_fob, focus=(585, 320)),
    dict(rank=2, label="Hold unlock", what="on many cars, holding unlock",
         why="rolls down every window.",
         draw=draw_windows, animate=anim_windows, focus=(630, 150)),
    dict(rank=1, label="Trunk handle", what="the glowing handle inside your trunk.",
         why="It's required in new US cars, so anyone trapped inside can escape.",
         draw=draw_trunk, animate=anim_trunk, focus=(400, 440)),
]

META = {
    "title": "Hidden Car Features Most Drivers Never Use 🚗 #shorts",
    "description": """Ranking hidden car features most drivers never use, and #1 could save a life 🚗

#4 – The tab on your rearview mirror
#3 – The metal key hidden in your key fob
#2 – Hold unlock to roll down every window (on many cars)
#1 – The glow-in-the-dark trunk release handle

Which one did you already know? Comment below 👇
Subscribe for more rankings and facts you didn't know you needed.

#shorts #cars #carhacks #didyouknow #facts #ranking""",
    "tags": ["hidden car features", "car features you didn't know", "car hacks", "car tips", "key fob hidden key",
             "key fob trick roll down windows", "rearview mirror tab", "rear view mirror night mode",
             "glow in the dark trunk handle", "emergency trunk release", "car secrets", "driving tips",
             "things you never noticed", "did you know", "fun facts", "ranking", "internet ranked", "shorts", "tech facts"],
}
