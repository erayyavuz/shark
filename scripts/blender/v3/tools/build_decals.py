"""
Builds the v3 (IP3251 / IP3251EUT) marking atlas (M_Decal / M_DockDisplay). Materials-agent owned.

  python3 scripts/blender/v3/tools/build_decals.py          (needs PyMuPDF for the manual vector art)

Every marking is EXTRACTED from SharkNinja artwork, never re-typeset:
  - "Shark" wordmark (shark_frame, shark_neck): vector header logo of the TR owner's manual (IP3251_TR_owners_manual.pdf
    p8 header), rendered at 2880 dpi. Same wordmark as on the product (cl-eut-01, user frame 1663).
  - "Shark POWERDETECT" (wand): official TR photo raw/tr-ip3251eut-11.jpg (4472 px, wand front face, near-frontal),
    background-normalised + soft threshold; rotated to horizontal.
  - "POWERDETECT" (powerdetect_plate, dock_powerdetect): the POWERDETECT part of that same wand artwork (POWER bold +
    DETECT light, the two-weight logotype seen on the handheld label in user frame 1663 and on the dock badge).
  - "duo clean DETECT": raw/cl-na-06.jpg (3600 px official render, head cover plate), un-bent along a quadratic baseline
    fit (the plate is curved and seen obliquely).
  - screen_icons_tr: TR manual p8 vector drawing of the handheld screen (Variant A). LED-ring arcs (modelled as emissive
    geometry) and the call-out arrow removed; glyph brightness kept as drawn (lit white / unlit grey); per-icon tints
    from the reference director's TR screen notes (ECO leaf green, battery bar cyan, power pill purple).
  - odour_dial: official TR photo raw/tr-ip3251eut-01.jpg inset (EU "ANTI-ODOUR TECHNOLOGY" dial face), ellipse
    rectified to a circle (affine).
  - dock_binfull: TR manual p14 vector inset 'TOZ KUTUSU DOLU GOSTERGESI' (bin-with-dust icon + moon), de-foreshortened.
Writes assets/source/textures/v3/decal_atlas.png and scripts/blender/v3/decals.json (UV rects, Blender convention).
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(V3, "..", "..", ".."))
REF = os.path.join(ROOT, "assets", "references", "ip3251")
RAW = os.path.join(REF, "raw")
PDF = os.path.join(REF, "technical", "manuals", "IP3251_TR_owners_manual.pdf")
OUT_TEX = os.path.join(ROOT, "assets", "source", "textures", "v3")
DEBUG = os.environ.get("DECAL_DEBUG")
AW, AH = 2048, 2048
PAD = 0.04


def smooth(x, lo, hi):
    t = np.clip((x - lo) / float(hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def from_img(im):
    return np.array(im).astype(float) / 255.0


def trim(a, thr=0.06, pad=2):
    ys, xs = np.where(a > thr)
    return a[max(0, ys.min() - pad):ys.max() + pad + 1, max(0, xs.min() - pad):xs.max() + pad + 1]


def dbg(name, a):
    if DEBUG:
        os.makedirs(DEBUG, exist_ok=True)
        (to_img(a) if isinstance(a, np.ndarray) and a.ndim == 2 else Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))).save(os.path.join(DEBUG, name + ".png"))


def map_coordinates(img, coords, order=1):
    """numpy bilinear sampler (scipy.ndimage.map_coordinates order=1 stand-in; edge-clamped)."""
    ys, xs = coords
    h, w = img.shape
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 2)
    fx = np.clip(xs - x0, 0, 1)
    fy = np.clip(ys - y0, 0, 1)
    a = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    b = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def pdf_clip(pno, rect, zoom):
    import fitz
    d = fitz.open(PDF)
    pm = d[pno].get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=fitz.Rect(*rect))
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.h, pm.w, pm.n)[..., :3].astype(float)


# ---------------------------------------------------------------- sources
def mask_shark():
    """TR manual p8 header wordmark: black ink on the light-grey header band."""
    im = pdf_clip(7, (359.8, 7.2, 408.4, 25.2), 40).mean(2)
    return trim(smooth(255 - im, 60, 160))


def _wand_crop():
    """tr-ip3251eut-11: wand front face, text column 'Shark POWERDETECT' read top->bottom (glyph tops to the right)."""
    im = np.array(Image.open(os.path.join(RAW, "tr-ip3251eut-11.jpg")).convert("RGB")).astype(float)
    x0, y0, x1, y1 = 2060, 200, 2190, 1400
    c = im[y0:y1, x0:x1].mean(2)
    # local background (champagne tube, lit gradient) via a wide max/blur -> ink darkness relative to it
    bg = np.array(to_img(c / 255).filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(10))) / 255.0 * 255
    dark = np.clip((bg - c) / np.maximum(bg, 1), 0, 1)
    a = smooth(dark, 0.18, 0.42)
    a = np.rot90(a, 1)   # CCW: top->bottom text becomes left->right, upright
    return a


def _unwarp_band(a, top0, top1, bot0, bot1, margin=0.25, out_h=None):
    """column-wise perspective fix for a text band: glyph top/bottom lines run linearly from (top0, bot0) at x=0 to
    (top1, bot1) at x=w-1. Rows are re-sampled so the band is level with constant height; columns are stretched by the
    local scale so far (smaller) glyphs regain their width."""
    h, w = a.shape
    x = np.arange(w, dtype=float)
    top = top0 + (top1 - top0) * x / (w - 1)
    bot = bot0 + (bot1 - bot0) * x / (w - 1)
    hh = bot - top
    H0 = hh[0]
    out_h = out_h or int(round(H0 * (1 + 2 * margin)))
    # x stretch: cumulative H0 / h(x)
    xs_out = np.concatenate([[0], np.cumsum(H0 / hh[:-1])])
    W = int(xs_out[-1])
    src_x = np.interp(np.arange(W), xs_out, x)
    t = (np.arange(out_h)[:, None] / (out_h - 1)) * (1 + 2 * margin) - margin   # 0 = top line, 1 = bottom line
    tt = np.interp(src_x, x, top)[None, :]
    bb = np.interp(src_x, x, bot)[None, :]
    sy = tt + t * (bb - tt)
    sx = np.broadcast_to(src_x[None, :], sy.shape)
    return map_coordinates(a, [sy, sx])


def mask_wand():
    a = _wand_crop()
    a[:30] = 0
    a[110:] = 0
    # measured glyph top/bottom lines (cap/baseline incl. 'k' ascender): top 55 -> 40, bottom 102 -> 81 over 1200 px
    a = _unwarp_band(a, 55.5, 39.5, 102.5, 80.5)
    K = 3
    a = from_img(to_img(a).resize((a.shape[1] * K, a.shape[0] * K), Image.LANCZOS))
    a = smooth(from_img(to_img(a).filter(ImageFilter.GaussianBlur(1.2))), 0.3, 0.6)
    a = trim(a)
    # tr-ip3251eut-11 sees the tube face obliquely, which compresses glyph HEIGHT (it runs across the tube). Restore the
    # true proportions from the orthographic front render cl-eut-01: ink 270 x 20.5 px = 174 x 13.2 mm -> aspect 13.2.
    h = int(round(a.shape[1] / WAND_ASPECT))
    a = from_img(to_img(a).resize((a.shape[1], h), Image.LANCZOS))
    # re-cut the stretched photo edges: blur + steeper threshold = clean glyph contours
    return smooth(from_img(to_img(a).filter(ImageFilter.GaussianBlur(3.0))), 0.42, 0.58)


WAND_ASPECT = 13.2


def split_powerdetect(a):
    """cut 'Shark ' off the wand lock-up at the widest empty column gap."""
    col = (a > 0.3).sum(0)
    empty = col == 0
    best, cur, bs, s = 0, 0, 0, 0
    for i, e in enumerate(empty):
        if e:
            if cur == 0:
                s = i
            cur += 1
            if cur > best:
                best, bs = cur, s
        else:
            cur = 0
    return trim(a[:, bs + best:]), trim(a[:, :bs]), best


def mask_duoclean():
    """cl-na-06 head cover plate: un-bend along a quadratic baseline through measured glyph-bottom points."""
    im = np.array(Image.open(os.path.join(RAW, "cl-na-06.jpg")).convert("RGB")).astype(float)
    X0, Y0, K = 660, 300, 3.0
    # baseline points in the 3x crop frame (d bowl, o bowl, D foot, last T foot) -> source px
    pts = np.array([(95, 545), (395, 452), (712, 325), (1185, 135)], float)
    px, py = X0 + pts[:, 0] / K, Y0 + pts[:, 1] / K
    cf = np.polyfit(px, py, 2)
    f = np.poly1d(cf)
    df = f.deriv()
    S = 6.0                     # output px per source px
    xs = [px.min() - 6]
    while xs[-1] < px.max() + 4:
        xs.append(xs[-1] + 1.0 / S / np.sqrt(1 + df(xs[-1]) ** 2))
    xs = np.array(xs)
    up_lo, up_hi = -12.0, 40.0   # source px below / above the baseline (rules + caps)
    js = np.arange(up_hi, up_lo, -1.0 / S)
    tx, ty = 1 / np.sqrt(1 + df(xs) ** 2), df(xs) / np.sqrt(1 + df(xs) ** 2)
    nx, ny = ty, -tx             # image 'up' normal (y down)
    sx = xs[None, :] + js[:, None] * nx[None, :]
    sy = f(xs)[None, :] + js[:, None] * ny[None, :]
    ch = [map_coordinates(im[..., k], [sy, sx], order=1) for k in range(3)]
    rgb = np.dstack(ch)
    L = rgb.mean(2)
    sat = rgb.max(2) - rgb.min(2)
    bg = np.array(to_img(L / 255).filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(20))) / 255.0 * 255
    dark = np.clip((bg - L) / np.maximum(bg, 1), 0, 1)
    a = smooth(dark, 0.22, 0.45) * (1 - smooth(sat, 35, 70))
    dbg("duo_unbent", rgb)
    return trim(smooth(from_img(to_img(a).filter(ImageFilter.GaussianBlur(1.5))), 0.3, 0.6))


def screen_icons():
    """TR manual p8 screen (Variant A). Returns (alpha, rgb 0..255)."""
    im = pdf_clip(7, (12.6, 124.1, 98.9, 210.5), 24)
    L = im.mean(2)
    h, w = L.shape
    dark = L < 40
    ys, xs = np.where(dark)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    R = (ys.max() - ys.min()) / 2
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - cx, yy - cy)
    keep = (r < 0.81 * R) & (xx < cx + 0.56 * R)
    lum = np.clip((L - 20) / 235.0, 0, 1) * keep
    # square crop = circumscribed square of the screen disc (the LED ring lies outside 0.83 R)
    x0, y0 = int(cx - R), int(cy - R)
    lum = lum[y0:y0 + int(2 * R), x0:x0 + int(2 * R)]
    n = lum.shape[0]
    yy, xx = np.mgrid[0:n, 0:lum.shape[1]] / float(n)
    rgb = np.ones(lum.shape + (3,)) * 255
    # TR unit shipping film (frames/vid-T9U8rtc6cJk-t1010.0, reference-director 2026-10-05) = this Variant A layout
    # WITHOUT the drop icon, printed in colour: ECO leaf green, DETECT target white, BOOST fan red, battery bar white,
    # battery+bolt white, 'FO' grey, power pill solid light grey with a dark glyph. Orientation unchanged: power pill
    # at the bottom (toward the grip), DETECT target at the top.
    drop = (xx > 0.42) & (xx < 0.58) & (yy > 0.34) & (yy < 0.49)
    lum[drop] = 0
    leaf = (xx > 0.23) & (xx < 0.39) & (yy > 0.23) & (yy < 0.39)
    fan = (xx > 0.61) & (xx < 0.77) & (yy > 0.23) & (yy < 0.39)
    for m, c in ((leaf, (92, 200, 110)), (fan, (232, 78, 96))):
        rgb[m] = c
        lum[m] = np.clip(lum[m] / max(lum[m].max(), 1e-3) * 0.9, 0, 1)
    rgb[(yy > 0.80)] = (226, 226, 228)
    fo = (xx > 0.62) & (xx < 0.71) & (yy > 0.64) & (yy < 0.71)
    lum[fo] = np.clip(lum[fo] / max(lum[fo].max(), 1e-3) * 0.8, 0, 1)   # film: 'FO' printed light, not dim grey
    a = smooth(lum, 0.10, 0.40)
    dbg("screen", a)
    return a, rgb, lum


def binfull():
    """TR manual p14 inset: icons on the black pill window. bin icon grey (as drawn), moon white."""
    im = pdf_clip(13, (277, 365, 315, 420), 40).mean(2)
    # icon boxes in this render (px): bin icon, moon
    bin_ = im[401:726, 517:951]
    moon = im[1012:1342, 550:1067]
    out = []
    for g in (bin_, moon):
        lum = np.clip((g - 15) / 240.0, 0, 1)
        lum = from_img(to_img(lum).resize((g.shape[1], int(g.shape[0] * 1.18)), Image.LANCZOS))
        out.append(trim(lum, 0.05, 6))
    return out


FR = os.path.join(REF, "frames")


def _bright_mask(path, box, lo=0.10, hi=0.30, K=4):
    """light ink on a grey moulding: brightness above the local background, upsampled K x."""
    im = np.array(Image.open(path).convert("RGB")).astype(float)
    x0, y0, x1, y1 = box
    L = im[y0:y1, x0:x1].mean(2)
    bg = np.array(to_img(L / 255).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(8))) / 255.0 * 255
    d = np.clip((L - bg) / 255.0, 0, 1)
    a = from_img(to_img(d).resize((L.shape[1] * K, L.shape[0] * K), Image.BICUBIC))
    a = smooth(from_img(to_img(a).filter(ImageFilter.GaussianBlur(K * 0.5))), lo, hi)
    return a


def mask_edge_detect():
    """vid-JCGXMfx8SG8 t176.9 (real unit close-up): 'EDGE DETECT' on the side-cap front face, reads bottom->top."""
    a = _bright_mask(os.path.join(FR, "vid-JCGXMfx8SG8-t0176.9.jpg"), (1866, 812, 1920, 1074), 0.07, 0.16)
    return trim(np.rot90(a, -1))   # clockwise -> horizontal, upright


def mask_foot():
    """same frame: shoe-sole pictogram on the deck, right of the neck plate in that view (product's left)."""
    a = _bright_mask(os.path.join(FR, "vid-JCGXMfx8SG8-t0176.9.jpg"), (1640, 610, 1718, 758), 0.08, 0.22)
    return trim(a)


LABEL_QUAD = ((635, 199), (783, 142), (805, 199), (660, 263))   # TL, TR, BR, BL in vid-wuXUwo0Itxg-t0160 (px)
LABEL_ASPECT = 2.05   # foreshortening corrected with the Shark wordmark's true aspect (3.84 vs 4.3 seen)


def label_rating():
    """white rating sticker on the neck underside: bilinear quad rectification. Returns (alpha, rgb)."""
    im = np.array(Image.open(os.path.join(FR, "vid-wuXUwo0Itxg-t0160.0.jpg")).convert("RGB")).astype(float)
    W = 600
    H = int(W / LABEL_ASPECT)
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = LABEL_QUAD
    u = (np.arange(W) + 0.5)[None, :] / W
    v = (np.arange(H) + 0.5)[:, None] / H
    sx = (1 - v) * ((1 - u) * x0 + u * x1) + v * ((1 - u) * x3 + u * x2)
    sy = (1 - v) * ((1 - u) * y0 + u * y1) + v * ((1 - u) * y3 + u * y2)
    rgb = np.dstack([map_coordinates(im[..., k], [sy, sx]) for k in range(3)])
    L = rgb.mean(2)
    # sticker = white field + black print; normalise paper to #f1f1ef, ink to #1c1c1e
    paper = np.percentile(L, 90)
    t = np.clip(L / paper, 0, 1)
    ink = smooth(1 - t, 0.25, 0.6)
    col = np.array([241, 241, 239])[None, None] * (1 - ink[..., None]) + np.array([28, 28, 30])[None, None] * ink[..., None]
    # rounded-rect alpha (corner r = 6 % of height)
    r = 0.12 * H
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    dx = np.maximum(0, np.maximum(r - xx, xx - (W - 1 - r)))
    dy = np.maximum(0, np.maximum(r - yy, yy - (H - 1 - r)))
    alpha = np.clip(r - np.hypot(dx, dy) + 0.5, 0, 1)
    dbg("label", col)
    return alpha, col


# ---------------------------------------------------------------- atlas
def place(atlas, a, rect, rgb, lum=None):
    """Fit alpha mask `a` into pixel rect (x0,y0,x1,y1, top-left origin) keeping aspect; return ink rect.
    rgb: (3,) colour or (h,w,3) colour image at a's resolution."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    iw, ih = w * (1 - 2 * PAD), h * (1 - 2 * PAD)
    s = min(iw / a.shape[1], ih / a.shape[0])
    nw, nh = max(1, int(a.shape[1] * s)), max(1, int(a.shape[0] * s))
    m = from_img(to_img(a).resize((nw, nh), Image.LANCZOS))
    ox, oy = x0 + (w - nw) // 2, y0 + (h - nh) // 2
    atlas[oy:oy + nh, ox:ox + nw, 3] = np.maximum(atlas[oy:oy + nh, ox:ox + nw, 3], m * 255)
    col = np.asarray(rgb, float)
    if col.ndim == 3:
        col = np.array(Image.fromarray(col.astype(np.uint8)).resize((nw, nh), Image.LANCZOS)).astype(float)
    else:
        col = np.broadcast_to(col, (nh, nw, 3))
    if lum is not None:
        L = from_img(to_img(lum).resize((nw, nh), Image.LANCZOS))
        col = col * np.clip(L * 1.15, 0, 1)[..., None]
    atlas[oy:oy + nh, ox:ox + nw, :3] = col
    return (ox, oy, ox + nw, oy + nh)


def place_row(atlas, parts, rect, gap_frac=0.12):
    """lay several (alpha, rgb) parts left->right inside rect, same height, centred."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    ih = h * (1 - 2 * PAD)
    widths = [p[0].shape[1] * ih / p[0].shape[0] for p in parts]
    gap = ih * gap_frac * 2
    total = sum(widths) + gap * (len(parts) - 1)
    s = min(1.0, w * (1 - 2 * PAD) / total)
    x = x0 + (w - total * s) / 2
    inks = []
    for (a, rgb), pw in zip(parts, widths):
        cw, chh = pw * s, ih * s
        r = (int(x), int(y0 + (h - chh) / 2), int(x + cw), int(y0 + (h + chh) / 2))
        inks.append(place(atlas, a, r, rgb, lum=a))
        x += cw + gap * s
    return (min(i[0] for i in inks), min(i[1] for i in inks), max(i[2] for i in inks), max(i[3] for i in inks))


def uv(r):
    """pixel rect (top-left origin) -> Blender UV rect [u0, v0, u1, v1] (v up)."""
    x0, y0, x1, y1 = r
    return [round(x0 / AW, 5), round(1 - y1 / AH, 5), round(x1 / AW, 5), round(1 - y0 / AH, 5)]


# name: slot px rect (x0,y0,x1,y1 top-left), ink sRGB, where
SLOTS = {
    "wand_shark_powerdetect": ((0, 0, 2048, 256), (58, 56, 52),
        "wand tube FRONT face. On the product the text reads TOP->BOTTOM along the wand and the glyph tops face the "
        "viewer's RIGHT (text rotated 90 deg clockwise; raw/tr-ip3251eut-11, cl-eut-01). Map u (atlas left->right) to "
        "wand top->bottom, v (glyph up) to product +x. cl-eut-01 (front ortho, 1.555 px/mm): ink 174 mm long x 13.2 mm "
        "high (incl. 'k' ascender), starts ~ 22 mm below the top collar. Dark graphite ink on M_Bronze."),
    "powerdetect_plate": ((0, 256, 1024, 384), (52, 50, 46),
        "champagne label band directly under the purple cap, front, horizontal, centred (user frame 1663, cl-eut-01). "
        "Ink length ~ 45 mm (same POWERDETECT artwork as the wand, true proportions). Dark ink on M_Champagne."),
    "dock_powerdetect": ((1024, 256, 2048, 384), (52, 50, 46),
        "dock tower front face, top-right badge (tr-part-2-0l-aed-eu-fisi-1, cl-eut-01): champagne plate with a thin "
        "dark border, POWERDETECT horizontal. Ink ~ 34 mm long. Plate geometry = M_Champagne."),
    "duoclean_detect": ((0, 384, 1280, 640), (54, 55, 58),
        "floorhead front cover plate (light grey strip on the clear cover, centred over the soft roller, cl-na-06 / "
        "cl-eut-01 / user 1663). Horizontal, glyph up = product up/back. Ink ~ 95 mm long. Dark grey ink."),
    "shark_frame": ((1280, 384, 2048, 640), (236, 237, 236),
        "handheld brushed-silver bin frame top band, front, centred, horizontal (user 1663: white/light ink; cl-eut-01 "
        "reads light grey). Ink width ~ 38 mm."),
    "shark_neck": ((0, 640, 768, 896), (228, 229, 228),
        "floorhead neck top plate (dark), light ink, glyph up = toward the wand / rear (user 1663, 1667). Ink ~ 36 mm."),
    "dock_binfull": ((768, 640, 1280, 896), (244, 246, 255),
        "dock DUST BIN FULL pill window (TR manual p14): bin-with-dust icon then moon, laid out along the pill's LONG "
        "axis = u (bin icon at low u = the end nearest the post), glyph up = +v. Use on an M_DockDisplay plate (glyphs "
        "glow when lit) over an M_Screen window. Brightness as drawn (bin icon grey, moon white)."),
    "screen_icons_tr": ((0, 1024, 1024, 2048), (255, 255, 255),
        "handheld round screen face, TR layout (TR manual p8 vector glyphs, confirmed + coloured by the TR unit's shipping "
        "film, frames/vid-T9U8rtc6cJk-t1010.0): DETECT target top (white), ECO leaf (green) / BOOST fan (red) either side, "
        "battery bar (white), battery-bolt + 'FO', solid power pill. No drop icon. Slot = circumscribed square of the BLACK screen disc (ring arcs excluded "
        "-> M_LEDRing geometry at 0.83-0.93 R). Glyph up = toward the handle-far edge (power pill nearest the grip)."),
    "odour_dial": ((1024, 1024, 2048, 2048), (40, 190, 168),
        "dock odour-neutraliser dial top face (EU print 'ANTI-ODOUR TECHNOLOGY' + hexagon logo, padlock, open-lock, "
        "+/- wedge arc; tr-ip3251eut-01 inset). Slot = circumscribed square of the face disc. Rim triangle index is "
        "NOT included (sits on the rim ring)."),
    "edge_detect": ((1280, 640, 2048, 768), (214, 215, 216),
        "floorhead side caps: front-top face of BOTH caps, 'EDGE DETECT' ('EDGE' bold) reading bottom->top on the real "
        "unit (vid-JCGXMfx8SG8 t176.9; glyph tops toward the head centre on the right cap). Light-grey ink. Ink ~ 26 mm."),
    "foot_icon": ((1664, 768, 1792, 1024), (214, 215, 216),
        "floorhead deck top, right of the neck plate as seen from the front-top (= product's LEFT), shoe-sole "
        "pictogram (step-on-to-release). Toe up = toward the rear/neck. Light-grey ink. Ink ~ 9 x 18 mm."),
    "rating_label": ((1280, 768, 1664, 960), (241, 241, 239),
        "floorhead neck UNDERSIDE white rating sticker 'Shark Power Nozzle / Model: IP3251 T6 / 14.5V 120W' "
        "(vid-wuXUwo0Itxg t160). Full-colour opaque sticker (white paper + black print, rounded corners); aspect 2.05 "
        "after foreshortening correction (low-res source: ~10 px glyphs). ~ 30 x 15 mm."),
}


def odour_dial_rect():
    """Affine-rectify the dial face ellipse from the tr-ip3251eut-01 inset to a circle; teal print -> alpha."""
    p = os.path.join(REF, "frames", "crop-tr01-dock-display-inset.jpg")
    im = np.array(Image.open(p).convert("RGB")).astype(float)
    # face ellipse (inner disc) in that crop, measured: centre / semi-axes / tilt
    cx, cy, ax, ay, ang = DIAL_ELLIPSE
    n = 900
    yy, xx = (np.mgrid[0:n, 0:n] - n / 2) / (n / 2)       # unit disc coords (x right, y down)
    t = np.deg2rad(ang)
    ex, ey = xx * ax, yy * ay
    sx = cx + ex * np.cos(t) - ey * np.sin(t)
    sy = cy + ex * np.sin(t) + ey * np.cos(t)
    rgb = np.dstack([map_coordinates(im[..., k], [sy, sx], order=1) for k in range(3)])
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    teal = smooth(g - r, 50, 100)
    inside = np.hypot(xx, yy) < 0.97
    dbg("dial_rect", rgb)
    return teal * inside


DIAL_ELLIPSE = (440.0, 260.0, 202.0, 122.0, -2.0)   # face disc in crop-tr01-dock-display-inset.jpg (measured on a grid)


def main():
    os.makedirs(OUT_TEX, exist_ok=True)
    atlas = np.zeros((AH, AW, 4), float)
    layout = {"atlas": "assets/source/textures/v3/decal_atlas.png", "size": [AW, AH],
              "uv_convention": "Blender UV, origin bottom-left, rect = [u0, v0, u1, v1]. 'ink' = tight box of the "
                               "marking; map your plate face to 'ink' (marking fills it edge to edge) or to 'slot' "
                               "(margin). glyph up = +v. Use materials.decal_uv(slot, s, t).",
              "slots": {}}
    shark = mask_shark()
    wand = mask_wand()
    pdet, shark_w, gap = split_powerdetect(wand)
    duo = mask_duoclean()
    sc_a, sc_rgb, sc_l = screen_icons()
    bin_i, moon_i = binfull()
    dial = odour_dial_rect()
    edge = mask_edge_detect()
    foot = mask_foot()
    lab_a, lab_rgb = label_rating()
    srcs = {}
    for name, (rect, rgb, where) in SLOTS.items():
        if name == "wand_shark_powerdetect":
            ink = place(atlas, wand, rect, rgb)
        elif name in ("powerdetect_plate", "dock_powerdetect"):
            ink = place(atlas, pdet, rect, rgb)
        elif name in ("shark_frame", "shark_neck"):
            ink = place(atlas, shark, rect, rgb)
        elif name == "duoclean_detect":
            ink = place(atlas, duo, rect, rgb)
        elif name == "screen_icons_tr":
            ink = place(atlas, sc_a, rect, sc_rgb, lum=sc_l)
            ink = rect_inset(rect)
        elif name == "odour_dial":
            ink = place(atlas, dial, rect, rgb)
            ink = rect_inset(rect)
        elif name == "edge_detect":
            ink = place(atlas, edge, rect, rgb)
        elif name == "foot_icon":
            ink = place(atlas, foot, rect, rgb)
        elif name == "rating_label":
            ink = place(atlas, lab_a, rect, lab_rgb)
        elif name == "dock_binfull":
            ink = place_row(atlas, [(bin_i, (244, 246, 255)), (moon_i, (244, 246, 255))], rect)
        layout["slots"][name] = {
            "slot": uv(rect), "ink": uv(ink),
            "inkAspect": round((ink[2] - ink[0]) / (ink[3] - ink[1]), 4),
            "colorSRGB": "#%02x%02x%02x" % tuple(rgb), "where": where, "status": "extracted",
        }
    _bleed(atlas)
    out = os.path.join(OUT_TEX, "decal_atlas.png")
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(out, optimize=True)
    with open(os.path.join(V3, "decals.json"), "w") as f:
        json.dump(layout, f, indent=2)
    print("atlas", out, os.path.getsize(out), "bytes")


def rect_inset(rect):
    """square slots (screen, dial): the disc fills the slot minus PAD on each side -> ink = that square."""
    x0, y0, x1, y1 = rect
    p = int((x1 - x0) * PAD)
    return (x0 + p, y0 + p, x1 - p, y1 - p)


def _bleed(atlas):
    """Dilate ink RGB into fully transparent texels (alpha untouched) so mips/filtering don't pull in black."""
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
