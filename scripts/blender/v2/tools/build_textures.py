"""
Procedural finish textures for the v2 materials (materials-agent owned).  python3 scripts/blender/v2/tools/build_textures.py

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
OUT = os.path.join(ROOT, "assets", "source", "textures", "v2")
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


def main():
    os.makedirs(OUT, exist_ok=True)
    # satin moulded plastic: fine isotropic grain (~0.3 mm) + soft low-frequency mottling
    grain = tile_noise(150, 2)
    mottle = tile_noise(4, 2)
    save_orm(0.46 + 0.05 * grain + 0.03 * mottle, 0.0, "plastic_orm.jpg")
    Image.fromarray(normal_from_height(grain, 0.6)).save(os.path.join(OUT, "plastic_normal.jpg"), quality=86)
    # brushed metal: long streaks along V (rows vary slowly, columns fast)
    streak = tile_noise(140, 3, aniso=(1.0, 45.0))
    fine = tile_noise(240, 1, aniso=(1.0, 20.0))
    patch = tile_noise(3, 2)
    save_orm(0.30 + 0.09 * streak + 0.04 * fine + 0.03 * patch, 1.0, "brushed_orm.jpg")
    Image.fromarray(normal_from_height(streak + 0.5 * fine, 0.8)).save(os.path.join(OUT, "brushed_normal.jpg"), quality=86)
    for n in ("plastic_orm.jpg", "plastic_normal.jpg", "brushed_orm.jpg", "brushed_normal.jpg"):
        print(n, os.path.getsize(os.path.join(OUT, n)))


if __name__ == "__main__":
    main()
