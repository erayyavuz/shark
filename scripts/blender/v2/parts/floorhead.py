"""
floorhead part (v2, IA3246GN Sagewood) — TurboPro Detect floor nozzle. Owned by the floorhead agent.
See ../PARTS_CONTRACT.md. Product coords (x right, up, fwd); origin = centre of the intake footprint on the floor.

Dimension ledger (metres). Sources:
  [F3]  owner's guide IA3000UK p.21 Fig.3 (FloorDetect, underside line drawing, 3.75 px/mm at W=260)
  [F2]  same page Fig.2 (EdgeDetect, side elevation line drawing)
  [P20] p.20 "removing squeegee" underside drawing (3 screws on the rear squeegee)
  [H1]  sn-gn-hero.png (Sagewood front, 3.29 px/mm on the head crop)
  [L01] sn-3241laa-01.jpg (head 3/4 close-up: end cap disc, LED bezel + blue L-strip, dot band, EdgeDetect window)
  [G2]  sn-gal2.jpg / amz pt04 (top-front: neck plate, knuckle, castellated skirt, hose, wheels)
  [CUT] amz pt11 (TurboPro cutaway: lobed copper roller + bristle row, radial-rib wheel)
  [inf] inferred
"""
import math

from mathutils import Vector

import lib
from lib import V, mk, bevel, extrude, fillet, catmull, offset_polyline, lathe, lathe_x, ring_mesh, rrect, toB, TAU, D

G = "FloorHead"
GW = "LowerWand"

# ------------------------------------------------------------------ ledger
HF = 0.044            # head front (clear comb bar) fwd [F3 intake centre 44 mm behind front]
X_IN = 0.1125         # inner face of the end caps = cover/tub half width [H1 caps ~17 mm wide]
X_OUT = 0.130         # outer face of the end caps (W 260) [spec]
CAP_REAR = -0.067     # [F3 box rear 106 mm behind front; F2]
CAP_TOP = 0.064       # [F2 ~64 mm]
R_UP, R_FWD = 0.0265, 0.0   # brushroll axis [F2 side disc centre ~29 mm high, 47 mm behind front]
R_CORE, R_LOBE, R_TIP = 0.0198, 0.0236, 0.0268  # roller core / copper fin lobes / bristle tips [CUT, H1]
R_HALF = 0.1035       # half length of the lobed roller body (206 mm + hubs ~ 211 mm path) [spec]
INT_F, INT_R = 0.030, -0.026  # intake opening fwd range (clear comb bar -> squeegee) [F3, real underside]
WX0, WX1, W_R, W_FWD, W_UP = 0.0490, 0.0635, 0.026, -0.100, 0.026  # rear wheels flank the plate [F3, G2, pt04]
PIV_UP = 0.045        # wand pitch axis height [F2, inf]
DISC_UP = 0.098       # knuckle copper disc centre [H1 116 px-mm minus ~18 mm perspective offset; F2]
PLATE_HW = 0.0480     # neck plate half width [F3 98 mm, G2 ~100 mm]
PLATE_F, PLATE_R = -0.0330, -0.1190   # plate nose (on the cover) / rear end [F3, G2]
PLATE_TOP = 0.0675    # plate top behind the sloped logo face [H1, F2]
WELL_HW, WELL_F = 0.0265, -0.0745     # hose well half width / front wall [G2, pt04]
WELL_FLOOR = 0.0350
CHEEK_X0 = WELL_HW

SM = lambda u, v, w: V(w, v, u)   # side map: u = fwd, v = up, w = x
FM = lambda u, v, w: V(u, v, w)   # front map: u = x, v = up, w = fwd


def _P():
    import params
    return params


# ------------------------------------------------------------------ small helpers
def _box(name, x0, x1, u0, u1, f0, f1, mat, grp, bev=None, seg=2):
    verts = [V(x, u, f) for x in (x0, x1) for u in (u0, u1) for f in (f0, f1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mk(name, verts, faces, mat, grp, smooth=False)
    if bev:
        bevel(ob, bev, seg)
    return ob


def _boxes(name, specs, mat, grp, smooth=False):
    """many boxes in one mesh. spec: (x0,x1,u0,u1,f0,f1) or 8 explicit Vector corners"""
    verts, faces = [], []
    for s in specs:
        b = len(verts)
        if len(s) == 8:
            verts += list(s)
        else:
            x0, x1, u0, u1, f0, f1 = s
            verts += [V(x, u, f) for x in (x0, x1) for u in (u0, u1) for f in (f0, f1)]
        faces += [(b + 0, b + 1, b + 3, b + 2), (b + 4, b + 6, b + 7, b + 5), (b + 0, b + 4, b + 5, b + 1),
                  (b + 2, b + 3, b + 7, b + 6), (b + 0, b + 2, b + 6, b + 4), (b + 1, b + 5, b + 7, b + 3)]
    return mk(name, verts, faces, mat, grp, smooth=smooth)


def _discs(name, centers, mat, grp, n=6):
    """flat polygon discs: centers = [(Vector c, Vector normal, radius)]"""
    verts, faces = [], []
    for c, nrm, r in centers:
        nrm = nrm.normalized()
        a = nrm.orthogonal().normalized()
        b2 = nrm.cross(a)
        base = len(verts)
        verts.append(c)
        for k in range(n):
            t = TAU * k / n
            verts.append(c + (a * math.cos(t) + b2 * math.sin(t)) * r)
        for k in range(n):
            faces.append((base, base + 1 + k, base + 1 + (k + 1) % n))
    return mk(name, verts, faces, mat, grp, smooth=False, recalc=False)


def _interp_profile(prof, up):
    """fwd on a front-face polyline (fwd, up) at a given height (first crossing from the bottom)"""
    for (f0, u0), (f1, u1) in zip(prof, prof[1:]):
        if (u0 - up) * (u1 - up) <= 0 and u1 != u0:
            t = (up - u0) / (u1 - u0)
            return f0 + (f1 - f0) * t
    return prof[0][0]


def sweep_corrugated(name, path, r0, amp, nridge, mat, grp, segs=None):
    segs = segs or max(16, D["lathe"] // 7)
    path = [Vector(p) for p in path]
    fine = []
    for i in range(len(path) - 1):
        for k in range(6):
            fine.append(path[i].lerp(path[i + 1], k / 6))
    fine.append(path[-1])
    L = sum((fine[i + 1] - fine[i]).length for i in range(len(fine) - 1))
    s = 0.0
    rings = []
    Bv = Vector((1, 0, 0))
    for i, c in enumerate(fine):
        if i:
            s += (fine[i] - fine[i - 1]).length
        a = fine[max(i - 1, 0)]
        b = fine[min(i + 1, len(fine) - 1)]
        T = (b - a).normalized()
        Nn = T.cross(Bv).normalized()
        rr = r0 + amp * math.cos(TAU * nridge * s / L)
        rings.append([toB(c + (Bv * math.cos(TAU * j / segs) + Nn * math.sin(TAU * j / segs)) * rr) for j in range(segs)])
    verts, faces = ring_mesh(rings, True, True)
    return mk(name, verts, faces, mat, grp)


def polar_uv(ob, origin, axis, ref, rmax):
    """spun-metal UVs for a lathed disc. The brushed textures streak along V, so V runs around the disc (concentric
    grooves) and U runs outward; both in 50 mm texture tiles (materials.ensure_uvs scale), V wraps an integer count."""
    wraps = max(1, round(TAU * rmax / 0.05))
    o = toB(Vector(origin))
    A = toB(Vector(axis)).normalized()
    U = toB(Vector(ref)).normalized()
    W = A.cross(U)
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        # polygon centre angle keeps the seam from smearing across a face
        pc = poly.center - o
        ac = math.atan2(pc.dot(W), pc.dot(U)) % TAU
        for li in poly.loop_indices:
            d = me.vertices[me.loops[li].vertex_index].co - o
            d = d - A * d.dot(A)
            r = d.length
            a = math.atan2(d.dot(W), d.dot(U)) % TAU if r > 1e-7 else ac
            if a - ac > math.pi:
                a -= TAU
            elif ac - a > math.pi:
                a += TAU
            uvl.data[li].uv = (min(r, rmax) / 0.05, wraps * a / TAU)
    return ob


# ------------------------------------------------------------------ profiles
def cover_outer():
    """clear cover outer section (fwd, up), front-bottom -> rear [H1, L01, CUT]"""
    return catmull([(0.0400, 0.0108), (0.0418, 0.0240), (0.0400, 0.0390), (0.0320, 0.0520), (0.0170, 0.0602),
                    (-0.0030, 0.0632), (-0.0240, 0.0622), (-0.0445, 0.0598)], per=max(4, int(round(3 * D["path"]))))


def cap_profile():
    pts = [(0.0425, 0.0020), (0.0472, 0.0300), (0.0390, CAP_TOP), (-0.0300, 0.0628), (CAP_REAR + 0.003, 0.0520),
           (CAP_REAR, 0.0060), (CAP_REAR + 0.006, 0.0020)]
    return fillet(pts, [0.002, 0.022, 0.022, 0.030, 0.013, 0.005, 0.002], max(8, D["corner"] + 2))


# ================================================================== body
def build_body(P):
    objs = []
    add = objs.append

    # ---- end caps (graphite) with copper side discs, bezel ring and EdgeDetect window [L01, F2]
    cp = cap_profile()
    for s, tag in ((1, "R"), (-1, "L")):
        ob = extrude(f"HeadCap_{tag}", cp, SM, s * X_IN, s * X_OUT, "M_Graphite", G)
        bevel(ob, 0.0045, max(4, D["bevel_seg"]), angle=30)
        add(ob)
        o = (s * X_OUT, R_UP, R_FWD)
        add(lathe(f"HeadCapRing_{tag}", [(0.0246, -0.0010), (0.0246, 0.0003), (0.0238, 0.0010), (0.0206, 0.0010),
                                         (0.0201, 0.0001), (0.0180, 0.0001)], o, (s, 0, 0), (0, 0, 1),
                  "M_Graphite", G, segs=max(48, D["lathe"] // 2), cap0=False, cap1=True))
        add(polar_uv(lathe(f"HeadCapDisc_{tag}", [(0.0199, -0.0004), (0.0199, 0.0010), (0.0192, 0.0016), (0.0140, 0.0018),
                                                  (0.0, 0.0019)], o, (s, 0, 0), (0, 0, 1), "M_CopperSatin", G,
                           segs=max(48, D["lathe"] // 2), cap0=True, cap1=False), o, (s, 0, 0), (0, 0, 1), 0.0199))
        # EdgeDetect sensor window toward the cap rear (oval bezel + glossy lens)
        win = rrect(0.0125, 0.0072, 0.0035)
        win = [(-0.047 + a, 0.0325 + b) for a, b in win]
        add(extrude(f"HeadEdgeBezel_{tag}", win, SM, s * (X_OUT - 0.0006), s * (X_OUT + 0.0005), "M_Graphite", G,
                    bev=0.0004, bev_seg=2))
        lens = rrect(0.0094, 0.0046, 0.0022)
        lens = [(-0.047 + a, 0.0325 + b) for a, b in lens]
        add(extrude(f"HeadEdgeLens_{tag}", lens, SM, s * (X_OUT + 0.0004), s * (X_OUT + 0.0008), "M_Screen", G))
        # small front glide rollers under the cap front corners [F3]
        add(lathe_x(f"HeadGlide_{tag}", [(0.0024, s * 0.1185), (0.0034, s * 0.1192), (0.0034, s * 0.1228),
                                         (0.0024, s * 0.1235)], 0.0036, 0.032, "M_Rubber", G, segs=20))
        # roller bearing hubs (dark) on the cap inner faces
        add(lathe_x(f"HeadBearing_{tag}", [(0.0150, s * (R_HALF + 0.0060)), (0.0150, s * (X_IN + 0.0002))],
                    R_UP, R_FWD, "M_Graphite", G, segs=48))

    # ---- right cap front: LED bezel + white LED (Reveal light) + blue L-shaped light pipe [H1, L01]
    bez = fillet([(0.1086, 0.0030), (0.1284, 0.0030), (0.1284, 0.0215), (0.1086, 0.0215)], [0.0015, 0.0025, 0.004, 0.003], 5)
    add(extrude("HeadLEDBezel", bez, FM, 0.0405, 0.0478, "M_Graphite", G, bev=0.0009, bev_seg=2))
    leds = []
    led_c = (0.1180, 0.0120, 0.0478)
    add(lathe("HeadLEDRing", [(0.0045, -0.0004), (0.0045, 0.0003), (0.0040, 0.0007), (0.0034, 0.0007), (0.0033, 0.0)],
              led_c, (0, 0, 1), (1, 0, 0), "M_Chrome", G, segs=32, cap0=False, cap1=False))
    leds.append(lathe("HeadLED", [(0.0033, -0.0006), (0.0033, 0.0002), (0.0028, 0.0009), (0.0015, 0.0012), (0.0, 0.0013)],
                      led_c, (0, 0, 1), (1, 0, 0), "M_LED", "HeadLights", segs=32, cap0=False))
    leds.append(_boxes("HeadRevealStrip", [(0.1281, 0.1300, 0.0035, 0.0290, 0.0410, 0.0475),
                                           (0.1060, 0.1300, 0.0016, 0.0034, 0.0400, 0.0476)], "M_LEDAccent", "HeadLights"))
    # left cap front foot
    foot = fillet([(-0.1286, 0.0022), (-0.1100, 0.0022), (-0.1100, 0.0110), (-0.1286, 0.0125)], [0.001, 0.001, 0.002, 0.003], 4)
    add(extrude("HeadFootL", foot, FM, 0.0405, 0.0468, "M_Graphite", G, bev=0.0007, bev_seg=2))

    # ---- clear cover (2 mm smoked shell) [H1, L01]
    outer = cover_outer()
    inner = offset_polyline(outer, 0.0019)
    # make sure the inner offset points inward (toward the roller axis)
    if (Vector(inner[len(inner) // 2]) - Vector((R_FWD, R_UP))).length > (Vector(outer[len(outer) // 2]) - Vector((R_FWD, R_UP))).length:
        inner = offset_polyline(outer, -0.0019)
    add(extrude("HeadCover", outer + inner[::-1], SM, -X_IN + 0.0002, X_IN - 0.0002, "M_ClearSmoke", G))
    # front comb bar (clear) with hair-guard teeth and four clip posts [H1, L01, F3]
    bar = fillet([(0.0300, 0.0036), (0.0446, 0.0036), (0.0450, 0.0112), (0.0340, 0.0122)], [0.0006, 0.0012, 0.0015, 0.001], 3)
    add(extrude("HeadCombBar", bar, SM, -X_IN + 0.0003, X_IN - 0.0003, "M_ClearSmoke", G, bev=0.0005, bev_seg=2))
    nt = 12
    teeth = []
    for i in range(nt):
        x = -0.099 + 0.198 * i / (nt - 1)
        teeth.append((x - 0.0019, x + 0.0019, 0.0010, 0.0040, 0.0300, 0.0430))
    add(_boxes("HeadCombTeeth", teeth, "M_ClearSmoke", G))
    clips = []
    pins = []
    for x in (-0.088, -0.041, 0.037, 0.086):
        clips.append((x - 0.0022, x + 0.0022, 0.0040, 0.0205, 0.0412, 0.0448))
        pins.append((x - 0.0008, x + 0.0008, 0.0060, 0.0190, 0.0420, 0.0436))
    ob = _boxes("HeadCombClips", clips, "M_ClearSmoke", G)
    bevel(ob, 0.0007, 2)
    add(ob)
    add(_boxes("HeadCombPins", pins, "M_Graphite", G))
    # dot-matrix band printed on the right end of the cover [H1, L01, G2]
    dots = []
    ncol = 7
    # resample the outer profile by arc length
    acc = [0.0]
    for a, b in zip(outer, outer[1:]):
        acc.append(acc[-1] + (Vector(b) - Vector(a)).length)
    def at_s(sv):
        for k in range(len(acc) - 1):
            if acc[k] <= sv <= acc[k + 1]:
                t = (sv - acc[k]) / max(acc[k + 1] - acc[k], 1e-9)
                p = Vector(outer[k]).lerp(Vector(outer[k + 1]), t)
                tg = (Vector(outer[k + 1]) - Vector(outer[k])).normalized()
                return p, tg
        return Vector(outer[-1]), (Vector(outer[-1]) - Vector(outer[-2])).normalized()
    # band from just above the LED bezel (up ~0.022) over the front curve to the top (fwd ~ -0.010)
    s_start = next(acc[k] for k in range(len(outer)) if outer[k][1] >= 0.0225)
    s_end = next(acc[k] for k in range(len(outer)) if outer[k][0] <= -0.008)
    pitch = 0.00135
    nrow = int((s_end - s_start) / pitch)
    for r in range(nrow):
        p, tg = at_s(s_start + r * pitch)
        nrm2 = Vector((tg.y, -tg.x))
        if nrm2.dot(p - Vector((R_FWD, R_UP))) < 0:
            nrm2 = -nrm2
        fade = 1.0 - 0.55 * (r / max(nrow - 1, 1))
        for c in range(ncol):
            x = X_IN - 0.0016 - c * pitch - (0.5 * pitch if r % 2 else 0)
            rad = 0.00042 * (1.0 - 0.10 * c) * fade
            q = p + nrm2 * 0.00008
            dots.append((V(x, q.y, q.x), V(0, nrm2.y, nrm2.x) - V(0, 0, 0), rad))
    add(_discs("HeadCoverDots", dots, "M_Graphite", G, n=6))

    # ---- decal plate: TURBOPRO DETECT on the cover front-left [H1: x -109..-36 mm, up 27..33 mm]
    add(decal_cover(outer))

    # ---- chassis tub (graphite) wrapping the roller rear + floor strips [CUT, F3]
    tub = []
    Rt = 0.0288
    for k in range(16):
        a = math.radians(100 + (222 - 100) * k / 15)
        tub.append((R_FWD + Rt * math.cos(a), R_UP + Rt * math.sin(a)))
    tub += [(INT_R, 0.0032), (CAP_REAR + 0.001, 0.0032), (CAP_REAR + 0.0005, 0.0120), (CAP_REAR + 0.0010, 0.0480),
            (-0.058, 0.0545), (-0.044, 0.0582), (-0.012, 0.0590)]
    ob = extrude("HeadTub", tub, SM, -X_IN + 0.0001, X_IN - 0.0001, "M_Graphite", G)
    bevel(ob, 0.0012, 2, angle=40)
    add(ob)
    # (no soleplate strip ahead of the roller: the clear comb bar is the front lip of the intake [real underside])
    # rear squeegee: NBR rubber band behind the intake with chevron diagonal ribs (apex at centre, pointing
    # forward) + 3 twist-lock knobs behind it (centre knob in a raised round boss) [rt-ia3241-build-quality, F3, P20]
    add(_box("HeadSqueegee", -0.1060, 0.1060, 0.0020, 0.0034, -0.0418, INT_R - 0.0004, "M_Rubber", G, bev=0.0005))
    ribs = []
    nrib = 7
    for sgn in (1, -1):
        for k in range(nrib):
            xa = 0.002 + k * 0.0148            # inner end of the rib
            xb = xa + 0.0128
            fa, fb = -0.0288, -0.0392           # inner end forward, outer end rearward
            if k == 0:
                xa, fa = 0.0005, -0.0278
            hw = 0.00075
            cs = []
            for xx, ff in ((xa, fa), (xb, fb)):
                for uu in (0.0012, 0.0021):
                    for d in (-hw, hw):
                        cs.append((sgn * xx, uu, ff + d))
            # corner order index = end*4 + up*2 + side  (matches the _boxes x/u/f convention)
            ribs.append([V(*c) for c in cs])
    ob = _boxes("HeadSqueegeeRibs", ribs, "M_Rubber", G)
    add(ob)
    add(lathe("HeadKnobBoss", [(0.0, 0.0), (0.0125, 0.0), (0.0125, 0.0007), (0.0112, 0.0012), (0.0080, 0.0012), (0.0078, 0.0004),
                               (0.0, 0.0004)], (0.0, 0.0032, -0.0568), (0, -1, 0), (1, 0, 0), "M_Graphite", G, segs=40))
    bars = []
    for i, (x, f, base) in enumerate(((-0.086, -0.0488, 0.0032), (0.0, -0.0568, 0.0028), (0.086, -0.0488, 0.0032))):
        add(lathe(f"HeadKnob_{'LCR'[i]}", [(0.0, 0.0), (0.0062, 0.0), (0.0062, 0.0006), (0.0055, 0.0011), (0.0, 0.0011)],
                  (x, base, f), (0, -1, 0), (1, 0, 0), "M_Graphite", G, segs=32))
        a_ = 0.55 if x <= 0 else -0.55
        ca, sa = math.cos(a_), math.sin(a_)
        cs = []
        for dl in (-0.0054, 0.0054):
            for uu in (base - 0.0022, base - 0.0010):
                for dw in (-0.0009, 0.0009):
                    cs.append(V(x + dl * ca - dw * sa, uu, f + dl * sa + dw * ca))
        bars.append(cs)
    add(_boxes("HeadKnobBars", bars, "M_Graphite", G))
    # small screws on the clear comb bar underside [real underside: 4 screws in round bosses]
    for i, x in enumerate((-0.088, -0.041, 0.037, 0.086)):
        add(lathe(f"HeadCombScrew_{i}", [(0.0, 0.0), (0.0024, 0.0), (0.0024, 0.0004), (0.0, 0.0006)], (x, 0.0036, 0.0398),
                  (0, -1, 0), (1, 0, 0), "M_Graphite", G, segs=16))

    # parting-line seam across the tub rear face (either side of the neck plate) [inf, real underside]
    seam = []
    for sg in (1, -1):
        x0, x1 = sorted((sg * (PLATE_HW + 0.001), sg * (X_IN - 0.001)))
        seam.append((x0, x1, 0.0290, 0.0297, CAP_REAR - 0.0002, CAP_REAR + 0.0012))
    add(_boxes("HeadTubSeam", seam, "M_Rubber", G))

    # ---- ribbed panels on the tub top behind the cover, either side of the neck plate [PDP3 top view]
    ribs = []
    for s in (1, -1):
        for k in range(5):
            f = -0.0475 - k * 0.0034
            up = 0.0545 + (f + 0.058) * (0.0582 - 0.0545) / 0.014
            x0, x1 = (PLATE_HW + 0.004, X_IN - 0.006) if s > 0 else (-X_IN + 0.006, -PLATE_HW - 0.004)
            ribs.append((x0, x1, up - 0.0006, up + 0.0009, f - 0.0007, f + 0.0007))
    ob = _boxes("HeadDeckRibs", ribs, "M_SageDeep", G)
    bevel(ob, 0.0003, 1)
    add(ob)

    # ---- neck plate (sage): one lofted U-slab, hose well at the rear centre, "Shark" decal on top [G2, pt04, F3]
    add(build_plate())
    add(decal_shark())
    # well rim (raised lip framing the hose well) [G2]
    rim = []
    for s in (1, -1):
        rim.append((s * (WELL_HW + 0.0003), s * (WELL_HW + 0.0028), PLATE_TOP - 0.001, PLATE_TOP + 0.0012, -0.1080, WELL_F + 0.0002))
    rim.append((-WELL_HW - 0.0028, WELL_HW + 0.0028, PLATE_TOP - 0.001, PLATE_TOP + 0.0012, WELL_F, WELL_F + 0.0028))
    ob = _boxes("HeadWellRim", rim, "M_Sage", G)
    bevel(ob, 0.0007, 2)
    add(ob)
    for s, tag in ((1, "R"), (-1, "L")):
        add(lathe_x(f"HeadPinBoss_{tag}", [(0.0072, s * (WELL_HW - 0.0016)), (0.0072, s * (WELL_HW + 0.0004))],
                    PIV_UP, W_FWD, "M_Graphite", G, segs=32, cap0=True, cap1=False))
    # underside of the neck region: FloorDetect sensor + vent slots + screws [F3]
    yb = 0.0040
    add(_box("HeadNeckBase", -PLATE_HW + 0.0025, PLATE_HW - 0.0025, yb, 0.0064, PLATE_R + 0.004, -0.0665, "M_Graphite", G, bev=0.0010))
    add(lathe("HeadFloorSensor", [(0.0, 0.0), (0.0040, 0.0), (0.0040, 0.0004), (0.0, 0.0006)], (-0.034, yb, -0.080),
              (0, -1, 0), (1, 0, 0), "M_ClearBin", G, segs=24))
    add(lathe("HeadFloorSensorRim", [(0.0040, 0.0), (0.0052, 0.0), (0.0052, 0.0005), (0.0040, 0.0005)], (-0.034, yb, -0.080),
              (0, -1, 0), (1, 0, 0), "M_Graphite", G, segs=24, cap0=False, cap1=False))
    vents = [(-0.0200 + k * 0.0074, -0.0145 + k * 0.0074, yb - 0.0008, yb + 0.0002, -0.0985, -0.0955) for k in range(6)]
    add(_boxes("HeadNeckVents", vents, "M_Rubber", G))
    for x in (-0.030, 0.030):
        add(lathe(f"HeadNeckScrew_{'L' if x < 0 else 'R'}", [(0.0, 0.0), (0.0026, 0.0), (0.0026, 0.0005), (0.0, 0.0007)],
                  (x, yb, -0.108), (0, -1, 0), (1, 0, 0), "M_Chrome", G, segs=16))

    # ---- rear wheels [G2, CUT, F3]
    for s, tag in ((1, "R"), (-1, "L")):
        add_wheel(objs, s, tag)
    # axle stubs between cheek and wheel
    for s, tag in ((1, "R"), (-1, "L")):
        add(lathe_x(f"HeadAxle_{tag}", [(0.0035, s * (PLATE_HW - 0.001)), (0.0035, s * (WX0 + 0.002))], W_UP, W_FWD,
                    "M_Graphite", G, segs=16))
    return objs, leds


def add_wheel(objs, s, tag):
    R = W_R
    x0, x1 = s * WX0, s * WX1
    segs = max(48, D["lathe"] // 2)
    tire = [(R - 0.0060, x0 + s * 0.0004), (R - 0.0012, x0), (R - 0.0001, x0 + s * 0.0016), (R, x0 + s * 0.0040),
            (R, x1 - s * 0.0040), (R - 0.0001, x1 - s * 0.0016), (R - 0.0012, x1), (R - 0.0060, x1 - s * 0.0004)]
    if s < 0:
        tire = tire[::-1]
    ob = lathe_x(f"HeadWheelTire_{tag}", tire, W_UP, W_FWD, "M_Graphite", G, segs=segs, cap0=False, cap1=False)
    bevel(ob, 0.0004, 1)
    objs.append(ob)
    # recessed faces (outer + inner), hub, centre bore
    for side, xx in (("Out", x1), ("In", x0)):
        d = -s if side == "Out" else s   # direction into the wheel
        prof = [(R - 0.0060, xx + d * 0.0004), (R - 0.0068, xx + d * 0.0016), (0.0080, xx + d * 0.0022),
                (0.0072, xx + d * 0.0008), (0.0048, xx + d * 0.0006), (0.0042, xx + d * 0.0030), (0.0, xx + d * 0.0030)]
        objs.append(lathe_x(f"HeadWheelFace{side}_{tag}", prof, W_UP, W_FWD, "M_Graphite", G, segs=segs, cap0=False, cap1=False))
    # radial ribs on the outer face [CUT]
    nrib = 60 if D["lathe"] > 120 else 30
    specs = []
    xa = x1 - s * 0.0022
    for k in range(nrib):
        th = TAU * k / nrib
        dv = Vector((0, math.cos(th), math.sin(th)))   # (x, up, fwd) offset dir in the wheel plane
        tv = Vector((0, -math.sin(th), math.cos(th)))
        cs = []
        for xx in (xa, xa + s * 0.0012):
            for rr in (0.0082, R - 0.0068):
                for tw in (-0.00028, 0.00028):
                    p = dv * rr + tv * tw
                    cs.append((xx, W_UP + p.y, W_FWD + p.z))
        # reorder to box corner convention: index = xi*4 + ui*2 + fi  (x, r, tw)
        specs.append([V(*c) for c in cs])
    objs.append(_boxes(f"HeadWheelRibs_{tag}", specs, "M_Graphite", G))


def _plate_h(f, centre):
    """plate top height at fwd f; centre stations drop into the hose well behind WELL_F"""
    if centre and f < WELL_F - 0.0010:
        return WELL_FLOOR
    if f > -0.0660:                      # sloped front face carrying the logo, rounds down onto the cover
        t = (f + 0.0660) / (PLATE_F + 0.0660)
        return PLATE_TOP - (PLATE_TOP - 0.0600) * t ** 1.35
    if f > -0.0880:
        return PLATE_TOP
    t = (f + 0.0880) / (PLATE_R + 0.0880)   # rear: slopes down over the wheels
    return PLATE_TOP - (PLATE_TOP - 0.0560) * t * t


def _plate_section(x, centre, inset):
    nf = max(28, int(14 * D["path"]))
    pts = []
    fs = [PLATE_F + (PLATE_R - PLATE_F) * k / nf for k in range(nf + 1)]
    fs = [f for f in fs if abs(f - WELL_F) > 0.0025]
    fs = sorted(fs + [WELL_F + 0.0004, WELL_F - 0.0010, WELL_F - 0.0018], reverse=True)
    fs[0], fs[-1] = PLATE_F - inset, PLATE_R + inset
    # rear end: round off the top-rear corner
    for f in fs:
        h = _plate_h(f, centre) - inset
        if f < PLATE_R + 0.008 + inset and not centre:
            q = (PLATE_R + 0.008 + inset - f) / 0.008
            h = h - (h - 0.020) * (1 - math.sqrt(max(0.0, 1 - q * q)))
        pts.append((f, h))
    # bottom (front over the tub at 0.045, rear region down to the floor-side base at 0.0055)
    pts += [(PLATE_R + inset + 0.0005, 0.0080), (PLATE_R + inset + 0.0040, 0.0055), (-0.0660, 0.0055), (-0.0640, 0.0450),
            (PLATE_F - inset - 0.004, 0.0450)]
    return pts


def build_plate():
    """single lofted sage slab: stations along x, each a closed (fwd, up) section"""
    rr = 0.0045                       # side edge rounding
    nr = 4
    # right side rounding (outer -> inner), flat region, well walls, centre
    side = sorted([(PLATE_HW - rr + rr * math.sin((math.pi / 2) * k / nr), rr * (1 - math.cos((math.pi / 2) * k / nr)))
                   for k in range(nr + 1)], key=lambda t: -t[0])
    flat = [(0.040, 0.0), (0.032, 0.0), (WELL_HW + 0.0012, 0.0)]
    wall = [(WELL_HW - 0.0005, 0.0)]
    centre = [(0.0, 0.0)]
    right = [(x, ins, False) for x, ins in side] + [(x, 0.0, False) for x, _ in flat] + [(x, 0.0, True) for x, _ in wall]
    seq = right + [(0.0, 0.0, True)] + [(-x, ins, c) for x, ins, c in right[::-1]]
    rings = []
    for x, ins, c in seq:
        sec = _plate_section(x, c, ins)
        rings.append([V(x, u, f) for f, u in sec])
    verts, faces = ring_mesh(rings, True, True)
    ob = mk("HeadNeckPlate", verts, faces, "M_Sage", G)
    return ob



# ================================================================== decals (M_Decal, atlas slots in decals.json)
def _duv(slot, sx, ty):
    import materials
    return materials.decal_uv(slot, sx, ty)


def decal_cover(outer):
    """'TURBOPRO DETECT' on the smoked window, left of centre [H1: x -109..-36 mm, up 27..33 mm; ink aspect 12.62]"""
    x0, x1 = -0.1105, -0.0355
    hgt = (x1 - x0) / 12.62
    uc = 0.0300
    u0, u1 = uc - hgt / 2, uc + hgt / 2
    front = [p for p in outer if p[1] <= 0.045]
    rows, nx = 4, 12
    verts, uvs, faces = [], [], []
    for r in range(rows + 1):
        up = u0 + (u1 - u0) * r / rows
        f = _interp_profile(front, up)
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            verts.append(V(x, up, f + 0.00025))
            uvs.append(_duv("turbopro_detect", i / nx, r / rows))
    for r in range(rows):
        for i in range(nx):
            a = r * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return mk("HeadDecal_TurboPro", verts, faces, "M_Decal", G, uvs=uvs, recalc=False)


def decal_shark():
    """'Shark' on the neck plate top, front half [G2/pt04: ~47 mm wide incl. swash, centre ~23 mm behind the nose]"""
    w = 0.0400
    h = w / 3.80
    fc = -0.0505
    verts, uvs = [], []
    for r, f in enumerate((fc + h / 2, fc - h / 2)):     # r=0 front (glyph bottom, reads from the front)
        for i, x in enumerate((-w / 2, w / 2)):
            verts.append(V(x, _plate_h(f, False) + 0.00025, f))
            uvs.append(_duv("shark_neck", i, r))
    return mk("HeadDecal_Shark", verts, [(0, 1, 3, 2)], "M_Decal", G, uvs=uvs, recalc=False, smooth=False)


# ================================================================== knuckle / neck (LowerWand)
def build_knuckle(P):
    """dark yoke fork on the pitch pins + sage-deep neck with the copper disc boss and notched tongue [G2, pt04, H1]"""
    objs = []
    add = objs.append
    wf = P.WAND_FWD
    top = P.WAND_SOCKET_UP
    # yoke (graphite): two arms from the pins up to a flange bridge behind/below the neck
    arm = fillet([(wf - 0.0095, PIV_UP - 0.0085), (wf + 0.0095, PIV_UP - 0.0085), (wf + 0.0135, 0.0880),
                  (wf - 0.0150, 0.0880)], [0.0085, 0.0085, 0.0015, 0.0015], max(5, D["corner"] - 2))
    for s, tag in ((1, "R"), (-1, "L")):
        ob = extrude(f"NeckYokeArm_{tag}", arm, SM, s * (WELL_HW - 0.0007), s * (WELL_HW - 0.0062), "M_Graphite", GW)
        bevel(ob, 0.0010, 2)
        add(ob)
        add(lathe_x(f"NeckPin_{tag}", [(0.0040, s * (WELL_HW - 0.0070)), (0.0040, s * (WELL_HW + 0.0002))],
                    PIV_UP, wf, "M_Graphite", GW, segs=20))
    fl = fillet([(wf + 0.0135, 0.0800), (wf + 0.0135, 0.0900), (wf - 0.0160, 0.0900), (wf - 0.0160, 0.0800)], 0.0015, 3)
    ob = extrude("NeckYokeFlange", fl, SM, -(WELL_HW - 0.0007), WELL_HW - 0.0007, "M_Graphite", GW)
    bevel(ob, 0.0010, 2)
    add(ob)
    # neck (sage deep) from the flange up to the wand socket seam [H1 44 -> 42 mm wide]
    st = [(0.0860, 0.0440, 0.0340, 0.0110, wf), (0.1200, 0.0440, 0.0350, 0.0120, wf), (0.1320, 0.0425, 0.0350, 0.0120, wf),
          (top, 0.0420, 0.0350, 0.0120, wf)]
    add(lib.loft_up("NeckKnuckle", st, "M_SageDeep", GW, cap_round=0.0015))
    # disc boss (front-facing cylinder merged into the neck) + copper spun disc [G2: boss 44, disc 35 mm]
    o = (0.0, DISC_UP, wf)
    segs = max(64, D["lathe"] // 2)
    add(lathe("NeckDiscBoss", [(0.0, 0.0), (0.0222, 0.0), (0.0222, 0.0195), (0.0214, 0.0210), (0.0200, 0.0215),
                               (0.0186, 0.0212), (0.0180, 0.0206), (0.0, 0.0206)], o, (0, 0, 1), (1, 0, 0), "M_SageDeep", GW,
              segs=segs, cap0=False, cap1=False))
    add(polar_uv(lathe("NeckDisc", [(0.0178, 0.0203), (0.0178, 0.0216), (0.0172, 0.0222), (0.0120, 0.0225), (0.0, 0.0227)],
                       o, (0, 0, 1), (1, 0, 0), "M_CopperSatin", GW, segs=segs, cap0=True, cap1=False),
                 o, (0, 0, 1), (1, 0, 0), 0.0178))
    # notched tongue under the boss (two legs) [G2, pt04]
    tg = [(-0.0125, 0.0690), (-0.0042, 0.0690), (-0.0042, 0.0735), (0.0042, 0.0735), (0.0042, 0.0690), (0.0125, 0.0690),
          (0.0125, 0.0840), (-0.0125, 0.0840)]
    tgf = fillet(tg, [0.0012, 0.0008, 0.0008, 0.0008, 0.0008, 0.0012, 0.0, 0.0], 3)
    ob = extrude("NeckTongue", tgf, FM, wf + 0.0110, wf + 0.0175, "M_SageDeep", GW)
    bevel(ob, 0.0009, 2)
    add(ob)
    # corrugated hose from the well floor up into the neck [G2, CUT]
    path = lib.bezier_path((0, WELL_FLOOR - 0.006, wf + 0.006), (0, 0.055, wf + 0.006), (0, 0.075, wf + 0.002), (0, 0.092, wf), 10)
    add(sweep_corrugated("NeckHose", path, 0.0150, 0.0012, 11, "M_Hose", GW))
    return objs


# ================================================================== brushroll
def build_roller():
    segs = max(64, int(D["roller_segs"] * 0.8))
    nr = max(24, int(D["roller_rings"] * 0.5))
    N = 8                     # copper chevron ridges around [rt-ia3241-build-quality, CUT]
    K = 1.20                  # chevron twist (rad) from centre to end [H1, pt04, real underside]
    A = R_LOBE - R_CORE
    end = 0.004
    xs = []
    for k in range(nr + 1):
        xs.append(-R_HALF + 2 * R_HALF * k / nr)
    # insert extra rings near x = 0 for the sharp chevron apex
    xs = sorted(set([round(x, 6) for x in xs] + [-0.0015, -0.0006, 0.0, 0.0006, 0.0015]))

    def lobe(th):
        u = (N * th + math.pi) % TAU - math.pi          # -pi..pi, crease at +-pi
        return 1.0 - abs(u / math.pi) ** 2.4

    def phi_of(x):
        return K * min(abs(x), R_HALF) / R_HALF

    def radius(x, thl):
        """thl = angle in the twisted (chevron-aligned) frame -> creases follow vertex columns exactly"""
        ax = abs(x)
        base = R_CORE + A * lobe(thl)
        if ax > R_HALF - end:
            q = (ax - (R_HALF - end)) / end
            taper = math.cos(q * math.pi / 2)
            return (R_CORE - 0.002) + (base - (R_CORE - 0.002)) * (0.35 + 0.65 * taper)
        return base

    verts, uvs, faces = [], [], []
    n = segs + 1
    for x in xs:
        ph = phi_of(x)
        for j in range(n):
            thl = TAU * j / segs
            r = radius(x, thl)
            th = thl + ph
            verts.append(Vector((x, r * math.sin(th), r * math.cos(th))))
            uvs.append((j / segs, (x + R_HALF) / (2 * R_HALF)))
    for i in range(len(xs) - 1):
        for j in range(segs):
            a, b = i * n + j, (i + 1) * n + j
            faces.append((a, a + 1, b + 1, b))
    for idx, ri in ((0, 0), (1, len(xs) - 1)):
        c = len(verts)
        verts.append(Vector((xs[ri], 0, 0)))
        uvs.append((0.5, 0.0 if idx == 0 else 1.0))
        for j in range(segs):
            a = ri * n + j
            faces.append((c, a + 1, a) if idx == 0 else (c, a, a + 1))
    body = mk("RollerFront", verts, faces, "M_CopperBrush", "RollerFront", uvs=uvs)

    # bristle strips (2, in lobe valleys) — serrated ribbons following the chevron [H1, pt04, CUT]
    bverts, bfaces = [], []
    ns = 150 if D["roller_segs"] > 100 else 70
    for row in range(2):
        t0 = math.pi / N + row * math.pi
        for i in range(ns + 1):
            x = -R_HALF + 0.003 + (2 * R_HALF - 0.006) * i / ns
            phi = K * abs(x) / R_HALF
            th = t0 + phi
            d = Vector((0, math.sin(th), math.cos(th)))
            tg = Vector((0, math.cos(th), -math.sin(th)))
            h = (math.sin(i * 12.9898 + row * 78.233) * 43758.5453) % 1.0
            tip = R_TIP - 0.0012 * h
            for rr, w in ((R_CORE - 0.0008, 0.0013), (tip, 0.0027)):
                for sg in (-1, 1):
                    bverts.append(Vector((x, 0, 0)) + d * rr + tg * (sg * w))
        base0 = len(bverts) - 4 * (ns + 1)
        for i in range(ns):
            a = base0 + 4 * i
            b = a + 4
            # quads: root-L(0) root-R(1) tip-L(2) tip-R(3)
            bfaces += [(a + 0, b + 0, b + 2, a + 2), (a + 1, a + 3, b + 3, b + 1), (a + 2, b + 2, b + 3, a + 3)]
        a = base0
        bfaces.append((a + 0, a + 2, a + 3, a + 1))
        a = base0 + 4 * ns
        bfaces.append((a + 0, a + 1, a + 3, a + 2))
    bristle = mk("RollerFrontBristles", bverts, bfaces, "M_Bristle", "RollerFront", smooth=False)
    # end hubs
    hubs = []
    for s in (1, -1):
        prof = [(0.0, s * (R_HALF - 0.001)), (0.0160, s * (R_HALF - 0.001)), (0.0165, s * (R_HALF + 0.0005)),
                (0.0150, s * (R_HALF + 0.0055)), (0.0060, s * (R_HALF + 0.0060)), (0.0, s * (R_HALF + 0.0060))]
        verts2, faces2 = [], []
        sg2 = 48
        rings = []
        for r, x in prof:
            rings.append([Vector((x, r * math.sin(TAU * j / sg2), r * math.cos(TAU * j / sg2))) for j in range(sg2)])
        verts2, faces2 = ring_mesh(rings, False, False)
        hubs.append(mk(f"RollerFrontHub_{s}", verts2, faces2, "M_Graphite", "RollerFront"))
    roller = lib.join_objects([body, bristle] + hubs, "RollerFront")
    roller.location = V(0, R_UP, R_FWD)
    # hidden belt-drive pulley inside the left end (the TurboPro head has one brushroll; contract wants a RollerRear)
    rings = []
    for r, x in [(0.0, -0.1080), (0.0075, -0.1080), (0.0075, -0.1000), (0.0, -0.1000)]:
        rings.append([Vector((0, r * math.sin(TAU * j / 16), r * math.cos(TAU * j / 16))) for j in range(16)])
    rv, rf = ring_mesh(rings, False, False)
    rear = mk("RollerRear", rv, rf, "M_Graphite", "RollerRear")
    rear.location = V(-0.104, 0.040, -0.040)
    rear.hide_render = True
    return roller, rear


# ================================================================== entry
def build(ctx):
    P = ctx["P"]
    body, leds = build_body(P)
    neck = build_knuckle(P)
    roller, rear = build_roller()
    wf = P.WAND_FWD
    return {
        "groups": {"FloorHead": body, "LowerWand": neck},
        "special": {"RollerFront": roller, "RollerRear": rear, "HeadLights": leds},
        "anchors": {
            "NeckPivot": (0.0, PIV_UP, wf),
            "WandSocket": (0.0, P.WAND_SOCKET_UP, wf),
            "IntakeFront": (0.0, 0.0, INT_F),
            "IntakeRear": (0.0, 0.0, INT_R),
        },
        "contacts": {
            "Contact_WheelL": (-(WX0 + WX1) / 2, 0.0, W_FWD),
            "Contact_WheelR": ((WX0 + WX1) / 2, 0.0, W_FWD),
            "Contact_GlideL": (-0.121, 0.0, 0.032),
            "Contact_GlideR": (0.121, 0.0, 0.032),
            "Contact_Brushroll": (0.0, 0.0, R_FWD),
            "Contact_CombFront": (0.0, 0.0, 0.042),
        },
        "nozzle": {"intakeWidth": 0.211, "intakeZMin": INT_R, "intakeZMax": INT_F},
        "notes": ("TurboPro Detect head (wheels x +-0.0490..0.0635, D 0.052, axle (up 0.026, fwd -0.100); knuckle top "
                  "section at WAND_SOCKET_UP: rounded rect 42 x 35 mm r12 centred on the wand axis). Single brushroll (RollerFront, axis x through (0,%.4f,%.4f), R fins %.4f / "
                  "bristle tips %.4f). RollerRear = hidden belt pulley (no second roller exists). Decals: see "
                  "HeadDecal_* atlas convention in floorhead.py." % (R_UP, R_FWD, R_LOBE, R_TIP)),
    }
