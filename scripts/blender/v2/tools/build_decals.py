"""
Builds the v2 marking atlas (M_Decal) from the official reference imagery. Materials-agent owned.

  python3 scripts/blender/v2/tools/build_decals.py

Every marking is EXTRACTED from SharkNinja imagery (crop -> deskew -> soft threshold to an alpha mask), never re-typeset:
  - "Shark" wordmark + "POWERDETECTSPEED" : IA3000 marketing lock-up (raw/sn-3241laa-13.jpg, 4500 px) — the same
    artwork that is printed on the handheld plate / band and on the copper wand (checked against the Sagewood hero
    raw/sn-gn-hero.png). (R) and (TM) marks removed (not visible on the product at any reference resolution).
  - "TURBOPRO DETECT" : brushroll window print, raw/sn-gal2.jpg (near-orthographic top-front view, 0.4 deg deskew).
  - display face icons : owner's guide p.7 illustration of the handheld UI screen (technical/manual_pages).
Ink colours are sampled from the Sagewood hero (sn-gn-hero.png).
Writes assets/source/textures/v2/decal_atlas.png and scripts/blender/v2/decals.json (UV rects, Blender convention).
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(V2, "..", "..", ".."))
RAW = os.path.join(ROOT, "assets", "references", "ia3246", "raw")
MAN = os.path.join(ROOT, "assets", "references", "ia3246", "technical", "manual_pages")
OUT_TEX = os.path.join(ROOT, "assets", "source", "textures", "v2")
AW, AH = 2048, 1024
PAD = 0.04


def smooth(x, lo, hi):
    t = np.clip((x - lo) / float(hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def mask_lockup(box, kill=()):
    im = np.array(Image.open(os.path.join(RAW, "sn-3241laa-13.jpg")).convert("RGB")).astype(float)
    x0, y0, x1, y1 = box
    a = smooth(im[y0:y1, x0:x1].max(2), 95, 185)
    for kx0, ky0, kx1, ky1 in kill:
        a[ky0 - y0:ky1 - y0, kx0 - x0:kx1 - x0] = 0
    return a


TB, TLO = 4.0, 0.30


def mask_turbo():
    """On-product print = TURBO light italic + PRO bold italic + DETECT light italic (sn-gal2 head close-up).
    gal2's 'TURBOPRO' is clean but the brush strip crosses the end of 'DETECT', so 'DETECT' is taken from the official
    TURBOPRO DETECT lock-up (amz ...pt11), whose light-italic DETECT is the same artwork: scaled to gal2's cap height
    it lands on gal2's DETECT extent within 2 px (747..882 vs 747..880). (The lock-up's TURBO/PRO weights are swapped
    vs the product, so only its DETECT is used.)"""
    K = 8
    cx0, cy0, cx1, cy1 = 530, 1300, 896, 1360
    im = Image.open(os.path.join(RAW, "sn-gal2.jpg")).convert("RGB").crop((cx0, cy0, cx1, cy1))
    im = im.resize((im.width * K, im.height * K), Image.LANCZOS).rotate(-0.42, resample=Image.BICUBIC)
    a = smooth(np.array(im).astype(float).min(2), 110, 170)
    a = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(TB))) / 255.0
    a = smooth(a, TLO, TLO + 0.12)
    split = (740 - cx0) * K
    a[:, split:] = 0
    rows = np.where((a[:, :split] > 0.5).any(1))[0]
    top, bot = rows.min(), rows.max()
    lk = np.array(Image.open(os.path.join(RAW, "amz-frosted-sage-ia3243-pt11-81nGT4DAH1L.jpg")).convert("RGB"))
    d = smooth(lk[363:516, 1466:2326].astype(float).max(2), 95, 185)
    h = bot - top + 1
    w = int(d.shape[1] * h / d.shape[0])
    d = np.array(Image.fromarray((d * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)) / 255.0
    x = (747 - cx0) * K
    if x + w > a.shape[1]:
        a = np.pad(a, ((0, 0), (0, x + w - a.shape[1] + 4)))
    a[top:top + h, x:x + w] = np.maximum(a[top:top + h, x:x + w], d[:, :w])
    return a


def mask_display():
    im = Image.open(os.path.join(MAN, "ia3000uk_og_p-07.png")).convert("L").crop((195, 255, 405, 495))
    im = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
    a = np.array(im).astype(float) / 255.0
    h, w = a.shape
    a[: int(0.16 * h), : int(0.3 * w)] = 0       # outer LED-ring arcs (modelled as emissive geometry, not decal)
    a[: int(0.16 * h), int(0.7 * w):] = 0
    # icons: white = lit, grey = unlit (as drawn in the guide); black screen -> transparent
    return a


def mask_moon():
    """Quiet-mode moon on the dock post (owner's guide p.16 inset: dark disc with a light crescent) -> crescent only."""
    im = Image.open(os.path.join(MAN, "ia3000uk_og_p-09.png")).convert("L").crop((126, 976, 174, 1024))
    K = 12
    im = im.resize((im.width * K, im.height * K), Image.BICUBIC)
    a = np.array(im).astype(float) / 255.0
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    cx, cy, r = 24 * K, 24 * K, 16.5 * K   # disc centre (150, 1000) page px, crescent lies inside r ~17
    inside = ((xx - cx) ** 2 + (yy - cy) ** 2) < r * r
    m = smooth(a, 0.45, 0.8) * inside
    m = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(K * 0.6))) / 255.0
    return smooth(m, 0.35, 0.6)


def trim(a, thr=0.06):
    ys, xs = np.where(a > thr)
    return a[max(0, ys.min() - 2):ys.max() + 3, max(0, xs.min() - 2):xs.max() + 3]


def place(atlas, a, rect, rgb, lum=None):
    """Fit alpha mask `a` into pixel rect (x0,y0,x1,y1, top-left origin) keeping aspect; return ink rect."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    iw, ih = w * (1 - 2 * PAD), h * (1 - 2 * PAD)
    s = min(iw / a.shape[1], ih / a.shape[0])
    nw, nh = max(1, int(a.shape[1] * s)), max(1, int(a.shape[0] * s))
    m = np.array(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)) / 255.0
    ox, oy = x0 + (w - nw) // 2, y0 + (h - nh) // 2
    atlas[oy:oy + nh, ox:ox + nw, 3] = np.maximum(atlas[oy:oy + nh, ox:ox + nw, 3], m * 255)
    col = np.array(rgb, float)
    if lum is not None:
        L = np.array(Image.fromarray((np.clip(lum, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)) / 255.0
        atlas[oy:oy + nh, ox:ox + nw, :3] = (L[..., None] * col)
    else:
        atlas[oy:oy + nh, ox:ox + nw, :3] = col
    return (ox, oy, ox + nw, oy + nh)


def uv(r):
    """pixel rect (top-left origin) -> Blender UV rect [u0, v0, u1, v1] (v up)."""
    x0, y0, x1, y1 = r
    return [round(x0 / AW, 5), round(1 - y1 / AH, 5), round(x1 / AW, 5), round(1 - y0 / AH, 5)]


SLOTS = [
    # name, slot px rect (x0,y0,x1,y1 top-left), ink sRGB, source, where on the product
    ("pds_wand_white", (0, 0, 2048, 224), (247, 247, 245), "lockup",
     "copper lower wand front face. Reads top->bottom along the wand; seen from the front the glyph tops face the viewer's "
     "right (text rotated 90 deg CW). Hero: ink length ~245 px / 1.559 = ~157 mm, cap height ~11 mm."),
    ("pds_band_dark", (0, 224, 2048, 448), (31, 33, 32), "lockup",
     "handheld: brushed silver band directly under the Shark plate, horizontal, centred. Hero: band ~90 px = 58 mm "
     "wide, ink fills ~85 % -> ~49 mm long, ~3.5 mm cap height."),
    ("shark_white", (0, 448, 768, 704), (244, 245, 244), "lockup",
     "handheld front grey plate (above the band), and the dark plate on the handle top (sn-gal1). Hero: ink width ~62 px "
     "= ~40 mm on the handheld."),
    ("shark_neck", (768, 448, 1536, 704), (224, 225, 224), "lockup",
     "floorhead neck/yoke top plate in front of the wand knuckle (printed light grey). Hero: ink width ~58 px = ~37 mm."),
    ("turbopro_detect", (0, 704, 1536, 832), (226, 226, 225), "turbo",
     "floorhead smoked brushroll window, left of centre, horizontal, on the window's front face. Hero: ink width "
     "~120 px / 1.6 = ~75 mm, starts ~22 mm from the window's left end."),
    ("display_icons", (1536, 448, 2048, 880), (159, 203, 230), "display",
     "handheld UI screen (rear of the handheld, above the handle, per owner's guide p.7): eco leaf / detect rings / "
     "boost swirl / drop icons, light bar, battery icon. Map onto the M_Screen face (decal plate 0.2 mm above). "
     "Ink brightness encodes lit vs unlit (grey) as drawn in the guide; lit glyph colour #9fcbe6 (ref-director median "
     "of the Sagewood display glyphs, light ice-blue)."),
    ("dock_moon", (1792, 896, 2048, 1024), (236, 237, 236), "moon",
     "dock: Quiet-mode moon icon above the slide switch (owner's guide p.16). Cell = the dock agent's existing square "
     "8.5 mm quad (u 0.875-1, v 0-0.125); the 256x128 px cell is drawn PRE-STRETCHED 2:1 so it reads round on that "
     "square quad (pixelAspect 2)."),
]


def main():
    os.makedirs(OUT_TEX, exist_ok=True)
    atlas = np.zeros((AH, AW, 4), float)
    shark = trim(mask_lockup((2000, 255, 2545, 410), kill=[(2510, 374, 2545, 410)]))
    pds = trim(mask_lockup((1515, 430, 2961, 550)))
    turbo = trim(mask_turbo())
    disp = mask_display()
    layout = {"atlas": "assets/source/textures/v2/decal_atlas.png", "size": [AW, AH],
              "uv_convention": "Blender UV, origin bottom-left, rect = [u0, v0, u1, v1]. 'ink' = tight box of the "
                               "letters; map your plate's full face to 'ink' so the marking fills it edge to edge, or "
                               "to 'slot' for a margin. glyph 'up' = +v.",
              "slots": {}}
    for name, rect, rgb, kind, where in SLOTS:
        if kind == "lockup":
            a = shark if name.startswith("shark") else pds
            ink = place(atlas, a, rect, rgb)
        elif kind == "turbo":
            ink = place(atlas, turbo, rect, rgb)
        elif kind == "moon":
            mm = trim(mask_moon())
            mm = np.array(Image.fromarray((mm * 255).astype(np.uint8)).resize((mm.shape[1] * 2, mm.shape[0]), Image.LANCZOS)) / 255.0
            ink = place(atlas, mm, rect, rgb)
        else:
            ink = place(atlas, smooth(disp, 0.14, 0.45), rect, rgb, lum=np.clip(disp * 1.4, 0, 1))
        layout["slots"][name] = {
            "slot": uv(rect), "ink": uv(ink),
            "inkAspect": round((ink[2] - ink[0]) / (ink[3] - ink[1]), 4),
            "colorSRGB": "#%02x%02x%02x" % rgb, "where": where,
            **({"pixelAspect": 2.0} if kind == "moon" else {}),
        }
    atlas[..., :3] = np.where(atlas[..., 3:4] > 0, atlas[..., :3], 0)
    out = os.path.join(OUT_TEX, "decal_atlas.png")
    _bleed(atlas)
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8), "RGBA").save(out, optimize=True)
    with open(os.path.join(V2, "decals.json"), "w") as f:
        json.dump(layout, f, indent=2)
    print("atlas", out, os.path.getsize(out), "bytes")


def _bleed(atlas):
    """Dilate ink RGB into fully transparent texels inside each slot (alpha untouched)."""
    a = atlas[..., 3]
    rgb = atlas[..., :3].copy()
    filled = a > 8
    for _ in range(12):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(a.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(rgb, dy, 0), dx, 1)
            sf = np.roll(np.roll(filled, dy, 0), dx, 1)
            acc += sh * sf[..., None]
            cnt += sf
        grow = (~filled) & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]
        filled = filled | grow
    atlas[..., :3] = rgb


if __name__ == "__main__":
    main()
