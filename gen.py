#!/usr/bin/env python3
"""Supernova Crown - a procedural space scene for ai-excited-01.

Renders, with a fixed seed and no external assets:
  * a supernova blast erupting behind a ringed planet,
  * expanding shockwave rings around the blast,
  * a dense starfield over deep-space teal darkness,
  * a glowing ocean below that catches the blast's reflection.

The scene is built at 2048x2048 (numpy for the light fields, Pillow for
the crisp shapes), downscaled to 1024x1024 with LANCZOS, and saved as
entry.png next to this file.  If the PNG is too large, its palette is
reduced step by step until it fits the 1,000,000-byte limit.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SEED = 20261116
BIG = 2048            # render resolution
SMALL = 1024          # final resolution
MAX_BYTES = 1_000_000
HERE = Path(__file__).resolve().parent


def light_field():
    """Background, supernova glow, shockwave rings and ocean (numpy)."""
    rng = np.random.default_rng(SEED)
    y, x = np.mgrid[0:BIG, 0:BIG].astype(np.float32)
    u, v = x / BIG, y / BIG

    # Deep-space backdrop: near-black blue at the top, teal at horizon.
    img = np.zeros((BIG, BIG, 3), dtype=np.float32)
    img[..., 0] = 4 + 10 * v
    img[..., 1] = 10 + 26 * v * v
    img[..., 2] = 22 + 30 * v

    # Supernova centre, slightly above middle: the planet sits over it.
    cx, cy = 0.50 * BIG, 0.40 * BIG
    dx, dy = x - cx, y - cy
    r = np.sqrt(dx * dx + dy * dy) / BIG
    ang = np.arctan2(dy, dx)

    # Radial falloff glow: white core -> gold -> orange -> teal halo.
    glow = np.exp(-r * 5.2)
    halo = np.exp(-r * 1.7)
    img[..., 0] += 255 * glow + 235 * halo * 0.55
    img[..., 1] += 244 * glow + 150 * halo * 0.55
    img[..., 2] += 205 * glow + 90 * halo * 0.60

    # Eruption rays: twelve broad beams modulated around the circle.
    rays = (0.5 + 0.5 * np.cos(ang * 12 + 1.3)) ** 6
    rays += 0.6 * (0.5 + 0.5 * np.cos(ang * 5 - 0.6)) ** 8
    beam = rays * np.exp(-r * 3.1)
    img[..., 0] += 200 * beam
    img[..., 1] += 120 * beam
    img[..., 2] += 55 * beam

    # Shockwave rings: sharp bright shells at growing radii.
    for radius, width, gain in ((0.19, 0.006, 150), (0.31, 0.009, 120),
                                (0.46, 0.013, 95), (0.64, 0.018, 70)):
        shell = np.exp(-((r - radius) / width) ** 2) * gain
        img[..., 0] += shell * 0.85
        img[..., 1] += shell
        img[..., 2] += shell

    # Glowing ocean: everything below the horizon line.
    horizon = 0.74
    sea = v > horizon
    depth = np.clip((v - horizon) / (1 - horizon), 0, 1)
    # Vertical teal gradient for the water itself.
    img[..., 0] = np.where(sea, 6 + 14 * depth, img[..., 0])
    img[..., 1] = np.where(sea, 60 - 26 * depth, img[..., 1])
    img[..., 2] = np.where(sea, 78 - 30 * depth, img[..., 2])
    # The blast's reflection: a warm column under the supernova,
    # broken into horizontal streaks so it reads as moving water.
    col = np.exp(-((u - 0.50) / 0.13) ** 2) * (1 - depth) ** 1.6
    streak = 0.65 + 0.35 * np.sin(v * 620 + 14 * np.sin(u * 40))
    flicker = rng.random((BIG // 16, BIG))
    flicker = np.repeat(flicker, 16, axis=0)[:BIG]
    refl = col * streak * (0.7 + 0.5 * flicker) * sea
    img[..., 0] += 235 * refl
    img[..., 1] += 140 * refl
    img[..., 2] += 45 * refl
    # Foam-bright horizon line.
    line = np.exp(-((v - horizon) / 0.0022) ** 2)
    img[..., 0] += 90 * line
    img[..., 1] += 150 * line
    img[..., 2] += 150 * line

    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def add_stars(img):
    """Deterministic starfield: dots, a few bright crosses, no text."""
    rng = np.random.default_rng(SEED + 7)
    draw = ImageDraw.Draw(img, "RGBA")
    for _ in range(1500):
        sx, sy = rng.random() * BIG, rng.random() * BIG * 0.72
        if rng.random() < 0.08:      # a handful of hero stars
            rad = rng.uniform(2.2, 4.2)
            col = (255, 250, 230, 255)
            draw.line([(sx - rad * 3, sy), (sx + rad * 3, sy)], fill=col)
            draw.line([(sx, sy - rad * 3), (sx, sy + rad * 3)], fill=col)
        else:
            rad = rng.uniform(0.6, 1.9)
            warm = rng.random() < 0.3
            col = (255, 214, 150, 230) if warm else (190, 240, 255, 230)
        draw.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=col)
    return img


def planet_layer():
    """The ringed planet as its own RGBA layer, lit from behind."""
    layer = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    pcx, pcy, pr = 0.50 * BIG, 0.42 * BIG, 0.155 * BIG

    # Back half of the ring system (drawn before the planet body).
    tilt = 0.30
    rw, rh = pr * 2.05, pr * 2.05 * tilt
    for k, (rr, col, w) in enumerate((
            (1.00, (255, 166, 66, 235), 15), (0.86, (94, 234, 212, 220), 11),
            (0.72, (255, 214, 130, 200), 8))):
        box = [pcx - rw * rr, pcy - rh * rr, pcx + rw * rr, pcy + rh * rr]
        draw.arc(box, start=180, end=360, fill=col, width=w)

    # Planet body: build a shaded sphere in numpy, paste it in.
    yy, xx = np.mgrid[0:BIG, 0:BIG].astype(np.float32)
    nx, ny = (xx - pcx) / pr, (yy - pcy) / pr
    d2 = nx * nx + ny * ny
    inside = d2 <= 1.0
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    bands = 0.5 + 0.5 * np.sin(ny * 13 + 1.8 * np.sin(nx * 3.5))
    sphere = np.zeros((BIG, BIG, 4), dtype=np.float32)
    shade = 0.24 + 0.76 * nz                       # limb darkening
    sphere[..., 0] = (26 + 90 * bands) * shade     # teal body,
    sphere[..., 1] = (96 + 105 * bands) * shade    # banded like a
    sphere[..., 2] = (118 + 92 * bands) * shade    # gas giant
    rim = np.clip((np.sqrt(d2) - 0.86) / 0.14, 0, 1) ** 2 * inside
    sphere[..., 0] += 255 * rim                    # orange corona rim
    sphere[..., 1] += 138 * rim                    # where the blast
    sphere[..., 2] += 40 * rim                     # leaks past it
    sphere[..., 3] = inside * 255
    layer.alpha_composite(
        Image.fromarray(np.clip(sphere, 0, 255).astype(np.uint8), "RGBA"))

    # Front half of the rings, crossing the planet's face.
    draw = ImageDraw.Draw(layer, "RGBA")
    for rr, col, w in ((1.00, (255, 176, 84, 245), 15),
                       (0.86, (110, 242, 220, 230), 11),
                       (0.72, (255, 222, 150, 210), 8)):
        box = [pcx - rw * rr, pcy - rh * rr, pcx + rw * rr, pcy + rh * rr]
        draw.arc(box, start=8, end=172, fill=col, width=w)
    return layer


def main():
    scene = light_field()
    scene = add_stars(scene)
    scene = scene.convert("RGBA")
    scene.alpha_composite(planet_layer())
    scene = scene.convert("RGB")
    # A whisper of blur melts banding before the downscale.
    scene = scene.filter(ImageFilter.GaussianBlur(0.6))
    final = scene.resize((SMALL, SMALL), Image.LANCZOS)

    out = HERE / "entry.png"
    final.save(out, "PNG", optimize=True)
    size = out.stat().st_size
    colors = 256
    while size > MAX_BYTES and colors >= 32:
        final.quantize(colors=colors, method=Image.MEDIANCUT) \
             .convert("RGB").save(out, "PNG", optimize=True)
        size = out.stat().st_size
        colors //= 2
    print(f"entry.png: {final.size[0]}x{final.size[1]}, {size} bytes")


if __name__ == "__main__":
    main()
