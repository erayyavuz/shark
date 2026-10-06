"""Re-encode one glTF texture for the shipped GLB (called by scripts/assets-build.mjs).
usage: python3 optimize_texture.py <in> <out> <name> <tier>
Rules: ORM/normal/colour maps without meaningful alpha -> JPEG; decal atlases (alpha) -> palette-quantized PNG;
balanced tier halves the resolution (min 256). Prints the output mime type."""
import sys
from PIL import Image

src, out, name, tier = sys.argv[1:5]
im = Image.open(src)
has_alpha = im.mode in ("RGBA", "LA", "P") and "atlas" in name
if tier == "balanced":
    w, h = im.size
    f = 0.5 if max(w, h) > 512 else 1.0
    if f < 1:
        im = im.resize((max(256, int(w * f)), max(256, int(h * f))), Image.LANCZOS)
if has_alpha:
    im = im.convert("RGBA").quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    im.save(out, "PNG", optimize=True)
    print("image/png")
else:
    im.convert("RGB").save(out, "JPEG", quality=88 if "normal" in name else 85, optimize=True, progressive=False)
    print("image/jpeg")
