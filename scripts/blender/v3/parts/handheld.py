"""handheld part (v3, IP3251 TR 'mor-siyah' colourway). See ../PARTS_CONTRACT.md.

Local frame (all private dimensions below in millimetres):
  d  = distance DOWN from the top of the purple cap (cap top = params.STICK_H)
  F  = fore-aft offset from the handheld (cap/motor) axis, + = product front
  x  = lateral, + = product +x;  theta = angle around the axis from +F toward +x
Handheld axis fwd = WAND_FWD - AX_OFF: the cap front face is flush with the upper-wand front face (V2 native px 1627-1634
vs 1633), wand fore-aft 46 -> axis offset 24 mm (PR4 quoted ~35 inferred; measured 23-25).

Measurement ledger (source V2 = IP1251UKT folded side photo, k = 0.2747 mm/px, same hardware; gridded crop in
assets/reference-comparison/v3/handheld/ref_v2_grid.png; cl-na-04 / user 1663 / 1668 for colour + layout):
  cap 0..54 (V2 0..53.8, PR4 53) R 45.5 (V7 88 wide, V2 97 deep incl. grip-root notch) ; 20 tapered V flutes (V2 pitch
  15 mm at the silhouette centre -> 18.7 deg; inset rim notches) ; glass disc r 41.5, LED ring r 34.5..36.5 (1668:
  ring/cap 245/304 px) ; power pill 18.6 x 11 at F -31 (inset: 0.75 R toward the grip)
  champagne plate d 56..67, theta +-38 top / +-30 bottom (cl-eut-01, 1663, cl-na-04)
  vent grilles 2 x (7 columns x 9/8 staggered vertical slots 1.5 x 4.7, pitch 5.9) d 58..110, theta 31..66 (cl-na-04,
  1663 counts; V2 side extent F 47..26)
  silver frame top d 117 (V2 y1160) .. bottom 302 ; window theta +-54 (V7 75 mm wide) d 141..271 ; Shark band 117..141
  purple bin ring d 141..168 (V2 140..167, PR4 30) ; clear bin to floor d 320 ; rear clear tail to F -72 + latch -92
  rear deck d 126..168 to F -100 (V2 lip f -100) ; handheld bottom d 346 (= HANDHELD_BOTTOM_UP)
  handle loop (V2): grip bar centre F -52/d 22 -> F -168/d 4, 30 x 29 ; window F -62..-163, d 24/38 .. 61/91 ;
  rear upright outer face F -211, top d -37 (handle top is ~37 mm ABOVE the cap top, V2 rows 2150..2320) ;
  battery lower bar top edge (-62,91)->(-163,61), bottom (-58,137)->(-204,97), 46 wide ; panel stadium ;
  round release button O21 at (-178, 28) + LED dot O2.6 at (-178, 47) on +x side (V2, cl-na-04) ; trigger (purple) under
  the grip front F -58..-79, d 40..62.
"""
import math

import bmesh
import bpy
from mathutils import Vector

import lib
from lib import mk, rrect, fillet, ring_mesh

G = "MotorAssembly"
TAU = math.tau
R = 44.6           # cap radius (front views: V7 88.1, cl-eut-01 89.4 wide)
RB = 44.4          # motor body radius
SR = R / 45.55     # cap profile authored at r 45.55 / h 54 (V2) -> rescaled to the front-view measurements
SD = 49.0 / 54.0
AX_OFF = 0.0215    # handheld axis behind the wand axis: cap front flush with upper-wand front (V2) -> R - 23
CAP_H = 49.0       # V7 + cl-eut-01 purple rows 123..198 (k 0.634 / 0.643)
HW = 27.0         # handle-loop half width (battery + rear upright): 1668 matched view + JCGX t0072.5 underside
KV2 = 0.91         # V2 handle/bin geometry rescale: V2 k (0.2747) reads the handheld ~9 % large vs the front views
TOP = 1.158
AXF = -0.105
Q = {}


# ------------------------------------------------------------------ coordinates
def H(x, d, F):
    """local mm -> Blender vector"""
    return lib.V(x / 1000.0, TOP - d / 1000.0, AXF + F / 1000.0)


def HP(x, d, F):
    """local mm -> product coords tuple (m)"""
    return (x / 1000.0, TOP - d / 1000.0, AXF + F / 1000.0)


def C(r, th, d):
    """cylindrical (r mm, theta rad from +F toward +x, d mm) -> Blender vector"""
    return H(r * math.sin(th), d, r * math.cos(th))


# ------------------------------------------------------------------ mesh helpers
def revolve(name, prof, thetas, mat, rmod=None, closed=True, cap0=False, cap1=False, smooth=True):
    """revolve a (r, d) profile around the handheld axis at the given angles; closed=True joins last->first profile pt"""
    rings = []
    for r, d in prof:
        ring = []
        for th in thetas:
            rr = rmod(th, d, r) if rmod else r
            ring.append(C(rr, th, d))
        rings.append(ring)
    verts, faces = ring_mesh(rings, cap0, cap1, closed_loop=closed)
    return mk(name, verts, faces, mat, G, smooth=smooth)


def thetas_uniform(n):
    return [TAU * i / n for i in range(n)]


def grid_solid(name, nu, nv, fo, fi, mat, smooth=True):
    """closed solid sheet: fo(u,v)/fi(u,v) -> Blender vectors for outer/inner surfaces, u,v in [0,1]"""
    verts = []
    for f in (fo, fi):
        for j in range(nv + 1):
            for i in range(nu + 1):
                verts.append(f(i / nu, j / nv))
    W = nu + 1
    off = W * (nv + 1)
    idx = lambda i, j, s=0: s + j * W + i  # noqa: E731
    faces = []
    for j in range(nv):
        for i in range(nu):
            faces.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)))
            faces.append((idx(i, j, off), idx(i, j + 1, off), idx(i + 1, j + 1, off), idx(i + 1, j, off)))
    for i in range(nu):
        faces.append((idx(i, 0), idx(i, 0, off), idx(i + 1, 0, off), idx(i + 1, 0)))
        faces.append((idx(i, nv), idx(i + 1, nv), idx(i + 1, nv, off), idx(i, nv, off)))
    for j in range(nv):
        faces.append((idx(0, j), idx(0, j + 1), idx(0, j + 1, off), idx(0, j, off)))
        faces.append((idx(nu, j), idx(nu, j, off), idx(nu, j + 1, off), idx(nu, j + 1)))
    return mk(name, verts, faces, mat, G, smooth=smooth)


def cyl_patch(name, r_out, r_in, th_fn, d_fn, nu, nv, mat, smooth=True):
    """patch of a cylinder shell; th_fn(u, v)->theta, d_fn(u, v)->d"""
    fo = lambda u, v: C(r_out, th_fn(u, v), d_fn(u, v))  # noqa: E731
    fi = lambda u, v: C(r_in, th_fn(u, v), d_fn(u, v))  # noqa: E731
    return grid_solid(name, nu, nv, fo, fi, mat, smooth)


def prism_x(name, pts_Fd, x0, x1, mat, bev=None, seg=None, smooth=True):
    """side-profile polygon [(F, d)] extruded laterally x0..x1 (mm)"""
    return lib.extrude(name, pts_Fd, lambda F, d, x: H(x, d, F), x0, x1, mat, G, bev=(bev / 1000.0 if bev else None),
                       bev_seg=seg, smooth=smooth)


def prism_d(name, pts_xF, d0, d1, mat, bev=None, seg=None, smooth=True):
    """plan polygon [(x, F)] extruded vertically d0..d1"""
    return lib.extrude(name, pts_xF, lambda x, F, d: H(x, d, F), d0, d1, mat, G, bev=(bev / 1000.0 if bev else None),
                       bev_seg=seg, smooth=smooth)


def prism_r(name, pts_ud, th, r0, r1, mat, d0=0.0, bev=None, seg=None):
    """polygon in the local tangent plane at angle th: (u tangential mm (+ toward +theta), dd) extruded radially r0..r1"""
    def mp(u, dd, r):
        p = Vector((r * math.sin(th) + u * math.cos(th), r * math.cos(th) - u * math.sin(th)))
        return H(p.x, d0 + dd, p.y)
    return lib.extrude(name, pts_ud, mp, r0, r1, mat, G, bev=(bev / 1000.0 if bev else None), bev_seg=seg)


def stadium(L, W, n=6, cx=0.0, cy=0.0):
    """stadium along u (length L, width W) centred at (cx, cy)"""
    r = W / 2
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((cx + L / 2 - r + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((cx - L / 2 + r + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def circle(r, n, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(TAU * i / n), cy + r * math.sin(TAU * i / n)) for i in range(n)]


def boolean(ob, cutters, op="DIFFERENCE"):
    for c in cutters:
        md = ob.modifiers.new("Bool", "BOOLEAN")
        md.operation = op
        md.solver = "EXACT"
        md.object = c
        c.hide_render = True
        c.hide_viewport = True
    lib.apply_modifiers(ob)
    for c in cutters:
        me = c.data
        bpy.data.objects.remove(c)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    return ob


def join(objs, name):
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    return lib.join_objects(objs, name)


def disc_xF(name, r, d, mat, n=48, cx=0.0, cF=0.0, uvf=None):
    """flat disc facing up at depth d (single n-gon fan)"""
    verts = [H(cx, d, cF)] + [H(cx + r * math.sin(TAU * i / n), d, cF + r * math.cos(TAU * i / n)) for i in range(n)]
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    uvs = None
    if uvf:
        uvs = [uvf(cx, cF)] + [uvf(cx + r * math.sin(TAU * i / n), cF + r * math.cos(TAU * i / n)) for i in range(n)]
    ob = mk(name, verts, faces, mat, G, smooth=False, uvs=uvs, recalc=False)
    _face(ob, Vector((0, 0, 1)))
    return ob


def _face(ob, want):
    """flip a single-sided mesh so its normals point along `want` (Blender space)"""
    me = ob.data
    me.update()
    if not me.polygons:
        return
    n = sum((p.normal for p in me.polygons), Vector())
    if n.dot(want) < 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()


# ================================================================== cap + screen
GLASS_R = 38.5
CAP_N = 18   # user 1663: groove pitch ~67 px at 4.16 px/mm near the front -> 16 mm -> 18 around


def groove_rmod(n=20, w_top=1.9, depth=1.55, d_end=36.0, phase=0.5, facet=0.0, d0=0.0):
    """tapered sawtooth flutes: steep dark wall on one side, wide lit bevel on the other (user 1663);
    facet>0 flattens the land between grooves toward an n-gon"""
    period = TAU / n

    def f(th, d, r):
        if r < 42.3:
            return r
        k = (th / period - phase)
        dk = (k - round(k)) * period  # signed angular distance to the nearest groove centre
        if facet > 0.0 and d > 0.8:
            phi = period / 2 - abs(dk)  # angle from the facet centre
            wgt = min(1.0, (d - 0.8) / 3.5)
            r = r + facet * wgt * (r * math.cos(period / 2) / math.cos(phi) - r)
        if d >= d_end or d < d0:
            return r
        t = 1.0 - (d - d0) / (d_end - d0)
        hw = (w_top / R) * t
        if hw <= 1e-6:
            return r
        if dk < 0:
            a = max(0.0, 1.0 - abs(dk) / (hw * 0.45))
        else:
            a = max(0.0, 1.0 - dk / (hw * 1.8))
        return r - depth * (t ** 0.7) * a

    return f


def groove_thetas(n=20, phase=0.5, offs_deg=None):
    offs_deg = offs_deg or Q["groove_offs"]
    period = 360.0 / n
    out = []
    for k in range(n):
        c = (k + phase) * period
        for o in offs_deg:
            out.append(math.radians(c + o * period / 18.0))
    return out


def build_cap(objs, display, decals):
    import materials
    # purple ribbed end cap (HEPA cover). closed ring profile (r, d), outer side first
    prof = [(41.0, 1.6), (41.6, 0.55), (42.4, 0.08), (43.4, 0.0), (44.4, 0.3), (45.1, 1.0), (45.45, 2.2), (45.55, 4.0),
            (45.55, 9), (45.55, 16), (45.55, 24), (45.55, 32), (45.55, 40), (45.55, 49), (45.5, 52.2), (45.35, 53.4),
            (44.9, 54.0), (43.0, 54.0), (43.0, 6.0), (41.0, 4.0)]
    prof = [(r * SR, d * SD if d > 3.0 else d) for r, d in prof]
    # user 1663: big rounded shoulder from the flat top rim into broad, slightly flat vertical facets
    prof = [(38.1, 1.6), (38.6, 0.6), (39.3, 0.15), (40.3, 0.0), (41.4, 0.12), (42.4, 0.5), (43.3, 1.25), (44.0, 2.3),
            (44.45, 3.6), (44.65, 5.2), (44.7, 7.0), (44.7, 12), (44.7, 18), (44.7, 24), (44.7, 32), (44.7, 40), (44.7, 44.5),
            (44.65, 47.4), (44.5, 48.5), (44.1, 49.0), (42.2, 49.0), (42.2, 6.0), (37.6, 4.0)]
    cap = revolve("HH_Cap", prof, groove_thetas(n=CAP_N), "M_Purple", rmod=groove_rmod(n=CAP_N, w_top=2.6, depth=1.7, d_end=38.0, d0=4.5, facet=0.85))
    objs.append(cap)
    # thin glossy lip ring at the cap's lower edge (cl-na-04 bright purple line) + 0.5 mm seam above the body
    lip = [(r * SR, d - 54.0 + CAP_H) for r, d in
           [(45.2, 53.6), (45.75, 53.9), (45.8, 56.2), (45.4, 56.6), (44.0, 56.6), (44.0, 53.6)]]
    objs.append(revolve("HH_CapLip", lip, thetas_uniform(Q["lathe"]), "M_Purple"))
    # black glass
    # user 1668 (matched camera): black glass to ~0.86 R, purple top rim + rounded shoulder outside it
    gl = [(GLASS_R - 0.8, 0.9), (GLASS_R - 0.15, 1.15), (GLASS_R, 1.8), (GLASS_R, 3.0)]
    objs.append(revolve("HH_ScreenGlass", gl, thetas_uniform(Q["lathe"]), "M_Screen", closed=False, cap0=True, cap1=True))
    # LED ring (emissive, runtime driven)
    rng = [(32.7, 0.78), (35.7, 0.78), (35.7, 0.95), (32.7, 0.95)]   # 1668: ring mid-line 0.767 x cap O
    led = revolve("HH_LEDRing", rng, thetas_uniform(Q["lathe"]), "M_LEDRing")
    objs.append(led)
    display.append(led)
    # icons decal: disc mapped onto the circumscribed square (viewer behind the cap: glyph up = +F, right = -x)
    rs = GLASS_R - 0.1

    def uv_sq(x, F):
        return materials.decal_uv("screen_icons_tr", (-x + rs) / (2 * rs), (F + rs) / (2 * rs), rect="slot")

    dec = disc_xF("HH_DecalScreen", rs, 0.66, "M_Decal", n=64, uvf=uv_sq)
    objs.append(dec)
    decals.append(dec)
    # power pill (raised, purple bezel + black glossy top)
    pc = (0.0, -0.66 * rs)   # atlas power icon centre (t 0.17); size from the official inset (0.23 x 0.14 of the disc)
    pill = stadium(18.0, 10.6, 8, pc[0], pc[1])
    bez = prism_d("HH_PowerPill", pill, 1.5, -1.0, "M_Purple", bev=0.7, seg=3)
    objs.append(bez)
    top = stadium(15.6, 8.2, 8, pc[0], pc[1])
    objs.append(prism_d("HH_PowerPillTop", top, -0.8, -1.35, "M_Screen", bev=0.35, seg=2))
    # icon on the pill top (same atlas sub-rect)
    v = [H(x, -1.62, F) for x, F in top]
    c = H(pc[0], -1.62, pc[1])
    verts = [c] + v
    n = len(v)
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    uvs = [uv_sq(pc[0], pc[1])] + [uv_sq(x, F) for x, F in top]
    pd = mk("HH_DecalPower", verts, faces, "M_Decal", G, smooth=False, uvs=uvs, recalc=False)
    _face(pd, Vector((0, 0, 1)))
    objs.append(pd)
    decals.append(pd)
    return HP(pc[0], -1.35, pc[1])


# ================================================================== motor body, plate, vents
PLATE_D = (52.0, 63.0)
PLATE_TH_TOP, PLATE_TH_BOT = math.radians(38.0), math.radians(30.0)


def plate_th(d):
    t = (d - PLATE_D[0]) / (PLATE_D[1] - PLATE_D[0])
    return PLATE_TH_TOP + (PLATE_TH_BOT - PLATE_TH_TOP) * t


def frame_top(th):
    a = abs(math.degrees(th))
    return 105.0 + 14.0 * (a / 78.0) ** 2.2


def frame_bot(th):
    a = abs(math.degrees(th))
    return 327.0 - 9.0 * max(0.0, (a - 48.0) / 30.0) ** 2


def build_body(objs):
    # main motor shell (closed ring with 2 mm wall), vents cut as real holes
    prof = [(43.5, 51.6), (44.1, 51.7), (RB, 52.2), (RB, 64), (RB, 80), (RB, 96), (RB, 112), (RB, 130.0),
            (RB - 2.0, 130.0), (RB - 2.0, 51.6)]
    body = revolve("HH_Body", prof, thetas_uniform(Q["body_n"]), "M_Gunmetal")
    cutters = []
    # cl-na-04 zoom: 10 staggered columns (3.4 mm pitch), 6 rows of 1.6 x 6.2 stadium slots, 8.6 mm row pitch
    slot_w, slot_l, pitch = 1.6, 6.2, 8.6
    d0 = 52.0
    cols = 10
    th0, th1 = math.radians(25.0), math.radians(68.0)
    for side in (-1, 1):
        for ci in range(cols):
            th = th0 + (th1 - th0) * ci / (cols - 1)
            stag = (ci % 2) * pitch / 2
            nrows = 6
            for ri in range(nrows):
                dc = d0 + slot_l / 2 + stag + ri * pitch
                if dc + slot_l / 2 > frame_top(th) - 3.0:
                    continue
                # keep clear of the champagne plate's slanted end
                if dc - slot_l / 2 < PLATE_D[1] + 0.8 and th < plate_th(min(dc, PLATE_D[1])) + math.radians(3.0):
                    continue
                pts = stadium(slot_l, slot_w, Q["slot_n"])
                pts = [(v, u) for u, v in pts]  # long axis vertical
                cutters.append(prism_r(f"HH_VentCut{side}_{ci}_{ri}", pts, side * th, 40.6, 47.0, "M_Gunmetal", d0=dc))
    cut = join(cutters, "HH_VentCutters")
    boolean(body, [cut])
    lib.bevel(body, 0.00035, 1, angle=50)
    objs.append(body)
    # dark motor/filter housing seen through the slots
    inner = [(41.7, 51.0), (41.7, 104.0), (36.0, 104.0), (36.0, 51.0)]
    objs.append(revolve("HH_VentBacking", inner, thetas_uniform(Q["lathe"] // 2), "M_Charcoal"))
    # champagne POWERDETECT plate (0.7 mm proud)
    nu, nv = Q["plate_nu"], 4
    pl = cyl_patch("HH_PlateChampagne", RB + 0.7, RB - 0.3,
                   lambda u, v: -plate_th(PLATE_D[0] + v * (PLATE_D[1] - PLATE_D[0])) * (1 - 2 * u),
                   lambda u, v: PLATE_D[0] + v * (PLATE_D[1] - PLATE_D[0]), nu, nv, "M_Champagne")
    lib.bevel(pl, 0.00035, 2, angle=30)
    objs.append(pl)


def curved_decal(name, slot, r, dc, width, height, objs, decals, nu=16):
    """horizontal decal strip on a cylinder of radius r (mm), centred at theta 0 (front), d centre dc"""
    import materials
    half = (width / 2) / r
    verts, uvs, faces = [], [], []
    for j in range(2):
        for i in range(nu + 1):
            th = -half + 2 * half * i / nu
            d = dc - height / 2 + height * j
            verts.append(C(r, th, d))
            uvs.append(materials.decal_uv(slot, i / nu, 1 - j))
    for i in range(nu):
        faces.append((i, i + 1, nu + 1 + i + 1, nu + 1 + i))
    ob = mk(name, verts, faces, "M_Decal", G, smooth=True, uvs=uvs, recalc=False)
    _face(ob, Vector((0, -1, 0)))
    objs.append(ob)
    decals.append(ob)
    return ob


# ================================================================== silver frame, bin ring, rails, deck
WIN = (128.0, 304.0)
WIN_TH = math.radians(49.0)   # purple-ring row width: cl-eut-01 +-50, V7 +-44; user 1663 ~+-38, crop-tr01 ~+-34
FRAME_TH = math.radians(78.0)


def build_frame(objs, decals):
    nu, nv = Q["frame_nu"], Q["frame_nv"]
    fr = cyl_patch("HH_FrameSilver", 45.8, 43.8,
                   lambda u, v: -FRAME_TH + 2 * FRAME_TH * u,
                   lambda u, v: frame_top(-FRAME_TH + 2 * FRAME_TH * u) + v * (frame_bot(-FRAME_TH + 2 * FRAME_TH * u)
                                                                               - frame_top(-FRAME_TH + 2 * FRAME_TH * u)),
                   nu, nv, "M_SilverBrush")
    wx = 45.8 * math.sin(WIN_TH)
    win = rrect(2 * wx, WIN[1] - WIN[0], 14.0, 12)
    wc = (WIN[0] + WIN[1]) / 2
    cut = lib.extrude("HH_WinCut", win, lambda x, dd, F: H(x, wc + dd, F), 5.0, 60.0, "M_SilverBrush", G)
    boolean(fr, [cut])
    lib.bevel(fr, 0.0007, 3, angle=30)
    objs.append(fr)
    curved_decal("HH_DecalShark", "shark_frame", 46.05, 116.8, 38.0, 38.0 / 3.837, objs, decals)
    # gunmetal side rails behind the frame (theta 76..94 deg)
    for s in (-1, 1):
        a0, a1 = math.radians(75.0), math.radians(95.0)
        rl = cyl_patch(f"HH_Rail{s}", 45.0, 43.0, lambda u, v, s=s: s * (a0 + (a1 - a0) * u),
                       lambda u, v: 112.0 + v * (326.0 - 112.0), 8, 10, "M_Gunmetal")
        lib.bevel(rl, 0.0006, 2, angle=30)
        objs.append(rl)
        # dust-cup release tab with 3 grooves (V2 '=' at F +5, d 147..163)
        th = s * math.radians(96.0)
        tab = rrect(9.0, 15.0, 1.6, 4)
        objs.append(prism_r(f"HH_CupRelease{s}", tab, th, 43.2, 45.7, "M_Gunmetal", d0=145.0, bev=0.5, seg=2))
        for k in range(3):
            g = rrect(5.6, 0.7, 0.3, 2)
            objs.append(prism_r(f"HH_CupReleaseGroove{s}{k}", [(u, v + (k - 1) * 3.0) for u, v in g], th, 45.5, 45.85,
                                "M_Charcoal", d0=145.0))


def build_bin_ring(objs):
    # purple ribbed ring at the top of the bin (notched top edge like the cap, cl-na-04 / 1663)
    prof = [(43.0, 129.5), (43.15, 130.2), (43.15, 155.8), (42.9, 157.6), (40.5, 157.6), (40.5, 129.5)]
    rm = groove_rmod(n=20, w_top=1.5, depth=0.9, d_end=9.0, phase=0.0)

    def rmod(th, d, r):
        return rm(th, d - 129.5, r) if r > 42.5 else r

    objs.append(revolve("HH_BinRing", prof, groove_thetas(phase=0.0), "M_Purple", rmod=rmod))


def deck_plan():
    pts = []
    for k in range(9):
        a = math.radians(68.0 + 22.0 * k / 8)
        pts.append((RB * math.sin(a), RB * math.cos(a)))
    pts += [(41.5, -45.0), (36.0, -74.0), (-36.0, -74.0), (-41.5, -45.0)]
    for k in range(9):
        a = math.radians(-90.0 + 22.0 * k / 8)
        pts.append((RB * math.sin(a), RB * math.cos(a)))
    return pts


def build_deck(objs):
    pl = deck_plan()
    rads = [0] * 9 + [16, 10, 10, 16] + [0] * 9
    pts = fillet(pl, rads, 5)
    dk = prism_d("HH_Deck", pts, 157.5, 119.0, "M_Gunmetal", bev=3.5, seg=4)
    objs.append(dk)
    # seam groove between deck and the frame region (dark line)
    objs.append(prism_d("HH_DeckSeam", fillet(deck_plan(), rads, 5), 158.1, 157.4, "M_Charcoal"))


# ================================================================== bin + cyclone
def bin_plan(inset=0.0, n_front=None):
    n_front = n_front or Q["bin_front"]
    r = 42.7 - inset
    pts = []
    for k in range(n_front + 1):
        a = math.radians(-90.0 + 180.0 * k / n_front)
        pts.append((r * math.sin(a), r * math.cos(a)))
    # straight sides back to the rear wall at F -72
    rear = -65.5 + inset
    rc = 11.0 - inset * 0.5
    xr = 38.5 - inset
    side = [(r, -8.0), (r - 0.8, -28.0), (xr + 0.6, -47.0)]
    corner = []
    cx, cy = xr - rc, rear + rc
    for k in range(7):
        a = math.radians(0 - 90.0 * k / 6)
        corner.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    pts += side + corner
    pts += [(-x, y) for x, y in reversed(corner)] + [(-x, y) for x, y in reversed(side)]
    return pts


def resample(pts, M):
    P = [Vector(p) for p in pts]
    segs = [(P[i] - P[i - 1]).length for i in range(1, len(P))] + [(P[0] - P[-1]).length]
    L = sum(segs)
    out = []
    i, acc = 0, 0.0
    for k in range(M):
        s = L * k / M
        while acc + segs[i] < s:
            acc += segs[i]
            i += 1
        t = (s - acc) / segs[i]
        a, b = P[i], P[(i + 1) % len(P)]
        out.append(tuple(a.lerp(b, t)))
    return out


BIN_TOP, BIN_FLOOR = 157.0, 308.0


def build_bin(objs):
    M = Q["bin_m"]
    outer = resample(bin_plan(0.0), M)
    inner = resample(bin_plan(1.6), M)
    ds = [BIN_TOP, 162, 180, 200, 220, 240, 260, 280, 298, BIN_FLOOR - 2.0]
    ro = [[H(x, d, F) for x, F in outer] for d in ds]
    ri = [[H(x, d, F) for x, F in inner] for d in ds[:-1] + [BIN_FLOOR - 3.6]]
    # outer: top rim -> down -> floor (rounded bottom edge)
    bot_o = [H(x * 0.97, BIN_FLOOR, F * 0.97 - 1.0) for x, F in outer]
    ro.append(bot_o)
    bot_i = [H(x * 0.97, BIN_FLOOR - 1.6, F * 0.97 - 1.0) for x, F in inner]
    ri = ri[:-1] + [ri[-1], bot_i]
    n = M
    verts = [v for r in ro for v in r] + [v for r in ri for v in r]
    RO, RI = len(ro), len(ri)
    off = RO * n
    faces = []
    for i in range(RO - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j))
    for i in range(RI - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((off + i * n + j, off + (i + 1) * n + j, off + (i + 1) * n + j2, off + i * n + j2))
    # top rim annulus
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((j, off + j, off + j2, j2))
    # floors (fans)
    verts.append(sum(bot_o, Vector()) / n)
    co = len(verts) - 1
    verts.append(sum(bot_i, Vector()) / n)
    ci = len(verts) - 1
    a, b = (RO - 1) * n, off + (RI - 1) * n
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((co, a + j2, a + j))
        faces.append((ci, b + j, b + j2))
    shell = mk("HH_DustbinShell", verts, faces, "M_ClearBin", G, smooth=True)
    objs.append(shell)
    # opaque bottom flap (bin-empty door) under the clear floor
    fl = resample(bin_plan(0.4), Q["bin_m"] // 2)
    objs.append(prism_d("HH_BinDoor", fl, BIN_FLOOR + 3.4, BIN_FLOOR - 0.2, "M_Gunmetal", bev=1.0, seg=2))
    # silver band at the bin bottom seen in the window (V7 / cl-na-04)
    ba = math.radians(80.0)
    bb = cyl_patch("HH_BinBandSilver", 40.9, 40.1, lambda u, v: -ba + 2 * ba * u, lambda u, v: 276.0 + 29.0 * v,
                   48, 2, "M_SilverBrush")
    objs.append(bb)
    # rear latches: top dust-cup latch (charcoal, cl-na-04 dark hook) + bottom bin-empty lever, joined by a rod
    lt = fillet([(-66.0, 157.0), (-86.5, 157.0), (-86.5, 164.5), (-82.0, 191.0), (-66.0, 191.0)], [0.5, 2, 2, 2, 0.5], 3)
    objs.append(prism_x("HH_LatchTop", lt, -11.0, 11.0, "M_Charcoal", bev=0.8, seg=2))
    for k in range(3):
        g = [(-82.2, 171.0 + 4.0 * k), (-83.6, 171.0 + 4.0 * k), (-83.4, 172.2 + 4.0 * k), (-82.0, 172.2 + 4.0 * k)]
        objs.append(prism_x(f"HH_LatchGrip{k}", g, -7.0, 7.0, "M_Gunmetal"))
    lb = fillet([(-66.0, 268.0), (-78.5, 268.0), (-82.0, 286.0), (-82.0, BIN_FLOOR + 2.0), (-66.0, BIN_FLOOR + 2.0)],
                [0.5, 3, 2, 1.5, 0.5], 3)
    objs.append(prism_x("HH_LatchBottom", lb, -9.0, 9.0, "M_Charcoal", bev=0.8, seg=2))
    rod = lib.lathe("HH_LatchRod", [(0.0, 0.0), (0.0011, 0.0), (0.0011, 0.077), (0.0, 0.077)], HP(0, 268.0, -67.6),
                    (0, 1, 0), (0, 0, 1), "M_Charcoal", G, segs=12)
    objs.append(rod)
    # moulded MAX fill line on both flanks of the clear tail (close-up pack: stepped bin with MAX line)
    for sg in (-1, 1):
        objs.append(prism_x(f"HH_BinMax{sg}", [(-20.0, 171.6), (-48.0, 171.6), (-48.0, 172.5), (-20.0, 172.5)],
                            *sorted((sg * 41.2, sg * 42.6)), "M_ClearBin"))
    return shell


def build_cyclone(objs):
    th = thetas_uniform(Q["lathe"])
    # silver cyclone shroud: chrome mesh band with fine ridges (perforated-mesh look) + brushed rims
    prof = [(29.5, BIN_TOP + 1.0)]
    for d in (BIN_TOP + 3.0, 172.0, 185.0):
        prof += [(32.5, d), (32.5, d + 12.0), (32.1, d + 12.4), (32.1, d + 12.8)]
    prof += [(32.5, 198.0), (30.5, 198.0), (30.5, BIN_TOP + 1.0)]
    objs.append(revolve("HH_CycloneMesh", prof, thetas_uniform(Q["lathe"]), "M_Chrome"))
    rim = [(33.3, BIN_TOP + 0.5), (33.3, BIN_TOP + 3.0), (31.5, BIN_TOP + 3.0), (31.5, BIN_TOP + 0.5)]
    objs.append(revolve("HH_CycloneRimTop", rim, th, "M_SilverBrush"))
    skirt = [(33.0, 196.5), (37.4, 201.5), (37.8, 203.0), (37.2, 204.2), (29.0, 203.0), (19.6, 204.0), (19.6, 196.5)]
    objs.append(revolve("HH_CycloneSkirt", skirt, th, "M_SilverBrush"))
    # lower cyclone body under the flange: wide frosted cylinder down to the bin-bottom band (cl-eut-01, crop-tr01)
    tube = [(33.6, 203.0), (33.6, 262.0), (33.0, 268.5), (31.0, 271.5), (24.0, 273.0), (3.0, 273.4)]
    objs.append(revolve("HH_CycloneTube", tube, th, "M_SilverBrush", closed=False, cap0=True, cap1=True))


def build_base(objs):
    """gunmetal bin base / socket below the frame, narrowing onto the wand interface"""
    wF = AX_OFF * 1000.0  # wand axis in local F
    # bottom footprint covers the wand agent's upper-wand housing top: fore-aft -46..+11 mm about the wand axis,
    # 46 mm wide (+1 mm skirt each side)
    fc = wF + (-46.0 + 11.0) / 2.0
    st = [(325.0, 88.6, 88.6, 44.0, 0.0), (329.0, 87.0, 87.0, 40.0, 0.5), (335.0, 76.0, 80.0, 30.0, fc * 0.4),
          (341.0, 60.0, 66.0, 18.0, fc * 0.8), (346.0, 48.0, 59.0, 10.0, fc)]
    stations = [(TOP - d / 1000.0, w / 1000.0, dd / 1000.0, r / 1000.0, AXF + cf / 1000.0) for d, w, dd, r, cf in st]
    stations = list(reversed(stations))  # bottom-up
    base = lib.loft_up("HH_Base", stations, "M_Gunmetal", G)
    lib.bevel(base, 0.0008, 2, angle=35)
    objs.append(base)
    # dark inlet throat ring at the very bottom (seen when the wand is detached)
    objs.append(prism_d("HH_InletThroat", fillet([(x, y + fc) for x, y in rrect(38.0, 49.0, 9.0, 6)], 0.0, 1),
                        346.3, 344.0, "M_Charcoal"))


# ================================================================== handle loop + battery
def build_handle(objs):
    k = KV2  # handle geometry authored in V2 mm (cap-top / axis relative), rescaled to the front-view scale

    def S(pts):
        return [(F * k, d * k) for F, d in pts]

    # front post / grip root (charcoal) holding the trigger
    post = fillet(S([(-36.0, 3.0), (-62.0, 8.0), (-63.5, 100.0), (-38.0, 108.0)]), [2, 6, 6, 2], 5)
    objs.append(prism_x("HH_GripRoot", post, -21.0, 21.0, "M_Charcoal", bev=7.0, seg=5))
    # grip bar: chunky, well-rounded matte-black soft-touch bar (user 1668: ~0.39 x cap O wide), rises toward the rear
    a = Vector(HP(0, 22.0 * k, -50.0 * k))
    b = Vector(HP(0, 4.0 * k, -170.0 * k))
    n = Q["grip_n"]
    path = [a.lerp(b, i / n) for i in range(n + 1)]

    def sec(t):
        bul = math.sin(math.pi * t)
        return ((37.0 + 1.8 * bul) / 1000.0, (32.0 + 1.5 * bul) / 1000.0, 14.0 / 1000.0)

    objs.append(lib.sweep("HH_Grip", path, sec, "M_Rubber", G))
    # wide charcoal neck where the grip leaves the body: nearly cap-wide under the cap, chamfering down onto the grip
    # (user 1668 matched view: dark shoulders under the cap rim; T9U8 t1000/t1005 grip-top close-ups)
    na = a + (a - b).normalized() * 0.012
    nb = a.lerp(b, 0.30)
    npath = [na.lerp(nb, i / 10) for i in range(11)]

    def nsec(t):
        e = (1.0 - t) ** 1.8
        return ((33.5 + 38.0 * e) / 1000.0, (29.5 + 12.0 * e) / 1000.0, (12.5 + 5.5 * e) / 1000.0)

    objs.append(lib.sweep("HH_GripNeck", npath, nsec, "M_Charcoal", G))
    # gunmetal trumpet flare where the grip runs into the rear upright (user 1668: grey flared base under the grip end)
    fa = a.lerp(b, 0.66)
    fb = b + (b - a).normalized() * 0.006
    fpath = [fa.lerp(fb, i / 8) for i in range(9)]

    def fsec(t):
        e = t ** 2.6   # concave trumpet (1668)
        return ((34.0 + (2 * HW - 34.0) * e) / 1000.0, (29.5 + 13.5 * e) / 1000.0, (12.5 + 6.0 * e) / 1000.0)

    objs.append(lib.sweep("HH_GripFlare", fpath, fsec, "M_Charcoal", G))
    # gunmetal upper section of the rear upright (above the battery)
    up = fillet(S([(-156.0, -37.0), (-183.0, -37.0), (-210.5, 0.0), (-210.5, 6.0), (-160.0, 6.0), (-156.0, -10.0)]),
                [12, 9, 8, 0.5, 0.5, 4], 6)
    objs.append(prism_x("HH_UprightTop", up, -HW, HW, "M_Charcoal", bev=7.0, seg=5))
    # battery: lower loop bar + rear lower upright (one L-shaped pack, charcoal)
    bat = [(-49.0, 96.0), (-62.0, 91.0), (-163.0, 61.0), (-163.5, 6.6), (-211.0, 6.6), (-212.0, 88.0), (-204.0, 97.5),
           (-100.0, 131.0), (-58.0, 138.0), (-46.0, 128.0)]
    batf = fillet(S(bat), [4, 5, 7, 0.8, 0.8, 4, 6, 4, 6, 6], 5)
    objs.append(prism_x("HH_Battery", batf, -HW - 1.0, HW + 1.0, "M_Charcoal", bev=6.0, seg=5))
    # seam between battery and the gunmetal frame (dark groove line)
    objs.append(prism_x("HH_BatterySeam", S([(-163.6, 5.6), (-210.9, 5.6), (-210.9, 6.7), (-163.6, 6.7)]), -HW - 0.6, HW + 0.6,
                        "M_Rubber"))
    # light-grey side panels with the battery's chamfered window, both sides (V2, cl-na-04)
    A = Vector((-60.0 * k, 118.5 * k))
    B = Vector((-157.0 * k, 79.5 * k))
    L = (B - A).length
    ang = math.atan2(B.y - A.y, B.x - A.x)
    pn = stadium(L, 17.0, 8, L / 2, 0.0)
    pts = [(A.x + u * math.cos(ang) - v * math.sin(ang), A.y + u * math.sin(ang) + v * math.cos(ang)) for u, v in pn]
    for s in (-1, 1):
        x0, x1 = (HW + 0.4, HW + 1.35) if s > 0 else (-HW - 1.35, -HW - 0.4)
        objs.append(prism_x(f"HH_BatPanel{s}", pts, x0, x1, "M_SilverBrush", bev=0.4, seg=2))
    # trigger (purple) under the grip front [V2 / cl-na-04]
    trg = fillet(S([(-58.0, 38.0), (-73.5, 41.0), (-79.0, 48.5), (-76.5, 55.5), (-68.0, 61.5), (-60.0, 62.5)]),
                 [1, 4, 3, 3, 3, 1], 5)
    objs.append(prism_x("HH_Trigger", trg, -6.5, 6.5, "M_Purple", bev=2.0, seg=3))
    # battery release button (round, +x side of the rear upright) + charge LED dot below it
    bx = HW
    btn = lib.lathe("HH_BatButton", [(0.0, 0.0), (0.0108, 0.0), (0.0108, 0.0006), (0.0102, 0.0011), (0.0090, 0.0011),
                                     (0.0088, 0.0004), (0.0070, 0.0012), (0.0040, 0.0019), (0.0, 0.0021)],
                    (bx / 1000.0, TOP - 0.028 * k, AXF - 0.178 * k), (1, 0, 0), (0, 1, 0), "M_Charcoal", G, segs=40)
    objs.append(btn)
    led = lib.lathe("HH_BatLED", [(0.0, 0.0), (0.0021, 0.0), (0.0021, 0.0004), (0.0013, 0.0007), (0.0, 0.0008)],
                    (bx / 1000.0, TOP - 0.047 * k, AXF - 0.178 * k), (1, 0, 0), (0, 1, 0), "M_Screen", G, segs=20)
    objs.append(led)
    # DC power jack on the underside of the rear corner (IP1000: jack under the handle)
    jack = lib.lathe("HH_PowerJack", [(0.0, 0.0011), (0.0026, 0.0011), (0.0034, 0.0), (0.0042, 0.0), (0.0042, -0.0003),
                                      (0.0, -0.0003)],
                     (0.0, TOP - 0.0985 * k, AXF - 0.186 * k), (0, -1, 0.3), (1, 0, 0), "M_Rubber", G, segs=24)
    objs.append(jack)
    # two screws on the rear face of the upright (V2 oval marks at d ~20 / ~45)
    for i, dd in enumerate((20.0, 46.0)):
        sc = lib.lathe(f"HH_Screw{i}", [(0.0, 0.0), (0.0022, 0.0), (0.0022, 0.0004), (0.0016, 0.0007), (0.0, 0.0008)],
                       (0.0, TOP - dd * k / 1000.0, AXF - 0.2114 * k), (0, 0, -1), (1, 0, 0), "M_Chrome", G, segs=16)
        objs.append(sc)
        rec = lib.lathe(f"HH_ScrewWell{i}", [(0.0, 0.0), (0.0030, 0.0), (0.0030, 0.0003), (0.0, 0.0003)],
                        (0.0, TOP - dd * k / 1000.0, AXF - 0.2111 * k), (0, 0, -1), (1, 0, 0), "M_Rubber", G, segs=20)
        objs.append(rec)
    # knurled pull strip along the battery's rear corner (V2 hatching)
    for i in range(14):
        dd = 14.0 + i * 5.6
        objs.append(prism_x(f"HH_Knurl{i}", S([(-211.9, dd), (-212.6, dd + 0.6), (-212.6, dd + 2.2), (-211.9, dd + 2.8)]),
                            -HW + 3.0, HW - 3.0, "M_Charcoal"))


# ================================================================== contents
def build_contents():
    pts = resample(bin_plan(2.2), 96)
    rings = []
    floor = BIN_FLOOR - 2.2
    top_h = 90.0
    for t in (0.0, 0.5, 0.92, 1.0):
        ring = []
        for x, F in pts:
            bump = 0.0
            if t >= 0.92:
                bump = (2.5 * math.sin(x * 0.23) * math.cos(F * 0.19) + 3.0 * (F / 72.0)) * (1.0 if t == 1.0 else 0.4)
            ring.append(H(x, floor - t * top_h - bump, F))
        rings.append(ring)
    verts, faces = ring_mesh(rings, True, True)
    ob = mk("DustbinContents", verts, faces, "M_Dust", G)
    lib.set_origin(ob, H(0.0, floor, -12.0))
    return ob


# ================================================================== build
def build(ctx):
    global TOP, AXF
    P = ctx["P"]
    TOP = P.STICK_H
    AXF = P.WAND_FWD - AX_OFF
    hi = ctx["tier"] == "high"
    Q.update({
        "lathe": 128 if hi else 48,
        "body_n": 240 if hi else 96,
        "frame_nu": 72 if hi else 32,
        "frame_nv": 22 if hi else 10,
        "bin_front": 40 if hi else 20,
        "bin_m": 120 if hi else 56,
        "grip_n": 14 if hi else 8,
        "slot_n": 4 if hi else 2,
        "plate_nu": 40 if hi else 20,
        "groove_offs": (-9, -5.5, -3.2, -2.0, -1.1, -0.45, 0, 0.45, 1.1, 2.0, 3.2, 5.5) if hi else (-9, -3.5, -1.2, 0, 1.2, 3.5),
    })
    objs, decals, display = [], [], []
    anchor = build_cap(objs, display, decals)
    build_body(objs)
    curved_decal("HH_DecalPowerdetect", "powerdetect_plate", RB + 0.95, 57.6, 45.0, 45.0 / 16.53, objs, decals)
    build_frame(objs, decals)
    build_bin_ring(objs)
    build_deck(objs)
    shell = build_bin(objs)
    build_cyclone(objs)
    build_base(objs)
    build_handle(objs)
    contents = build_contents()
    for o in objs + [contents]:
        o["grp"] = G
    import os
    import materials
    if not os.path.exists(os.path.join(materials.TEX, "decal_atlas.png")):
        for o in decals:  # atlas not published yet: an untextured M_Decal renders as white cards in previews
            o.hide_render = True
    notes = (
        "IP3251 handheld. Axis fwd = WAND_FWD - 0.024 (cap front flush with upper-wand front, V2). Cap top = STICK_H; the "
        "handle loop's rear upright rises ~34 mm ABOVE the cap top (V2 rows 2150-2320) -> handheld max up = STICK_H + 0.037. "
        "Screen on the cap end face, glyph-up = +fwd (read from behind the handle); PowerControlAnchor = top of the power pill. "
        "DustbinShell = clear bin (front D r 43.6 + rear tail to 72 mm behind the axis, floor at STICK_H-0.320). "
        "DustbinContents origin = bin floor; full height 100 mm at scale 1. Display = LED ring (M_LEDRing). "
        "Battery LED dot is M_Screen (non-emissive; real LED is yellow/green/white, not ring purple)."
    )
    disp = [o for o in display]
    return {
        "groups": {G: [o for o in objs if o not in disp] + [contents]},
        "special": {"DustbinShell": shell, "DustbinContents": contents, "Display": disp},
        "anchors": {"PowerControlAnchor": anchor, "MotorAssembly": (0.0, P.HANDHELD_BOTTOM_UP, P.WAND_FWD)},
        "notes": notes,
    }
