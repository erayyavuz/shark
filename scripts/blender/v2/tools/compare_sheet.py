"""python3 scripts/blender/v2/tools/compare_sheet.py <render.png> <out.png> [ref=raw/sn-gn-hero.png]
Side-by-side: official Sagewood hero (product crop, key-green -> studio grey) | render (same height), with colour
patches of key regions sampled in both (render patches by relative position on the product bbox)."""
import sys
import numpy as np
from PIL import Image, ImageDraw

ref_p = sys.argv[3] if len(sys.argv) > 3 else "assets/references/ia3246/raw/sn-gn-hero.png"
ref = Image.open(ref_p).convert("RGB")
a = np.array(ref).astype(int)
key = (np.abs(a - [71, 112, 76]).sum(2) < 14)
a[key] = [40, 40, 40]
ref = Image.fromarray(a.astype(np.uint8)).crop((760, 90, 1320, 1900))
ren = Image.open(sys.argv[1]).convert("RGB")
r = np.array(ren).astype(int)
bgc = r[5, 5]
mask = np.abs(r - bgc).sum(2) > 18
ys, xs = np.where(mask)
ren = ren.crop((xs.min() - 20, ys.min() - 20, xs.max() + 20, ys.max() + 20))
H = 1400
ref = ref.resize((int(ref.width * H / ref.height), H))
ren = ren.resize((int(ren.width * H / ren.height), H))
sheet = Image.new("RGB", (ref.width + ren.width + 30, H + 40), (40, 40, 40))
sheet.paste(ref, (0, 40))
sheet.paste(ren, (ref.width + 30, 40))
d = ImageDraw.Draw(sheet)
d.text((10, 10), "REF sn-gn-hero (Sagewood)", fill=(255, 255, 255))
d.text((ref.width + 40, 10), "RENDER " + sys.argv[1].split("/")[-2] + "/" + sys.argv[1].split("/")[-1], fill=(255, 255, 255))
sheet.save(sys.argv[2])
print(sys.argv[2])
