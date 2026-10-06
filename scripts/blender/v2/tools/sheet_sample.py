"""python3 sheet_sample.py sheet.png  — median colours of matched regions on a compare_sheet (ref left, render right)."""
import sys
import numpy as np
from PIL import Image
a = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(int)
# (name, ref box, render box) in sheet px — tuned to the front-view sheets
R = {
    "sage dock": ((130, 860, 190, 1100), (560, 870, 600, 1100)),
    "plinth":    ((130, 1210, 180, 1290), (560, 1220, 600, 1290)),
    "copper":    ((200, 760, 212, 830), (628, 770, 640, 840)),
    "graphite":  ((210, 520, 235, 600), (628, 520, 650, 600)),
    "cap sage":  ((180, 70, 250, 100), (605, 75, 680, 100)),
}
for k, (rb, nb) in R.items():
    f = lambda b: np.median(a[b[1]:b[3], b[0]:b[2]].reshape(-1, 3), 0).astype(int)
    r, n = f(rb), f(nb)
    print(f"{k:10s} ref #{r[0]:02x}{r[1]:02x}{r[2]:02x} {tuple(r)}  render #{n[0]:02x}{n[1]:02x}{n[2]:02x} {tuple(n)}")
