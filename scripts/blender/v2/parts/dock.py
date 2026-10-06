"""dock part (v2, IA3246GN). Owned by the dock agent. See ../PARTS_CONTRACT.md.

Clean & Empty auto-empty dock, built in the product frame around the docked vacuum (wand axis x=0, fwd=P.WAND_FWD).

Architecture (manual IA3000UK p.6 assembly, p.16-19 dock pages; sn-3241laa-01 dock empty; sn-gn-hero; 5050 Auto-Empty):
  * thin floor BASE PLATE (dark) with a front tongue under the floorhead's rear wheels (wheel wells so the
    head stays at floor level), rubber feet, accessory-storage peg at the right-rear corner;
  * dark PLINTH (motor base) up to ~180 mm: front U-arch recess behind the head neck, right-side filter door
    with diagonal grille + round push button, rear power socket + plug + cord;
  * thin bright ring at the plinth/bin seam;
  * sage DUST BIN tower (171 W x 172 D, top 504 mm) with a vertical parting seam just behind the front corners,
    dust-bin window (smoked, fill line) on the right side, rear latch pocket + lower tab;
  * TOP CAP: seam at 476 mm, rear top slopes down, carry-handle slot, small bin button (US: no odour dial),
    notch where the charging post enters;
  * CHARGING POST (58 x 60) rising from the tower front to a flared bracket and the U-CRADLE cup around the
    handheld base (open front channel for the wand), evacuation port + rubber seal in the cup floor,
    charging-contact block on the inner rear wall, Quiet-mode slide switch + moon icon on the rear face.

Local dimension ledger (metres, product coords x/up/fwd). [H1]=sn-gn-hero px measure (1.559 px/mm),
[M]=manual line drawing ratio, [5050]=auto-empty side render ratio, [L]=lead interface.
"""
import math

import bmesh
import bpy
from mathutils import Vector

# ----------------------------------------------------------------------------------------------- ledger
TW = 0.171            # tower width [H1 267 px]
TD = 0.172            # tower depth [M side view 83 u vs plate 140 u, 5050 ratio; fitted to L=375]
TF = -0.145           # tower front face fwd [5050: wand axis -> bin front = 0.26 * depth] (wand axis -0.100 [L])
TR = TF - TD          # -0.317 tower rear
TCF = (TF + TR) / 2
RF, RB = 0.030, 0.060  # flat front face behind the wand (hero), rounder rear;  plan corner radii front / rear [3241laa-01, manual 3D views]
TOP_H = 0.504         # tower top at the front [H1 786 px]
CAP_SEAM = 0.476      # top-cap parting line [H1 ~478]
TOP_DROP = 0.008      # rear-top slope drop [5050, manual side view]
SLOPE_F = -0.282      # where the rear-top slope starts
PLINTH_TOP = 0.1795   # dark plinth top [H1 ~185 incl. ring]
RING0, RING1 = 0.1798, 0.1857  # bright seam ring
SEAM_Y = 0.033        # vertical bin seam, relative to tower plan centre (front corner end) [3241laa-01]
WIN_F = -0.213        # dust-bin window centre fwd (right side) [M p.6 side, p.17]
WIN_UP = (0.270, 0.400)  # [H1 273-401]
PLATE_W = 0.222       # base plate width [H1 dark corners, room for the peg]
PLATE_F, PLATE_R = -0.071, -0.331  # plate front / rear [L=375 -> rear -0.331; front stops 6 mm behind the head end caps (floor-level, fwd -0.065)]
PARK_HW, PARK_BACK = 0.0695, -0.1315  # U parking pocket in the tongue for the head neck plate + rear wheels (|x|<0.0635, fwd>-0.126) [floorhead part]
PLATE_T = 0.0095      # plate top
PW, PD, PR = 0.066, 0.060, 0.018   # charging post section [H1 104 px strips either side of the wand = 66 wide; 5050 ~62 deep]
PCF = TF - 0.021 - PD / 2          # post centre fwd: post enters the cap behind its 16 mm front shoulder so the shoulder runs continuously behind the wand [hero]
CW, CD = 0.105, 0.142              # cradle cup outer [H1 164 px = 105; depth between M post drawing (130) and flat-lay cradle piece (~158)]
CCF = -0.1655                      # cup centre fwd (front -0.0945, rear -0.2365); side ears hug the handheld (fwd -0.079..-0.206)
CUP_T = 0.0045                     # cup wall
CUP_SEAM = 0.8175                  # bracket / cup parting line [M rear view]
CUP_FLOOR = 0.828                  # inner floor (handheld bottom plane 0.835) [L]
RIM_F, RIM_R = 0.866, 0.898        # rim top: front saddle / taller rear wing [H1 865; US manual p.7 quiet view + UK p.6 post drawing: rear higher]
CUP_TAPER = 1.0                    # no plan taper: the handheld is 90 wide back to fwd -0.206
WING_HW = 0.037                    # the taller rear wing only spans |x|<~0.045 (hidden behind the handheld in the hero front view) [harbor-slate cradle]
FLARE_F, FLARE_R = 0.742, 0.781    # where the bracket flare leaves the post (front / rear) [H1 ~760, M]
NOTCH_HW = 0.030                   # half width of the open wand channel through the cradle front
NOTCH_BACK = -0.1265               # back face of the wand channel (wand/connector reaches -0.1236)
HH_HW = 0.0475                     # clearance channel for the handheld base above the cup floor (handheld +-0.045)
WHEEL_X, WHEEL_F = 0.056, -0.100   # floorhead rear wheels: x 0.049-0.0635, D 52 mm, axle fwd -0.100 [L, floorhead agent]

GRP = "Dock"
_objs = []
_lights = []


def _V(x, up, fwd):
    return Vector((x, -fwd, up))


# ----------------------------------------------------------------------------------------------- geometry
def contour(w, d, rf, rb, cf=0.0, cx=0.0, notch=None, dn=0.0008, g=0.0008, q=1.0, taper=1.0):
    """rounded-rect plan (x, fwd) with front radius rf, rear radius rb, fixed per-segment counts so that
    contours of different sizes correspond vertex-for-vertex. notch=y (relative) inserts a V seam on both sides."""
    h = d / 2
    rf = max(0.0008, min(rf, w / 2 - 1e-4, h - 1e-4))
    rb = max(0.0008, min(rb, w / 2 - 1e-4, h - 1e-4))
    nc = max(5, int(round(11 * q)))
    nfs = max(3, int(round(6 * q)))
    nr = max(4, int(round(10 * q)))
    ns = max(4, int(round(12 * q)))
    pts = []

    def line(a, b, n):
        for i in range(n):
            t = i / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

    def arc(c, r, a0, a1, n):
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))

    def side(sx):
        # sx=+1 right side going rear; sx=-1 left side going front
        y0, y1 = (h - rf, -h + rb) if sx > 0 else (-h + rb, h - rf)
        x = sx * w / 2
        if notch is not None and min(y0, y1) + g < notch < max(y0, y1) - g:
            sgn = 1 if y1 > y0 else -1
            line((x, y0), (x, notch - sgn * g), ns)
            pts.append((x, notch - sgn * g))
            pts.append((x - sx * dn, notch))
            line((x, notch + sgn * g), (x, y1), ns)
        else:
            line((x, y0), (x, y1), 2 * ns + 2)

    line((0, h), (w / 2 - rf, h), nfs)
    arc((w / 2 - rf, h - rf), rf, 90, 0, nc)
    side(1)
    arc((w / 2 - rb, -h + rb), rb, 0, -90, nc)
    line((w / 2 - rb, -h), (-w / 2 + rb, -h), nr)
    arc((-w / 2 + rb, -h + rb), rb, -90, -180, nc)
    side(-1)
    arc((-w / 2 + rf, h - rf), rf, 180, 90, nc)
    line((-w / 2 + rf, h), (0, h), nfs)
    if taper != 1.0:
        pts = [(x * (1.0 - (1.0 - taper) * (h - y) / d), y) for x, y in pts]
    return [(cx + x, cf + y) for x, y in pts]


def inset(w, d, rf, rb, s, **kw):
    return contour(w - 2 * s, d - 2 * s, rf - s, rb - s, **kw)


def mesh_from_rings(name, rings, mat, cap0=True, cap1=True, smooth=True):
    """rings: list of lists of (x, up, fwd)"""
    L = _lib()
    vr = [[_V(*p) for p in r] for r in rings]
    verts, faces = L.ring_mesh(vr, cap0, cap1)
    ob = L.mk(name, verts, faces, mat, GRP, smooth=smooth)
    return ob


def keep(ob):
    _objs.append(ob)
    return ob


def prism_xz(name, pts_xu, f0, f1, mat, bev=None):
    """2D (x, up) polygon extruded along fwd"""
    L = _lib()
    return L.extrude(name, pts_xu, lambda u, v, w: _V(u, v, w), f0, f1, mat, GRP, bev=bev)


def prism_fu(name, pts_fu, x0, x1, mat, bev=None):
    """2D (fwd, up) polygon extruded along x"""
    L = _lib()
    return L.extrude(name, pts_fu, lambda u, v, w: _V(w, v, u), x0, x1, mat, GRP, bev=bev)


def prism_plan(name, pts_xf, u0, u1, mat, bev=None):
    """2D plan (x, fwd) polygon extruded along up"""
    L = _lib()
    return L.extrude(name, pts_xf, lambda u, v, w: _V(u, w, v), u0, u1, mat, GRP, bev=bev)


def frame_prism(name, outer, inner, mapf, w0, w1, mat):
    """closed frame (outer contour minus inner contour, same vertex count) extruded w0..w1"""
    L = _lib()
    n = len(outer)
    verts = [mapf(u, v, w0) for u, v in outer] + [mapf(u, v, w1) for u, v in outer]
    verts += [mapf(u, v, w0) for u, v in inner] + [mapf(u, v, w1) for u, v in inner]
    faces = []
    for j in range(n):
        k = (j + 1) % n
        faces.append((j, k, n + k, n + j))                    # outer wall
        faces.append((2 * n + k, 2 * n + j, 3 * n + j, 3 * n + k))  # inner wall
        faces.append((k, j, 2 * n + j, 2 * n + k))            # w0 annulus
        faces.append((n + j, n + k, 3 * n + k, 3 * n + j))    # w1 annulus
    return L.mk(name, verts, faces, mat, GRP, smooth=False)


def tube(name, path, r, mat, segs=16, cap=True):
    """circular tube along a product-coords path with parallel-transport frames"""
    L = _lib()
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
        rings.append([L.toB(path[i] + (Nn * math.cos(math.tau * j / segs) + B * math.sin(math.tau * j / segs)) * r)
                      for j in range(segs)])
    verts, faces = L.ring_mesh(rings, cap, cap)
    return L.mk(name, verts, faces, mat, GRP)


def rr2(w, h, r, cx=0.0, cy=0.0, n=None):
    L = _lib()
    return [(cx + x, cy + y) for x, y in L.rrect(w, h, r, n)]


def ellipse(a, b, cx=0.0, cy=0.0, n=48):
    return [(cx + a * math.cos(math.tau * i / n), cy + b * math.sin(math.tau * i / n)) for i in range(n)]


def boolean_cut(ob, cutters, reshade=True):
    """EXACT boolean difference; faces created by a cutter take the cutter's material (TRANSFER)."""
    L = _lib()
    flat = []
    for c in cutters:
        flat.extend(c if isinstance(c, list) else [c])
    cutters = flat
    for c in cutters:
        md = ob.modifiers.new("Cut", "BOOLEAN")
        md.operation = "DIFFERENCE"
        md.solver = "EXACT"
        md.object = c
        try:
            md.material_mode = "TRANSFER"
        except Exception:
            pass
        c.hide_render = True
        c.hide_viewport = True
    L.apply_modifiers(ob)
    for c in cutters:
        me = c.data
        bpy.data.objects.remove(c)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    if reshade:
        me = ob.data
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
    return ob


def join_cutters(cs, name):
    return cs


_LIB = {}


def _lib():
    return _LIB["lib"]


# ----------------------------------------------------------------------------------------------- parts
def build_plate(q):
    L = _lib()
    pd = PLATE_F - PLATE_R
    pcf = (PLATE_F + PLATE_R) / 2
    prf, prb = 0.066, 0.046
    stations = [(0.0018, 0.0015), (0.0006, 0.0020), (0.0, 0.0032), (0.0, 0.0050), (0.0022, 0.0080),
                (0.0040, 0.0091), (0.0052, PLATE_T)]
    rings = []
    for s, up in stations:
        c = inset(PLATE_W, pd, prf, prb, s, cf=pcf, q=q)
        rings.append([(x, up, f) for x, f in c])
    plate = mesh_from_rings("Dock_BasePlate", rings, "M_SageDeep")
    cut = []
    # U parking pocket: the floorhead neck plate + rear wheels stand on the floor inside the tongue [lead-approved,
    # floorhead footprint |x|<0.0635 back to fwd -0.126]
    cut.append(prism_plan("cut_park", contour(2 * PARK_HW, 0.10, 0.004, 0.012, cf=PARK_BACK + 0.05, q=0.7), -0.01, 0.03, "M_SageDeep"))
    # cord channel notch at the rear edge
    cut.append(prism_plan("cut_cordnotch", rr2(0.010, 0.020, 0.003, 0.0, PLATE_R, n=4), 0.0060, 0.03, "M_SageDeep"))
    boolean_cut(plate, [join_cutters(cut, "cut_plate")])
    keep(plate)
    # rubber feet
    for sx in (-1, 1):
        for f in (PLATE_F - 0.030, PLATE_R + 0.030):
            keep(L.lathe_up("Dock_Foot", [(0, 0.0), (0.0062, 0.0), (0.0068, 0.0006), (0.0068, 0.0017), (0, 0.0017)],
                            f, "M_Rubber", GRP, cx=sx * 0.084, segs=24))
    # accessory storage peg (right-rear corner) [manual p.6/17, 3241laa-01]
    peg = L.lathe_up("Dock_AccessoryPeg",
                     [(0, PLATE_T - 0.001), (0.0088, PLATE_T - 0.001), (0.0088, PLATE_T + 0.0015),
                      (0.0076, PLATE_T + 0.0028), (0.0076, 0.0215), (0.0071, 0.0222), (0.0071, 0.0238),
                      (0.0076, 0.0245), (0.0076, 0.0285), (0.0068, 0.0302), (0.0045, 0.0310), (0, 0.0311)],
                     -0.190, "M_SageDeep", GRP, cx=0.098, segs=40)
    keep(peg)


def build_plinth(q):
    L = _lib()
    w, d = TW + 0.0012, TD + 0.0012
    st = [(0.0, 0.0080), (0.0, 0.0300), (0.0, 0.1000), (0.0, PLINTH_TOP - 0.0030), (0.0006, PLINTH_TOP - 0.0010),
          (0.0020, PLINTH_TOP - 0.0001), (0.0040, PLINTH_TOP)]
    rings = []
    for s, up in st:
        c = inset(w, d, RF, RB, s, cf=TCF, q=q)
        rings.append([(x, up, f) for x, f in c])
    pl = mesh_from_rings("Dock_Plinth", rings, "M_SageDeep")
    front = TF + 0.0006
    rear = TR - 0.0006
    xr = w / 2
    cuts = []
    # front U-arch recess behind the floorhead neck [3241laa-01, manual p.6/17]
    aw, atop = 0.058, 0.148
    arch = [(-aw / 2, 0.0), (aw / 2, 0.0)]
    for i in range(0, 13):
        a = math.radians(0 + 180 * i / 12)
        arch.append((aw / 2 * math.cos(a), atop - aw / 2 + aw / 2 * math.sin(a)))
    arch = [arch[0], arch[1]] + arch[2:]
    cuts.append(prism_xz("cut_arch", arch, front - 0.010, front + 0.02, "M_SageDeep"))
    # right-side filter door: outline groove, diagonal grille slots, round button [manual p.6 side, p.19; AE video]
    df0, df1 = TCF - 0.017, TCF + 0.033          # door fwd span (side flat region)
    du0, du1 = 0.022, 0.166
    dcf, dcu = (df0 + df1) / 2, (du0 + du1) / 2
    outer = rr2(df1 - df0, du1 - du0, 0.010, dcf, dcu, n=6)
    inner = rr2(df1 - df0 - 0.0016, du1 - du0 - 0.0016, 0.0092, dcf, dcu, n=6)
    cuts.append(frame_prism("cut_door", outer, inner, lambda u, v, ww: _V(ww, v, u), xr - 0.0012, xr + 0.01, "M_Graphite"))
    slots = []
    gu0, gu1 = du0 + 0.010, du0 + 0.098
    gf0, gf1 = df0 + 0.010, df1 - 0.010
    pitch = 0.0062
    k = 0
    t = gf0 - (gu1 - gu0)
    while t < gf1:
        # 45 deg slot from (t, gu0) to (t + (gu1-gu0), gu1), clipped to the grille box
        a = (t, gu0)
        b = (t + (gu1 - gu0), gu1)
        # clip parametric
        t0 = max(0.0, (gf0 - a[0]) / (b[0] - a[0]))
        t1 = min(1.0, (gf1 - a[0]) / (b[0] - a[0]))
        if t1 - t0 > 0.12:
            p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            ln = math.hypot(dx, dy)
            ux, uy = dx / ln, dy / ln
            nx, ny = -uy, ux
            hw = 0.00125
            pts = []
            for i in range(7):
                aa = math.pi / 2 + math.pi * i / 6
                pts.append((p0[0] + hw * (math.cos(aa) * ux + math.sin(aa) * nx), p0[1] + hw * (math.cos(aa) * uy + math.sin(aa) * ny)))
            for i in range(7):
                aa = -math.pi / 2 + math.pi * i / 6
                pts.append((p1[0] + hw * (math.cos(aa) * ux + math.sin(aa) * nx), p1[1] + hw * (math.cos(aa) * uy + math.sin(aa) * ny)))
            slots.append(prism_fu("cut_slot", pts, xr - 0.0045, xr + 0.01, "M_Graphite"))
            k += 1
        t += pitch * math.sqrt(2)
    cuts.extend(slots)
    # button recess ring
    bcf, bcu = dcf + 0.012, du1 - 0.024
    cuts.append(prism_fu("cut_btn", ellipse(0.0118, 0.0118, bcf, bcu, 40), xr - 0.0020, xr + 0.01, "M_Graphite"))
    # rear power socket recess
    cuts.append(prism_xz("cut_socket", ellipse(0.0090, 0.0090, 0.0, 0.034, 32), rear - 0.01, rear + 0.0040, "M_Graphite"))
    boolean_cut(pl, [join_cutters(cuts, "cut_plinth")])
    keep(pl)
    # door push button
    keep(L.lathe("Dock_DoorButton", [(0, 0.0034), (0.0055, 0.0033), (0.0085, 0.0028), (0.0098, 0.0018), (0.0100, 0.0), (0.0, 0.0)],
                 (xr - 0.0018, bcu, bcf), (1, 0, 0), (0, 1, 0), "M_SageDeep", GRP, segs=40))
    # power plug + cord (separate object so the scene can hide it)
    plug = L.lathe("Dock_Plug", [(0, 0.0), (0.0068, 0.0), (0.0072, 0.0010), (0.0072, 0.0140), (0.0060, 0.0170),
                                 (0.0036, 0.0205), (0.0030, 0.0290), (0, 0.0290)],
                   (0.0, 0.034, rear + 0.0035), (0, 0, -1), (1, 0, 0), "M_Rubber", GRP, segs=32)
    keep(plug)
    path = L.bezier_path(Vector((0.0, 0.034, rear - 0.0280)), Vector((0.0, 0.034, rear - 0.060)),
                         Vector((0.004, 0.0029, rear - 0.050)), Vector((0.050, 0.0029, rear - 0.120)), 18)
    path2 = L.bezier_path(Vector((0.050, 0.0029, rear - 0.120)), Vector((0.066, 0.0029, rear - 0.190)),
                          Vector((0.140, 0.0029, rear - 0.230)), Vector((0.230, 0.0029, rear - 0.260)), 18)
    keep(tube("Dock_Cord", list(path) + list(path2)[1:], 0.0029, "M_Rubber", segs=16))


def build_ring():
    w, d = TW - 0.0010, TD - 0.0010
    rings = [[(x, up, f) for x, f in contour(w, d, RF - 0.0005, RB - 0.0005, cf=TCF)] for up in (RING0, RING1)]
    keep(mesh_from_rings("Dock_SeamRing", rings, "M_Chrome"))


HANDLE_F = -0.268                  # carry-handle slot centre (behind the post)


def top_h(fwd):
    if fwd >= SLOPE_F:
        return TOP_H
    t = min(1.0, (SLOPE_F - fwd) / (SLOPE_F - TR))
    return TOP_H - TOP_DROP * (t * t * (3 - 2 * t) * 0.35 + t * t * 0.65)


def build_bin(q):
    L = _lib()
    b0, b1 = RING1 + 0.0003, CAP_SEAM - 0.0004
    st = [(0.0016, b0), (0.0006, b0 + 0.0005), (0.0, b0 + 0.0016), (0.0, 0.230), (0.0, 0.330), (0.0, 0.420),
          (0.0, b1 - 0.0016), (0.0006, b1 - 0.0005), (0.0016, b1)]
    rings = []
    for s, up in st:
        c = inset(TW, TD, RF, RB, s, cf=TCF, notch=SEAM_Y - 0.0 if s == 0 else SEAM_Y, q=q)
        rings.append([(x, up, f) for x, f in c])
    body = mesh_from_rings("Dock_BinBody", rings, "M_Sage")
    xr = TW / 2
    cuts = []
    # dust-bin window recess (right side) [H1, manual p.16 'dust bin window']
    wu0, wu1 = WIN_UP
    cuts.append(prism_fu("cut_win", rr2(0.0118, wu1 - wu0, 0.0055, WIN_F, (wu0 + wu1) / 2, n=8), xr - 0.0030, xr + 0.01, "M_Graphite"))
    boolean_cut(body, cuts)
    keep(body)
    # smoked window insert + fill line
    win = prism_fu("Dock_BinWindow", rr2(0.0104, wu1 - wu0 - 0.0014, 0.0048, WIN_F, (wu0 + wu1) / 2, n=8),
                   xr - 0.0024, xr - 0.0007, "M_ClearSmoke")
    L.bevel(win, 0.0005, 2)
    keep(win)
    fill = prism_fu("Dock_BinFillLine", rr2(0.0050, 0.0007, 0.0003, WIN_F + 0.0005, wu1 - 0.040, n=2),
                    xr - 0.0012, xr - 0.0005, "M_Sage")
    keep(fill)
    # rear canister latch (pocket + tab) and lower tab [rt-ia3241-in-the-box canister face; manual side views]
    keep(rear_latch(0.318))
    tb = prism_xz("Dock_RearTab", rr2(0.022, 0.0065, 0.0028, 0.0, 0.228, n=6), TR - 0.0050, TR + 0.002, "M_Sage")
    L.bevel(tb, 0.0008, 2)
    keep(tb)


def rear_latch(up):
    """latch pocket cut into a small raised pad on the canister rear, with a hooked tab inside"""
    L = _lib()
    pad = prism_xz("Dock_RearLatch", rr2(0.034, 0.034, 0.006, 0.0, up, n=6), TR - 0.0030, TR + 0.002, "M_Sage")
    boolean_cut(pad, [prism_xz("cut_latch", rr2(0.024, 0.024, 0.004, 0.0, up + 0.001, n=6), TR - 0.01, TR - 0.0005, "M_SageDeep")])
    tab = prism_xz("Dock_RearLatchTab", rr2(0.016, 0.006, 0.0022, 0.0, up - 0.004, n=4), TR - 0.0040, TR, "M_SageDeep")
    L.bevel(tab, 0.0006, 2)
    keep(tab)
    return pad


def build_cap(q):
    L = _lib()
    c0 = CAP_SEAM + 0.0004
    re = 0.016
    rings = []

    def ring(s, upf):
        c = inset(TW, TD, RF, RB, s, cf=TCF, q=q)
        return [(x, upf(f), f) for x, f in c]

    rings.append(ring(0.0016, lambda f: c0))
    rings.append(ring(0.0006, lambda f: c0 + 0.0005))
    rings.append(ring(0.0, lambda f: c0 + 0.0016))
    for k in range(0, 7):
        ph = (math.pi / 2) * k / 6
        s = re * (1 - math.cos(ph))
        rings.append(ring(s, lambda f, ph=ph: top_h(f) - re + re * math.sin(ph)))
    for s in (0.0195, 0.025, 0.032, 0.041, 0.051, 0.062, 0.072, 0.080):
        rings.append(ring(s, lambda f: top_h(f)))
    cap = mesh_from_rings("Dock_TopCap", rings, "M_Sage")
    cuts = []
    # notch where the charging post passes through the cap (0.8 mm seam gap)
    pc = contour(PW + 0.0016, PD + 0.0016, PR + 0.0008, PR + 0.0008, cf=PCF, q=q)
    cuts.append(prism_plan("cut_post", pc, CAP_SEAM - 0.01, TOP_H + 0.02, "M_Sage"))
    # carry-handle slot (finger recess, dark) [manual p.17 'lift it out by the handle']
    hs = [(x, f) for x, f in rr2(0.0195, 0.058, 0.0097, -0.010, HANDLE_F, n=8)]
    cuts.append(prism_plan("cut_handle", hs, TOP_H - 0.013, TOP_H + 0.02, "M_SageDeep"))
    # bin/evacuate button recess ring
    cuts.append(prism_plan("cut_topbtn", ellipse(0.0078, 0.0078, 0.041, TF - 0.100, 32), TOP_H - 0.0016, TOP_H + 0.02, "M_SageDeep"))
    # (UK-only anti-odour dial omitted: US IA3000 guide has no dial) [TECHNICAL_REFERENCE 6.4]
    boolean_cut(cap, [join_cutters(cuts, "cut_cap")])
    keep(cap)
    # handle grip bar across the slot (lets the slot read as a handle)
    bar = L.sweep("Dock_HandleBar", [Vector((-0.010, TOP_H - 0.0045, HANDLE_F + 0.024)), Vector((-0.010, TOP_H - 0.0045, HANDLE_F - 0.024))],
                  lambda t: (0.0150, 0.0050, 0.0022), "M_SageDeep", GRP)
    keep(bar)
    # top button
    keep(L.lathe_up("Dock_TopButton", [(0, TOP_H + 0.0020), (0.0040, TOP_H + 0.0018), (0.0060, TOP_H + 0.0010),
                                       (0.0066, TOP_H - 0.0003), (0.0066, TOP_H - 0.0016), (0, TOP_H - 0.0016)],
                    TF - 0.100, "M_SageDeep", GRP, cx=0.041, segs=32))


def build_post_and_cradle(q):
    L = _lib()
    post = contour(PW, PD, PR, PR, cf=PCF, q=q)
    cup = contour(CW, CD, 0.014, 0.022, cf=CCF, q=q, taper=CUP_TAPER)
    n = len(post)
    ups = [CAP_SEAM - 0.010, 0.560, 0.650, 0.720, FLARE_F - 0.004]
    ups += [FLARE_F + (CUP_SEAM - 0.0012 - FLARE_F) * (i / 16) for i in range(1, 17)]
    rings = []

    def flare_pt(i, up):
        a = (cup[i][1] - (CCF - CD / 2)) / CD          # 0 rear .. 1 front
        hb = FLARE_R + (FLARE_F - FLARE_R) * a
        top = CUP_SEAM - 0.0012
        t = 0.0 if up <= hb else min(1.0, (up - hb) / (top - hb))
        f = 1 - math.cos(t * math.pi / 2)
        f = f ** 1.25
        return (post[i][0] + (cup[i][0] - post[i][0]) * f, post[i][1] + (cup[i][1] - post[i][1]) * f)

    for up in ups:
        rings.append([(p[0], up, p[1]) for p in (flare_pt(i, up) for i in range(n))])
    # small top round-over into the parting line
    for s, du in ((0.0006, -0.0004), (0.0016, 0.0)):
        c = contour(CW - 2 * s, CD - 2 * s, 0.014 - s, 0.022 - s, cf=CCF, q=q, taper=CUP_TAPER)
        rings.append([(x, CUP_SEAM - 0.0004 + du, f) for x, f in c])
    br = mesh_from_rings("Dock_PostBracket", rings, "M_Sage")

    # cradle cup shell: outer wall -> rounded rim -> inner wall -> floor
    t = CUP_T
    outer = cup
    innr = contour(CW - 2 * t, CD - 2 * t, 0.014 - t, 0.022 - t, cf=CCF, q=q, taper=CUP_TAPER)
    flo = contour(CW - 2 * t - 0.004, CD - 2 * t - 0.004, 0.014 - t - 0.002, 0.022 - t - 0.002, cf=CCF, q=q, taper=CUP_TAPER)

    def rim(f, x=0.0):
        a = ((CCF + CD / 2) - f) / CD      # 0 front .. 1 rear
        a = max(0.0, min(1.0, a))
        a = a * a * (3 - 2 * a)
        ax = abs(x)
        wx = 1.0 if ax <= WING_HW else max(0.0, 1.0 - (ax - WING_HW) / 0.0105)
        wx = wx * wx * (3 - 2 * wx)
        dip = 0.019 * math.sin(math.pi * min(1.0, a / 0.92)) ** 1.5    # side walls dip between front ear and rear wing [harbor cradle]
        return RIM_F - dip * (1 - wx) + ((RIM_R - RIM_F) * a) * wx

    c0 = CUP_SEAM + 0.0004
    crings = []
    for s, du in ((0.0016, 0.0), (0.0006, 0.0005), (0.0, 0.0016)):
        c = contour(CW - 2 * s, CD - 2 * s, 0.014 - s, 0.022 - s, cf=CCF, q=q, taper=CUP_TAPER)
        crings.append([(x, c0 + du, f) for x, f in c])
    for k in (0.25, 0.5, 0.75):
        crings.append([(x, c0 + 0.0016 + (rim(f, x) - t / 2 - c0 - 0.0016) * k, f) for x, f in outer])
    for k in range(0, 9):
        ph = math.pi * k / 8
        bl = (1 - math.cos(ph)) / 2
        r = []
        for i in range(n):
            x = outer[i][0] + (innr[i][0] - outer[i][0]) * bl
            f = outer[i][1] + (innr[i][1] - outer[i][1]) * bl
            r.append((x, rim(f, x) - t / 2 + (t / 2) * math.sin(ph), f))
        crings.append(r)
    for k in (0.35, 0.75):
        crings.append([(x, rim(f, x) - t / 2 - (rim(f, x) - t / 2 - CUP_FLOOR - 0.002) * k, f) for x, f in innr])
    crings.append([(x, CUP_FLOOR + 0.0012, f) for x, f in innr])
    crings.append([(x, CUP_FLOOR, f) for x, f in flo])
    cupm = mesh_from_rings("Dock_CradleCup", crings, "M_Sage")

    # open wand channel through bracket + cup front [hero: wings either side of the dark upper wand]
    def notch():
        return prism_plan("cut_notch", contour(2 * NOTCH_HW, 0.10, 0.0012, 0.008, cf=NOTCH_BACK + 0.05, q=0.6),
                          0.70, 0.95, "M_Sage")
    # evacuation port: oval through the cup floor into a dark well in the bracket
    port_a, port_b, port_f = 0.0205, 0.0170, CCF - 0.017
    boolean_cut(br, [notch(), prism_plan("cut_portwell", ellipse(port_a, port_b, 0.0, port_f, 56), CUP_SEAM - 0.030,
                                         CUP_SEAM + 0.02, "M_Graphite")])
    hhcut = prism_plan("cut_hh", contour(2 * HH_HW, 0.10, 0.0012, 0.006, cf=NOTCH_BACK + 0.05, q=0.6), 0.812, 0.95, "M_Sage")
    cuts = [notch(), hhcut, prism_plan("cut_port", ellipse(port_a, port_b, 0.0, port_f, 56), CUP_SEAM - 0.01, CUP_FLOOR + 0.01, "M_Graphite")]
    # quiet-mode switch recess on the rear face [manual p.16 'Quiet mode']
    sw_up = 0.856
    cuts.append(prism_xz("cut_switch", rr2(0.032, 0.0205, 0.0055, 0.0, sw_up, n=6), CCF - CD / 2 - 0.01,
                         CCF - CD / 2 + 0.0022, "M_Graphite"))
    boolean_cut(cupm, [join_cutters(cuts, "cut_cup")])
    keep(br)
    keep(cupm)
    # port seal (rubber lip, elliptical)
    def ell(th, h, r):
        e = 1.0 / math.sqrt((math.cos(th) / 1.0) ** 2 + (math.sin(th) / (port_b / port_a)) ** 2)
        return r * e
    keep(L.lathe("Dock_PortSeal", [(1.0, 0.0), (1.12, 0.0), (1.20, 0.0012), (1.20, 0.0026), (1.12, 0.0032),
                                   (1.02, 0.0030), (0.97, 0.0010), (0.97, -0.004), (1.0, -0.004)],
                 (0.0, CUP_FLOOR, port_f), (0, 1, 0), (1, 0, 0), "M_Rubber", GRP, segs=72,
                 rmod=lambda th, h, r: ell(th, h, r) * port_a, cap0=False, cap1=False, closed=True))
    # port flap / grate (dark) a little below the seal
    keep(L.lathe("Dock_PortFlap", [(0, -0.006), (0.98, -0.006), (0.98, -0.0075), (0, -0.0075)],
                 (0.0, CUP_FLOOR, port_f), (0, 1, 0), (1, 0, 0), "M_Graphite", GRP, segs=56,
                 rmod=lambda th, h, r: ell(th, h, r) * port_a))
    # charging contact block on the inner rear wall + two pins
    ri = CCF - CD / 2 + t
    blk = prism_xz("Dock_ContactBlock", rr2(0.028, 0.0095, 0.003, 0.0, 0.8445, n=5), ri - 0.0003, ri + 0.0035, "M_Graphite")
    L.bevel(blk, 0.0007, 2)
    keep(blk)
    for sx in (-1, 1):
        keep(L.lathe("Dock_ContactPin", [(0, 0.0048), (0.0012, 0.0046), (0.0016, 0.0040), (0.0016, 0.0), (0, 0.0)],
                     (sx * 0.0070, 0.8445, ri + 0.0030), (0, 0, 1), (1, 0, 0), "M_Chrome", GRP, segs=20))
    keep(L.lathe("Dock_CradleScrew", [(0, 0.0012), (0.0016, 0.0011), (0.0022, 0.0006), (0.0024, 0.0), (0, 0.0)],
                 (0.0, 0.872, ri), (0, 0, 1), (1, 0, 0), "M_Graphite", GRP, segs=20))
    # quiet switch slider + grip ridges
    ro = CCF - CD / 2
    sl = prism_xz("Dock_QuietSwitch", rr2(0.023, 0.0145, 0.0035, -0.004, sw_up, n=5), ro + 0.0008, ro + 0.0024, "M_Graphite")
    L.bevel(sl, 0.0006, 2)
    keep(sl)
    for dx in (-0.0085, 0.0005):
        rg = prism_xz("Dock_QuietRidge", rr2(0.0022, 0.0100, 0.0010, -0.004 + dx + 0.004, sw_up, n=3), ro + 0.0002, ro + 0.0009, "M_Graphite")
        keep(rg)
    # moon icon decal plate above the switch (M_Decal atlas cell, see notes)
    du, dv = 0.0085, 0.0085
    z = ro - 0.00025
    cxu = sw_up + 0.0215
    mx = 0.0
    verts = [_V(mx + du / 2, cxu - dv / 2, z), _V(mx - du / 2, cxu - dv / 2, z), _V(mx - du / 2, cxu + dv / 2, z), _V(mx + du / 2, cxu + dv / 2, z)]
    # faces the rear (-fwd); seen from behind, image-right is product -x, so u grows toward -x
    uvs = [(0.875, 0.0), (1.0, 0.0), (1.0, 0.125), (0.875, 0.125)]
    dec = L.mk("Dock_DecalMoon", verts, [(0, 1, 2, 3)], "M_Decal", GRP, smooth=False, uvs=uvs, recalc=False)
    keep(dec)


# ----------------------------------------------------------------------------------------------- entry
def build(ctx):
    global _objs, _lights
    _objs, _lights = [], []
    _LIB["lib"] = ctx["lib"]
    P = ctx["P"]
    q = 1.0 if ctx.get("tier", "high") == "high" else 0.45
    assert abs(P.WAND_FWD - (-0.100)) < 0.03, "dock layout assumes the wand axis near fwd -0.100"
    build_plate(q)
    build_plinth(q)
    build_ring()
    build_bin(q)
    build_cap(q)
    build_post_and_cradle(q)
    for o in _objs:
        o["grp"] = GRP
    notes = ("Dock (Clean & Empty, US variant: no odour dial) in product frame. Tower 171W x 172D, front fwd %.3f, rear %.3f, "
             "top %.3f; plinth to %.3f. Base plate fwd %.3f..%.3f (L = head front +0.044 -> %.0f mm), with a U parking pocket "
             "|x|<%.4f back to fwd %.4f so the floorhead neck plate + rear wheels stand on the floor (no intersection; checked by BVH). "
             "Charging post %.0f x %.0f mm rises from the tower front; cradle cup inner floor %.3f (handheld bottom 0.835), "
             "front saddle rim %.3f, rear wing %.3f (only |x|<%.3f); open wand channel |x|<%.3f back to fwd %.4f, handheld channel "
             "|x|<%.4f above 0.812. Evacuation port (oval seal) in the cup floor, contact block + 2 pins on the inner rear wall, "
             "Quiet slider + moon icon on the cradle rear face. No dock LED in any reference -> no DockLights. No Shark badge on "
             "the dock in references -> none. M_Decal: Dock_DecalMoon uses atlas cell u 0.875-1.0, v 0.0-0.125 (moon icon, "
             "white on transparent, upright). Dock_Cord (+Dock_Plug) are separate meshes and can be hidden."
             % (TF, TR, TOP_H, PLINTH_TOP, PLATE_F, PLATE_R, (0.044 - PLATE_R) * 1000, PARK_HW, PARK_BACK, PW * 1000, PD * 1000,
                CUP_FLOOR, RIM_F, RIM_R, WING_HW, NOTCH_HW, NOTCH_BACK, HH_HW))
    return {"groups": {"Dock": list(_objs)}, "special": {"DockLights": list(_lights)} if _lights else {},
            "anchors": {}, "notes": notes}
