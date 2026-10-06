"""
Procedural finish textures for the v3 (IP3251) materials (materials-agent owned).  python3 scripts/blender/v3/tools/build_textures.py

v3 additions: ORM tiles are generated PER ROUGHNESS (orm_<finish>_r<NN>.jpg, mean G = that material's roughness) so the
glTF export (roughnessFactor 1 x texture) and Cycles both see each material's own roughness; fabric_normal.jpg (fibre
fuzz for the soft rollers); roller_front_basecolor.jpg (black microfibre with the two-start turquoise helix of spare part
383CH1000EUT, raw/tr-part-agiz-yumusak-rulo-1.png).

All tiles are seamless, 512 px, mapped at 1 tile = 50 mm by materials.ensure_uvs() (box projection, V = product up on
side faces), so 0.1 mm per texel.
  plastic_orm.jpg      G = roughness 0.46 +- grain (satin moulded texture, Sagewood/graphite plastics), B = 0 metal
  plastic_normal.jpg   very fine moulded micro-texture (OpenGL +Y normal)
  brushed_orm.jpg      G = roughness 0.30 +- streaks along V (anodized brushed copper / brushed silver), B = 1 metal
  brushed_normal.jpg   brushed micro-grooves along V
Values are absolute (glTF roughnessFactor = 1); the runtime may scale per material (three multiplies factor x map).
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "source", "textures", "v3")
N = 512
rng = np.random.default_rng(3246)


def tile_noise(scale, octaves=4, aniso=None):
    """seamless fBm via FFT-filtered white noise; `scale` = cutoff in cycles per tile. aniso=(sx, sy) divides the
    cutoff per axis (sy >> sx = features long along V/rows-direction, i.e. vertical brushed streaks)."""
    f = np.zeros((N, N))
    fy = np.fft.fftfreq(N)[:, None]
    fx = np.fft.fftfreq(N)[None, :]
    for o in range(octaves):
        w = rng.standard_normal((N, N))
        sx, sy = aniso if aniso else (1, 1)
        r = np.sqrt((fx * sx) ** 2 + (fy * sy) ** 2) * N / (scale / 2 ** o)
        filt = np.exp(-(r ** 2))
        f += np.real(np.fft.ifft2(np.fft.fft2(w) * filt)) * 0.55 ** o
    f -= f.mean()
    return f / (np.abs(f).max() + 1e-9)


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    n = np.dstack([-dx, dy, np.ones_like(h)])  # OpenGL (+Y up in texture = -row)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def save_orm(rough, metal, name):
    img = np.zeros((N, N, 3), np.uint8)
    img[..., 0] = 255
    img[..., 1] = np.clip(rough * 255, 0, 255).astype(np.uint8)
    img[..., 2] = int(metal * 255)
    Image.fromarray(img).save(os.path.join(OUT, name), quality=88)


def _grain():
    return tile_noise(150, 2), tile_noise(4, 2)


def build_orm(finish, rough):
    """per-roughness ORM tile; returns file name (cached on disk, deterministic seed per finish)."""
    global rng
    name = f"orm_{finish}_r{int(round(rough * 100)):02d}.jpg"
    rng = np.random.default_rng(3251 + (0 if finish == "plastic" else 7))
    if finish == "plastic":
        grain, mottle = _grain()
        save_orm(rough + 0.05 * grain + 0.03 * mottle, 0.0, name)
    else:
        streak = tile_noise(140, 3, aniso=(1.0, 45.0))
        fine = tile_noise(240, 1, aniso=(1.0, 20.0))
        patch = tile_noise(3, 2)
        save_orm(rough + 0.05 * streak + 0.025 * fine + 0.02 * patch, 1.0, name)  # r1: 0.09/0.04/0.03 read as wood grain
    return name


def fabric_normal():
    """microfibre fuzz: dense short fibres (random oriented dashes) + fine noise; 1 tile = 20 mm (ensure_uvs tile)."""
    global rng
    rng = np.random.default_rng(99)
    h = tile_noise(220, 2) * 0.6 + tile_noise(60, 2) * 0.4
    Image.fromarray(normal_from_height(h, 1.6)).save(os.path.join(OUT, "fabric_normal.jpg"), quality=88)


# soft roller (front): U = around the roller (0..1 = 360 deg), V = along the axis (0 = product left end, 1 = right end).
ROLLER_TURNS = 4.0          # one helix pitch = 1/4 of the roller length (4 stripe pairs along the spare-part photo)
ROLLER_W, ROLLER_OFF = 0.11, 0.31   # stripe width / second-start offset, fractions of the pitch
TEAL, BLACK = (24, 181, 163), (21, 23, 23)   # spare-part render: stripe median #13948 7 / lit #18c2b2 ; fibre #141616


def roller_front():
    global rng
    rng = np.random.default_rng(383)
    W, H = 1024, 2048
    u = (np.arange(W) + 0.5)[None, :] / W
    v = (np.arange(H) + 0.5)[:, None] / H
    p = 1.0 / ROLLER_TURNS
    d = np.mod((v - p * u) / p, 1.0)
    fuzz = np.array(Image.fromarray(((np.random.default_rng(5).random((H // 2, W // 2))) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)) / 255.0
    e = 0.012 + 0.01 * fuzz          # ragged pile edge
    def band(c):
        return np.clip((d - (c - ROLLER_W / 2) + e) / (2 * e), 0, 1) * np.clip(((c + ROLLER_W / 2) - d + e) / (2 * e), 0, 1)
    m = np.maximum(band(ROLLER_W / 2 + 0.02), band(ROLLER_OFF + ROLLER_W / 2))
    lum = 0.88 + 0.24 * (np.random.default_rng(6).random((H, W)) - 0.5)
    img = (np.array(BLACK)[None, None] * (1 - m[..., None]) + np.array(TEAL)[None, None] * m[..., None]) * lum[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "roller_front_basecolor.jpg"), quality=90)


def main():
    import sys
    os.makedirs(OUT, exist_ok=True)
    global rng
    rng = np.random.default_rng(3246)
    grain, mottle = _grain()
    Image.fromarray(normal_from_height(grain, 0.6)).save(os.path.join(OUT, "plastic_normal.jpg"), quality=86)
    streak = tile_noise(140, 3, aniso=(1.0, 45.0))
    fine = tile_noise(240, 1, aniso=(1.0, 20.0))
    Image.fromarray(normal_from_height(streak + 0.5 * fine, 0.8)).save(os.path.join(OUT, "brushed_normal.jpg"), quality=86)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import ast
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "materials.py")).read()
    cols = ast.literal_eval(src[src.index("COLOURS = {") + 10: src.index("\n}\n", src.index("COLOURS = {")) + 2])
    for name, (_h, rough, _m, finish, _n) in cols.items():
        if finish in ("plastic", "brushed"):
            print(name, build_orm(finish, rough))
    fabric_normal()
    roller_front()
    for n in sorted(os.listdir(OUT)):
        print(n, os.path.getsize(os.path.join(OUT, n)))


if __name__ == "__main__":
    main()
