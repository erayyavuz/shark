"""dock part (v3, IP3251 / XDCKIP3000 Clean & Empty auto-empty base). Owned by the dock agent. See ../PARTS_CONTRACT.md.

Built in the product frame around the DOCKED vacuum: the stick is assumed lifted by RAISE (= plate top under the
floorhead rear wheels). Production-photo proportions (the EUIPO 015044754-0001 drawing is used for shape only; its
proportions are the earlier design: shorter tower, fluted plinth, longer post).

Architecture (production photos tr-part-2-0l-aed-eu-fisi-1, cl-eut-01, JCGX t0011.6/t0020.3/t0098.6,
ph7l t0344/t0352, user-video-1663, manual tr_og p04/p13/p14/p16):
  * thin dark BASE PLATE (13.5 mm) under the tower, with a front tongue that carries the floorhead rear wheels
    (head nose overhangs it onto the floor), 4 rubber feet;
  * dark smooth PLINTH (to 0.195) with the same plan as the tower; right side: removable filter door (outline
    groove, diagonal slots rising to the rear, round push button low at the rear); rear-left: power socket + cord;
  * white TOWER: plan = front face with a semicircular channel for the post, both front corners chamfered
    (19 x 40 mm), square-ish right-rear corner, big chamfer at the rear-left (odour-dial corner). Split into
      - fixed front-right STUB (triangular top, DUST BIN FULL pill light, POWERDETECT badge on its front face),
      - removable BIN body + LID (seam 24 mm under the top); top flat for the front 50 mm, then slopes 40 mm down to
        the rear; carry-handle trough across the top with the dark release button; odour dial in a well at the
        rear-left corner (black puck, printed face via decal, fold-flat loop handle);
  * dark round CHARGING POST: Ø67 sleeve from the plate up the tower channel (arched opening at the bottom front),
    joint just above the tower top, Ø64 upper post, flared bracket into the CRADLE: a block over the post with the
    U-cup (open front, tall front ears, saddle back wall) around the handheld bin base, wand channel through the
    floor, charging-contact block on the inner rear wall, notch for the handheld's rear latch, side wings with the
    Quiet-mode slide switch on the right wing, post-release latch on the rear top. Cup centred on the handheld bin axis
    (HH_BIN_F), which sits behind the wand axis.

Local ledger (metres, product coords x/up/fwd). [S]=JCGX t0020.3 side photo, scale from system depth 0.472 = 687 px
(1455 px/m); [F]=cl-eut-01 front ortho (1.555 px/mm wand plane); [I]=isolated dock render; [T]=ph7l t0352 top view;
[L]=lead interface; [M]=manual drawing.
"""
import math

import bmesh
import bpy
from mathutils import Vector

GRP = "Dock"

# ----------------------------------------------------------------------------------------------- ledger
RAISE = 0.0135          # plate top = docked lift of the stick [S: plate side 20 px; rear wheels stand on it]
PLATE_T = RAISE
PLATE_R = -0.430        # plate rear = head nose (+0.042) - 0.472 [L]
PLATE_F = -0.104        # plate front edge [S 474 px ahead of the rear]
PLATE_W = 0.228         # [EUIPO front ratio 116/104 x tower; user frame: narrower than the 263 mm head]
TW = 0.205              # tower width [F 320-323 px]
HW = TW / 2
TF = -0.206             # tower front face (white) [S -0.200; moved 6 mm back with the post for wand-latch clearance]
TR = -0.405             # tower rear [S]
TOP_F = 0.518           # top at the front (stub + front 50 mm of the lid) [S 753 px, F ~0.52]
TOP_DROP = 0.040        # slope down to the rear [S 58 px, manual p04]
SLOPE_F = TF - 0.050    # where the slope starts
PLINTH_TOP = 0.195      # dark plinth top [S 0.183, I 0.203, F 0.218 (perspective-biased high)]
LID_GAP = 0.024         # lid seam below the top surface
CH_X, CH_F = 0.019, 0.040  # front corner chamfers: x extent / fwd extent [F 30 px; S strip]
RC_X, RC_F = -0.040, -0.330  # rear-left chamfer endpoints (rear face x / left side fwd) [T, canister render]
PC_F = -0.212           # post centre fwd: sleeve front -0.1785 clears the MultiFLEX rear latch (-0.175) [S -0.206, wand part]
SLEEVE_R = 0.0335       # lower post sleeve radius [F channel 70 mm]
POST_R = 0.032          # upper post radius [I]
NOTCH_R = 0.0355        # tower channel radius (2 mm shadow gap)
JOINT_UP = 0.527        # sleeve / upper post joint [I: 9 mm above the tower top]
SPLIT_A = (-HW + CH_X, TF)      # stub/bin seam on the top: diagonal from the front-left chamfer ...
SPLIT_B = (HW, TF - 0.050)      # ... past the post to the right side (vertical seam there) [T ph7l t0352, S]
CUP_C = None            # cup centre (x, fwd) = handheld axis, set from params
CUP_RI = 0.0500         # cup cavity half width (handheld bin x +-0.0464)
CUP_REAR = -0.2135      # cup cavity rear wall (handheld bin back -0.210)
CR_HW = 0.062           # cradle half width [I ~0.125]
CR_F, CR_R = -0.098, PC_F - 0.038  # cradle block front / rear
CR_BOT = 0.814          # cradle block underside
BR_BOT = 0.748          # bracket starts on the post [I: cradle overall 0.128 tall]
EAR_UP = 0.903          # back-wall side tops = cradle top [F cradle top 0.907, I]
JAW_UP = 0.858          # front jaw tops [ph7l t0344 side]
BACK_UP = 0.886         # back wall top
REAR_UP = 0.870         # rear block top at the very rear
WAND_CH_HW = 0.0260     # wand channel half width through cup floor / bracket (upper wand housing +-0.023)
WAND_CH_BACK = -0.1725  # channel back face (upper wand housing rear -0.169)
HH_BIN_F = -0.1445      # handheld bin/cap axis fwd = WAND_FWD - 0.0215 [handheld agent]; bin x +-0.046, rear -0.210, latch -0.231
DIAL_C = (-0.052, -0.353)  # odour dial centre [T, user frame]
DIAL_R = 0.031          # [manual p05/06: ~1/3 of the tower depth]
HANDLE_F = -0.292       # handle trough centre fwd [T]
DOOR_F = (-0.396, -0.300)  # filter door fwd span on the right side [S, JCGX t0098.6]
DOOR_U = (0.024, 0.183)
BTN_FU = (-0.364, 0.052)   # door push button centre [S]

_LIB = {}
_objs = []
_lights = []


def L():
    return _LIB["lib"]


def _V(x, up, fwd):
    return Vector((x, -fwd, up))


def keep(ob):
    _objs.append(ob)
    return ob


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------------------------- 2D helpers
def clip(poly, a, b, keep_left=True, off=0.0):
    """Sutherland-Hodgman against the line a->b (offset by `off` toward the kept side)."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln       # left normal
    sgn = 1 if keep_left else -1

    def d(p):
        return sgn * ((p[0] - ax) * nx + (p[1] - ay) * ny) - off

    out = []
    N = len(poly)
    for i in range(N):
        p, q = poly[i], poly[(i + 1) % N]
        dp, dq = d(p), d(q)
        if dp >= 0:
            out.append(p)
        if (dp >= 0) != (dq >= 0):
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    # drop near-duplicates
    res = []
    for p in out:
        if not res or math.hypot(p[0] - res[-1][0], p[1] - res[-1][1]) > 1e-5:
            res.append(p)
    if len(res) > 2 and math.hypot(res[0][0] - res[-1][0], res[0][1] - res[-1][1]) < 1e-5:
        res.pop()
    return res


def offset(poly, dist):
    """miter offset of a closed polygon; positive = outward (assumes CCW in (x, fwd))."""
    N = len(poly)
    out = []
    for i in range(N):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % N])
        e0 = (p1 - p0)
        e1 = (p2 - p1)
        if e0.length < 1e-9 or e1.length < 1e-9:
            out.append(tuple(p1))
            continue
        e0.normalize()
        e1.normalize()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        m = (n0 + n1)
        if m.length < 1e-6:
            m = n0
        m.normalize()
        k = max(0.3, m.dot(n1))
        out.append(tuple(p1 + m * (dist / k)))
    return out


def area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        a += x0 * y1 - x1 * y0
    return a / 2


def ccw(poly):
    return poly if area(poly) > 0 else poly[::-1]


def ray_hit(poly, c, ang):
    d = (math.cos(ang), math.sin(ang))
    best = None
    N = len(poly)
    for i in range(N):
        a, b = poly[i], poly[(i + 1) % N]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wy = a[0] - c[0], a[1] - c[1]
        t = (wx * ey - wy * ex) / den
        s = (wx * d[1] - wy * d[0]) / den
        if t > 0 and -1e-9 <= s <= 1 + 1e-9:
            if best is None or t > best:
                best = t
    return (c[0] + d[0] * best, c[1] + d[1] * best)


def circle(r, cx=0.0, cy=0.0, n=48, a0=0.0):
    return [(cx + r * math.cos(a0 + math.tau * i / n), cy + r * math.sin(a0 + math.tau * i / n)) for i in range(n)]


def rr2(w, h, r, cx=0.0, cy=0.0, n=None):
    return [(cx + x, cy + y) for x, y in L().rrect(w, h, r, n)]


def stadium(p0, p1, hw, n=6):
    """2D slot between p0 and p1 with half width hw (rounded ends)"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    pts = []
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((p0[0] + hw * (math.cos(a) * ux + math.sin(a) * nx), p0[1] + hw * (math.cos(a) * uy + math.sin(a) * ny)))
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((p1[0] + hw * (math.cos(a) * ux + math.sin(a) * nx), p1[1] + hw * (math.cos(a) * uy + math.sin(a) * ny)))
    return pts


# ----------------------------------------------------------------------------------------------- mesh helpers
def bm_to_obj(bm, name, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.validate()
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
    me.materials.append(L().MATS[mat])
    ob = L().link(bpy.data.objects.new(name, me))
    ob["grp"] = GRP
    return ob


def slab(name, plan, z0, z1, mat, top=None, bis_f=(), bis_x=(), smooth=True):
    """plan (x, fwd) polygon extruded z0..z1, optional extra cuts (bisect at fwd / x values) and a top height
    function top(x, fwd) that rescales every vertex height linearly between z0 and top(x, fwd)."""
    bm = bmesh.new()
    plan = ccw(plan)
    b = [bm.verts.new((x, -f, z0)) for x, f in plan]
    t = [bm.verts.new((x, -f, z1)) for x, f in plan]
    n = len(plan)
    bm.faces.new(b[::-1])
    bm.faces.new(t)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((b[i], b[j], t[j], t[i]))
    for f in bis_f:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, -f, 0), plane_no=(0, 1, 0))
    for x in bis_x:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    if top:
        for v in bm.verts:
            tt = (v.co.z - z0) / (z1 - z0)
            v.co.z = z0 + tt * (top(v.co.x, -v.co.y) - z0)
    return bm_to_obj(bm, name, mat, smooth)


def bevel_mod(ob, width, seg=None, angle=30, harden=True):
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width = width
    md.segments = seg if seg is not None else L().D["bevel_seg"]
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(angle)
    md.use_clamp_overlap = True
    md.harden_normals = harden
    return ob


def boolean_cut(ob, cutters):
    for c in cutters:
        md = ob.modifiers.new("Cut", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.solver = "EXACT"
        md.object = c
        try:
            md.material_mode = "TRANSFER"
        except Exception:  # noqa: BLE001
            pass
        c.hide_render = True
        c.hide_viewport = True
    L().apply_modifiers(ob)
    for c in cutters:
        me = c.data
        bpy.data.objects.remove(c)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = ob.data
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(40))
    return ob


def prism_plan(name, pts, u0, u1, mat="M_DockGraphite"):
    """(x, fwd) polygon extruded along up"""
    return L().extrude(name, pts, lambda u, v, w: _V(u, w, v), u0, u1, mat, GRP)


def prism_fu(name, pts, x0, x1, mat="M_DockGraphite"):
    """(fwd, up) polygon extruded along x"""
    return L().extrude(name, pts, lambda u, v, w: _V(w, v, u), x0, x1, mat, GRP)


def prism_xu(name, pts, f0, f1, mat="M_DockGraphite"):
    """(x, up) polygon extruded along fwd"""
    return L().extrude(name, pts, lambda u, v, w: _V(u, v, w), f0, f1, mat, GRP)


def tube(name, path, r, mat, segs=16):
    path = [Vector(p) for p in path]
    N = len(path)
    T = [(path[min(i + 1, N - 1)] - path[max(i - 1, 0)]).normalized() for i in range(N)]
    ref = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    Nn = T[0].cross(ref).normalized()
    rings = []
    for i in range(N):
        if i > 0:
            Nn = (Nn - T[i] * Nn.dot(T[i])).normalized()
        B = T[i].cross(Nn)
        rings.append([L().toB(path[i] + (Nn * math.cos(math.tau * j / segs) + B * math.sin(math.tau * j / segs)) * r)
                      for j in range(segs)])
    verts, faces = L().ring_mesh(rings, True, True)
    return L().mk(name, verts, faces, mat, GRP)


def decal_quad(name, corners, slot, mat="M_Decal", uv_corners=((0, 0), (1, 0), (1, 1), (0, 1))):
    """corners: 4 product-coord points (bl, br, tr, tl as seen by the viewer)"""
    import materials as M
    verts = [_V(*c) for c in corners]
    uvs = [M.decal_uv(slot, s, t) for s, t in uv_corners]
    return L().mk(name, verts, [(0, 1, 2, 3)], mat, GRP, smooth=False, uvs=uvs, recalc=False)


# ----------------------------------------------------------------------------------------------- plans
def tower_plan(q=1.0, grow=0.0):
    """tower outline (x, fwd), CCW. grow > 0 enlarges uniformly (approx)."""
    F = L().fillet
    nc = max(3, int(round(7 * q)))
    raw = [
        ((NOTCH_R, TF), 0.0012),
        ((HW - CH_X, TF), 0.006),
        ((HW, TF - CH_F), 0.006),
        ((HW, TR), 0.030),
        ((RC_X, TR), 0.016),
        ((-HW, RC_F), 0.016),
        ((-HW, TF - CH_F), 0.006),
        ((-HW + CH_X, TF), 0.006),
        ((-NOTCH_R, TF), 0.0012),
    ]
    pts = [p for p, _ in raw]
    rad = [r for _, r in raw]
    # semicircular post channel (centre PC_F) going around the rear of the post
    na = max(8, int(round(20 * q)))
    pts.append((-NOTCH_R, PC_F))
    rad.append(0.0)
    for i in range(1, na):
        a = math.pi + math.pi * i / na
        pts.append((NOTCH_R * math.cos(a), PC_F + NOTCH_R * math.sin(a)))
        rad.append(0.0)
    pts.append((NOTCH_R, PC_F))
    rad.append(0.0)
    poly = F(pts, rad, nc)
    poly = ccw(poly)
    if grow:
        poly = offset(poly, grow)
    return poly


def top_h(x, f):
    """tower top surface (lid/bin); flat at the front, slopes to the rear"""
    t = max(0.0, min(1.0, (SLOPE_F - f) / (SLOPE_F - TR)))
    s = t * t * 0.25 + t * 0.75 if t < 1 else 1.0
    return TOP_F - 0.002 - TOP_DROP * s


# ----------------------------------------------------------------------------------------------- base plate
def build_plate(q):
    lib = L()
    pd = PLATE_F - PLATE_R
    pcf = (PLATE_F + PLATE_R) / 2
    base = ccw(lib.fillet([(PLATE_W / 2, PLATE_F), (-PLATE_W / 2, PLATE_F), (-PLATE_W / 2, PLATE_R), (PLATE_W / 2, PLATE_R)],
                          [0.024, 0.024, 0.018, 0.018], max(4, int(round(9 * q)))))
    # profile: (inset, up)  rounded bottom edge, vertical side, chamfered/rounded top edge
    prof = [(0.0022, 0.0), (0.0008, 0.0006), (0.0, 0.0020), (0.0, PLATE_T - 0.0042), (0.0010, PLATE_T - 0.0020),
            (0.0024, PLATE_T - 0.0006), (0.0042, PLATE_T)]
    rings = [[_V(x, up, f) for x, f in offset(base, -s)] for s, up in prof]
    verts, faces = lib.ring_mesh(rings, True, False)
    # top: one flat n-gon
    n = len(base)
    ob_v = list(verts)
    a = (len(prof) - 1) * n
    faces.append(tuple(range(a, a + n)))
    plate = lib.mk("Dock_BasePlate", ob_v, faces, "M_DockGraphite", GRP)
    keep(plate)
    # rubber feet
    for sx in (-1, 1):
        for f in (PLATE_F - 0.030, PLATE_R + 0.028):
            keep(lib.lathe_up("Dock_Foot", [(0, -0.0004), (0.0068, -0.0004), (0.0072, 0.0002), (0.0072, 0.0012), (0, 0.0012)],
                              f, "M_Rubber", GRP, cx=sx * (PLATE_W / 2 - 0.026), segs=max(12, int(24 * q))))
    return plate


# ----------------------------------------------------------------------------------------------- plinth
def build_plinth(q):
    lib = L()
    plan = tower_plan(q, grow=0.0004)
    pl = slab("Dock_Plinth", plan, PLATE_T, PLINTH_TOP - 0.0006, "M_DockGraphite")
    xr = HW + 0.0004
    cuts = []
    # filter door outline groove (rounded rect, 0.8 mm) [S, JCGX t0098.6/t0101.5]
    df0, df1 = DOOR_F
    du0, du1 = DOOR_U
    dcf, dcu = (df0 + df1) / 2, (du0 + du1) / 2
    outer = rr2(df1 - df0, du1 - du0, 0.012, dcf, dcu, n=6)
    inner = rr2(df1 - df0 - 0.0016, du1 - du0 - 0.0016, 0.0112, dcf, dcu, n=6)
    fr = frame_prism("cut_door", outer, inner, lambda u, v, w: _V(w, v, u), xr - 0.0015, xr + 0.01, "M_Rubber")
    cuts.append(fr)
    # diagonal slots rising toward the rear (fwd decreases as up increases), clipped to the grille box
    gf0, gf1 = df0 + 0.009, df1 - 0.009
    gu0, gu1 = du0 + 0.009, du1 - 0.009
    bcf, bcu = BTN_FU
    pitch = 0.0078
    hw = 0.00165
    k = -40
    while k < 40:
        # line: up - gu0 = -(fwd - c) ; parametrised by c
        c = gf1 + k * pitch * math.sqrt(2)
        k += 1
        # intersection of the 45 deg line fwd = c - (up - gu0) with the box
        pts = []
        for up in (gu0, gu1):
            f = c - (up - gu0)
            if gf0 <= f <= gf1:
                pts.append((f, up))
        for f in (gf0, gf1):
            up = gu0 + (c - f)
            if gu0 <= up <= gu1:
                pts.append((f, up))
        pts = sorted(set((round(a, 7), round(b, 7)) for a, b in pts), key=lambda p: p[1])
        if len(pts) < 2:
            continue
        p0, p1 = pts[0], pts[-1]
        # keep clear of the push button (lower rear corner)
        def near_btn(p):
            return math.hypot(p[0] - bcf, p[1] - bcu) < 0.0215
        if near_btn(p0) or near_btn(p1) or near_btn(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)):
            # shorten from the bottom end until clear
            for tcut in (0.25, 0.4, 0.55, 0.7):
                pa = (p0[0] + (p1[0] - p0[0]) * tcut, p0[1] + (p1[1] - p0[1]) * tcut)
                if not near_btn(pa):
                    p0 = pa
                    break
            else:
                continue
        ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if ln < 0.010:
            continue
        sh = 0.0025 / ln
        a = (p0[0] + (p1[0] - p0[0]) * sh, p0[1] + (p1[1] - p0[1]) * sh)
        b = (p1[0] - (p1[0] - p0[0]) * sh, p1[1] - (p1[1] - p0[1]) * sh)
        cuts.append(prism_fu("cut_slot", stadium(a, b, hw, n=4 if q < 1 else 6), xr - 0.0055, xr + 0.01, "M_Rubber"))
    # push-button recess
    cuts.append(prism_fu("cut_btn", circle(0.0150, bcf, bcu, n=max(24, int(40 * q))), xr - 0.0030, xr + 0.01, "M_Rubber"))
    # rear power socket recess (rear-left, low) [T: cord leaves at the rear-left corner]
    sx, su = RC_X + 0.010, 0.034
    cuts.append(prism_xu("cut_socket", circle(0.0085, sx, su, n=24), TR - 0.01, TR + 0.006, "M_Rubber"))
    boolean_cut(pl, cuts)
    bevel_mod(pl, 0.0012, seg=2)
    keep(pl)
    # push button (dark, domed, with a finger dimple ring)
    keep(lib.lathe("Dock_DoorButton", [(0, 0.0012), (0.0060, 0.0011), (0.0105, 0.0006), (0.0122, -0.0004),
                                       (0.0128, -0.0014), (0.0128, -0.0030), (0, -0.0030)],
                   (xr - 0.0012, bcu, bcf), (1, 0, 0), (0, 1, 0), "M_DockGraphite", GRP, segs=max(24, int(40 * q))))
    # plug + cord
    plug = lib.lathe("Dock_Plug", [(0, 0.0), (0.0074, 0.0), (0.0078, 0.0012), (0.0078, 0.0130), (0.0062, 0.0165),
                                   (0.0036, 0.0200), (0.0030, 0.0270), (0, 0.0270)],
                     (sx, su, TR + 0.0040), (0, 0, -1), (1, 0, 0), "M_Rubber", GRP, segs=24)
    keep(plug)
    p0 = Vector((sx, su, TR - 0.0225))
    # cord drops behind the plate and runs back toward the wall socket [ph7l t0352]
    path = lib.bezier_path(p0, p0 + Vector((0, 0, -0.022)), Vector((sx, 0.0029, PLATE_R - 0.010)),
                           Vector((sx - 0.004, 0.0029, PLATE_R - 0.045)), 14)
    path2 = lib.bezier_path(Vector((sx - 0.004, 0.0029, PLATE_R - 0.045)), Vector((sx - 0.010, 0.0029, PLATE_R - 0.110)),
                            Vector((sx + 0.030, 0.0029, PLATE_R - 0.150)), Vector((sx + 0.020, 0.0029, PLATE_R - 0.230)), 14)
    keep(tube("Dock_Cord", list(path) + list(path2)[1:], 0.0029, "M_Rubber", segs=12))


def frame_prism(name, outer, inner, mapf, w0, w1, mat):
    n = len(outer)
    verts = [mapf(u, v, w0) for u, v in outer] + [mapf(u, v, w1) for u, v in outer]
    verts += [mapf(u, v, w0) for u, v in inner] + [mapf(u, v, w1) for u, v in inner]
    faces = []
    for j in range(n):
        k = (j + 1) % n
        faces.append((j, k, n + k, n + j))
        faces.append((2 * n + k, 2 * n + j, 3 * n + j, 3 * n + k))
        faces.append((k, j, 2 * n + j, 2 * n + k))
        faces.append((n + j, n + k, 3 * n + k, 3 * n + j))
    return L().mk(name, verts, faces, mat, GRP, smooth=False)


# ----------------------------------------------------------------------------------------------- tower
def split_plans(q):
    P = tower_plan(q)
    stub = clip(P, SPLIT_A, SPLIT_B, keep_left=True, off=0.0004)    # front-right of the seam line
    binp = clip(P, SPLIT_A, SPLIT_B, keep_left=False, off=0.0004)
    return ccw(stub), ccw(binp)


def build_tower(q):
    lib = L()
    stub, binp = split_plans(q)
    bf = [SLOPE_F, SLOPE_F - 0.04, SLOPE_F - 0.08, SLOPE_F - 0.12]
    b0 = PLINTH_TOP + 0.0006

    def lid_seam(x, f):
        return top_h(x, f) - LID_GAP

    # bin body
    body = slab("Dock_BinBody", binp, b0, 0.50, "M_White", top=lambda x, f: lid_seam(x, f) - 0.0004, bis_f=bf)
    # bin release button + bottom tab on the rear-left chamfer face [canister render tr-part-2-0l-aed-toz-haznesi-1-1]
    c0, c1 = Vector((RC_X, TR)), Vector((-HW, RC_F))
    T = (c1 - c0).normalized()
    N = Vector((-T.y, T.x))
    if N.dot(Vector((-1, -1))) < 0:
        N = -N
    mid = (c0 + c1) / 2

    def fmap(cu, cv):
        def m(u, v, w):
            p = mid + T * u + N * w
            return _V(p.x, v, p.y)
        return m
    bcut = [L().extrude("cut_binbtn", rr2(0.017, 0.024, 0.004, 0.0, 0.292, n=5), fmap(0, 0), -0.004, 0.01, "M_DockGraphite", GRP),
            L().extrude("cut_bintab", rr2(0.016, 0.009, 0.0025, 0.0, 0.212, n=4), fmap(0, 0), -0.0025, 0.01, "M_DockGraphite", GRP)]
    boolean_cut(body, bcut)
    bevel_mod(body, 0.0016, seg=3)
    keep(body)
    bb = L().extrude("Dock_BinReleaseSide", rr2(0.0125, 0.017, 0.003, 0.0, 0.2905, n=5), fmap(0, 0), -0.0035, -0.0012, "M_White", GRP)
    bevel_mod(bb, 0.0008, seg=2, harden=False)
    keep(bb)
    tb = L().extrude("Dock_BinTab", rr2(0.013, 0.006, 0.002, 0.0, 0.2105, n=4), fmap(0, 0), -0.0025, 0.0018, "M_White", GRP)
    bevel_mod(tb, 0.0007, seg=2, harden=False)
    keep(tb)
    # lid (rounder top edge) + handle trough + dial well
    lid = slab("Dock_BinLid", binp, 0.40, 0.52, "M_White", bis_f=bf,
               top=None)
    # rescale heights: bottom ring -> lid seam, top ring -> top_h
    me = lid.data
    for v in me.vertices:
        x, f = v.co.x, -v.co.y
        v.co.z = (lid_seam(x, f) + 0.0004) if v.co.z < 0.45 else top_h(x, f)
    cuts = []
    # carry-handle trough across the top (behind the post) [T, canister render]
    tw, td = 0.100, 0.034
    cuts.append(prism_plan("cut_trough", rr2(tw, td, 0.012, 0.004, HANDLE_F, n=max(4, int(8 * q))), 0.45, 0.60, "M_White"))
    # dial well
    dz = top_h(*DIAL_C)
    cuts.append(prism_plan("cut_dialwell", circle(DIAL_R + 0.0035, DIAL_C[0], DIAL_C[1], n=max(32, int(64 * q))),
                           dz - 0.010, 0.60, "M_DockGraphite"))
    boolean_cut(lid, cuts)
    bevel_mod(lid, 0.0030, seg=max(3, lib.D["bevel_seg"]), angle=28)
    keep(lid)
    # trough floor + grip lip (separate piece sitting 22 mm below the local top, reads as the recess bottom)
    tf_up = top_h(0.0, HANDLE_F) - 0.022
    fl = prism_plan("Dock_TroughFloor", rr2(tw - 0.0008, td - 0.0008, 0.0116, 0.004, HANDLE_F, n=max(4, int(8 * q))),
                    tf_up - 0.004, tf_up, "M_White")
    keep(fl)
    # dark release button on the front rim of the trough [T, canister render]
    bf_ = HANDLE_F + td / 2 + 0.0145
    bz = top_h(0.0, bf_)
    btn = prism_plan("Dock_BinRelease", rr2(0.054, 0.022, 0.0075, 0.004, bf_, n=max(4, int(7 * q))), bz - 0.004, bz + 0.0045,
                     "M_DockGraphite")
    bevel_mod(btn, 0.0018, seg=3)
    keep(btn)
    # stub (front-right, fixed, flat triangular top)
    st = slab("Dock_FrontStub", stub, b0, TOP_F, "M_White")
    bevel_mod(st, 0.0022, seg=3)
    keep(st)
    build_dial(q)
    build_badge_and_light(q)


def build_dial(q):
    lib = L()
    cx, cf = DIAL_C
    dz = top_h(cx, cf)
    wf = dz - 0.010             # well floor
    segs = max(40, int(72 * q))
    # socket ring (grey) at the well floor
    keep(lib.lathe_up("Dock_DialSocket", [(DIAL_R + 0.0034, wf - 0.001), (DIAL_R + 0.0034, wf + 0.003), (DIAL_R + 0.0012, wf + 0.003),
                                          (DIAL_R + 0.0012, wf), (0, wf)], cf, "M_Gunmetal", GRP, cx=cx, segs=segs))
    # black puck: grooved body, flip-up ring handle (folded flat) around a recessed flat printed face
    # [crop-tr01-dock-display-inset, manual p05/06]
    top = dz + 0.0030
    R = DIAL_R
    body = [(0, wf + 0.001), (R - 0.0010, wf + 0.001), (R, wf + 0.002), (R, wf + 0.0045), (R - 0.0012, wf + 0.0052),
            (R - 0.0012, wf + 0.0062), (R, wf + 0.0069), (R, top - 0.0048), (R - 0.0015, top - 0.0042), (0, top - 0.0042)]
    keep(lib.lathe_up("Dock_OdourDial", body, cf, "M_Screen", GRP, cx=cx, segs=segs))
    ri = 0.80 * R
    ring = [(ri, top - 0.0042), (R - 0.0004, top - 0.0042), (R, top - 0.0036), (R, top - 0.0009), (R - 0.0009, top),
            (ri + 0.0012, top), (ri + 0.0002, top - 0.0006), (ri, top - 0.0016)]
    rg = lib.lathe_up("Dock_DialRing", ring, cf, "M_Screen", GRP, cx=cx, segs=segs, cap0=False, cap1=False, closed=True)
    # two hinge gaps at the sides of the ring (it flips up about the x axis)
    gaps = [prism_plan("cut_ringgap", rr2(0.006, 0.0040, 0.0006, cx + sx * (R - 0.003), cf, n=2), top - 0.0045, top + 0.01, "M_Screen")
            for sx in (-1, 1)]
    boolean_cut(rg, gaps)
    keep(rg)
    face_z = top - 0.0016
    keep(lib.lathe_up("Dock_DialFace", [(0, face_z), (ri + 0.0004, face_z), (ri + 0.0004, top - 0.0044), (0, top - 0.0044)],
                      cf, "M_Screen", GRP, cx=cx, segs=segs))
    # printed face (decal disc; 'odour_dial' slot = circumscribed square of the face disc)
    nd = max(32, int(64 * q))
    rr = ri - 0.0004
    z = face_z + 0.00025
    verts = [_V(cx, z, cf)] + [_V(cx + rr * math.cos(math.tau * i / nd), z, cf + rr * math.sin(math.tau * i / nd)) for i in range(nd)]
    faces = [(0, i + 1, (i + 1) % nd + 1) for i in range(nd)]
    import materials as M

    # read from the front of the dock: s = +x, t = toward the rear (non-mirrored seen from above)
    def uvp(dx, df):
        return M.decal_uv("odour_dial", 0.5 + dx / (2 * rr), 0.5 - df / (2 * rr))
    uvs = [uvp(0, 0)] + [uvp(rr * math.cos(math.tau * i / nd), rr * math.sin(math.tau * i / nd)) for i in range(nd)]
    keep(lib.mk("Dock_DialPrint", verts, faces, "M_Decal", GRP, smooth=False, uvs=uvs, recalc=False))


def build_badge_and_light(q):
    lib = L()
    # POWERDETECT champagne badge, front face of the stub, top-right of the post [F, I]
    bw, bh = 0.046, 0.0130
    bx = NOTCH_R + 0.0060 + bw / 2
    bu = TOP_F - 0.022
    plate = prism_xu("Dock_Badge", rr2(bw, bh, 0.0012, bx, bu, n=3), TF - 0.0002, TF + 0.0008, "M_Champagne")
    bevel_mod(plate, 0.0003, seg=2, harden=False)
    keep(plate)
    iw, ih = 0.038, 0.038 / 16.5
    z = TF + 0.0011
    keep(decal_quad("Dock_BadgePrint", [(bx - iw / 2, bu - ih / 2, z), (bx + iw / 2, bu - ih / 2, z),
                                        (bx + iw / 2, bu + ih / 2, z), (bx - iw / 2, bu + ih / 2, z)], "dock_powerdetect"))
    # DUST BIN FULL pill window on the stub top, long axis along the stub diagonal [T, JCGX t0011.6, manual p14]
    cx, cf = 0.063, TF - 0.0205
    ang = math.atan2(SPLIT_B[1] - SPLIT_A[1], SPLIT_B[0] - SPLIT_A[0])   # seam direction
    pl_, pw_ = 0.038, 0.0170
    pill = [(cx + x * math.cos(ang) - y * math.sin(ang), cf + x * math.sin(ang) + y * math.cos(ang))
            for x, y in rr2(pl_, pw_, pw_ / 2 - 0.0002, n=max(6, int(10 * q)))]
    glass = prism_plan("Dock_BinFullWindow", pill, TOP_F - 0.002, TOP_F + 0.0006, "M_Screen")
    bevel_mod(glass, 0.0004, seg=2, harden=False)
    keep(glass)
    # icons (glow when the bin is full): quad on the glass, glyph up toward the post/front
    iw, ih = 0.027, 0.027 / 2.83
    z = TOP_F + 0.00085

    def P(x, y):
        return (cx + x * math.cos(ang) - y * math.sin(ang), z, cf + x * math.sin(ang) + y * math.cos(ang))

    icon = decal_quad("Dock_BinFullIcons", [P(-iw / 2, ih / 2), P(iw / 2, ih / 2), P(iw / 2, -ih / 2), P(-iw / 2, -ih / 2)],
                      "dock_binfull", mat="M_DockDisplay")
    keep(icon)
    _lights.append(icon)


# ----------------------------------------------------------------------------------------------- post + cradle
def build_post(q):
    lib = L()
    segs = max(32, int(72 * q))
    # lower sleeve (plate -> joint), round top edge
    prof = [(0, PLATE_T - 0.001), (SLEEVE_R, PLATE_T - 0.001), (SLEEVE_R, JOINT_UP - 0.0030), (SLEEVE_R - 0.0006, JOINT_UP - 0.0010),
            (SLEEVE_R - 0.0018, JOINT_UP - 0.0001), (POST_R - 0.0004, JOINT_UP), (0, JOINT_UP)]
    sl = lib.lathe_up("Dock_PostSleeve", prof, PC_F, "M_Gunmetal", GRP, segs=segs)
    # arched opening at the bottom front [I, F]
    aw, atop = 0.040, 0.152
    arch = [(-aw / 2, PLATE_T - 0.01), (aw / 2, PLATE_T - 0.01)]
    na = 14
    for i in range(na + 1):
        a = math.pi * i / na
        arch.append((aw / 2 * math.cos(a), atop - aw / 2 + aw / 2 * math.sin(a)))
    arch = arch[:2] + arch[2:]
    boolean_cut(sl, [prism_xu("cut_arch", arch, PC_F - 0.010, PC_F + 0.05, "M_Rubber")])
    keep(sl)
    # upper post
    keep(lib.lathe_up("Dock_Post", [(0, JOINT_UP + 0.0006), (POST_R - 0.0012, JOINT_UP + 0.0006), (POST_R, JOINT_UP + 0.0020),
                                    (POST_R, BR_BOT + 0.020), (0, BR_BOT + 0.020)], PC_F, "M_Gunmetal", GRP, segs=segs))


def cradle_top(x, f):
    """cup walls: low front jaws, concave rise to the tall back wall (saddle in the middle), flat rear block
    [ph7l t0344/t0616 side views, I front]"""
    cf = CUP_C[1]
    s = max(0.0, min(1.0, ((cf + 0.006) - f) / 0.040))     # 0 at the jaw front zone .. 1 at the back wall
    h = JAW_UP + (EAR_UP - JAW_UP) * (1 - math.sqrt(max(0.0, 1 - s * s)))
    sad = smoothstep(cf - 0.020, cf - 0.042, f) * (1 - smoothstep(cf - 0.052, cf - 0.066, f))
    h -= (EAR_UP - BACK_UP) * sad * max(0.0, 1 - (x / 0.046) ** 2)
    return h


def build_cradle(q):
    lib = L()
    nc = max(4, int(round(9 * q)))
    plan = ccw(lib.fillet([(CR_HW, CR_F), (-CR_HW, CR_F), (-CR_HW, CR_R), (CR_HW, CR_R)], [0.018, 0.018, 0.040, 0.040], nc))
    cf = CUP_C[1]
    bis_f = [cf + 0.012, cf + 0.004, cf - 0.004, cf - 0.012, cf - 0.018, cf - 0.024, cf - 0.029, cf - 0.034, cf - 0.042,
             cf - 0.050, cf - 0.058, cf - 0.066, cf - 0.080]
    bis_x = [-0.040, -0.025, -0.012, 0.0, 0.012, 0.025, 0.040]
    blk = slab("Dock_Cradle", plan, CR_BOT, 0.95, "M_Gunmetal", top=cradle_top, bis_f=bis_f, bis_x=bis_x)
    cuts = []
    # U cavity around the handheld bin: circle + straight front opening
    floor = P_HB - 0.0020
    cav = lib.fillet([(CUP_RI, CR_F + 0.02), (CUP_RI, CUP_REAR), (-CUP_RI, CUP_REAR), (-CUP_RI, CR_F + 0.02)],
                     [0.0, 0.030, 0.030, 0.0], max(6, int(14 * q)))
    cuts.append(prism_plan("cut_cup", cav, floor, 1.0, "M_DockGraphite"))
    # wand channel through the cup floor and the bracket (open front)
    ch = rr2(2 * WAND_CH_HW, 0.12, 0.006, 0.0, WAND_CH_BACK + 0.06, n=4)
    cuts.append(prism_plan("cut_wand", ch, 0.70, 1.0, "M_DockGraphite"))
    # Quiet-mode slide switch recess on the right side face, low on the front jaw [ph7l t0344/t0616, manual p14]
    sw_f, sw_u = cf + 0.004, 0.833
    WW = 0.0085                                   # side wing thickness
    # notch in the back wall for the handheld's rear bin latch (x +-9 mm, to fwd -0.227, from 0.861 up)
    cuts.append(prism_plan("cut_hhlatch", rr2(0.026, 0.027, 0.004, 0.0, CUP_REAR - 0.0095, n=4), 0.853, 1.0, "M_Gunmetal"))
    # post-release latch: small square push button in a pad on the rear top [boru render]
    la_f, la_x = CR_R + 0.016, 0.031
    cuts.append(prism_plan("cut_latch", rr2(0.016, 0.0125, 0.003, la_x, la_f, n=4), EAR_UP - 0.004, 1.0, "M_Rubber"))
    boolean_cut(blk, cuts)
    bevel_mod(blk, 0.0018, seg=3, angle=32)
    keep(blk)
    # bracket: loft from the upper post (circle) to the cradle underside outline
    c = (0.0, (PC_F + CR_R + CR_F + CR_F) / 4 + 0.01)
    c = (0.0, -0.190)
    n = max(48, int(96 * q))
    angs = [math.tau * i / n for i in range(n)]
    post = circle(POST_R, 0.0, PC_F, n=200)
    r0 = [ray_hit(post, c, a) for a in angs]
    r1 = [ray_hit(plan, c, a) for a in angs]
    rings = []
    nr = max(6, int(12 * q))
    for k in range(nr + 1):
        t = k / nr
        s = t ** 1.8
        up = BR_BOT + (CR_BOT + 0.0012 - BR_BOT) * t
        rings.append([_V(a[0] + (b[0] - a[0]) * s, up, a[1] + (b[1] - a[1]) * s) for a, b in zip(r0, r1)])
    verts, faces = lib.ring_mesh(rings, False, True)
    br = lib.mk("Dock_CradleBracket", verts, faces, "M_Gunmetal", GRP)
    boolean_cut(br, [prism_plan("cut_wand2", ch, 0.70, 1.0, "M_DockGraphite")])
    keep(br)
    # charging contacts: block on the inner rear wall + 2 square pads [manual p09/p14]
    ri = CUP_REAR
    cu = floor + 0.016
    blk2 = prism_xu("Dock_ContactBlock", rr2(0.030, 0.020, 0.003, 0.0, cu, n=4), ri - 0.002, ri + 0.0115, "M_DockGraphite")
    bevel_mod(blk2, 0.0008, seg=2, harden=False)
    keep(blk2)
    for sx in (-1, 1):
        pad = prism_xu("Dock_ContactPad", rr2(0.0055, 0.0055, 0.0006, sx * 0.0065, cu, n=2), ri + 0.0114, ri + 0.0126, "M_Chrome")
        keep(pad)
    # side wings: shoulders stepping out below the jaw tops (cradle reads wider at mid height) [I front, ph7l t0616]
    for sx in (-1, 1):
        prof = [(CR_F - 0.0005, 0.814), (cf - 0.030, 0.826), (cf - 0.036, 0.836), (cf - 0.036, 0.851), (CR_F - 0.0005, 0.851)]
        prof = lib.fillet(prof, [0.006, 0.006, 0.004, 0.004, 0.005], 4)
        x0, x1 = sx * (CR_HW - 0.003), sx * (CR_HW + WW)
        wg = prism_fu("Dock_CradleWing", prof, min(x0, x1), max(x0, x1), "M_Gunmetal")
        if sx > 0:
            boolean_cut(wg, [prism_fu("cut_switch", rr2(0.032, 0.0115, 0.0035, sw_f, sw_u, n=5), CR_HW + WW - 0.0030, CR_HW + WW + 0.01, "M_Rubber")])
        bevel_mod(wg, 0.0016, seg=3)
        keep(wg)
    # slider knob (fan <- -> moon), parked at the fan (front) end = auto-empty on
    xs = CR_HW + WW
    kn = prism_fu("Dock_QuietSlider", rr2(0.0105, 0.0090, 0.0025, sw_f + 0.0080, sw_u, n=4), xs - 0.0030, xs + 0.0006, "M_DockGraphite")
    bevel_mod(kn, 0.0006, seg=2, harden=False)
    keep(kn)
    for dz in (-0.0022, 0.0, 0.0022):
        keep(prism_fu("Dock_QuietRidge", rr2(0.0075, 0.0007, 0.0003, sw_f + 0.0080, sw_u + dz, n=2), xs + 0.0004, xs + 0.0010, "M_DockGraphite"))
    lb = prism_plan("Dock_ReleaseLatch", rr2(0.0140, 0.0105, 0.0025, la_x, la_f, n=4), EAR_UP - 0.0045, EAR_UP - 0.0010, "M_DockGraphite")
    bevel_mod(lb, 0.0006, seg=2, harden=False)
    keep(lb)


# ----------------------------------------------------------------------------------------------- entry
P_HB = 0.8255


def build(ctx):
    global _objs, _lights, CUP_C, P_HB
    _objs, _lights = [], []
    _LIB["lib"] = ctx["lib"]
    P = ctx["P"]
    q = 1.0 if ctx.get("tier", "high") == "high" else 0.5
    CUP_C = (0.0, HH_BIN_F)
    P_HB = P.HANDHELD_BOTTOM_UP + RAISE
    build_plate(q)
    build_plinth(q)
    build_tower(q)
    build_post(q)
    build_cradle(q)
    for o in _objs:
        o["grp"] = GRP
    notes = ("IP3251 dock (XDCKIP3000) built around the stick lifted by RAISE=%.4f m (plate top; floorhead rear wheels "
             "stand on the plate tongue, nose overhangs it). Plate fwd %.3f..%.3f x %.3f W; tower %.3f W, fwd %.3f..%.3f, top "
             "%.3f front -> %.3f rear, plinth to %.3f; post centre fwd %.3f (sleeve R %.4f, upper R %.4f, joint %.3f); cradle "
             "cup cavity +-%.4f x to fwd %.4f around the handheld bin axis, floor %.4f, top %.3f. DockLights = bin-full icon quad "
             "(M_DockDisplay, dock_binfull UVs). Decals: dock_powerdetect (badge), odour_dial (disc on the dial top). "
             "Dock_Cord + Dock_Plug can be hidden." %
             (RAISE, PLATE_R, PLATE_F, PLATE_W, TW, TF, TR, TOP_F, TOP_F - TOP_DROP, PLINTH_TOP, PC_F, SLEEVE_R, POST_R,
              JOINT_UP, CUP_RI, CUP_REAR, P_HB - 0.002, EAR_UP))
    return {"groups": {"Dock": list(_objs)}, "special": {"DockLights": list(_lights)} if _lights else {},
            "anchors": {}, "notes": notes}
