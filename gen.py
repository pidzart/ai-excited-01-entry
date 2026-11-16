#!/usr/bin/env python3
"""Procedural render for ai-excited-01 entry6: ringed planet eclipsing a supernova,
over a dark teal ocean. 2048x2048 render, LANCZOS downscale to 1024x1024."""
import math, random, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SEED = 20261116
rng = random.Random(SEED)
np_rng = np.random.default_rng(SEED)

S = 2048
W = H = S
CX, CY = 1024, 560          # supernova core centre (peeks over the planet limb)
PLANET_C = (1024, 1180)     # planet centre
PLANET_R = 520
HORIZON = int(H * 0.72)     # ocean starts here (bottom 28%)

img = np.zeros((H, W, 3), dtype=np.float32)

# ---------- 1. deep-space vertical gradient ----------
yy = np.linspace(0, 1, H)[:, None]
top = np.array([6, 8, 26], dtype=np.float32)
bot = np.array([2, 3, 10], dtype=np.float32)
img += top[None, None, :] * (1 - yy)[:, :, None] + bot[None, None, :] * yy[:, :, None]

# ---------- 2. nebula: soft magenta / cyan blobs ----------
neb = np.zeros((H, W, 3), dtype=np.float32)
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
blobs = []
for _ in range(26):
    bx = rng.uniform(0, W); by = rng.uniform(0, HORIZON)
    br = rng.uniform(180, 520)
    col = rng.choice([
        np.array([150, 30, 120]),   # magenta
        np.array([20, 110, 150]),   # cyan
        np.array([90, 40, 140]),    # violet
        np.array([160, 60, 40]),    # ember
    ])
    amp = rng.uniform(0.10, 0.30)
    d2 = ((X - bx) ** 2 + (Y - by) ** 2) / (br * br)
    neb += amp * np.exp(-d2)[..., None] * col[None, None, :]
neb_img = Image.fromarray(np.clip(neb, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(90))
img += np.asarray(neb_img, dtype=np.float32)

# ---------- 3. stars (~2400) ----------
star_layer = Image.new("RGB", (W, H), (0, 0, 0))
sd = ImageDraw.Draw(star_layer)
n_stars = 2400
for _ in range(n_stars):
    x = rng.uniform(0, W); y = rng.uniform(0, HORIZON * 1.02)
    b = rng.uniform(60, 255)
    r = rng.choice([1, 1, 1, 2, 2, 3])
    tint = rng.choice([(255, 255, 255), (255, 240, 200), (200, 220, 255), (255, 210, 180)])
    c = tuple(int(b * t / 255) for t in tint)
    sd.ellipse([x - r, y - r, x + r, y + r], fill=c)
    if r >= 3 and rng.random() < 0.5:  # cross flare on the brightest
        L = r * 4
        sd.line([x - L, y, x + L, y], fill=c, width=1)
        sd.line([x, y - L, x, y + L], fill=c, width=1)
img += np.asarray(star_layer, dtype=np.float32)

# ---------- 4. supernova core: radial glow + corona rays ----------
R = np.sqrt((X - CX) ** 2 + (Y - CY) ** 2)
ang = np.arctan2(Y - CY, X - CX)
core = np.exp(-(R / 210.0) ** 2)                       # blinding centre
halo = np.exp(-(R / 620.0) ** 1.6)                      # wide halo
# radial corona rays: angular modulation, stronger near core
rays = 0.55 + 0.45 * np.abs(np.sin(ang * 9 + 0.7 * np.sin(ang * 23)))
rayfield = np.exp(-R / 900.0) * rays
gold = np.array([255, 214, 130], dtype=np.float32)
white = np.array([255, 250, 235], dtype=np.float32)
img += (core[..., None] * 1.15 * white[None, None, :]
        + halo[..., None] * 0.85 * gold[None, None, :]
        + rayfield[..., None] * 0.35 * gold[None, None, :])
# white-hot pinpoint
img += np.exp(-(R / 55.0) ** 2)[..., None] * np.array([255, 255, 255], dtype=np.float32) * 1.2

# ---------- 5. shockwave rings (3 thin, around core) ----------
for rr, amp in ((620, 0.55), (820, 0.38), (1040, 0.25)):
    ring = np.exp(-((R - rr) / 7.0) ** 2) * amp
    img += ring[..., None] * np.array([255, 220, 160], dtype=np.float32)[None, None, :]

# ---------- 6. colossal dark planet (silhouette) + rim light ----------
d_planet = np.sqrt((X - PLANET_C[0]) ** 2 + (Y - PLANET_C[1]) ** 2)
inside = d_planet < PLANET_R
# dark disc: near-black with faint deep-blue sheen
planet_col = np.array([10, 12, 26], dtype=np.float32)
img[inside] = img[inside] * 0.06 + planet_col
# subtle surface shading: slightly lighter upper-left limb
shade = np.exp(-((X - (PLANET_C[0] - 260)) ** 2 + (Y - (PLANET_C[1] - 260)) ** 2) / (2 * 420.0 ** 2))
img[inside] += (shade[inside] * 14)[..., None]
# rim light: thin bright crescent on the core-facing (upper) edge
rim = np.exp(-((d_planet - (PLANET_R - 4)) / 5.0) ** 2)
upper = np.clip(((PLANET_C[1] - Y) / PLANET_R) * 1.2 + 0.15, 0, 1)  # brightest on limb facing the core
img += (rim * upper)[..., None] * np.array([255, 200, 110], dtype=np.float32)[None, None, :] * 0.9

# ---------- 7. tilted planet ring, gold -> cyan gradient ----------
ring_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(ring_layer)
# ring as many small arc segments so colour can sweep gold -> cyan
cx, cy = PLANET_C
rx, ry = 820, 220          # tilted ellipse radii (tilt via flattened ellipse)
tilt = -18                 # degrees
# draw in a rotated frame: draw ellipse on temp layer, rotate, paste
tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(tmp)
for a0 in range(0, 360, 2):
    t = a0 / 360.0
    # gold (255,200,90) -> cyan (70,210,235) sweep across the ring
    gg = (255, 200, 90); cc = (70, 210, 235)
    col = tuple(int(gg[i] + (cc[i] - gg[i]) * t) for i in range(3))
    td.arc([cx - rx, cy - ry, cx + rx, cy + ry], start=a0, end=a0 + 2.5,
           fill=col + (235,), width=22)
tmp = tmp.rotate(tilt, resample=Image.BICUBIC, center=(cx, cy))
# inner thin bright edge of the ring
tmp2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
t2 = ImageDraw.Draw(tmp2)
t2.arc([cx - rx, cy - ry, cx + rx, cy + ry], start=0, end=360,
       fill=(255, 240, 200, 160), width=3)
tmp2 = tmp2.rotate(tilt, resample=Image.BICUBIC, center=(cx, cy))
ring_layer = Image.alpha_composite(ring_layer, tmp)
ring_layer = Image.alpha_composite(ring_layer, tmp2)
# mask ring to only where it is OUTSIDE the planet disc (front part passes in front
# of the planet's lower half: keep segments below planet centre line visible)
ring_arr = np.asarray(ring_layer, dtype=np.float32)
# front arc: keep ring pixels whose y is below planet centre (in front of planet)
front = (Y > PLANET_C[1] + 40)
behind = ~front
# behind-planet part: hide where it would cross the planet disc
hide = behind & inside
ring_arr[hide] = 0
# also hide ring where it crosses the supernova core glare? keep it, it glows there.
img = img * (1 - ring_arr[..., 3:4] / 255.0) + ring_arr[..., :3] * (ring_arr[..., 3:4] / 255.0)

# ---------- 8. particles / streaks (~1500) ----------
part = Image.new("RGB", (W, H), (0, 0, 0))
pd = ImageDraw.Draw(part)
for _ in range(1500):
    # denser near the core / along the ring plane
    if rng.random() < 0.55:
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(PLANET_R * 0.9, 1250)
        x = CX + rr * math.cos(a); y = CY + rr * math.sin(a) * 0.55
    else:
        x = rng.uniform(0, W); y = rng.uniform(0, HORIZON)
    if not (0 <= x < W and 0 <= y < H):
        continue
    L = rng.uniform(4, 26)
    th = rng.uniform(0, 2 * math.pi)
    b = rng.uniform(80, 255)
    col = rng.choice([(255, 220, 160), (255, 255, 255), (140, 230, 255), (255, 160, 200)])
    c = tuple(int(b * v / 255) for v in col)
    pd.line([x, y, x + L * math.cos(th), y + L * math.sin(th)], fill=c, width=1)
img += np.asarray(part, dtype=np.float32) * 0.85

# ---------- 9. dark teal ocean (bottom 28%) + reflection column ----------
ocean = np.zeros((H, W, 3), dtype=np.float32)
oy = np.linspace(0, 1, H - HORIZON)[:, None]
o_top = np.array([8, 42, 48], dtype=np.float32)
o_bot = np.array([2, 14, 20], dtype=np.float32)
ocean[HORIZON:] = o_top[None, None, :] * (1 - oy)[:, :, None] + o_bot[None, None, :] * oy[:, :, None]
# gentle horizontal wave shimmer
wave = (np.sin(Y * 0.11 + 3.0 * np.sin(X * 0.004)) * 0.5 + 0.5)
ocean += (wave * 4.0)[..., None] * np.array([0.4, 1.0, 1.0], dtype=np.float32)[None, None, :]
# reflection column under the core: bright vertical glow, glittering
col_x = CX
col_w = 150.0
refl = np.exp(-((X - col_x) / col_w) ** 2) * np.exp(-(Y - HORIZON) / 420.0)
refl = np.where(Y >= HORIZON, refl, 0.0)
ocean += refl[..., None] * np.array([255, 200, 110], dtype=np.float32)[None, None, :] * 0.85
# glitter sparkles in the column
glit = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glit)
for _ in range(420):
    gx = rng.gauss(col_x, 90); gy = rng.uniform(HORIZON, H)
    if not (0 <= gx < W):
        continue
    b = rng.uniform(120, 255)
    r = rng.choice([1, 1, 2])
    c = (int(b), int(b * 0.85), int(b * 0.55))
    gd.ellipse([gx - r, gy - r, gx + r, gy + r], fill=c)
ocean += np.asarray(glit, dtype=np.float32)
img[HORIZON:] = ocean[HORIZON:]
# horizon glow line
img[HORIZON - 3:HORIZON + 3] += np.array([60, 90, 80], dtype=np.float32)

# ---------- 10. finish: clip, downscale, save ----------
out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode="RGB")
out = out.filter(ImageFilter.GaussianBlur(0.6))  # tame single-pixel noise for PNG size
out = out.resize((1024, 1024), Image.LANCZOS)
out.save("entry.png", optimize=True)
import os
size = os.path.getsize("entry.png")
print("entry.png bytes:", size, "limit 1048576, ok:", size <= 1048576)
print("dimensions:", out.size)
print("sha256:", hashlib.sha256(open("entry.png", "rb").read()).hexdigest())
