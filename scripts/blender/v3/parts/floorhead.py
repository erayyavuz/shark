"""
floorhead part (v3, IP3251 / IP1251 shared hardware) — DuoClean Detect floor nozzle. Owned by the floorhead agent.
See ../PARTS_CONTRACT.md. Product coords (x right, up, fwd); the head is positioned relative to the wand axis
(P.WAND_FWD): nose = WAND_FWD + NOSE_TO_AXIS, so it stays right whatever the lead settles WAND_FWD on.

Internally every fore-aft value is d = distance BEHIND THE NOSE (metres); F(d) converts to product fwd.

Dimension ledger. Sources:
  [S1]  manual tr_og_p-16 Fig.1 side elevation (scaled by wheel D 47 mm -> 0.224 mm/px); Fig.3 underside
  [S18] manual tr_og_p-18 underside (0.3925 mm/px across the 263 mm width): squeegee screws, locks, chevron V
  [V5]  V5 bottom-left top-down quadrant (0.3985 mm/px): roller bands, neck plate, Light Detect window
  [V2]  V2 IP1251 head close (side cap teardrop panel, roller end button, edge-sensor oval, wheel, neck)
  [CR]  frames/crop-tr01-floorhead (corner LED wedges, cover tiers, duoclean plate, neck disc + castellated tongue)
  [U]   user frames 1663-1667 (colours, rear violet glow by the wheels, white front spill 1667, purple side caps)
  [VID] PRODUCT_REFERENCE_IP3251 v2 video frames: wuX-t0160 underside, JCG-t0176.9 top deck, cHk-t0009 headlights,
        YVH-t0013 rear violet glow, wuX-t0340 side cap
Lights: front corner housings = WHITE headlights (M_LED) + white floor bars under the front corners; violet strip
behind the roller window + violet LEDs at the rear corners beside the wheels (M_LEDAccent).
  [inf] inferred
"""
import math
import random

from mathutils import Vector

import lib
from lib import V, mk, bevel, extrude, fillet, catmull, lathe, ring_mesh, rrect, toB, TAU, D

G = "FloorHead"
GW = "LowerWand"

# ------------------------------------------------------------------ ledger (d = metres behind the nose)
NOSE_TO_AXIS = 0.165  # nose -> wand axis [S1 167, V5 163]
HALF_W = 0.1315       # outer half width (263 mm) [official]
X_IN = 0.1120         # side-cap inner face = cover / deck half width [V5, CR]
BODY_D = 0.131        # nose -> rear edge of the side caps / deck [V5 125-132, S1 129]
# front brushroll (black bristle roll, teal double-helix stripes via M_RollerFront) at the very front under the clear
# lip [wuX-t0160 bay ~0.7x the mint bay, V5 band d 10-36, spare part 383CH1000EUT]
RF_R, RF_D, RF_HALF = 0.0205, 0.0250, 0.1030
# rear soft roller (large mint plush + one golden fibre V strip) under the top window [wuX-t0160, U 1663, V5 d 36-86]
RR_CORE, RR_TIP, RR_D, RR_UP, RR_HALF = 0.0270, 0.0285, 0.0720, 0.0290, 0.1010
INT_D0, INT_D1 = 0.004, 0.0860            # intake opening (soleplate hole) [S18]
WHEEL_R, WHEEL_W, WHEEL_X, WHEEL_D = 0.0235, 0.0160, 0.0585, 0.1690   # rear wheels [S1, S18 +-57 mm, V5]
PIV_UP = 0.042        # neck pitch barrel axis height [V2, S18, inf]
DISC_UP = None        # = P.NECK_DISC_UP
PLATE_D0, PLATE_D1, PLATE_HW = 0.0905, 0.183, 0.0535   # neck plate plan [V5 86..177 mm, 110 mm wide]
WELL_HW, WELL_D0 = 0.0255, 0.141                       # neck well in the plate rear [S18, V2]


def F(d):
    return _NOSE - d


_NOSE = 0.084


def SM(u, v, w):
    """side map: u = fwd, v = up, w = x"""
    return V(w, v, u)


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
    """many boxes in one mesh. spec: (x0,x1,u0,u1,f0,f1) or 8 explicit corner Vectors in the same order"""
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


def _quad_uv(name, corners, uvs, mat, grp):
    """single quad (4 Blender Vectors, CCW seen from outside) with per-vertex UVs"""
    return mk(name, corners, [(0, 1, 2, 3)], mat, grp, smooth=False, uvs=uvs, recalc=False)


def _aspect(slot, default):
    try:
        import materials as MT
        return float(MT.DECALS[slot].get("inkAspect", default))
    except Exception:  # noqa: BLE001
        return default


def _slot_uvs(slot, rect="ink"):
    import materials as MT
    try:
        return [MT.decal_uv(slot, 0, 0, rect), MT.decal_uv(slot, 1, 0, rect), MT.decal_uv(slot, 1, 1, rect),
                MT.decal_uv(slot, 0, 1, rect)]
    except Exception:  # noqa: BLE001
        return [(0, 0), (1, 0), (1, 1), (0, 1)]


def decal_quad(name, c, sdir, tdir, w, h, slot, outward, off=0.0):
    """M_Decal plate centred at product point c: s (reading) along sdir, t (glyph up) along tdir. The decal material
    culls back faces, so the winding is fixed so that s x t points along `outward` (s is never flipped: a flip would
    mirror the print; instead the caller must pass a non-mirrored s/t pair)."""
    sdir, tdir = Vector(sdir).normalized(), Vector(tdir).normalized()
    n = sdir.cross(tdir)
    assert n.dot(outward) > 0, f"{name}: mirrored decal frame"
    c = Vector(c) + Vector(outward).normalized() * off
    pts = [c - sdir * w / 2 - tdir * h / 2, c + sdir * w / 2 - tdir * h / 2, c + sdir * w / 2 + tdir * h / 2,
           c - sdir * w / 2 + tdir * h / 2]
    return _quad_uv(name, [V(*p) for p in pts], _slot_uvs(slot), "M_Decal", G)


def edge_decal(s):
    """'EDGE DETECT' strip following the curved cap top (d 0.041 -> ~0.067), x centred on the cap's flat top band"""
    prof = [p for p in cap_profile() if p[1] > 0.045 and 0.041 < p[0] < 0.095]
    prof.sort()
    # resample by arc length
    L = [0.0]
    for a, b in zip(prof, prof[1:]):
        L.append(L[-1] + math.dist(a, b))
    ink = 0.0260
    s0 = 0.0
    ink = min(ink, L[-1])

    def at(sv):
        for i in range(len(L) - 1):
            if L[i] <= sv <= L[i + 1]:
                t = (sv - L[i]) / max(1e-9, L[i + 1] - L[i])
                a, b = prof[i], prof[i + 1]
                p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                tg = Vector((b[0] - a[0], b[1] - a[1])).normalized()
                return p, tg
        return prof[-1], Vector((1, 0))

    hw = ink / _aspect("edge_detect", 5.2137) / 2
    xc = s * (X_IN + HALF_W) / 2
    n = 10
    uv = _slot_uvs("edge_detect")
    verts, uvs, faces = [], [], []
    for k in range(n + 1):
        f = k / n
        (d, up), tg = at(s0 + ink * f)
        nrm = Vector((-tg.y, tg.x))  # (d, up) normal
        if nrm.y < 0:
            nrm = -nrm
        dd, uu = d + nrm.x * 0.0003, up + nrm.y * 0.0003
        # +x cap: reading toward the rear (d increasing), glyph tops toward -x; -x cap mirrors the frame (reads forward)
        sr = f if s > 0 else 1 - f
        for side in (0, 1):
            x = xc + (s * hw if side == 0 else -s * hw)  # side 0 = outer (t=0), side 1 = inner (t=1)
            verts.append(V(x, uu, F(dd)))
            u0, v0 = uv[0]
            u1, v1 = uv[2]
            uvs.append((u0 + (u1 - u0) * sr, v0 + (v1 - v0) * side))
    for k in range(n):
        a = 2 * k
        faces.append((a, a + 2, a + 3, a + 1))
    ob = mk(f"HeadDecal_edge_{'R' if s > 0 else 'L'}", verts, faces, "M_Decal", G, smooth=False, uvs=uvs, recalc=False)
    # winding: face normal must point up/outward
    me = ob.data
    if me.polygons[0].normal.z < 0:
        for p in me.polygons:
            p.flip()
    return ob


def offset_closed(pts, dist):
    """offset a closed CCW 2D polygon inward by dist (miter, clamped)"""
    out = []
    N = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % N][1] - pts[(i + 1) % N][0] * pts[i][1] for i in range(N))
    sgn = 1 if area > 0 else -1
    for i in range(N):
        a, b, c = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % N])
        t1 = (b - a).normalized() if (b - a).length > 1e-9 else Vector((1, 0))
        t2 = (c - b).normalized() if (c - b).length > 1e-9 else t1
        n1 = Vector((-t1.y, t1.x)) * sgn
        n2 = Vector((-t2.y, t2.x)) * sgn
        n = (n1 + n2)
        if n.length < 1e-6:
            n = n1
        n.normalize()
        k = 1.0 / max(0.35, n.dot(n1))
        out.append(tuple(b + n * dist * k))
    return out


def sweep_corrugated(name, path, r0, amp, nridge, mat, grp, segs=None):
    segs = segs or max(16, D["lathe"] // 6)
    path = [Vector(p) for p in path]
    fine = []
    for i in range(len(path) - 1):
        for k in range(8):
            fine.append(path[i].lerp(path[i + 1], k / 8))
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
    verts, faces = ring_mesh(rings, False, False)
    return mk(name, verts, faces, mat, grp)


def polar_uv(ob, origin, axis, ref, rmax):
    """spun-metal UVs: V runs around the disc (concentric grooves), U outward"""
    wraps = max(1, round(TAU * rmax / 0.05))
    o = toB(Vector(origin))
    A = toB(Vector(axis)).normalized()
    U = toB(Vector(ref)).normalized()
    W = A.cross(U)
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        pc = poly.center - o
        ac = math.atan2(pc.dot(W), pc.dot(U)) % TAU
        for li in poly.loop_indices:
            dv = me.vertices[me.loops[li].vertex_index].co - o
            dv = dv - A * dv.dot(A)
            r = dv.length
            a = math.atan2(dv.dot(W), dv.dot(U)) % TAU if r > 1e-7 else ac
            if a - ac > math.pi:
                a -= TAU
            elif ac - a > math.pi:
                a += TAU
            uvl.data[li].uv = (min(r, rmax) / 0.05, wraps * a / TAU)
    return ob


def _pts_df(pts):
    """(d, up) -> (fwd, up)"""
    return [(F(d), u) for d, u in pts]


# ------------------------------------------------------------------ profiles (d, up)
def cap_profile():
    """side cap rounded-triangle 'lozenge' [S1 Fig.1: nose 0, peak d 70 up 62, rear round end d 128]"""
    pts = [(0.0040, 0.0015), (0.0000, 0.0300), (0.0700, 0.0700), (0.1330, 0.0330), (0.1250, 0.0015)]
    return fillet(pts, [0.0025, 0.0060, 0.0280, 0.0260, 0.0035], max(8, D["corner"] + 2))


def panel_profile():
    """purple teardrop inset panel on the cap [S1 inner outline, V2]"""
    pts = [(0.0110, 0.0075), (0.0040, 0.0190), (0.0600, 0.0615), (0.0915, 0.0345), (0.0855, 0.0075)]
    return fillet(pts, [0.0040, 0.0075, 0.0150, 0.0210, 0.0060], max(8, D["corner"] + 2))


def cover_outer():
    """ONE continuous clear cover section (d, up): floor-level front bumper -> vertical clear front over the black
    brushroll -> angled badge facet -> smooth dome over the mint roller -> rear edge at the violet strip.
    [pdp DuoCleanDetect, crop-cl-eut-01 front, crop-tr01, cHk-t0009, V2]"""
    # tiers seen in UDDjkrKD7Mk-t0189 (front straight): clear bumper box -> shelf -> badge slope -> ledge ->
    # upper face (mint roller behind) -> rounded top edge -> dome
    pts = [(0.0040, 0.0026), (0.0000, 0.0050), (-0.0012, 0.0110), (-0.0012, 0.0285), (0.0012, 0.0325),
           (0.0035, 0.0355), (0.0105, 0.0485), (0.0140, 0.0505), (0.0168, 0.0560), (0.0205, 0.0665),
           (0.0270, 0.0718), (0.0400, 0.0738), (0.0640, 0.0735), (0.0860, 0.0718)]
    return catmull(pts, per=max(3, int(round(2 * D["path"]))))


FACET = ((0.0035, 0.0355), (0.0105, 0.0485))   # angled badge facet on the cover front face (d, up)


def deck_profile():
    """rear deck shell behind the cover, between the caps (d, up); its front underside arches over the mint roller"""
    pts = [(0.1060, 0.0060), (0.1050, 0.0420), (0.0900, 0.0575), (0.0858, 0.0700), (0.0905, 0.0728),
           (0.1100, 0.0722), (0.1300, 0.0590), (0.1345, 0.0420), (0.1345, 0.0080), (0.1300, 0.0055)]
    return fillet(pts, [0.001, 0.006, 0.004, 0.002, 0.004, 0.012, 0.010, 0.004, 0.003, 0.001], max(6, D["corner"]))


def plate_top(d):
    """neck plate top height vs d"""
    t = (d - PLATE_D0) / (PLATE_D1 - PLATE_D0)
    return 0.0770 - 0.0040 * t


# ================================================================== body
def build_body(P):
    objs = []
    add = objs.append
    leds = []

    # ---- side caps (charcoal) + purple teardrop panel + turquoise roller-release button + Edge Detect oval
    cp = _pts_df(cap_profile())
    pp = _pts_df(panel_profile())
    for s, tag in ((1, "R"), (-1, "L")):
        ob = extrude(f"HeadCap_{tag}", cp, SM, s * X_IN, s * HALF_W, "M_Charcoal", G)
        bevel(ob, 0.0058, max(5, D["bevel_seg"] + 1), angle=30)
        add(ob)
        # recessed groove around the panel (dark), then the purple panel slightly proud of it
        groove = offset_closed(pp, -0.0011)
        add(extrude(f"HeadCapGroove_{tag}", groove, SM, s * (HALF_W - 0.0010), s * (HALF_W + 0.0001), "M_Rubber", G))
        pan = extrude(f"HeadCapPanel_{tag}", pp, SM, s * (HALF_W - 0.0008), s * (HALF_W + 0.0007), "M_Purple", G)
        bevel(pan, 0.0006, 2, angle=30)
        add(pan)
        # roller end disc + turquoise release button concentric with the front roller axis [V2, CR, S1 Fig.2]
        o = (s * (HALF_W + 0.0006), RF_R, F(RF_D))
        add(lathe(f"HeadEndDisc_{tag}", [(0.0102, -0.0002), (0.0102, 0.0004), (0.0097, 0.0009), (0.0, 0.0009)],
                  o, (s, 0, 0), (0, 0, 1), "M_Charcoal", G, segs=max(40, D["lathe"] // 4), cap0=True, cap1=False))
        add(lathe(f"HeadRollerBtn_{tag}", [(0.0072, 0.0005), (0.0072, 0.0030), (0.0067, 0.0040), (0.0045, 0.0044),
                                           (0.0, 0.0045)], o, (s, 0, 0), (0, 0, 1), "M_Turquoise", G,
                  segs=max(40, D["lathe"] // 4), cap0=True, cap1=False))
        # Edge Detect oval window toward the cap rear [S1 Fig.1, V2, tr_og_p-17 Fig.3]
        ov = rrect(0.0150, 0.0058, 0.0029)
        ov = [(F(0.1130) + a, 0.0215 + b) for a, b in ov]
        bz = rrect(0.0172, 0.0080, 0.0040)
        bz = [(F(0.1130) + a, 0.0215 + b) for a, b in bz]
        add(extrude(f"HeadEdgeBezel_{tag}", bz, SM, s * (HALF_W - 0.0006), s * (HALF_W + 0.0004), "M_Gunmetal", G,
                    bev=0.0004, bev_seg=2))
        add(extrude(f"HeadEdgeLens_{tag}", ov, SM, s * (HALF_W + 0.0003), s * (HALF_W + 0.0007), "M_Screen", G))

        # ---- front corner headlight housing: angular gunmetal shoulder on the lip-box end, inner edge slanting down
        # toward the badge, white headlight window low on its front face [cl-eut-01, cHk-t0009, CR]
        hp = [(0.0835, 0.0350), (0.1315, 0.0300), (0.1315, 0.0545), (0.1200, 0.0562), (0.1000, 0.0560),
              (0.0835, 0.0470)]
        hp = fillet(hp, [0.0008, 0.0010, 0.0040, 0.0030, 0.0030, 0.0015], 4)
        lean = 0.15

        def dfront(up):
            return -0.0010 + (up - 0.0300) * lean

        def hmap(u, v, w, s=s):
            d = dfront(v) if w < 0.5 else 0.0380
            return V(s * u, v, F(d))

        w = extrude(f"HeadLightHousing_{tag}", hp, hmap, 0.0, 1.0, "M_Charcoal", G)
        bevel(w, 0.0010, 3, angle=30)
        add(w)
        # emitter + clear lens on the front face
        def fpt(x, up, off):
            return V(s * x, up, F(dfront(up) - off))

        xs0, xs1, u0, u1 = 0.1000, 0.1220, 0.0420, 0.0500
        # dark PCB pocket behind the lens with 3 small white LED chips in a row [UDDjkrKD7Mk-t0189, cHk-t0009]
        add(mk(f"HeadLedPcb_{tag}", [fpt(xs0, u0, 0.0001), fpt(xs1, u0, 0.0001), fpt(xs1, u1, 0.0001),
                                      fpt(xs0, u1, 0.0001)], [(0, 1, 2, 3)], "M_Screen", G, smooth=False))
        ev, ef = [], []
        for k in range(3):
            xc = (xs0 + xs1) / 2 + s * (k - 1) * 0.0042
            b0 = len(ev)
            ev += [fpt(xc - 0.0013, u0 + 0.0022, 0.0003), fpt(xc + 0.0013, u0 + 0.0022, 0.0003),
                   fpt(xc + 0.0013, u1 - 0.0022, 0.0003), fpt(xc - 0.0013, u1 - 0.0022, 0.0003)]
            ef.append((b0, b0 + 1, b0 + 2, b0 + 3))
        em = mk(f"HeadLedFront_{tag}", ev, ef, "M_LED", G, smooth=False)
        leds.append(em)
        lens = rrect(xs1 - xs0 + 0.0024, u1 - u0 + 0.0024, 0.0016)
        lv, lf = [], []
        for off in (0.0004, 0.0011):
            for (a, b) in lens:
                lv.append(fpt((xs0 + xs1) / 2 + a, (u0 + u1) / 2 + b, off))
        n = len(lens)
        lf.append(tuple(range(n)))
        lf.append(tuple(range(2 * n - 1, n - 1, -1)))
        for j in range(n):
            j2 = (j + 1) % n
            lf.append((j, j2, n + j2, n + j))
        add(mk(f"HeadLedLens_{tag}", lv, lf, "M_ClearCover", G, smooth=False))
        # small dark sensor window inboard-below the lens [pdp DuoCleanDetect, crop-tr01]
        dw_ = rrect(0.0050, 0.0042, 0.0010)
        dv = [fpt(0.0910 + a, 0.0420 + b, 0.0003) for a, b in dw_]
        add(mk(f"HeadLedSensor_{tag}", dv, [tuple(range(len(dv)))], "M_Screen", G, smooth=False))

        # ---- white headlight bar under the bottom front corner (floor spill) [cHk-t0009, wuX-t0340, U 1667]
        x0, x1 = sorted((s * 0.0985, s * 0.1255))
        bar = _box(f"HeadLedBar_{tag}", x0, x1, 0.0016, 0.0034, F(0.0125), F(0.0035), "M_LED", G)
        leds.append(bar)
        # ---- violet under-glow LED at the rear corner beside the wheel (facing down/back) [U 1664-1666, YVH-t0013]
        x0, x1 = sorted((s * 0.0680, s * 0.1000))
        rb = _box(f"HeadLedRear_{tag}", x0, x1, 0.0042, 0.0082, F(0.1352), F(0.1290), "M_LEDAccent", G)
        leds.append(rb)
        # roller bearing hub on the cap inner face (behind the roller end)
        add(lathe(f"HeadBearing_{tag}", [(0.0130, s * (RF_HALF + 0.0035)), (0.0130, s * (X_IN + 0.0002))],
                  (0, RF_R, F(RF_D)), (1, 0, 0), (0, 0, 1), "M_Charcoal", G, segs=32, cap0=True, cap1=False))
        add(lathe(f"HeadBrushHub_{tag}", [(0.0105, s * (RR_HALF + 0.0030)), (0.0105, s * (X_IN + 0.0002))],
                  (0, RR_UP, F(RR_D)), (1, 0, 0), (0, 0, 1), "M_Charcoal", G, segs=28, cap0=True, cap1=False))

    # ---- ONE continuous clear cover shell (2.2 mm polycarbonate) between the caps [pdp, CR, cl-eut-01, U]
    co = cover_outer()
    ci = lib.offset_polyline(co, -0.0028)  # inward (polyline runs up/back in (d, up))
    if ci[len(ci) // 2][1] > co[len(co) // 2][1]:
        ci = lib.offset_polyline(co, 0.0028)
    outline = [(F(d), u) for d, u in co] + [(F(d), u) for d, u in reversed(ci)]
    cov = extrude("HeadCover", outline, SM, -X_IN - 0.0004, X_IN + 0.0004, "M_ClearCover", G)
    bevel(cov, 0.0008, 2, angle=50)
    add(cov)
    # thick clear rolled rim along the top-front edge of the window (reads as a glossy bar in every front view)
    # [cl-eut-01, UDDjkrKD7Mk-t0189, crop-tr01]
    add(lathe("HeadCoverRim", [(0.0034, -X_IN + 0.0006), (0.0042, -X_IN + 0.0030), (0.0042, X_IN - 0.0030),
                               (0.0034, X_IN - 0.0006)], (0, 0.0700, F(0.0255)), (1, 0, 0), (0, 0, 1),
              "M_ClearCover", G, segs=24, cap0=True, cap1=True))
    # dark recessed cavity ends inside the cover (seen through the clear ends), set 3 mm inside the cap faces
    wall = [(F(d), u - 0.0024) for d, u in co if d > 0.002] + [(F(0.0880), 0.0060), (F(0.0060), 0.0060)]
    for s_ in (1, -1):
        add(extrude(f"HeadCavityEnd_{'R' if s_ > 0 else 'L'}", wall, SM, s_ * (X_IN - 0.0060), s_ * (X_IN - 0.0005),
                    "M_Rubber", G))
    # horizontal rail + vertical clip ribs on the bumper front face [CR, cl-eut-01]
    add(_box("HeadCoverRail", -X_IN, X_IN, 0.0268, 0.0286, F(-0.0030), F(-0.0008), "M_ClearCover", G, bev=0.0005))
    clips = []
    for xc in (-0.1060, -0.0560, 0.0, 0.0560, 0.1060):
        clips.append((xc - 0.0028, xc + 0.0028, 0.0060, 0.0268, F(-0.0026), F(-0.0008)))
    add(_boxes("HeadCoverClips", clips, "M_ClearCover", G))
    # clear bumper end blocks in front of the cap noses (bottom corners) [cl-eut-01: to |x| 127 mm, 0-30 mm high]
    for s_ in (1, -1):
        x0, x1 = sorted((s_ * (X_IN - 0.0004), s_ * 0.1275))
        add(_box(f"HeadBumperEnd_{'R' if s_ > 0 else 'L'}", x0, x1, 0.0030, 0.0290, F(-0.0012), F(0.0040), "M_ClearCover", G,
                 bev=0.0008))
    # dark rubber floor lip under the bumper
    add(_box("HeadFrontLip", -0.1110, 0.1110, 0.0006, 0.0034, F(0.0055), F(0.0020), "M_Rubber", G, bev=0.0005))

    # ---- duoclean DETECT grey plate + decal on the cover facet [CR, U 1663]
    import materials as MT
    fa, fb = Vector((F(FACET[0][0]), FACET[0][1])), Vector((F(FACET[1][0]), FACET[1][1]))
    tv = (fb - fa)
    nv = Vector((-tv.y, tv.x)).normalized()
    if nv.x < 0:  # outward = forward
        nv = -nv
    # plate: 92 x ~13.5 mm (fits the facet), centred
    PW = 0.1000

    def fp(x, t, off):
        q = fa + tv * t + nv * off
        return V(x, q.y, q.x)

    L = tv.length
    hb = 0.47 * L
    # trapezoid badge with angled ends (wider at the bottom) [cHk-t0009, U 1663]
    pl = fillet([(-PW / 2 - 0.004, -hb), (PW / 2 + 0.004, -hb), (PW / 2 - 0.003, hb), (-PW / 2 + 0.003, hb)],
                0.0012, 3)
    pv, pf = [], []
    for off in (0.0002, 0.0012):
        for a, b in pl:
            pv.append(fp(a, 0.5 + b / L, off))
    n = len(pl)
    pf.append(tuple(range(n)))
    pf.append(tuple(range(2 * n - 1, n - 1, -1)))
    for j in range(n):
        j2 = (j + 1) % n
        pf.append((j, j2, n + j2, n + j))
    plate = mk("HeadDuoPlate", pv, pf, "M_LabelGrey", G, smooth=False)
    add(plate)
    asp = _aspect("duoclean_detect", 7.85)
    dw = min(0.0745, asp * 0.80 * L)  # ink ~74-76 mm on the real badge (UDDjkrKD7Mk-t0189, cl-eut-01: 76 mm)
    dh = dw / asp
    th = dh / L
    corners = [fp(-dw / 2, 0.5 - th / 2, 0.00145), fp(dw / 2, 0.5 - th / 2, 0.00145),
               fp(dw / 2, 0.5 + th / 2, 0.00145), fp(-dw / 2, 0.5 + th / 2, 0.00145)]
    add(_quad_uv("HeadDecal_duoclean", corners, _slot_uvs("duoclean_detect"), "M_Decal", G))

    # ---- rear deck housing between the caps
    dp = _pts_df(deck_profile())
    dk = extrude("HeadDeck", dp, SM, -X_IN - 0.0004, X_IN + 0.0004, "M_Charcoal", G)
    bevel(dk, 0.0012, 2, angle=40)
    add(dk)
    # violet light strip along the rear edge of the roller window [JCG-t0176.9, YVH-t0013]
    vs = _box("HeadVioletStrip", -X_IN + 0.0005, X_IN - 0.0005, 0.0712, 0.0736, F(0.0884), F(0.0858), "M_LEDAccent", G)
    leds.append(vs)
    # seam line across the deck top where the top shell meets the chassis
    add(_box("HeadDeckSeam", -X_IN, X_IN, 0.0080, 0.0090, F(0.1352), F(0.1340), "M_Rubber", G))
    # inner roller tub: rear wall + divider behind the front roller (dark, hides the floor through the cover)
    add(_box("HeadTubRear", -X_IN, X_IN, 0.0070, 0.0430, F(0.1060), F(0.1030), "M_Rubber", G))

    # ---- soleplate frame with the intake opening (underside) [S18]
    outer = [(x, d) for x, d in rrect(2 * X_IN, BODY_D - 0.003, 0.004)]
    inner = [(x, d) for x, d in rrect(2 * 0.1045, INT_D1 - INT_D0, 0.003)]
    oc = (BODY_D - 0.003) / 2 + 0.003
    ic = (INT_D1 + INT_D0) / 2
    verts, faces = [], []
    n = len(outer)
    for up in (0.0030, 0.0068):
        verts += [V(x, up, F(oc + d)) for x, d in outer]
        verts += [V(x, up, F(ic + d)) for x, d in inner]
    # bottom ring (o0,i0), top ring (o1,i1)
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((o0 + j, o0 + j2, i0 + j2, i0 + j))
        faces.append((o1 + j, i1 + j, i1 + j2, o1 + j2))
        faces.append((o0 + j, o1 + j, o1 + j2, o0 + j2))
        faces.append((i0 + j, i0 + j2, i1 + j2, i1 + j))
    add(mk("HeadSole", verts, faces, "M_Charcoal", G, smooth=False))

    # ---- divider bar between the two roller bays with a fine comb into the front brushroll [wuX-t0160]
    teeth = [(-0.1040, 0.1040, 0.0030, 0.0085, F(0.0432), F(0.0372))]
    nt = 64 if D["lathe"] > 100 else 32
    for k in range(nt):
        xc = -0.101 + 0.202 * k / (nt - 1)
        teeth.append((xc - 0.0006, xc + 0.0006, 0.0050, 0.0080, F(0.0372), F(0.0335)))
    dv = _boxes("HeadDividerComb", teeth, "M_Charcoal", G)
    add(dv)
    # ---- rear saw-tooth Anti-Hair-Wrap comb bar behind the mint roller (12 diagonal teeth) [wuX-t0160]
    add(_box("HeadSawBar", -0.1060, 0.1060, 0.0026, 0.0070, F(0.0975), F(0.0860), "M_Charcoal", G, bev=0.0006))
    saw = []
    for k in range(12):
        xc = -0.0935 + 0.187 * k / 11
        # skewed triangle tooth (long edge along the bar, tip toward the roller), extruded 3 mm tall
        tri = [(xc - 0.0075, F(0.0860)), (xc + 0.0060, F(0.0860)), (xc + 0.0040, F(0.0805))]
        vs = [V(x, u, f) for u in (0.0034, 0.0066) for (x, f) in tri]
        saw.append(vs)
    sv, sf = [], []
    for vs in saw:
        b0 = len(sv)
        sv += vs
        sf += [(b0, b0 + 1, b0 + 2), (b0 + 5, b0 + 4, b0 + 3), (b0, b0 + 3, b0 + 4, b0 + 1), (b0 + 1, b0 + 4, b0 + 5, b0 + 2),
               (b0 + 2, b0 + 5, b0 + 3, b0)]
    add(mk("HeadSawTeeth", sv, sf, "M_Charcoal", G, smooth=False))

    # ---- rear squeegee plate + 4 screws + rubber lip [S16 Fig.3, S18]
    add(_box("HeadSqueegeePlate", -0.1040, 0.1040, 0.0026, 0.0040, F(0.1170), F(0.0985), "M_Charcoal", G, bev=0.0006))
    add(_box("HeadSqueegeeLip", -0.1020, 0.1020, 0.0004, 0.0030, F(0.1010), F(0.0985), "M_Rubber", G, bev=0.0004))
    for k, xc in enumerate((-0.1060 + 0.004, -0.0355, 0.0355, 0.1060 - 0.004)):
        o = (xc, 0.0026, F(0.1090))
        sc = lathe(f"HeadSqScrew_{k}", [(0.0024, 0.0), (0.0024, -0.0005), (0.0019, -0.0009), (0.0, -0.0010)],
                   o, (0, 1, 0), (1, 0, 0), "M_Chrome", G, segs=20, cap0=False, cap1=True)
        add(sc)
        add(_boxes(f"HeadSqScrewX_{k}", [(xc - 0.0016, xc + 0.0016, 0.0014, 0.0017, F(0.1093), F(0.1087)),
                                          (xc - 0.0003, xc + 0.0003, 0.0014, 0.0017, F(0.1106), F(0.1074))],
                   "M_Rubber", G))
    # rating label on the neck underside ("Shark Power Nozzle", white; no print slot yet) [wuX-t0160]
    lw = 0.0300
    lh = lw / _aspect("rating_label", 2.0643)
    add(decal_quad("HeadDecal_rating", Vector((0.0, 0.00968, F(0.1610))), Vector((-1, 0, 0)), Vector((0, 0, -1)),
                   lw, lh, "rating_label", Vector((0, -1, 0))))
    # 2 quarter-turn locks either side of the neck (big slotted heads, arrow ribs) [S16 Fig.3]
    for s, tag in ((1, "R"), (-1, "L")):
        xc = s * 0.0360
        o = (xc, 0.0100, F(0.1385))
        add(lathe(f"HeadLock_{tag}", [(0.0072, 0.0), (0.0072, -0.0022), (0.0066, -0.0030), (0.0, -0.0031)],
                  o, (0, 1, 0), (1, 0, 0), "M_SilverBrush", G, segs=36, cap0=False, cap1=True))
        ang = math.radians(35 * s)
        ca, sa = math.cos(ang), math.sin(ang)
        cs = []
        for a, b in ((-0.0060, -0.0009), (0.0060, -0.0009), (0.0060, 0.0009), (-0.0060, 0.0009)):
            cs.append((xc + a * ca - b * sa, F(0.1385) + a * sa + b * ca))
        sl = [V(x, u, f) for u in (0.0066, 0.0071) for (x, f) in cs]
        add(mk(f"HeadLockSlot_{tag}", sl, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3),
                                           (3, 7, 4, 0)], "M_Rubber", G, smooth=False))

    # ---- neck plate (gunmetal) with hose well, "Shark" decal, Light Detect window [V5, V2, U]
    plan = [(-PLATE_HW + 0.004, PLATE_D0), (PLATE_HW - 0.004, PLATE_D0), (PLATE_HW, PLATE_D1), (WELL_HW, PLATE_D1),
            (WELL_HW, WELL_D0), (-WELL_HW, WELL_D0), (-WELL_HW, PLATE_D1), (-PLATE_HW, PLATE_D1)]
    plan = fillet(plan, [0.016, 0.016, 0.009, 0.002, 0.006, 0.006, 0.002, 0.009], max(6, D["corner"]))
    pmap = lambda x, d, w: V(x, 0.0580 + w * (plate_top(d) - 0.0580), F(d))  # noqa: E731
    pl = extrude("HeadNeckPlate", plan, pmap, 0.0, 1.0, "M_Charcoal", G)
    bevel(pl, 0.0030, max(3, D["bevel_seg"]), angle=35)
    add(pl)
    # yoke cheeks rising either side of the neck well (hold the barrel pins) [JCG-t0176.9, V2]
    chk = [(0.1405, plate_top(0.1405) - 0.002), (0.1405, 0.0770), (0.1470, 0.0795), (0.1780, 0.0795),
           (0.1830, 0.0765), (0.1830, plate_top(0.183) - 0.002)]
    chk = _pts_df(fillet(chk, [0.0, 0.004, 0.006, 0.006, 0.004, 0.0], 4))
    for s in (1, -1):
        c = extrude(f"HeadNeckCheek_{'R' if s > 0 else 'L'}", chk, SM, s * (WELL_HW + 0.0008), s * (PLATE_HW - 0.0040),
                    "M_Charcoal", G)
        bevel(c, 0.0022, 3, angle=30)
        add(c)
    # raised rear deck blocks either side of the neck plate [JCG-t0176.9, U 1663]
    for s in (1, -1):
        x0, x1 = sorted((s * (PLATE_HW + 0.0035), s * (X_IN - 0.0030)))
        rb = _box(f"HeadDeckStep_{'R' if s > 0 else 'L'}", x0, x1, 0.0600, 0.0748, F(0.1300), F(0.1105), "M_Charcoal", G)
        bevel(rb, 0.0022, 3)
        add(rb)
    # neck block under the plate between the wheels (cheeks + front wall + cradle) [S18]
    blk = [(-0.0490, -WELL_HW - 0.0010, 0.0100, 0.0490, F(0.1820), F(0.1300)),
           (WELL_HW + 0.0010, 0.0490, 0.0100, 0.0490, F(0.1820), F(0.1300)),
           (-WELL_HW - 0.001, WELL_HW + 0.001, 0.0100, 0.0490, F(0.1430), F(0.1300)),
           (-WELL_HW - 0.001, WELL_HW + 0.001, 0.0100, 0.0180, F(0.1820), F(0.1300))]
    nb = _boxes("HeadNeckBlock", blk, "M_Charcoal", G)
    bevel(nb, 0.0015, 2)
    add(nb)
    # Floor Detect sensor (underside, user's right of the neck = -x) [UK p.11 Fig.4]
    add(lathe("HeadFloorSensor", [(0.0045, 0.0), (0.0045, -0.0006), (0.0030, -0.0008), (0.0, -0.0008)],
              (-0.0300, 0.0100, F(0.1400)), (0, 1, 0), (1, 0, 0), "M_Screen", G, segs=24, cap0=False, cap1=True))
    # Light Detect round window on the plate rear, +x side (user's left; right of the plate seen from the front)
    # [tr_og_p-17 Fig.2, JCG-t0176.9, V5 |x| 30 d 133]
    ld_d = 0.1300
    ld_up = plate_top(ld_d)
    add(lathe("HeadLightDetectRing", [(0.0052, -0.0010), (0.0052, 0.0006), (0.0046, 0.0010), (0.0034, 0.0010),
                                      (0.0032, 0.0004)], (0.0300, ld_up, F(ld_d)), (0, 1, 0), (1, 0, 0),
              "M_Charcoal", G, segs=32, cap0=False, cap1=False))
    add(lathe("HeadLightDetectLens", [(0.0033, 0.0002), (0.0028, 0.0008), (0.0, 0.0011)], (0.0300, ld_up, F(ld_d)),
              (0, 1, 0), (1, 0, 0), "M_Screen", G, segs=32, cap0=True, cap1=False))
    # "Shark" on the plate top; glyph up toward the rear/wand [decals.json shark_neck, ink ~36-40 mm]
    sw = 0.0400
    sh = sw / _aspect("shark_neck", 3.84)
    sd0 = 0.0960
    sd1 = sd0 + sh
    cs = [V(-sw / 2, plate_top(sd0) + 0.00028, F(sd0)), V(sw / 2, plate_top(sd0) + 0.00028, F(sd0)),
          V(sw / 2, plate_top(sd1) + 0.00028, F(sd1)), V(-sw / 2, plate_top(sd1) + 0.00028, F(sd1))]
    add(_quad_uv("HeadDecal_shark", cs, _slot_uvs("shark_neck"), "M_Decal", G))
    # footprint pictogram on the deck, +x side in front of the step block, toe toward the rear [JCG-t0176.9]
    fw = 0.0090
    fh = fw / _aspect("foot_icon", 0.4766)
    add(decal_quad("HeadDecal_foot", Vector((0.0930, 0.07235, F(0.1010))), Vector((1, 0, 0)), Vector((0, 0, -1)),
                   fw, fh, "foot_icon", Vector((0, 1, 0))))
    # "EDGE DETECT" along the top of both side caps behind the headlight housing, glyph tops toward the centre
    for s_ in (1, -1):
        add(edge_decal(s_))

    # ---- rear wheels [S1, V2, U 1667]
    for s, tag in ((1, "R"), (-1, "L")):
        add_wheel(objs, s, tag)
    return objs, leds


def add_wheel(objs, s, tag):
    xc = s * WHEEL_X
    o = (xc, WHEEL_R, F(WHEEL_D))
    A = (s, 0, 0)
    hw = WHEEL_W / 2
    objs.append(lathe(f"HeadWheelTyre_{tag}", [(0.0150, -hw), (0.0205, -hw), (0.0228, -hw + 0.0018),
                                                (WHEEL_R, -hw + 0.0045), (WHEEL_R, hw - 0.0045),
                                                (0.0228, hw - 0.0018), (0.0205, hw), (0.0180, hw),
                                                (0.0178, hw - 0.0010)], o, A, (0, 0, 1), "M_Rubber", G,
                      segs=max(48, D["lathe"] // 3), cap0=False, cap1=False))
    # face (gunmetal) with recessed hub, both sides
    objs.append(lathe(f"HeadWheelFace_{tag}", [(0.0180, hw - 0.0010), (0.0170, hw - 0.0016), (0.0068, hw - 0.0016),
                                                (0.0062, hw - 0.0004), (0.0042, hw - 0.0004), (0.0040, hw - 0.0022),
                                                (0.0, hw - 0.0022)], o, A, (0, 0, 1), "M_Gunmetal", G,
                      segs=max(48, D["lathe"] // 3), cap0=False, cap1=True))
    objs.append(lathe(f"HeadWheelInner_{tag}", [(0.0152, -hw), (0.0140, -hw + 0.0010), (0.0, -hw + 0.0010)], o, A,
                      (0, 0, 1), "M_Charcoal", G, segs=32, cap0=False, cap1=True))
    objs.append(lathe(f"HeadWheelHub_{tag}", [(0.0040, hw - 0.0022), (0.0040, hw - 0.0012), (0.0030, hw - 0.0008),
                                               (0.0, hw - 0.0008)], o, A, (0, 0, 1), "M_SilverBrush", G, segs=24,
                      cap0=False, cap1=True))
    # radial ribs on the outer face
    ribs = []
    nr = 36 if D["lathe"] > 100 else 18
    xo = xc + s * (hw - 0.0016)
    for k in range(nr):
        a = TAU * k / nr
        ca, sa = math.cos(a), math.sin(a)
        r0, r1, t = 0.0072, 0.0166, 0.00035
        corners = []
        for xx in (xo, xo + s * 0.0006):
            for uu in (r0, r1):
                for tt in (-t, t):
                    corners.append(V(xx, WHEEL_R + uu * sa + tt * ca, F(WHEEL_D) + uu * ca - tt * sa))
        ribs.append(corners)
    objs.append(_boxes(f"HeadWheelRibs_{tag}", ribs, "M_Gunmetal", G))
    # axle stub between the neck block and the wheel
    objs.append(lathe(f"HeadAxle_{tag}", [(0.0035, s * 0.0485), (0.0035, s * (WHEEL_X - hw + 0.0005))],
                      (0, WHEEL_R, F(WHEEL_D)), (1, 0, 0), (0, 0, 1), "M_Charcoal", G, segs=16, cap0=True, cap1=True))


# ================================================================== neck (LowerWand)
def build_neck(P):
    objs = []
    add = objs.append
    f0 = P.WAND_FWD
    disc_up = P.NECK_DISC_UP
    top = P.WAND_SOCKET_UP
    # pitch barrel (lateral cylinder) seated in the plate well
    add(lathe("NeckBarrel", [(0.0130, -0.0238), (0.0168, -0.0236), (0.0176, -0.0222), (0.0176, 0.0222),
                             (0.0168, 0.0236), (0.0130, 0.0238)], (0, PIV_UP, f0), (1, 0, 0), (0, 0, 1),
              "M_Charcoal", GW, segs=max(40, D["lathe"] // 4), cap0=True, cap1=True))
    # barrel side bosses (pivot pins visible inside the cheeks)
    for s in (1, -1):
        add(lathe(f"NeckPin_{'R' if s > 0 else 'L'}", [(0.0060, s * 0.0238), (0.0060, s * 0.0252)],
                  (0, PIV_UP, f0), (1, 0, 0), (0, 0, 1), "M_Gunmetal", GW, segs=20, cap0=True, cap1=True))
    # lower duct from the barrel up
    add(lathe("NeckDuct", [(0.0164, 0.0480), (0.0170, 0.0560), (0.0170, 0.0690), (0.0158, 0.0705)],
              (0, 0, f0), (0, 1, 0), (0, 0, 1), "M_Charcoal", GW, segs=max(40, D["lathe"] // 4), cap0=False, cap1=False))
    # corrugated hose between the duct and the connector [V2, CR]
    add(sweep_corrugated("NeckHose", [(0, 0.0700, f0 - 0.001), (0, 0.0850, f0 - 0.002), (0, 0.1010, f0 - 0.001)],
                         0.0152, 0.0011, 7, "M_Hose", GW))
    # front spine of the swivel yoke (in front of the hose) up to the disc boss
    sp = [(f0 + 0.0130, 0.0600), (f0 + 0.0215, 0.0600), (f0 + 0.0255, 0.0860), (f0 + 0.0130, 0.0880)]
    spo = extrude("NeckSpine", fillet(sp, [0.002, 0.003, 0.004, 0.003], 4), SM, -0.0175, 0.0175, "M_Gunmetal", GW)
    bevel(spo, 0.0018, 3)
    add(spo)
    # castellated tongue under the disc boss (the 'cog' plate) [CR]
    tg = []
    tg.append((-0.0230, 0.0230, 0.0840, 0.0895, f0 + 0.0040, f0 + 0.0300))
    for xc in (-0.0175, -0.0058, 0.0058, 0.0175):
        tg.append((xc - 0.0040, xc + 0.0040, 0.0840, 0.0895, f0 + 0.0300, f0 + 0.0365))
    tgo = _boxes("NeckTongue", tg, "M_Gunmetal", GW)
    bevel(tgo, 0.0008, 2)
    add(tgo)
    # connector body: rounded-rect loft from the tongue up to the wand socket
    st = [(0.0970, 0.0500, 0.0520, 0.0150, f0 + 0.0030),
          (0.1300, 0.0500, 0.0540, 0.0150, f0 + 0.0040),
          (0.1600, 0.0470, 0.0510, 0.0140, f0 + 0.0020),
          (0.2100, 0.0430, 0.0480, 0.0130, f0 + 0.0005),
          (top, 0.0400, 0.0460, 0.0120, f0)]
    add(lib.loft_up("NeckConnector", st, "M_Gunmetal", GW, cap_round=0.0025))
    # parting seam band near the top (connector -> wand cuff joint)
    add(lib.loft_up("NeckConnectorSeam", [(top - 0.0040, 0.0404, 0.0464, 0.0122, f0), (top - 0.0030, 0.0404, 0.0464, 0.0122, f0)],
                    "M_Charcoal", GW))
    # disc boss on the connector front + purple spun disc (front facing) [V7, CR]
    bo = (0, disc_up, f0 + 0.0240)
    add(lathe("NeckDiscBoss", [(0.0215, -0.0060), (0.0215, 0.0040), (0.0208, 0.0052), (0.0178, 0.0054),
                               (0.0178, 0.0050)], bo, (0, 0, 1), (1, 0, 0), "M_Gunmetal", GW,
              segs=max(48, D["lathe"] // 3), cap0=False, cap1=False))
    disc = lathe("NeckDisc", [(0.0175, 0.0040), (0.0175, 0.0058), (0.0167, 0.0066), (0.0110, 0.0070), (0.0, 0.0071)],
                 bo, (0, 0, 1), (1, 0, 0), "M_Purple", GW, segs=max(48, D["lathe"] // 3), cap0=True, cap1=False)
    add(polar_uv(disc, bo, (0, 0, 1), (1, 0, 0), 0.0175))
    # oval release button on the connector front (centred 0.079 above the disc) [PR4 2b]
    bu = disc_up + 0.079
    fr = _front_of(st, bu)
    ring = rrect(0.0190, 0.0300, 0.0090)
    bz = extrude("NeckReleaseBezel", [(x, bu + y) for x, y in ring], lambda u, v, w: V(u, v, w),
                 fr - 0.0020, fr + 0.0010, "M_Charcoal", GW, bev=0.0006, bev_seg=2)
    add(bz)
    bt = rrect(0.0160, 0.0270, 0.0078)
    btn = extrude("NeckReleaseBtn", [(x, bu + y) for x, y in bt], lambda u, v, w: V(u, v, w),
                  fr - 0.0010, fr + 0.0024, "M_Gunmetal", GW, bev=0.0009, bev_seg=3)
    add(btn)
    add(lathe("NeckReleaseDot", [(0.0016, 0.0), (0.0016, 0.0003), (0.0, 0.0004)], (0, bu + 0.0080, fr + 0.0024),
              (0, 0, 1), (1, 0, 0), "M_Charcoal", GW, segs=16, cap0=True, cap1=False))
    return objs


def _front_of(st, up):
    for a, b in zip(st, st[1:]):
        if a[0] <= up <= b[0]:
            t = (up - a[0]) / (b[0] - a[0])
            d = a[2] + (b[2] - a[2]) * t
            c = a[4] + (b[4] - a[4]) * t
            return c + d / 2
    return st[-1][4] + st[-1][2] / 2


# ================================================================== rollers
def build_roller_front():
    """black soft fabric roller, turquoise helical stripes come from M_RollerFront (U around, V along the axis)
    [spare 383CH1000EUT, CR, V5]"""
    hi = D["lathe"] > 100
    ns = 72 if hi else 40
    nx = 90 if hi else 44
    up, f = RF_R, F(RF_D)
    # rings: dense over the rounded fabric ends, sparse along the body (stripes come from the texture)
    xs = []
    ne = 5
    for i in range(ne):
        xs.append(-RF_HALF + 0.0040 * (i / ne) ** 1.5)
    nmid = max(8, nx // 3)
    for i in range(nmid + 1):
        xs.append(-RF_HALF + 0.0040 + (2 * RF_HALF - 0.0080) * i / nmid)
    for i in range(ne - 1, -1, -1):
        xs.append(RF_HALF - 0.0040 * (i / ne) ** 1.5)
    nx = len(xs) - 1
    verts, faces, uvs = [], [], []
    for i, x in enumerate(xs):
        e = RF_HALF - abs(x)
        rr = RF_R - (0.0030 * (1 - min(1, e / 0.0035)) ** 2)
        for j in range(ns + 1):  # duplicated seam column for clean UV wrap
            th = TAU * j / ns
            verts.append(V(x, up + rr * math.sin(th), f + rr * math.cos(th)))
            uvs.append((j / ns, (x + RF_HALF) / (2 * RF_HALF)))
    W = ns + 1
    for i in range(nx):
        for j in range(ns):
            a = i * W + j
            faces.append((a, a + 1, a + W + 1, a + W))
    for i, vv in ((0, 0.0), (nx, 1.0)):
        c = len(verts)
        verts.append(V(xs[i], up, f))
        uvs.append((0.5, vv))
        for j in range(ns):
            a = i * W + j
            faces.append((c, a + 1, a) if i == 0 else (c, a, a + 1))
    ob = mk("RollerFront", verts, faces, "M_RollerFront", G, uvs=uvs)
    parts = [ob]
    for s in (1, -1):
        parts.append(lathe(f"RollerFrontCap_{s}", [(0.0110, s * (RF_HALF - 0.0015)), (0.0124, s * (RF_HALF + 0.0005)),
                                                   (0.0124, s * (RF_HALF + 0.0030)), (0.0080, s * (RF_HALF + 0.0040)),
                                                   (0.0, s * (RF_HALF + 0.0040))], (0, up, f), (1, 0, 0), (0, 0, 1),
                           "M_Charcoal", G, segs=32, cap0=True, cap1=True))
    j = lib.join_objects(parts, "RollerFront")
    lib.set_origin(j, V(0, up, f))
    return j


def build_roller_rear():
    """turquoise brushroll core + yellow chevron fibre strip (apex at the centre, leading forward) [S18, U 1663, V5]"""
    hi = D["lathe"] > 100
    up, f = RR_UP, F(RR_D)
    core = lathe("RollerRear", [(0.0130, -RR_HALF), (RR_CORE - 0.0030, -RR_HALF + 0.0004), (RR_CORE - 0.0006, -RR_HALF + 0.0030),
                                (RR_CORE, -RR_HALF + 0.0070), (RR_CORE, RR_HALF - 0.0070), (RR_CORE - 0.0006, RR_HALF - 0.0030),
                                (RR_CORE - 0.0030, RR_HALF - 0.0004), (0.0130, RR_HALF)],
                 (0, up, f), (1, 0, 0), (0, 0, 1), "M_Turquoise", G, segs=48 if hi else 28, cap0=True, cap1=True)
    parts = [core]
    rnd = random.Random(7)
    nxs = 70 if hi else 34
    k = 1.55 / RR_HALF  # chevron twist: ~89 deg from the apex to each end
    th0 = math.radians(95)  # apex angle position (front-top in the rest pose)
    hw_ang = 0.0065 / RR_CORE
    for side in (1, -1):
        rings = []
        for i in range(nxs + 1):
            x = side * (RR_HALF - 0.004) * i / nxs
            th = th0 - k * abs(x)
            r_in = RR_CORE - 0.0006
            r_out = RR_TIP + rnd.uniform(-0.0004, 0.0003)
            ring = []
            for rr, dth in ((r_in, -hw_ang), (r_in, hw_ang), (r_out, hw_ang * 0.8), (r_out, -hw_ang * 0.8)):
                a = th + dth
                ring.append(V(x, up + rr * math.sin(a), f + rr * math.cos(a)))
            rings.append(ring)
        verts, faces = ring_mesh(rings, True, True)
        parts.append(mk(f"RollerRearFibre_{side}", verts, faces, "M_RollerFibre", G, smooth=False))
    for s in (1, -1):
        parts.append(lathe(f"RollerRearCap_{s}", [(0.0135, s * (RR_HALF - 0.0010)), (0.0135, s * (RR_HALF + 0.0030)),
                                                  (0.0, s * (RR_HALF + 0.0030))], (0, up, f), (1, 0, 0), (0, 0, 1),
                           "M_Charcoal", G, segs=24, cap0=True, cap1=True))
    j = lib.join_objects(parts, "RollerRear")
    lib.set_origin(j, V(0, up, f))
    return j


# ================================================================== entry
def build(ctx):
    global _NOSE
    P = ctx["P"]
    _NOSE = P.WAND_FWD + NOSE_TO_AXIS
    body, leds = build_body(P)
    neck = build_neck(P)
    rf = build_roller_front()
    rr = build_roller_rear()
    ic = (INT_D0 + INT_D1) / 2
    return {
        "groups": {"FloorHead": body, "LowerWand": neck},
        "special": {"RollerFront": rf, "RollerRear": rr, "HeadLights": leds},
        "anchors": {
            "NeckPivot": (0.0, PIV_UP, P.WAND_FWD),
            "WandSocket": (0.0, P.WAND_SOCKET_UP, P.WAND_FWD),
            "IntakeFront": (0.0, 0.0, F(INT_D0)),
            "IntakeRear": (0.0, 0.0, F(INT_D1)),
            "IntakeCentre": (0.0, 0.0, F(ic)),
            "LightFrontL": (-0.1110, 0.0460, F(0.0030)),
            "LightFrontR": (0.1110, 0.0460, F(0.0030)),
            "LightRearL": (-0.0840, 0.0042, F(0.1330)),
            "LightRearR": (0.0840, 0.0042, F(0.1330)),
        },
        "contacts": {
            "Contact_WheelL": (-WHEEL_X, 0.0, F(WHEEL_D)),
            "Contact_WheelR": (WHEEL_X, 0.0, F(WHEEL_D)),
            "Contact_RollerFront": (0.0, 0.0, F(RF_D)),
            "Contact_CapL": (-0.1220, 0.0, F(0.0300)),
            "Contact_CapR": (0.1220, 0.0, F(0.0300)),
        },
        "nozzle": {"intakeWidth": 2 * 0.1045, "intakeZMin": F(INT_D1), "intakeZMax": F(INT_D0)},
        "notes": ("DuoClean Detect head positioned from the wand axis: nose fwd = WAND_FWD + %.3f = %.4f, intake centre "
                  "fwd %.4f. RollerFront = black bristle brushroll (M_RollerFront, U around / V along x), R %.4f, axis "
                  "(up %.4f, fwd %.4f). RollerRear = large mint soft roller + golden chevron fibre strip, R %.4f (strip "
                  "%.4f), axis (up %.4f, fwd %.4f). NeckPivot = lateral barrel axis (up %.3f) on the wand axis; "
                  "LowerWand = barrel, duct, hose, yoke spine, castellated tongue, connector + release button, purple "
                  "disc. HeadLights joins M_LED (white front headlights + under-corner bars) and M_LEDAccent (violet strip "
                  "+ rear-corner bars). Decals: duoclean_detect, shark_neck, edge_detect (both caps), foot_icon (+x deck), "
                  "rating_label (neck underside)." % (NOSE_TO_AXIS, _NOSE, F(ic), RF_R, RF_R, F(RF_D), RR_CORE, RR_TIP,
                                                       RR_UP, F(RR_D), PIV_UP)),
    }
