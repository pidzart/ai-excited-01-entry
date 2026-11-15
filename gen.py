#!/usr/bin/env python3
"""Procedural supernova-eclipse render for ai-excited-01. Pure PIL + stdlib."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

SEED = 20261116
S = 2048            # supersample size
OUT = 1024
CX, CY = S // 2, int(S * 0.50)   # planet / core centre
PR = 462                          # planet radius
HORIZON = int(S * 0.72)

# --- iteration knobs (edited between renders) ---
CORE_BOOST = 1.3
STREAKS = 300
PARTICLES = 1500
RIM = 255

random.seed(SEED)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ---------- sky gradient ----------
top = (8, 4, 28); mid = (26, 10, 58); low = (10, 22, 52)
grad = Image.new("RGB", (1, S))
for y in range(S):
    t = y / S
    c = lerp(top, mid, t / 0.5) if t < 0.5 else lerp(mid, low, (t - 0.5) / 0.5)
    grad.putpixel((0, y), c)
img = grad.resize((S, S)).convert("RGB")

# ---------- nebula ----------
neb = Image.new("RGB", (S, S), (0, 0, 0))
nd = ImageDraw.Draw(neb, "RGBA")
neb_cols = [(255, 40, 180), (40, 220, 255), (130, 60, 255), (255, 80, 200), (30, 120, 255)]
for _ in range(90):
    cx = random.uniform(0, S); cy = random.uniform(0, S * 0.85)
    rx = random.uniform(180, 620); ry = rx * random.uniform(0.25, 0.55)
    col = random.choice(neb_cols)
    nd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (random.randint(8, 20),))
neb = neb.filter(ImageFilter.GaussianBlur(90))
img = ImageChops.add(img, neb)

# ---------- starfield ----------
sd = ImageDraw.Draw(img, "RGBA")
for _ in range(2400):
    x = random.uniform(0, S); y = random.uniform(0, HORIZON + 60)
    r = random.choice([1, 1, 1, 2, 2, 3])
    a = random.randint(70, 255)
    tint = random.choice([(255, 255, 255), (200, 230, 255), (255, 240, 210)])
    sd.ellipse([x - r, y - r, x + r, y + r], fill=tint + (a,))
    if r == 3:  # tiny cross sparkle
        sd.line([x - 7, y, x + 7, y], fill=tint + (a // 3,), width=1)
        sd.line([x, y - 7, x, y + 7], fill=tint + (a // 3,), width=1)

# ---------- supernova core glow (layered, additive) ----------
glow = Image.new("RGB", (S, S), (0, 0, 0))
gd = ImageDraw.Draw(glow)
layers = [  # (radius, colour)
    (900, (60, 36, 8)), (700, (110, 66, 14)), (540, (170, 110, 26)),
    (420, (230, 170, 60)), (330, (255, 214, 120)), (255, (255, 238, 190)),
    (190, (255, 250, 225)),
]
for rad, col in layers:
    c = tuple(min(255, int(v * CORE_BOOST)) for v in col)
    gd.ellipse([CX - rad, CY - rad, CX + rad, CY + rad], fill=c)
glow = glow.filter(ImageFilter.GaussianBlur(60))
img = ImageChops.add(img, glow)
# white-hot centre
hot = Image.new("RGB", (S, S), (0, 0, 0))
hd = ImageDraw.Draw(hot)
hd.ellipse([CX - 195, CY - 195, CX + 195, CY + 195], fill=(255, 252, 240))
hot = hot.filter(ImageFilter.GaussianBlur(35))
img = ImageChops.add(img, hot)

# ---------- radial light streaks (crown rays) ----------
st = Image.new("RGBA", (S, S), (0, 0, 0, 0))
std = ImageDraw.Draw(st)
for _ in range(STREAKS):
    ang = random.uniform(0, math.tau)
    r0 = PR * random.uniform(0.55, 0.95)
    ln = random.uniform(260, 1150) * random.choice([1, 1, 1.4])
    r1 = r0 + ln
    x0, y0 = CX + r0 * math.cos(ang), CY + r0 * math.sin(ang)
    x1, y1 = CX + r1 * math.cos(ang), CY + r1 * math.sin(ang)
    warm = random.random() < 0.7
    col = (255, 220, 140) if warm else (150, 235, 255)
    std.line([x0, y0, x1, y1], fill=col + (random.randint(50, 170),), width=random.choice([2, 3, 4, 6]))
st = st.filter(ImageFilter.GaussianBlur(2))
img = Image.alpha_composite(img.convert("RGBA"), st).convert("RGB")

# ---------- shockwave rings ----------
sw = Image.new("RGBA", (S, S), (0, 0, 0, 0))
swd = ImageDraw.Draw(sw)
for rad, alpha, wdt in [(620, 200, 7), (800, 130, 5), (1010, 70, 4)]:
    swd.ellipse([CX - rad, CY - rad, CX + rad, CY + rad], outline=(190, 240, 255, alpha), width=wdt)
sw = sw.filter(ImageFilter.GaussianBlur(3))
img = Image.alpha_composite(img.convert("RGBA"), sw).convert("RGB")

# ---------- planet ring: BACK half ----------
ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rd = ImageDraw.Draw(ring)
RW, RH = PR * 1.85, PR * 0.52   # wide, tilted (flat) ellipse
for i, (sc, al) in enumerate([(1.0, 210), (0.88, 130), (1.14, 90)]):
    col = (255, 205, 110) if i == 0 else ((120, 230, 255) if i == 1 else (255, 170, 220))
    rd.ellipse([CX - RW * sc, CY - RH * sc, CX + RW * sc, CY + RH * sc], outline=col + (al,), width=16 - i * 3)
ring_back = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ring_back.paste(ring.crop((0, 0, S, CY)), (0, 0))
img = Image.alpha_composite(img.convert("RGBA"), ring_back).convert("RGB")

# ---------- planet disc ----------
planet = Image.new("RGBA", (S, S), (0, 0, 0, 0))
pd = ImageDraw.Draw(planet)
pd.ellipse([CX - PR, CY - PR, CX + PR, CY + PR], fill=(10, 8, 26, 255))
# subtle radial shading: darker bottom, faint violet top-left sheen
for rad in range(PR, 0, -14):
    t = rad / PR
    col = (int(8 + 16 * (1 - t)), int(6 + 10 * (1 - t)), int(24 + 30 * (1 - t)))
    pd.ellipse([CX - rad, CY - rad, CX + rad, CY + rad], fill=col + (255,))
# surface band hints (very subtle arcs)
for k in range(5):
    yy = CY - PR * 0.5 + k * PR * 0.24
    pd.arc([CX - PR * 0.92, yy - PR * 0.34, CX + PR * 0.92, yy + PR * 0.34],
           start=15, end=165, fill=(70, 60, 130, 13), width=6)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).ellipse([CX - PR, CY - PR, CX + PR, CY + PR], fill=255)
img.paste(Image.alpha_composite(Image.new("RGBA", (S, S), (0, 0, 0, 0)), planet).convert("RGB"), (0, 0), mask)
# bright rim arc (corona edge) — top and sides
rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rid = ImageDraw.Draw(rim)
for wdt, al in [(14, 90), (8, 160), (4, RIM)]:
    rid.arc([CX - PR, CY - PR, CX + PR, CY + PR], start=140, end=400, fill=(255, 236, 180, al), width=wdt)
rim = rim.filter(ImageFilter.GaussianBlur(3))
img = Image.alpha_composite(img.convert("RGBA"), rim).convert("RGB")

# ---------- planet ring: FRONT half (across lower front) ----------
ring_front = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ring_front.paste(ring.crop((0, CY, S, S)), (0, CY))
img = Image.alpha_composite(img.convert("RGBA"), ring_front).convert("RGB")
# front ring bright core line
fl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
fld = ImageDraw.Draw(fl)
fld.arc([CX - RW, CY - RH, CX + RW, CY + RH], start=0, end=180, fill=(255, 226, 150, 235), width=5)
img = Image.alpha_composite(img.convert("RGBA"), fl.filter(ImageFilter.GaussianBlur(1))).convert("RGB")

# ---------- ocean ----------
oc = ImageDraw.Draw(img, "RGBA")
oc.rectangle([0, HORIZON, S, S], fill=(4, 26, 38, 255))
oc.line([0, HORIZON, S, HORIZON], fill=(140, 240, 255, 255), width=4)
oc.line([0, HORIZON + 5, S, HORIZON + 5], fill=(255, 220, 150, 160), width=2)
# shimmer streaks, densest in reflection column under planet
for _ in range(900):
    in_col = random.random() < 0.55
    if in_col:
        x = random.gauss(CX, 190)
    else:
        x = random.uniform(0, S)
    y = random.uniform(HORIZON + 8, S - 6)
    depth = (y - HORIZON) / (S - HORIZON)
    wdt = random.uniform(8, 90) * (0.4 + depth)
    dist = abs(x - CX) / (S / 2)
    a = int(max(8, (200 * (1 - dist) + 40) * random.uniform(0.3, 1.0)))
    col = random.choice([(255, 224, 150), (140, 235, 255), (255, 255, 255), (255, 170, 220)])
    oc.line([x - wdt / 2, y, x + wdt / 2, y], fill=col + (min(255, a),), width=random.choice([2, 3, 4]))
# bright reflection column core
col_glow = Image.new("RGB", (S, S), (0, 0, 0))
cg = ImageDraw.Draw(col_glow)
cg.polygon([(CX - 150, HORIZON), (CX + 150, HORIZON), (CX + 300, S), (CX - 300, S)], fill=(95, 70, 28))
img = ImageChops.add(img, col_glow.filter(ImageFilter.GaussianBlur(50)))

# ---------- foreground particles / streaks toward viewer ----------
pt = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ptd = ImageDraw.Draw(pt)
for _ in range(PARTICLES):
    ang = random.uniform(0, math.tau)
    r = random.uniform(PR * 0.4, S * 0.75)
    x, y = CX + r * math.cos(ang), CY + r * math.sin(ang)
    if not (0 <= x < S and 0 <= y < S):
        continue
    if math.hypot(x - CX, y - CY) < PR + 18:
        continue
    col = random.choice([(255, 230, 170), (170, 240, 255), (255, 255, 255), (255, 160, 230)])
    a = random.randint(60, 230)
    if random.random() < 0.35 and y < HORIZON:  # short radial streak (sky only)
        ln = random.uniform(10, 46) * (r / S + 0.4)
        ptd.line([x, y, x + ln * math.cos(ang), y + ln * math.sin(ang)], fill=col + (a,), width=3)
    else:
        rr = random.choice([2, 2, 3, 4])
        ptd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (a,))
img = Image.alpha_composite(img.convert("RGBA"), pt).convert("RGB")

# ---------- vignette ----------
vig = Image.new("L", (S, S), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-S * 0.25, -S * 0.25, S * 1.25, S * 1.25], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(220))
black = Image.new("RGB", (S, S), (0, 0, 0))
img = Image.composite(img, ImageChops.multiply(img, black), vig)
img = ImageEnhance.Brightness(img).enhance(1.06)
img = ImageEnhance.Contrast(img).enhance(1.05)

# ---------- final glow pass + downscale ----------
small = img.resize((OUT, OUT), Image.LANCZOS)
glow_copy = small.filter(ImageFilter.GaussianBlur(18))
small = ImageChops.screen(small, ImageEnhance.Brightness(glow_copy).enhance(0.35))
small.save("entry.png", optimize=True)
print("saved entry.png")
