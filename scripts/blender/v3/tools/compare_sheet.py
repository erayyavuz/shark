"""python3 scripts/blender/v3/tools/compare_sheet.py <render_dir> <out.png> [label]
Materials comparison sheet for v3 (IP3251):
  row 1: official front render raw/cl-eut-01 (key-green -> studio grey) | preview 'front'
  row 2: user frame user-video-1663 (colour truth, product crop) | preview 'q_r' (similar 3/4 from the right)
  row 3: close-ups: user 1663 handheld | render handheld ; user 1663 floorhead | render floorhead
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
REF = os.path.join(ROOT, "assets", "references", "ip3251")


def autocrop(im, pad=20):
    r = np.array(im).astype(int)
    mask = np.abs(r - r[5, 5]).sum(2) > 18
    ys, xs = np.where(mask)
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + pad, ys.max() + pad))


def fit_h(im, h):
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


def row(pairs, h):
    ims = [fit_h(p, h) for p, _ in pairs]
    w = sum(i.width for i in ims) + 20 * (len(ims) - 1)
    out = Image.new("RGB", (w, h + 28), (36, 36, 38))
    d = ImageDraw.Draw(out)
    x = 0
    for im, (_, label) in zip(ims, pairs):
        out.paste(im, (x, 28))
        d.text((x + 6, 8), label, fill=(240, 240, 240))
        x += im.width + 20
    return out


def main():
    rd, out = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(rd.rstrip("/"))
    eut = Image.open(os.path.join(REF, "raw", "cl-eut-01.png")).convert("RGBA")
    bg = Image.new("RGBA", eut.size, (128, 128, 128, 255))
    bg.alpha_composite(eut)
    a = np.array(bg.convert("RGB")).astype(int)
    key = np.abs(a - [71, 112, 76]).sum(2) < 14
    a[key] = [128, 128, 128]
    eut = autocrop(Image.fromarray(a.astype(np.uint8)))
    u = Image.open(os.path.join(REF, "user", "user-video-1663.jpg")).convert("RGB")
    user = u.crop((330, 100, 960, 2240))
    rows = []
    fr = os.path.join(rd, "front.png")
    qr = os.path.join(rd, "q_r.png")
    if os.path.exists(fr):
        rows.append(row([(eut, "REF cl-eut-01 (official front)"), (autocrop(Image.open(fr).convert("RGB")), f"RENDER {label}/front")], 1100))
    if os.path.exists(qr):
        r = autocrop(Image.open(qr).convert("RGB"))
        rows.append(row([(user, "USER 1663 (colour truth)"), (r, f"RENDER {label}/q_r")], 1100))
        # close-ups from relative positions of the q_r product bbox
        W, H = r.size
        hh = r.crop((int(W * 0.15), 0, int(W * 0.75), int(H * 0.30)))
        fh = r.crop((0, int(H * 0.80), int(W * 0.65), H))
        rows.append(row([(u.crop((540, 100, 920, 1000)), "USER handheld"), (hh, "RENDER handheld"),
                         (u.crop((470, 1850, 950, 2230)), "USER floorhead"), (fh, "RENDER floorhead")], 520))
    W = max(r.width for r in rows)
    sheet = Image.new("RGB", (W, sum(r.height for r in rows) + 10 * len(rows)), (36, 36, 38))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 10
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, quality=88)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
