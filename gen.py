#!/usr/bin/env python3
"""Aurora Detonation - a deterministic cosmic scene for ai-excited-01.

Painted entirely in code (numpy light fields + Pillow shapes), fixed seed:
  * a supernova detonation: white-hot core, amber mid-glow, violet fringe,
    plus long diffraction-style rays fanning out across the sky,
  * a sparse-to-dense star field with a few bright sparkle stars,
  * a ringed gas giant hanging in front of the blast, mostly silhouette,
    its rings catching firelight on the near edge,
  * a dark ocean strip along the bottom that mirrors the explosion in a
    trembling column of light.

Rendered at 1600x1600, downsampled to 1024x1024, saved as entry.png
beside this script.  If the file overshoots the byte budget the colour
palette is stepped down until it fits.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SEED = 20261116
SS = 1600                 # supersample canvas
OUT = 1024                # delivered size
BUDGET = 1_000_000        # hard byte ceiling for entry.png
HERE = Path(__file__).resolve().parent


def sky_and_blast():
    """Vectorised light field: backdrop, detonation glow, rays, ocean."""
    yy, xx = np.mgrid[0:SS, 0:SS].astype(np.float32)
    u = xx / SS
    v = yy / SS

    # Backdrop: ink-blue zenith melting into deep teal near the horizon.
    pic = np.empty((SS, SS, 3), dtype=np.float32)
    pic[..., 0] = 3.0 + 7.0 * v
    pic[..., 1] = 8.0 + 20.0 * v ** 2
    pic[..., 2] = 20.0 + 26.0 * v

    # Nebula wash: two soft off-centre clouds tinting the backdrop,
    # violet on the left, teal on the right.
    neb1 = np.exp(-(((u - 0.18) / 0.34) ** 2 + ((v - 0.22) / 0.30) ** 2))
    neb2 = np.exp(-(((u - 0.86) / 0.30) ** 2 + ((v - 0.55) / 0.36) ** 2))
    pic[..., 0] += 34 * neb1 + 10 * neb2
    pic[..., 1] += 12 * neb1 + 30 * neb2
    pic[..., 2] += 52 * neb1 + 44 * neb2

    # Detonation centre, high enough that the planet can eclipse it.
    ex, ey = 0.52 * SS, 0.38 * SS
    dx, dy = xx - ex, yy - ey
    dist = np.hypot(dx, dy) / SS
    theta = np.arctan2(dy, dx)

    # Three nested glow shells: core (with a hotter inner heart),
    # amber blanket, violet fringe.
    core = np.exp(-dist * 7.5) + 0.9 * np.exp(-dist * 16.0)
    blanket = np.exp(-dist * 2.6)
    fringe = np.exp(-dist * 1.1)
    pic[..., 0] += 255 * core + 232 * blanket * 0.5 + 96 * fringe * 0.45
    pic[..., 1] += 246 * core + 138 * blanket * 0.5 + 52 * fringe * 0.45
    pic[..., 2] += 214 * core + 64 * blanket * 0.5 + 150 * fringe * 0.45

    # Rays: two interleaved fan systems, one fine and one bold.
    fine = (0.5 + 0.5 * np.cos(theta * 18 + 0.7)) ** 9
    bold = (0.5 + 0.5 * np.cos(theta * 7 - 1.9)) ** 5
    beam = (0.65 * fine + 0.85 * bold) * np.exp(-dist * 2.4)
    pic[..., 0] += 168 * beam
    pic[..., 1] += 96 * beam
    pic[..., 2] += 40 * beam

    # Expanding pressure shells from the blast.
    for rad, wid, amp in ((0.16, 0.005, 120), (0.27, 0.008, 100),
                          (0.41, 0.012, 78), (0.58, 0.017, 52)):
        ring = np.exp(-((dist - rad) / wid) ** 2) * amp
        pic[..., 0] += ring * 0.8
        pic[..., 1] += ring * 0.95
        pic[..., 2] += ring

    # Ocean: the bottom band below the horizon line.
    horizon = 0.76
    sea = v > horizon
    depth = np.clip((v - horizon) / (1.0 - horizon), 0, 1)
    pic[..., 0] = np.where(sea, 5.0 + 10.0 * depth, pic[..., 0])
    pic[..., 1] = np.where(sea, 52.0 - 20.0 * depth, pic[..., 1])
    pic[..., 2] = np.where(sea, 66.0 - 24.0 * depth, pic[..., 2])

    # Mirror column: the blast reflected, chopped by wave streaks.
    rng = np.random.default_rng(SEED + 31)
    col = np.exp(-((u - 0.52) / 0.11) ** 2) * (1.0 - depth) ** 1.8
    chop = 0.6 + 0.4 * np.sin(v * 540.0 + 9.0 * np.sin(u * 34.0))
    grain = rng.random((SS // 20, SS)).repeat(20, axis=0)[:SS]
    mirror = col * chop * (0.72 + 0.45 * grain) * sea
    pic[..., 0] += 228 * mirror
    pic[..., 1] += 128 * mirror
    pic[..., 2] += 42 * mirror

    # A bright seam right on the horizon.
    seam = np.exp(-((v - horizon) / 0.002) ** 2)
    pic[..., 0] += 70 * seam
    pic[..., 1] += 130 * seam
    pic[..., 2] += 132 * seam

    return Image.fromarray(np.clip(pic, 0, 255).astype(np.uint8), "RGB")


def sprinkle_stars(img):
    """Seeded star field: pinpoints plus a few four-point sparkles."""
    rng = np.random.default_rng(SEED + 101)
    draw = ImageDraw.Draw(img, "RGBA")
    for _ in range(2100):
        sx = rng.random() * SS
        sy = rng.random() * SS * 0.74
        roll = rng.random()
        if roll < 0.06:
            r = rng.uniform(2.0, 3.8)
            tint = (255, 248, 224, 255)
            draw.line([(sx - 3 * r, sy), (sx + 3 * r, sy)], fill=tint)
            draw.line([(sx, sy - 3 * r), (sx, sy + 3 * r)], fill=tint)
        else:
            r = rng.uniform(0.5, 1.7)
            tint = ((255, 206, 140, 225) if rng.random() < 0.28
                    else (186, 232, 255, 225))
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=tint)

    # Shooting stars: a few bright heads with fading segmented tails.
    for _ in range(7):
        mx = rng.random() * SS * 0.88
        my = rng.random() * SS * 0.45
        length = rng.uniform(50, 130)
        slope = rng.uniform(0.25, 0.5)
        for k in range(24):
            t = k / 24
            px, py = mx + length * t, my + length * slope * t
            alpha = int(230 * (1 - t) ** 2)
            r = 1.6 * (1 - t) + 0.4
            draw.ellipse([px - r, py - r, px + r, py + r],
                         fill=(255, 244, 214, alpha))
    return img


def giant_with_rings():
    """Ringed planet on a transparent layer, backlit by the blast."""
    layer = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    gx, gy, gr = 0.52 * SS, 0.40 * SS, 0.145 * SS
    tilt = 0.29
    wide, high = gr * 2.1, gr * 2.1 * tilt

    # Rear ring arcs first so the planet body covers their middle.
    pen = ImageDraw.Draw(layer, "RGBA")
    for scale, rgba, w in ((1.00, (255, 158, 58, 225), 13),
                           (0.85, (88, 226, 205, 205), 10),
                           (0.71, (255, 208, 122, 185), 7)):
        box = [gx - wide * scale, gy - high * scale,
               gx + wide * scale, gy + high * scale]
        pen.arc(box, start=180, end=360, fill=rgba, width=w)

    # Planet disc: numpy shading with banding and a scorched rim.
    yy, xx = np.mgrid[0:SS, 0:SS].astype(np.float32)
    nx, ny = (xx - gx) / gr, (yy - gy) / gr
    d2 = nx * nx + ny * ny
    disc = d2 <= 1.0
    nz = np.sqrt(np.clip(1.0 - d2, 0, 1))
    bands = 0.5 + 0.5 * np.sin(ny * 11.0 + 1.5 * np.sin(nx * 3.0))
    body = np.zeros((SS, SS, 4), dtype=np.float32)
    shade = 0.22 + 0.78 * nz
    body[..., 0] = (22 + 78 * bands) * shade
    body[..., 1] = (84 + 96 * bands) * shade
    body[..., 2] = (104 + 84 * bands) * shade
    lip = np.clip((np.sqrt(d2) - 0.85) / 0.15, 0, 1) ** 2 * disc
    body[..., 0] += 255 * lip
    body[..., 1] += 130 * lip
    body[..., 2] += 36 * lip
    body[..., 3] = disc * 255
    layer.alpha_composite(
        Image.fromarray(np.clip(body, 0, 255).astype(np.uint8), "RGBA"))

    # Front ring arcs crossing the disc.
    pen = ImageDraw.Draw(layer, "RGBA")
    for scale, rgba, w in ((1.00, (255, 170, 76, 235), 13),
                           (0.85, (102, 236, 214, 215), 10),
                           (0.71, (255, 216, 140, 195), 7)):
        box = [gx - wide * scale, gy - high * scale,
               gx + wide * scale, gy + high * scale]
        pen.arc(box, start=8, end=172, fill=rgba, width=w)
    return layer


def render():
    canvas = sprinkle_stars(sky_and_blast()).convert("RGBA")
    canvas.alpha_composite(giant_with_rings())
    canvas = canvas.convert("RGB").filter(ImageFilter.GaussianBlur(0.5))
    final = canvas.resize((OUT, OUT), Image.LANCZOS)

    target = HERE / "entry.png"
    final.save(target, "PNG", optimize=True)
    size = target.stat().st_size
    colours = 256
    while size > BUDGET and colours >= 32:
        final.quantize(colors=colours, method=Image.MEDIANCUT) \
             .convert("RGB").save(target, "PNG", optimize=True)
        size = target.stat().st_size
        colours //= 2
    print(f"wrote {target.name}: {OUT}x{OUT}, {size} bytes")


if __name__ == "__main__":
    render()
