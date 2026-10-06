"""
Procedural reconstruction of the Shark PowerDetect stick vacuum (IP1251EUT working assumption).

Run (headless):
  Blender -b --factory-startup -P scripts/blender/build_powerdetect.py -- [--tier all|high|balanced] [--no-export]

Outputs (relative to project root):
  assets/source/powerdetect.blend         editable source (high tier, parts unjoined, modifiers live)
  assets/source/textures/roller_front.png baked stripe texture for the DuoClean soft roller
  public/models/powerdetect-high.glb      ~120k-220k tris
  public/models/powerdetect-balanced.glb  ~50k-100k tris, identical node names/hierarchy
  public/models/rig.json                  measured nozzle geometry, pivots, anchors, bounds
  assets/source/build_report.json         per-tier tri counts / material list (consumed by assets-build.mjs)

Authoring frame: Blender Z-up, product front = Blender -Y. The glTF exporter (+Y up) maps Blender (x,y,z) to
glTF (x, z, -y) so the head front becomes glTF +Z, as required by src/contracts/world.ts.
All dimensions come from scripts/blender/params.py (measurement ledger).
"""
import bpy
import bmesh
import math
import os
import sys
import json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import importlib
import params as P

importlib.reload(P)

TAU = math.tau
D = P.DETAIL["high"]  # replaced per tier in build()
MATS = {}


# =====================================================================================  coordinates
def V(x, up, fwd):
    """product coords (x, up, fwd) -> Blender vector"""
    return Vector((x, -fwd, up))


def PV(x, up, fwd):
    return Vector((x, up, fwd))


def toB(p):
    return Vector((p[0], -p[2], p[1]))


# =====================================================================================  materials
def srgb2lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def principled(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    return m, nt, bsdf


def make_materials(roller_img):
    MATS.clear()
    for name, (rgb, rough, metal) in P.COLORS.items():
        m, nt, b = principled(name)
        b.inputs["Base Color"].default_value = (*[srgb2lin(c) for c in rgb], 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if name == "M_LED":
            b.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
            b.inputs["Emission Strength"].default_value = 1.0
        if name == "M_LightStrip":
            b.inputs["Emission Color"].default_value = (*[srgb2lin(c) for c in rgb], 1.0)
            b.inputs["Emission Strength"].default_value = 0.6
        if name == "M_Screen":
            b.inputs["Coat Weight"].default_value = 1.0
            b.inputs["Coat Roughness"].default_value = 0.03
        MATS[name] = m
    for name, rough, tint in (("M_ClearBin", 0.03, (0.97, 0.975, 0.98)), ("M_ClearCover", 0.05, (0.94, 0.95, 0.955))):
        m, nt, b = principled(name)
        b.inputs["Base Color"].default_value = (*tint, 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.49
        m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else None
        MATS[name] = m
    # front soft roller: baked stripe texture
    m, nt, b = principled("M_RollerFront")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = roller_img
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Sheen Weight"].default_value = 0.0
    MATS["M_RollerFront"] = m


def make_roller_texture(path, w=1024, h=512):
    """U = around circumference, V = along roller axis. Black microfiber with 4 groups of 3 turquoise
    tilted ring stripes, mirrored about the center so the front view reads as a chevron (V1/V5)."""
    import numpy as np

    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    U, Vv = np.meshgrid(u, v)  # shape (h, w)
    L = P.ROLLER_F_LEN
    x = (Vv - 0.5) * L
    th = U * TAU
    col = np.zeros((h, w, 3))
    base = np.array([srgb2lin(21), srgb2lin(22), srgb2lin(23)])
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, (h, w)) * 0.004
    col[:] = base
    col += noise[..., None]
    turq = np.array([srgb2lin(c) for c in P.ROLLER_STRIPE])
    mask = np.zeros((h, w))
    A = 0.011
    for xc in (-0.068, -0.024, 0.024, 0.068):
        sgn = 1.0 if xc > 0 else -1.0
        for off in (-0.0062, 0.0, 0.0062):
            xl = xc + off + sgn * A * np.sin(th)
            d = np.abs(x - xl)
            hw = 0.0016
            aa = 0.0005
            mask = np.maximum(mask, np.clip((hw + aa - d) / (2 * aa), 0, 1))
    fib = 0.85 + 0.15 * rng.random((h, w))
    col = col * (1 - mask[..., None]) + (turq * fib[..., None]) * mask[..., None]
    col = np.clip(col, 0, 1)
    # to sRGB for storage
    srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(col, 1 / 2.4) - 0.055)
    rgba = np.concatenate([srgb, np.ones((h, w, 1))], axis=2).astype(np.float32)
    img = bpy.data.images.new("roller_front", w, h, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.pack()
    return img


# =====================================================================================  mesh helpers
COLL = None


def link(ob):
    COLL.objects.link(ob)
    return ob


def mk(name, verts, faces, mat, grp, smooth=True, uvs=None, recalc=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    if uvs is not None:
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = uvs[vi]
    me.validate()
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    if smooth:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
    else:
        me.shade_flat()
    me.materials.append(MATS[mat])
    ob = link(bpy.data.objects.new(name, me))
    ob["grp"] = grp
    return ob


def bevel(ob, width, seg=None, angle=35):
    md = ob.modifiers.new("Bevel", "BEVEL")
    md.width = width
    md.segments = seg if seg is not None else D["bevel_seg"]
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(angle)
    md.use_clamp_overlap = True
    md.harden_normals = False
    return ob


def ring_mesh(rings, cap0=True, cap1=True, closed_loop=False):
    """rings: list of lists (same count) of Blender Vectors (closed loops). Returns verts, faces."""
    n = len(rings[0])
    verts, faces = [], []
    for r in rings:
        verts.extend(r)
    R = len(rings)
    for i in range(R - 1 + (1 if closed_loop else 0)):
        a = i * n
        b = ((i + 1) % R) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if not closed_loop:
        if cap0:
            c = sum(rings[0], Vector()) / n
            verts.append(c)
            ci = len(verts) - 1
            for j in range(n):
                faces.append((ci, (j + 1) % n, j))
        if cap1:
            c = sum(rings[-1], Vector()) / n
            verts.append(c)
            ci = len(verts) - 1
            a = (R - 1) * n
            for j in range(n):
                faces.append((ci, a + j, a + (j + 1) % n))
    return verts, faces


def rrect(w, d, r, n=None):
    n = n or D["corner"]
    r = max(1e-4, min(r, w / 2 - 1e-5, d / 2 - 1e-5))
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def fillet(pts, rad, n=None):
    n = n or D["corner"]
    out = []
    N = len(pts)
    for i in range(N):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % N])
        r = rad[i] if isinstance(rad, (list, tuple)) else rad
        d1 = p0 - p1
        d2 = p2 - p1
        l1, l2 = d1.length, d2.length
        d1.normalize()
        d2.normalize()
        ang = d1.angle(d2)
        if r <= 0 or ang < 1e-3 or ang > math.pi - 1e-3:
            out.append(tuple(p1))
            continue
        t = r / math.tan(ang / 2)
        t = min(t, 0.48 * l1, 0.48 * l2)
        r = t * math.tan(ang / 2)
        a = p1 + d1 * t
        b = p1 + d2 * t
        bis = (d1 + d2).normalized()
        c = p1 + bis * (r / math.sin(ang / 2))
        a0 = math.atan2(a.y - c.y, a.x - c.x)
        a1 = math.atan2(b.y - c.y, b.x - c.x)
        da = (a1 - a0 + math.pi) % TAU - math.pi
        for k in range(n + 1):
            aa = a0 + da * k / n
            out.append((c.x + r * math.cos(aa), c.y + r * math.sin(aa)))
    return out


def catmull(pts, per=8, closed=False):
    pts = [Vector(p) for p in pts]
    out = []
    N = len(pts)
    rng = range(N) if closed else range(N - 1)
    for i in rng:
        p0 = pts[(i - 1) % N] if closed else pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[(i + 1) % N]
        p3 = pts[(i + 2) % N] if closed else pts[min(i + 2, N - 1)]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(pts[-1])
    return [tuple(p) for p in out]


def hull2d(points):
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def offset_polyline(pts, d):
    """offset an open 2D polyline by d along its left normal"""
    out = []
    N = len(pts)
    for i in range(N):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, N - 1)])
        t = (b - a).normalized()
        nrm = Vector((-t.y, t.x))
        out.append(tuple(Vector(pts[i]) + nrm * d))
    return out


def extrude(name, pts2d, mapf, w0, w1, mat, grp, bev=None, bev_seg=None, smooth=True):
    """prism: 2D polygon (u,v) extruded along w; mapf(u,v,w)->Blender Vector"""
    n = len(pts2d)
    verts = [mapf(u, v, w0) for u, v in pts2d] + [mapf(u, v, w1) for u, v in pts2d]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((j, j2, n + j2, n + j))
    ob = mk(name, verts, faces, mat, grp, smooth=smooth)
    if bev:
        bevel(ob, bev, bev_seg)
    return ob


def lathe(name, prof, origin, axis, ref, mat, grp, segs=None, cap0=True, cap1=True, closed=False, rmod=None, arc=None):
    """revolve prof [(r,h)] about axis through origin (product coords). theta=0 along ref."""
    segs = segs or D["lathe"]
    A = Vector(axis).normalized()
    U = Vector(ref).normalized()
    W = A.cross(U)
    O = Vector(origin)
    rings = []
    for r, h in prof:
        ring = []
        for j in range(segs):
            th = TAU * j / segs
            rr = rmod(th, h, r) if rmod else r
            p = O + A * h + (U * math.cos(th) + W * math.sin(th)) * rr
            ring.append(toB(p))
        rings.append(ring)
    verts, faces = ring_mesh(rings, cap0, cap1, closed_loop=closed)
    return mk(name, verts, faces, mat, grp)


UPA, FWDA, XA = (0, 1, 0), (0, 0, 1), (1, 0, 0)


def lathe_up(name, prof, cfwd, mat, grp, cx=0.0, **kw):
    return lathe(name, prof, (cx, 0, cfwd), UPA, FWDA, mat, grp, **kw)


def lathe_x(name, prof, cup, cfwd, mat, grp, **kw):
    return lathe(name, prof, (0, cup, cfwd), XA, FWDA, mat, grp, **kw)


def loft_up(name, stations, mat, grp, cap_round=0.0, n=None, sec=None):
    """stations: [(up, w, d, r, cfwd)] rounded-rect sections stacked along up. cap_round adds rounded ends."""
    n = n or D["corner"]
    rings = []

    def ring(up, w, d, r, cf, inset=0.0):
        pts = sec(w - 2 * inset, d - 2 * inset) if sec else rrect(w - 2 * inset, d - 2 * inset, max(r - inset, 0.0006), n)
        return [V(px, up, cf + py) for px, py in pts]

    st = [list(x) for x in stations]
    steps = 3 if cap_round > 0 else 0
    if steps:
        # rounded ends stay inside the station range: first/last station rings move inward by cap_round
        st[0][0] += cap_round
        st[-1][0] -= cap_round
        up, w, d, r, cf = st[0]
        for k in range(steps, 0, -1):
            ph = (math.pi / 2) * k / steps
            rings.append(ring(up - cap_round * math.sin(ph), w, d, r, cf, cap_round * (1 - math.cos(ph))))
    for s_ in st:
        rings.append(ring(*s_))
    if steps:
        up, w, d, r, cf = st[-1]
        for k in range(1, steps + 1):
            ph = (math.pi / 2) * k / steps
            rings.append(ring(up + cap_round * math.sin(ph), w, d, r, cf, cap_round * (1 - math.cos(ph))))
    # fix rounded-end ordering: start rings must be at or above the first station (inside the body)
    verts, faces = ring_mesh(rings, True, True)
    return mk(name, verts, faces, mat, grp)


def sweep(name, path, secf, mat, grp, cap_round=0.0, lateral=(1, 0, 0)):
    """sweep a section along a path in product coords. secf(t)->(w,h,r); w along `lateral`."""
    path = [Vector(p) for p in path]
    Bv = Vector(lateral)
    N = len(path)
    rings = []

    def frame(i):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, N - 1)]
        T = (b - a).normalized()
        Nn = T.cross(Bv).normalized()
        return T, Nn

    def ring_at(c, T, Nn, w, h, r, inset=0.0):
        pts = rrect(w - 2 * inset, h - 2 * inset, max(r - inset, 0.0006))
        return [toB(c + Bv * px + Nn * py) for px, py in pts]

    steps = 3 if cap_round > 0 else 0
    T0, N0 = frame(0)
    w, h, r = secf(0.0)
    for k in range(steps, 0, -1):
        ph = (math.pi / 2) * k / steps
        rings.append(ring_at(path[0] - T0 * cap_round * math.sin(ph), T0, N0, w, h, r, cap_round * (1 - math.cos(ph))))
    for i, c in enumerate(path):
        T, Nn = frame(i)
        w, h, r = secf(i / (N - 1))
        rings.append(ring_at(c, T, Nn, w, h, r))
    T1, N1 = frame(N - 1)
    w, h, r = secf(1.0)
    for k in range(1, steps + 1):
        ph = (math.pi / 2) * k / steps
        rings.append(ring_at(path[-1] + T1 * cap_round * math.sin(ph), T1, N1, w, h, r, cap_round * (1 - math.cos(ph))))
    verts, faces = ring_mesh(rings, True, True)
    return mk(name, verts, faces, mat, grp)


def bezier_path(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return out


def nseg(base):
    return max(4, int(round(base * D["path"])))


# =====================================================================================  floorhead
def build_floorhead():
    G = "FloorHead"
    xi = P.HEAD_INNER_HALF
    xo = P.HEAD_HALF_W - 0.0047  # grey body face; purple panel + button reach the published 0.263 width
    Rf, Ff = P.ROLLER_F_R, P.ROLLER_F_FWD
    Fr = P.HEAD_FRONT
    side_map = lambda u, v, w: V(w, v, u)

    # --- side bodies (grey) with purple teardrop panels, turquoise button (right only, V9) and edge-sensor slot
    side = [(Fr - 0.004, 0.004), (Fr, 0.030), (Fr - 0.016, 0.052), (-0.040, 0.064), (P.HEAD_REAR - 0.002, 0.050), (P.HEAD_REAR + 0.004, 0.004)]
    side_pts = fillet(side, [0.010, 0.016, 0.040, 0.030, 0.020, 0.006], max(6, D["corner"] + 2))
    c1, r1 = (0.042, 0.025), 0.0125
    c2, r2 = (-0.023, 0.034), 0.0235
    circ = [(c[0] + rr * math.cos(a * TAU / 48), c[1] + rr * math.sin(a * TAU / 48)) for c, rr in ((c1, r1), (c2, r2)) for a in range(48)]
    tear = hull2d([(round(p[0], 6), round(p[1], 6)) for p in circ])
    for s, tag in ((1, "R"), (-1, "L")):
        extrude(f"HeadSide_{tag}", side_pts, side_map, s * xi, s * xo, "M_Housing", G, bev=0.0085, bev_seg=max(4, D["bevel_seg"] + 1))
        extrude(f"HeadSidePanel_{tag}", tear, side_map, s * (xo - 0.0006), s * (xo + 0.0013), "M_Purple", G, bev=0.0008, bev_seg=2)
        btn_mat = "M_Turquoise" if s > 0 else "M_Purple"
        lathe(f"HeadSideButton_{tag}", [(0.0082, 0.0), (0.0082, 0.0024), (0.0072, 0.0037), (0.0040, 0.0043)], (s * (xo + 0.0009), c1[1], c1[0]), (s, 0, 0), FWDA, btn_mat, G, segs=max(24, D["lathe"] // 2))
        slot = fillet([(-0.059, 0.0268), (-0.047, 0.0268), (-0.047, 0.0330), (-0.059, 0.0330)], 0.003)
        extrude(f"HeadSideSlot_{tag}", slot, side_map, s * (xo - 0.0004), s * (xo + 0.0006), "M_HousingDark", G)
        # front corner blocks carrying the LED windows
        blk = fillet([(0.044, 0.045), (0.060, 0.040), (Fr - 0.0015, 0.050), (Fr - 0.005, 0.067), (0.043, 0.071)], [0.002, 0.004, 0.003, 0.004, 0.003])
        extrude(f"HeadCorner_{tag}", blk, side_map, s * 0.0802, s * (xi + 0.0004), "M_Housing", G, bev=0.0012, bev_seg=2)
        rail = fillet([(0.044, 0.067), (0.043, 0.071), (0.010, 0.0768), (-0.026, 0.0705), (-0.026, 0.0655), (0.010, 0.0722)], 0.002)
        extrude(f"HeadRail_{tag}", rail, side_map, s * 0.0802, s * (xi + 0.0004), "M_Housing", G, bev=0.001, bev_seg=2)
        lathe_x(f"RollerFrontBearing_{tag}", [(0.0105, s * (P.ROLLER_F_LEN / 2 + 0.0002)), (0.0105, s * (xi + 0.0002))], Rf, Ff, "M_HousingDark", G, segs=32)
        lathe_x(f"RollerRearBearing_{tag}", [(0.008, s * (P.ROLLER_R_LEN / 2 + 0.0002)), (0.008, s * (xi + 0.0002))], P.ROLLER_R_R + 0.001, P.ROLLER_R_FWD, "M_HousingDark", G, segs=24)

    # --- LED windows (white trapezoids on the corner block fronts) -> HeadLights
    leds = []
    for s, tag in ((1, "R"), (-1, "L")):
        trap = [(s * 0.0855, 0.0515), (s * 0.0965, 0.0515), (s * 0.0980, 0.0610), (s * 0.0840, 0.0610)]
        if s < 0:
            trap = trap[::-1]
        verts = []
        for depth in (-0.0018, 0.0009):
            for x, up in trap:
                ff = (Fr - 0.0015) - (up - 0.050) * (0.0035 / 0.017) + depth
                verts.append(V(x, up, ff))
        faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        leds.append(mk(f"LED_{tag}", verts, faces, "M_LED", "HeadLights", smooth=False))

    # --- clear cover (curved shell, 2.2 mm) over the front roller
    outer = catmull([(Fr - 0.0045, 0.014), (Fr - 0.0015, 0.034), (Fr - 0.006, 0.055), (0.050, 0.0695), (0.024, 0.0762), (-0.004, 0.0752), (-0.026, 0.0685)], per=nseg(8))
    inner = offset_polyline(outer, 0.0022)  # left normal of this front->rear polyline points inward
    extrude("HeadCover", outer + inner[::-1], side_map, -0.0800, 0.0800, "M_ClearCover", G)
    # dark label plate on the cover front (blank: no reproduced lettering)
    seg = catmull([p for p in outer if 0.036 <= p[1] <= 0.047], per=2)
    lo = offset_polyline(seg, -0.00015)
    hi = offset_polyline(seg, -0.0009)
    extrude("HeadLabelPlate", lo + hi[::-1], side_map, -0.035, 0.035, "M_HousingDark", G, bev=0.0004, bev_seg=1)
    # thin purple light strip along the rear edge of the roller window (V3/V5)
    ls = fillet([(-0.0215, 0.0690), (-0.0175, 0.0715), (-0.0185, 0.0735), (-0.0230, 0.0712)], 0.0006, 2)
    extrude("HeadLightStrip", ls, side_map, -0.079, 0.079, "M_LightStrip", G)

    # --- chassis tub (dark): wraps behind the front roller and arches over the rear brushroll
    pts = []
    for k in range(13):
        a = math.radians(122 + 93 * k / 12)
        pts.append((Ff + 0.032 * math.cos(a), Rf + 0.032 * math.sin(a)))
    pts += [(0.004, 0.0045), (-0.012, 0.0045)]
    cr, cu, Rr = P.ROLLER_R_FWD, P.ROLLER_R_R + 0.001, 0.0235
    for k in range(15):
        a = math.radians(-25 + 230 * k / 14)
        pts.append((cr + Rr * math.cos(a), cu + Rr * math.sin(a)))
    pts += [(-0.058, 0.0045), (P.HEAD_REAR, 0.009), (P.HEAD_REAR, 0.052), (-0.048, 0.058), (-0.024, 0.056), (-0.010, 0.047), (0.008, 0.045)]
    extrude("HeadChassis", pts, side_map, -xi, xi, "M_HousingDark", G, bev=0.0012, bev_seg=1)

    # --- grey bridge plate on top rear + blank logo emboss
    br = fillet([(-0.020, 0.0725), (-0.023, 0.059), (P.HEAD_REAR - 0.002, 0.050), (P.HEAD_REAR - 0.0025, 0.060), (-0.058, 0.066)], [0.003, 0.002, 0.002, 0.008, 0.03])
    extrude("HeadBridge", br, side_map, -xi - 0.0004, xi + 0.0004, "M_Housing", G, bev=0.0016)
    emb = rrect(0.044, 0.013, 0.004)
    verts = []
    n = len(emb)
    for dz in (-0.0004, 0.0007):
        for px, py in emb:
            fwd = -0.040 + py
            verts.append(V(0.028 + px, 0.066 + (fwd + 0.058) * 0.171 + dz, fwd))
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(j, (j + 1) % n, n + (j + 1) % n, n + j) for j in range(n)]
    mk("HeadBridgeEmboss", verts, faces, "M_Housing", G, smooth=False)

    # --- neck yoke cheeks + base, wheels, axle, corrugated hose visible between the cheeks (V7)
    ax = P.WAND_AXIS_FWD
    yk = fillet([(-0.058, 0.014), (-0.054, 0.058), (ax + 0.016, 0.108), (ax - 0.014, 0.110), (ax - 0.022, 0.062), (ax - 0.020, 0.020), (ax - 0.004, 0.012)], [0.004, 0.010, 0.012, 0.012, 0.012, 0.008, 0.004])
    for s, tag in ((1, "R"), (-1, "L")):
        extrude(f"YokeCheek_{tag}", yk, side_map, s * 0.0138, s * P.YOKE_HALF_W, "M_Housing", G, bev=0.002)
    # broad rear neck plate between the wheels (V5 top view), carries the axle bosses
    ykb = fillet([(-0.056, 0.010), (-0.056, 0.046), (ax - 0.004, 0.040), (ax - 0.024, 0.030), (ax - 0.026, 0.012)], [0.003, 0.006, 0.012, 0.010, 0.004])
    extrude("NeckPlate", ykb, side_map, -(P.WHEEL_X_IN - 0.0015), P.WHEEL_X_IN - 0.0015, "M_Housing", G, bev=0.0025)
    hose_path = bezier_path((0, 0.030, -0.060), (0, 0.048, -0.072), (0, 0.068, ax - 0.002), (0, 0.090, ax), nseg(16))
    sweep_corrugated("NeckHose", hose_path, 0.0102, 0.0011, 8, "M_Hose", G)
    lathe_x("WheelAxle", [(0.0045, -(P.WHEEL_X_IN + P.WHEEL_W)), (0.0045, P.WHEEL_X_IN + P.WHEEL_W)], P.WHEEL_R, P.WHEEL_FWD, "M_HousingDark", G, segs=16)
    R = P.WHEEL_R
    for s, tag in ((1, "R"), (-1, "L")):
        x0 = s * P.WHEEL_X_IN
        x1 = s * (P.WHEEL_X_IN + P.WHEEL_W)
        tire = [(R - 0.0065, x0), (R - 0.0012, x0), (R, x0 + s * 0.0022), (R, x1 - s * 0.0022), (R - 0.0012, x1), (R - 0.0065, x1)]
        lathe_x(f"WheelTire_{tag}", tire, R, P.WHEEL_FWD, "M_Rubber", G, cap0=False, cap1=False, segs=max(32, D["lathe"] // 2))
        ridge = lambda th, h, r: r
        lathe_x(f"WheelFaceOut_{tag}", [(R - 0.0063, x1 - s * 0.0004), (0.0088, x1 - s * 0.0020)], R, P.WHEEL_FWD, "M_Silver", G, cap0=False, cap1=False, segs=max(32, D["lathe"] // 2))
        lathe_x(f"WheelFaceIn_{tag}", [(R - 0.0063, x0 + s * 0.0004), (0.0088, x0 + s * 0.0020)], R, P.WHEEL_FWD, "M_Silver", G, cap0=False, cap1=False, segs=32)
        lathe_x(f"WheelHub_{tag}", [(0.0090, x1 - s * 0.0021), (0.0080, x1 - s * 0.0009), (0.0035, x1 - s * 0.0005)], R, P.WHEEL_FWD, "M_HousingDark", G, cap0=False, cap1=True, segs=32)
        lathe_x(f"WheelHubIn_{tag}", [(0.0090, x0 + s * 0.0021), (0.0080, x0 + s * 0.0009)], R, P.WHEEL_FWD, "M_HousingDark", G, cap0=False, cap1=True, segs=24)
        # radial ribs on the outer face (V2: radial-line wheel face)
        nrib = 36 if D["lathe"] > 60 else 18
        verts, faces = [], []
        for k in range(nrib):
            th = TAU * k / nrib
            dvec = Vector((0, math.cos(th), math.sin(th)))
            tvec = Vector((0, -math.sin(th), math.cos(th)))
            b = len(verts)
            for rr, xx in ((0.0095, x1 - s * 0.0019), (R - 0.0068, x1 - s * 0.0006)):
                for tw in (-0.00045, 0.00045):
                    for dx in (0.0, s * 0.0006):
                        p = Vector((xx + dx, 0, 0)) + dvec * rr + tvec * tw
                        verts.append(V(p.x, R + p.z, P.WHEEL_FWD + p.y))
            # 8 verts: box
            idx = [b + i for i in range(8)]
            faces += [(idx[0], idx[2], idx[3], idx[1]), (idx[4], idx[5], idx[7], idx[6]), (idx[0], idx[1], idx[5], idx[4]), (idx[2], idx[6], idx[7], idx[3]), (idx[1], idx[3], idx[7], idx[5]), (idx[0], idx[4], idx[6], idx[2])]
        mk(f"WheelRibs_{tag}", verts, faces, "M_Silver", G, smooth=False)

    rf = build_roller_front()
    rr = build_roller_rear()
    return leds, rf, rr


def sweep_corrugated(name, path, r0, amp, nridge, mat, grp, segs=None):
    segs = segs or max(16, D["lathe"] // 4)
    path = [Vector(p) for p in path]
    # resample for ridges
    fine = []
    for i in range(len(path) - 1):
        for k in range(4):
            fine.append(path[i].lerp(path[i + 1], k / 4))
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


def build_roller_front():
    R, L = P.ROLLER_F_R, P.ROLLER_F_LEN
    segs, nr = D["roller_segs"], D["roller_rings"]
    xs = []
    end = 0.004
    # rounded ends
    prof = []
    for k in range(4):
        a = (math.pi / 2) * k / 4
        prof.append((-L / 2 + end * (1 - math.sin(a + 0.0001)) * 0 + end * (1 - math.cos(a)) * 0 + end - end * math.cos(a), R - end + end * math.sin(a)))
    # simpler explicit profile (x, r)
    prof = [(-L / 2, R - end), (-L / 2 + end * (1 - math.cos(math.radians(45))), R - end + end * math.sin(math.radians(45))), (-L / 2 + end, R)]
    for k in range(1, nr):
        prof.append((-L / 2 + end + (L - 2 * end) * k / nr, R))
    prof += [(L / 2 - end, R), (L / 2 - end * (1 - math.cos(math.radians(45))), R - end + end * math.sin(math.radians(45))), (L / 2, R - end)]
    verts, uvs, faces = [], [], []
    n = segs + 1
    for i, (x, r) in enumerate(prof):
        for j in range(n):
            th = TAU * j / segs
            verts.append(Vector((x, r * math.sin(th), r * math.cos(th))))  # local (Blender): spin about X
            uvs.append((j / segs, (x + L / 2) / L))
    for i in range(len(prof) - 1):
        for j in range(segs):
            a, b = i * n + j, (i + 1) * n + j
            faces.append((a, a + 1, b + 1, b))
    for idx, ring0 in ((0, 0), (1, len(prof) - 1)):
        c = len(verts)
        verts.append(Vector((prof[ring0][0], 0, 0)))
        uvs.append((0.5, 0.0 if idx == 0 else 1.0))
        for j in range(segs):
            a = ring0 * n + j
            faces.append((c, a + 1, a) if idx == 0 else (c, a, a + 1))
    ob = mk("RollerFront", verts, faces, "M_RollerFront", "RollerFront", uvs=uvs)
    ob.location = V(0, R, P.ROLLER_F_FWD)
    return ob


def build_roller_rear():
    R, L, Rc = P.ROLLER_R_R, P.ROLLER_R_LEN, P.ROLLER_R_CORE
    cu, cf = R + 0.001, P.ROLLER_R_FWD
    core = lathe_x("RollerRearCore", [(Rc * 0.7, -L / 2), (Rc, -L / 2 + 0.002), (Rc, L / 2 - 0.002), (Rc * 0.7, L / 2)], 0, 0, "M_HousingDark", "RollerRear", segs=max(16, D["lathe"] // 4))
    # bristle tufts in two chevron helices
    verts, faces = [], []
    ntuft = 46 if D["lathe"] > 60 else 26
    sides = 6 if D["lathe"] > 60 else 4
    for row in range(2):
        for i in range(ntuft):
            t = i / (ntuft - 1)
            x = -L / 2 + 0.006 + (L - 0.012) * t
            th = row * math.pi + abs(x) / (L / 2) * math.pi * 0.9
            d = Vector((0, math.sin(th), math.cos(th)))
            e1 = Vector((1, 0, 0))
            e2 = d.cross(e1)
            base = len(verts)
            for (rad, rr) in ((Rc - 0.001, 0.0018), (R, 0.0028)):
                for k in range(sides):
                    a = TAU * k / sides
                    verts.append(Vector((x, 0, 0)) + d * rad + (e1 * math.cos(a) + e2 * math.sin(a)) * rr)
            for k in range(sides):
                k2 = (k + 1) % sides
                faces.append((base + k, base + k2, base + sides + k2, base + sides + k))
            faces.append(tuple(base + sides + k for k in range(sides)))
    tufts = mk("RollerRearBristles", verts, faces, "M_Bristle", "RollerRear", smooth=True)
    # join core + tufts into RollerRear (origin on axis)
    ob = join_objects([core, tufts], "RollerRear")
    ob.location = V(0, cu, cf)
    return ob


def join_objects(objs, name):
    for o in objs:
        apply_modifiers(o)
    target = objs[0]
    with bpy.context.temp_override(active_object=target, selected_editable_objects=objs, object=target):
        bpy.ops.object.join()
    target.name = name
    target.data.name = name
    return target


def apply_modifiers(ob):
    if not ob.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)


# =====================================================================================  wand
def wand_sec(w, d):
    hx, hd = w / 2, d / 2
    oct_ = [(hx, hd * 0.50), (hx * 0.56, hd), (-hx * 0.56, hd), (-hx, hd * 0.50), (-hx, -hd * 0.50), (-hx * 0.56, -hd), (hx * 0.56, -hd), (hx, -hd * 0.50)]
    return fillet(oct_, 0.0042, max(2, D["corner"] - 1))


def oval(cx, cy, a, b, n=32):
    return [(cx + a * math.cos(TAU * k / n), cy + b * math.sin(TAU * k / n)) for k in range(n)]


def front_map(u, v, w):
    """(x, up) plane extruded along fwd"""
    return V(u, v, w)


def build_lower_wand():
    G = "LowerWand"
    ax = P.WAND_AXIS_FWD
    npv = P.NECK_PIVOT
    # hinge barrel on the pitch axis (sits between the yoke cheeks)
    lathe_x("NeckBarrel", [(0.0105, -0.0132), (0.0122, -0.0124), (0.0122, 0.0124), (0.0105, 0.0132)], npv[1], npv[2], "M_Housing", G, segs=max(24, D["lathe"] // 2))
    # knuckle rising into the collar
    loft_up("NeckKnuckle", [(npv[1] - 0.006, 0.026, 0.030, 0.008, ax), (npv[1] + 0.008, 0.036, 0.042, 0.012, ax), (P.COLLAR[0] + 0.004, P.COLLAR_W[0], P.COLLAR_D, 0.014, ax)], "M_Housing", G, cap_round=0.003)
    # purple swivel disc facing front (V7), slightly tilted up (V1), grey tabbed ring
    A = Vector((0, math.sin(math.radians(15)), math.cos(math.radians(15))))
    O = Vector((0, P.NECK_DISC_UP, ax + 0.019))
    tabs = lambda th, h, r: r + (0.0024 if (math.cos(th * 4) > 0.55 and r > 0.0165) else 0)
    lathe("NeckDiscRing", [(0.0050, 0.0), (0.0175, 0.0), (0.0175, 0.0036), (0.0150, 0.0044)], O, A, Vector((1, 0, 0)), "M_Housing", G, segs=max(48, D["lathe"]), rmod=tabs)
    lathe("NeckDisc", [(0.0148, 0.0038), (0.0146, 0.0056), (0.0132, 0.0064), (0.0, 0.0066)], O, A, Vector((1, 0, 0)), "M_Purple", G, segs=max(32, D["lathe"] // 2), cap0=True, cap1=False)
    # neck connector / collar, tapering 0.046 -> 0.036
    c0, c1 = P.COLLAR
    wb, wt = P.COLLAR_W
    cd = P.COLLAR_D
    loft_up("Collar", [(c0, wb, cd, 0.014, ax), (c0 + 0.040, wb, cd + 0.002, 0.015, ax), (c0 + 0.095, 0.041, cd - 0.001, 0.013, ax), (c1, wt + 0.0015, 0.0475, 0.011, ax)], "M_Housing", G)
    # light-grey oval release button on the front (V7)
    extrude("CollarButton", oval(0, P.COLLAR_BTN_UP, 0.0085, 0.0135), front_map, ax + 0.0228, ax + 0.0258, "M_Housing", G, bev=0.0012, bev_seg=2)
    extrude("CollarButtonRing", oval(0, P.COLLAR_BTN_UP, 0.0105, 0.0155), front_map, ax + 0.0222, ax + 0.0246, "M_HousingDark", G, bev=0.0006, bev_seg=1)
    # grey cuff at the wand bottom with the lock-tab slot
    u0, u1 = P.CUFF
    loft_up("Cuff", [(u0, 0.0385, 0.0490, 0.011, ax), (u1, 0.0372, 0.0478, 0.011, ax)], "M_Housing", G)
    lathe_up("CuffSeam", [(0.03, u0 - 0.0005), (0.03, u0 + 0.0005)], ax, "M_HousingDark", G, segs=48, cap0=False, cap1=False, rmod=lambda th, h, r: ell_r(th, 0.0196, 0.0248))
    extrude("CuffSlot", [(px, 0.268 + py) for px, py in rrect(0.012, 0.0045, 0.0015)], front_map, ax + 0.0228, ax + 0.0250, "M_HousingDark", G)
    # purple wand tube (rounded-rect, soft facets)
    ww, wd = P.WAND_SEC
    loft_up("WandTube", [(P.WAND[0] - 0.002, ww, wd, 0, ax), (P.WAND[1] + 0.002, ww, wd, 0, ax)], "M_PurpleMatte", G, sec=wand_sec)
    # fold housing (wand-side half of the MultiFLEX hinge): taper 0.036 -> 0.051
    fp = P.FOLD_PIVOT
    fw = P.FOLD_W[0]
    loft_up("FoldLower", [(P.WAND[1] - 0.003, 0.0365, 0.0478, 0.010, ax), (P.WAND[1] + 0.025, 0.045, 0.054, 0.013, ax + 0.002), (fp[1] - 0.017, fw, 0.064, 0.015, ax + 0.006), (fp[1] + 0.004, fw, 0.066, 0.015, ax + 0.007)], "M_Housing", G)
    # dark release latch on the rear (M4)
    extrude("FoldLatch", [(px, fp[1] - 0.020 + py) for px, py in rrect(0.018, 0.040, 0.004)], front_map, ax + 0.007 - 0.033 - 0.0065, ax + 0.007 - 0.033 + 0.002, "M_HousingDark", G, bev=0.0015, bev_seg=2)
    # hinge barrel + purple pivot caps on both sides (total width 0.063)
    half = P.FOLD_W[1] / 2
    lathe_x("FoldBarrel", [(0.0100, -(fw / 2 + 0.0008)), (P.FOLD_CAP_R, -(fw / 2 + 0.0002)), (P.FOLD_CAP_R, fw / 2 + 0.0002), (0.0100, fw / 2 + 0.0008)], fp[1], fp[2], "M_Housing", G, segs=max(32, D["lathe"] // 2))
    for s, tag in ((1, "R"), (-1, "L")):
        lathe_x(f"FoldCap_{tag}", [(P.FOLD_CAP_R, s * (fw / 2 - 0.001)), (P.FOLD_CAP_R, s * (half - 0.0015)), (P.FOLD_CAP_R - 0.0015, s * half), (0.0, s * (half + 0.0002))], fp[1], fp[2], "M_Purple", G, segs=max(32, D["lathe"] // 2), cap0=True, cap1=False)


def ell_r(th, a, b):
    """radius of an ellipse (semi-axes a along x, b along fwd) in direction th (th=0 -> fwd)"""
    return 1.0 / math.sqrt((math.sin(th) / a) ** 2 + (math.cos(th) / b) ** 2)


def build_upper_wand():
    G = "UpperWand"
    ax = P.WAND_AXIS_FWD
    fp = P.FOLD_PIVOT
    hb = P.HANDHELD_BOTTOM
    uw = P.UPPER_W
    loft_up("FoldUpper", [(fp[1] - 0.004, P.FOLD_W[0], 0.066, 0.015, ax + 0.007), (fp[1] + 0.033, 0.049, 0.059, 0.014, ax + 0.004), (fp[1] + 0.061, uw, 0.052, 0.013, ax + 0.001)], "M_Housing", G)
    lathe_up("UpperSeam", [(0.03, fp[1] + 0.0605), (0.03, fp[1] + 0.0615)], ax + 0.001, "M_HousingDark", G, segs=48, cap0=False, cap1=False, rmod=lambda th, h, r: ell_r(th, uw / 2 + 0.0004, 0.0264))
    loft_up("UpperConnector", [(fp[1] + 0.061, uw, 0.052, 0.013, ax + 0.001), (P.UPPER_BTN_UP - 0.022, uw, 0.052, 0.013, ax), (P.UPPER_BTN_UP, 0.049, 0.053, 0.014, ax - 0.001), (P.UPPER_BTN_UP + 0.022, uw + 0.001, 0.054, 0.014, ax - 0.003), (hb + 0.010, 0.046, 0.058, 0.014, ax - 0.005)], "M_Housing", G)
    extrude("UpperButton", oval(0, P.UPPER_BTN_UP, 0.0110, 0.0170), front_map, ax + 0.0225, ax + 0.0272, "M_HousingDark", G, bev=0.0016, bev_seg=2)


# =====================================================================================  motor assembly
def dsec_fn(bf, front, rback, rc):
    """D-shaped handheld section: round back (radius rback about the body axis), flat front at `front`."""
    nb = max(8, D["lathe"] // 4)

    def f(w, d):
        R = w / 2
        fr = front - bf
        pts = [(R * math.cos(math.pi + math.pi * k / nb), R * math.sin(math.pi + math.pi * k / nb)) for k in range(nb + 1)]
        # back half circle from -x to +x through -fwd; then front corners
        pts = pts[::-1]  # +x .. -x via back
        poly = [(R, 0.0)] + [p for p in pts[1:-1]] + [(-R, 0.0), (-R, fr), (R, fr)]
        rad = [0.0] * (len(poly) - 2) + [rc, rc]
        out = fillet(poly, rad)
        return out

    return f


def build_motor_assembly():
    G = "MotorAssembly"
    bf = P.BODY_FWD
    Rb = P.BODY_R
    front = P.FRAME_FRONT

    # grey bin base (round) + front socket where the upper wand plugs in
    b0, b1 = P.BASE
    lathe_up("BinBase", [(0.040, b0), (Rb - 0.004, b0 + 0.0004), (Rb - 0.0005, b0 + 0.004), (Rb, b0 + 0.010), (Rb, b1 - 0.002), (Rb - 0.002, b1)], bf, "M_Housing", G, cap0=True, cap1=False)
    ax = P.WAND_AXIS_FWD
    loft_up("BinSocket", [(b0, 0.046, 0.050, 0.014, ax - 0.006), (b1 - 0.004, 0.046, 0.050, 0.014, ax - 0.008)], "M_Housing", G, cap_round=0.003)
    # slim silver front frame rails hugging the bin (V7: silver frame either side of the front window)
    for s_, tag in ((1, "R"), (-1, "L")):
        th0, th1 = math.radians(36) * s_, math.radians(88) * s_
        sec = sector_sec(min(th0, th1), max(th0, th1), Rb - 0.0012, Rb + 0.0030)
        loft_up(f"FrameRail_{tag}", [(b1 - 0.004, 0, 0, 0, bf), (P.SILVER_BAND[0] + 0.002, 0, 0, 0, bf)], "M_Silver", G, sec=lambda w, d, sec=sec: sec)
    # clear bin shell with real wall thickness (visible through the window and from sides/rear)
    c0, c1 = P.BIN
    Ro, w = P.BIN_R, P.BIN_WALL
    shell = lathe_up("DustbinShell", [(Ro - w, c0), (Ro, c0), (Ro + 0.0004, c1), (Ro + 0.0004 - w, c1)], bf, "M_ClearBin", "DustbinShell", closed=True, cap0=False, cap1=False)
    # silver cyclone shroud band (lower window) + central cone + dark mesh screen
    s0, s1 = P.SHROUD
    lathe_up("CycloneShroud", [(0.0405, s0), (0.0410, s0 + 0.003), (0.0410, s1 - 0.004), (0.0390, s1), (0.0300, s1 + 0.002)], bf, "M_Silver", G, cap0=True, cap1=False)
    # frosted inner mesh shroud (reads light grey through the window in V7/V4)
    lathe_up("InnerShroud", [(0.0300, s1 + 0.002), (0.0300, s1 + 0.062), (0.0240, s1 + 0.068)], bf, "M_Silver", G, cap0=False, cap1=True, rmod=lambda th, h, r: r - (0.0004 if (math.cos(th * 72) > 0.2 and r > 0.0295) else 0), segs=D["lathe"] * 2)
    # cyclone cone at the top of the bin (funnel up into the motor)
    lathe_up("CycloneCone", [(0.0125, s1 + 0.066), (0.0215, c1 - 0.020), (0.0380, c1 - 0.004), (0.0400, c1 - 0.0005)], bf, "M_Silver", G, cap0=True, cap1=False)
    # thin edge beads on the clear bin rims (catch a highlight)
    for k_, hh in enumerate((c0 + 0.0008, c1 - 0.0010)):
        lathe_up(f"BinRim_{k_}", [(Ro - 0.0004, hh - 0.0010), (Ro + 0.0009, hh - 0.0006), (Ro + 0.0009, hh + 0.0006), (Ro - 0.0004, hh + 0.0010)], bf, "M_Label", G, cap0=False, cap1=False)
    dust = lathe_up("DustbinContents", [(0.0310, s1 + 0.001), (0.0412, s1 + 0.001), (0.0412, s1 + 0.052), (0.0315, s1 + 0.045)], bf, "M_Dust", "DustbinContents", closed=True, cap0=False, cap1=False, segs=max(24, D["lathe"] // 3))
    # bin rear lid latch + hinge (bottom-emptying lid)
    extrude("BinLatch", [(px, s0 + 0.016 + py) for px, py in rrect(0.020, 0.026, 0.004)], front_map, bf - Ro - 0.010, bf - Ro + 0.003, "M_Housing", G, bev=0.0015, bev_seg=2)
    extrude("BinLatchTab", [(px, s0 + 0.004 + py) for px, py in rrect(0.012, 0.008, 0.002)], front_map, bf - Ro - 0.013, bf - Ro - 0.008, "M_HousingDark", G, bev=0.001, bev_seg=1)
    # purple ribbed ring at the bin top (round)
    pr0, pr1 = P.PURPLE_RING
    lathe_up("PurpleRing", [(0.0410, pr0), (0.0452, pr0 + 0.0008), (0.0458, pr0 + 0.003), (0.0458, pr1 - 0.003), (0.0450, pr1), (0.0410, pr1)], bf, "M_Purple", G, rmod=lambda th, h, r: r - (0.0005 if (math.cos(th * 40) > 0.3 and r > 0.0455) else 0), segs=D["lathe"] * 2 if D["lathe"] > 60 else D["lathe"])
    # silver band (blank logo zone) + motor housing, D section
    sb0, sb1 = P.SILVER_BAND
    lathe_up("SilverBand", [(0.0405, sb0), (Rb - 0.0004, sb0 + 0.0005), (Rb + 0.0002, sb0 + 0.0025), (Rb + 0.0002, sb1 - 0.0025), (Rb - 0.0006, sb1), (0.0405, sb1)], bf, "M_Silver", G)
    m0, m1 = P.MOTOR
    R = P.MOTOR_R
    motor = lathe_up("MotorHousing", [(0.0395, m0), (R - 0.0006, m0 + 0.0006), (R, m0 + 0.003), (R + 0.0004, m0 + 0.025), (R, m1 - 0.010), (R - 0.0010, m1 - 0.002), (0.0400, m1)], bf, "M_Housing", G, segs=D["lathe"] * 2 if D["lathe"] > 60 else D["lathe"])
    lathe_up("MotorInnerCan", [(R - 0.0035, m0 + 0.003), (R - 0.0035, m1 - 0.002)], bf, "M_HousingDark", G, cap0=False, cap1=True)
    cutter = vent_cutter(bf, P.MOTOR_R)
    bm = motor.modifiers.new("Vents", "BOOLEAN")
    bm.operation = "DIFFERENCE"
    bm.solver = "EXACT"
    bm.object = cutter
    cutter.hide_render = True
    cutter.hide_viewport = True
    # purple filter/end cap: tapered axial flutes, slightly domed; dark round control screen on the end face
    c0_, c1_ = P.CAP
    Rc = P.CAP_R
    N = P.CAP_RIBS

    def flutes(th, h, r):
        if r < Rc - 0.002:
            return r
        f = (th * N / TAU) % 1.0
        dd = min(f, 1 - f)
        fade = max(0.0, min(1.0, (c0_ + 0.040 - h) / 0.032))
        g = max(0.0, 1 - dd / 0.16)
        return r - 0.0020 * g * fade

    segs = N * (10 if D["lathe"] > 60 else 5)
    cap_prof = [(0.0410, c0_), (0.0442, c0_ + 0.0006), (Rc, c0_ + 0.0030)]
    for k in range(1, 8):
        cap_prof.append((Rc, c0_ + 0.0030 + 0.037 * k / 7))
    cap_prof += [(Rc - 0.0010, c1_ - 0.0075), (Rc - 0.0035, c1_ - 0.0025), (Rc - 0.0075, c1_ - 0.0004), (P.SCREEN_R + 0.0025, c1_), (P.SCREEN_R + 0.0012, c1_ - 0.0010)]
    lathe_up("FilterCap", cap_prof, bf, "M_Purple", G, rmod=flutes, segs=segs, cap0=False, cap1=False)
    lathe_up("ScreenBezel", [(P.SCREEN_R + 0.0014, c1_ - 0.0012), (P.SCREEN_R + 0.0008, c1_ + 0.0002), (P.SCREEN_R, c1_ + 0.0002), (P.SCREEN_R, c1_ - 0.0004)], bf, "M_HousingDark", G, cap0=False, cap1=False)
    lathe_up("ControlScreen", [(P.SCREEN_R, c1_ - 0.0004), (P.SCREEN_R - 0.004, c1_ + 0.0004), (0.0, c1_ + 0.0008)], bf, "M_Screen", G, cap0=False, cap1=False)
    # power button at the screen edge nearest the handle (rear)
    lathe_up("PowerButton", [(0.0042, c1_ + 0.0004), (0.0040, c1_ + 0.0012), (0.0, c1_ + 0.0014)], bf - P.SCREEN_R + 0.0065, "M_HousingDark", G, segs=24, cap0=False, cap1=False)
    build_handle(G, bf)
    return shell, dust, cutter


def sector_sec(th0, th1, r0, r1, n=None):
    """annular sector polygon in (x, fwd-offset) coords; theta=0 is front"""
    n = n or max(4, D["corner"])
    outer = [(r1 * math.sin(th0 + (th1 - th0) * k / n), r1 * math.cos(th0 + (th1 - th0) * k / n)) for k in range(n + 1)]
    inner = [(r0 * math.sin(th1 - (th1 - th0) * k / n), r0 * math.cos(th1 - (th1 - th0) * k / n)) for k in range(n + 1)]
    return outer + inner


def vent_cutter(bf, R):
    """two rectangular dotted grilles on the front-left / front-right of the round motor (V4/V7)."""
    verts, faces = [], []
    m0, m1 = P.MOTOR
    cols, rows = 5, 7
    for s in (1, -1):
        thc = math.radians(50) * s
        for j in range(cols):
            for i in range(rows):
                up = m0 + 0.0095 + i * 0.0060
                th = thc + math.radians(6.2) * (j - (cols - 1) / 2) + (math.radians(1.6) if i % 2 else 0)
                c = PV(math.sin(th) * R, up, bf + math.cos(th) * R)
                rad = PV(math.sin(th), 0, math.cos(th))
                tan = PV(math.cos(th), 0, -math.sin(th))
                upv = PV(0, 1, 0)
                hw, hh, hd = 0.0013, 0.0021, 0.0035
                base = len(verts)
                for dz in (-hd, hd):
                    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                        verts.append(toB(c + rad * dz + tan * (a * hw) + upv * (b * hh)))
                faces += [(base + 0, base + 1, base + 2, base + 3), (base + 7, base + 6, base + 5, base + 4), (base + 0, base + 4, base + 5, base + 1), (base + 1, base + 5, base + 6, base + 2), (base + 2, base + 6, base + 7, base + 3), (base + 3, base + 7, base + 4, base + 0)]
    return mk("VentCutter", verts, faces, "M_HousingDark", "_cutter", smooth=False)


def build_handle(G, bf):
    # grip (upper bar, purple trigger), battery (lower bar, light-grey label panels), rear post with round button
    ga, gb = P.GRIP_A, P.GRIP_B
    gw, gh = P.GRIP_SEC
    gp = bezier_path((0, ga[0], ga[1]), (0, ga[0] + 0.006, ga[1] - 0.040), (0, gb[0] - 0.008, gb[1] + 0.040), (0, gb[0], gb[1]), nseg(14))
    sweep("Grip", gp, lambda t: (0.028, 0.030, 0.0136), "M_Housing", G, cap_round=0.006)
    gp2 = [p + Vector((0, -0.0095, 0)) for p in gp[3:-2]]
    sweep("GripPad", gp2, lambda t: (0.021, 0.014, 0.0068), "M_HousingDark", G, cap_round=0.004)
    ba, bb = P.BATT_A, P.BATT_B
    bw, bh = P.BATT_SEC
    bp = bezier_path((0, ba[0], ba[1]), (0, ba[0] + 0.004, ba[1] - 0.040), (0, bb[0] - 0.004, bb[1] + 0.040), (0, bb[0], bb[1]), nseg(12))
    sweep("Battery", bp, lambda t: (bw, bh, 0.017), "M_Housing", G, cap_round=0.008)
    a, b = Vector(bp[2]), Vector(bp[-3])
    mid = (a + b) / 2
    T = (b - a).normalized()
    Nn = T.cross(Vector((1, 0, 0))).normalized()
    lab = rrect(0.092, 0.020, 0.010)
    for s, tag in ((1, "R"), (-1, "L")):
        verts = []
        n = len(lab)
        for dx in (bw / 2 - 0.0006, bw / 2 + 0.0010):
            for px, py in lab:
                p = mid + T * (px - 0.004) + Nn * py
                verts.append(toB(Vector((s * dx, p.y, p.z))))
        faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(j, (j + 1) % n, n + (j + 1) % n, n + j) for j in range(n)]
        bevel(mk(f"BatteryLabel_{tag}", verts, faces, "M_Label", G), 0.0005, 1)
    pu0, pu1, pd, pw = P.POST
    pf = P.HANDLE_REAR + pd / 2
    loft_up("HandlePost", [(pu0, pw, pd, 0.018, pf), (pu1, pw * 0.96, pd * 0.94, 0.017, pf - 0.001)], "M_Housing", G, cap_round=0.012)
    loft_up("HandlePostRear", [(pu0 + 0.014, pw * 0.84, 0.006, 0.0025, P.HANDLE_REAR + 0.0022), (pu1 - 0.014, pw * 0.82, 0.006, 0.0025, P.HANDLE_REAR + 0.0022)], "M_HousingDark", G, cap_round=0.002)
    bu = bb[0]
    for s, tag in ((1, "R"), (-1, "L")):
        lathe_x(f"PostButtonRing_{tag}", [(0.0120, s * (pw / 2 - 0.0008)), (0.0120, s * (pw / 2 + 0.0006)), (0.0102, s * (pw / 2 + 0.0012))], bu, pf, "M_HousingDark", G, segs=40, cap0=False, cap1=True)
        lathe_x(f"PostButton_{tag}", [(0.0090, s * (pw / 2 + 0.0008)), (0.0090, s * (pw / 2 + 0.0024)), (0.0075, s * (pw / 2 + 0.0034)), (0.0, s * (pw / 2 + 0.0038))], bu, pf, "M_Housing", G, segs=40, cap0=False, cap1=False)
    gx = ga[1] - 0.006
    trg = fillet([(gx + 0.004, ga[0] - 0.008), (gx + 0.002, ga[0] - 0.022), (gx - 0.007, ga[0] - 0.028), (gx - 0.016, ga[0] - 0.021), (gx - 0.019, ga[0] - 0.006)], [0.001, 0.004, 0.006, 0.004, 0.001])
    extrude("Trigger", trg, lambda u, v, w: V(w, v, u), -0.0068, 0.0068, "M_Purple", G, bev=0.0018, bev_seg=2)


# =====================================================================================  rig
def empty(name, loc_prod, parent=None):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = 0.02
    link(ob)
    ob.location = V(*loc_prod)
    if parent:
        set_parent(ob, parent)
    return ob


def set_parent(child, parent):
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Identity(4)
    child.matrix_basis = parent.matrix_world.inverted() @ mw


def build(tier):
    global D, COLL
    D = P.DETAIL[tier]
    COLL = bpy.context.scene.collection
    tex_dir = os.path.join(ROOT, "assets", "source", "textures")
    os.makedirs(tex_dir, exist_ok=True)
    img = make_roller_texture(os.path.join(tex_dir, "roller_front.png"))
    make_materials(img)

    leds, rf, rr = build_floorhead()
    build_lower_wand()
    build_upper_wand()
    shell, dust, cutter = build_motor_assembly()
    for o in list(COLL.objects):
        if o.get("grp") == "_skip":
            bpy.data.objects.remove(o, do_unlink=True)

    # ---- hierarchy (all rest rotations identity)
    root = empty("VacuumRoot", (0, 0, 0))
    head = empty("FloorHead", (0, 0, 0), root)
    neck = empty("NeckPivot", P.NECK_PIVOT, head)
    lw = empty("LowerWand", P.NECK_PIVOT, neck)
    flex = empty("FlexPivot", P.FOLD_PIVOT, lw)
    uw = empty("UpperWand", P.FOLD_PIVOT, flex)
    motor = empty("MotorAssembly", (0, P.HANDHELD_BOTTOM, P.BODY_FWD), uw)
    empty("IntakeFront", (0, 0, P.ROLLER_F_FWD), head)
    empty("IntakeRear", (0, 0, P.ROLLER_R_FWD), head)
    fca = empty("FloorContactAnchors", (0, 0, 0), head)
    cx = P.ROLLER_F_LEN / 2 - 0.012
    for nm, loc in (
        ("Contact_RollerFront_L", (-cx, 0, P.ROLLER_F_FWD)),
        ("Contact_RollerFront_R", (cx, 0, P.ROLLER_F_FWD)),
        ("Contact_RollerRear_L", (-cx, 0, P.ROLLER_R_FWD)),
        ("Contact_RollerRear_R", (cx, 0, P.ROLLER_R_FWD)),
        ("Contact_Wheel_L", (-(P.WHEEL_X_IN + P.WHEEL_W / 2), 0, P.WHEEL_FWD)),
        ("Contact_Wheel_R", (P.WHEEL_X_IN + P.WHEEL_W / 2, 0, P.WHEEL_FWD)),
    ):
        empty(nm, loc, fca)
    pca = empty("PowerControlAnchor", (0.0, P.CAP[1] + 0.0014, P.BODY_FWD - P.SCREEN_R + 0.0065), motor)

    # HeadLights mesh (joined LEDs), origin between the two LEDs
    hl = join_objects(leds, "HeadLights")
    set_origin(hl, V(0, 0.056, 0.085))
    set_parent(hl, head)
    set_parent(rf, head)
    set_parent(rr, head)
    set_origin(shell, V(0, P.BIN[0], P.BODY_FWD))
    set_parent(shell, motor)
    set_origin(dust, V(0, P.SHROUD[1] + 0.001, P.BODY_FWD))
    set_parent(dust, motor)
    # rig-named mesh nodes become empties with a *_Mesh child: glTF optimizers (meshopt quantization) may put a
    # dequantization transform on mesh nodes, which must never collide with runtime rotation/scale on rig nodes.
    for ob in (hl, rf, rr, shell, dust):
        wrap_mesh_in_empty(ob)
    groups = {"FloorHead": head, "LowerWand": lw, "UpperWand": uw, "MotorAssembly": motor}
    for o in list(COLL.objects):
        g = o.get("grp")
        if g in groups and o.type == "MESH" and o.parent is None:
            set_parent(o, groups[g])
    cutter.parent = motor
    cutter.matrix_parent_inverse = motor.matrix_world.inverted()
    return {"root": root, "groups": groups, "cutter": cutter, "special": [hl, rf, rr, shell, dust]}


def wrap_mesh_in_empty(ob):
    name = ob.name
    par = ob.parent
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.name = name + "_Mesh"
    ob.data.name = name + "_Mesh"
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.02
    link(e)
    e.location = mw.translation
    if par:
        set_parent(e, par)
    set_parent(ob, e)
    return e


def set_origin(ob, world_pt):
    mw = ob.matrix_world.copy()
    local = mw.inverted() @ world_pt
    ob.data.transform(Matrix.Translation(-local))
    ob.location = ob.location + (mw.to_3x3() @ local)


def finalize_for_export(ctx):
    """apply modifiers, join static parts per rig group, set smoothing/sharp edges."""
    groups = ctx["groups"]
    names = {"FloorHead": "FloorHead_Body", "LowerWand": "LowerWand_Body", "UpperWand": "UpperWand_Body", "MotorAssembly": "MotorAssembly_Body"}
    for gname, emp in groups.items():
        parts = [o for o in emp.children if o.type == "MESH" and o.get("grp") == gname]
        for o in parts:
            apply_modifiers(o)
        j = join_objects(parts, names[gname])
        set_origin(j, emp.matrix_world.translation)
    bpy.data.objects.remove(ctx["cutter"], do_unlink=True)
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            apply_modifiers(o)
            me = o.data
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(38))
            # merge coincident verts introduced by modifiers/joins
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bm.to_mesh(me)
            bm.free()


def tri_count():
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    per = {}
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        per[o.name] = len(me.loop_triangles)
        total += per[o.name]
        o.evaluated_get(dg).to_mesh_clear()
    return total, per


def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=False,
        export_image_format="AUTO",
        use_selection=False,
    )


def gl(v):
    """Blender world vector -> glTF/runtime coords"""
    return [round(v.x, 5), round(v.z, 5), round(-v.y, 5)]


def world_bbox(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objs:
        if o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
        ev.to_mesh_clear()
    return mn, mx


def measure_rig(ctx):
    head = bpy.data.objects["FloorHead"]
    head_meshes = [o for c in head.children if c.name != "NeckPivot" for o in ([c] + list(c.children_recursive)) if o.type == "MESH"]  # excludes the NeckPivot subtree
    hmn, hmx = world_bbox(head_meshes)
    rf = bpy.data.objects["RollerFront"]
    rr = bpy.data.objects["RollerRear"]
    fmn, fmx = world_bbox([bpy.data.objects["RollerFront_Mesh"]])
    rmn, rmx = world_bbox([bpy.data.objects["RollerRear_Mesh"]])
    # intake: inside the side caps; contact footprint from rear brushroll back edge to front roller front edge
    side_r = bpy.data.objects.get("FloorHead_Body") or bpy.data.objects.get("HeadSide_R")
    nozzle = {
        "intakeWidth": round(2 * P.HEAD_INNER_HALF, 4),
        "intakeZMin": round(-rmx.y, 4),
        "intakeZMax": round(-fmn.y, 4),
        "shellWidth": round(hmx.x - hmn.x, 4),
        "shellZMin": round(-hmx.y, 4),
        "shellZMax": round(-hmn.y, 4),
    }
    allm = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
    amn, amx = world_bbox(allm)
    anchors = {}
    for nm in ("NeckPivot", "FlexPivot", "PowerControlAnchor", "IntakeFront", "IntakeRear", "MotorAssembly", "LowerWand", "UpperWand"):
        anchors[nm] = gl(bpy.data.objects[nm].matrix_world.translation)
    contacts = {o.name: gl(o.matrix_world.translation) for o in bpy.data.objects["FloorContactAnchors"].children}
    return {
        "units": "meters",
        "upAxis": "+Y",
        "headFront": "+Z (FloorHead local)",
        "nozzle": nozzle,
        "rollerFrontRadius": P.ROLLER_F_R,
        "rollerRearRadius": P.ROLLER_R_R,
        "rollerFrontLength": P.ROLLER_F_LEN,
        "rollerRearLength": P.ROLLER_R_LEN,
        "rollerFrontCenter": gl(rf.matrix_world.translation),
        "rollerRearCenter": gl(rr.matrix_world.translation),
        "neckPivot": anchors["NeckPivot"],
        "flexPivot": anchors["FlexPivot"],
        "powerControlAnchor": anchors["PowerControlAnchor"],
        "anchors": anchors,
        "contacts": contacts,
        "bounds": {"min": gl(Vector((amn.x, amx.y, amn.z))), "max": gl(Vector((amx.x, amn.y, amx.z))), "size": [round(amx.x - amn.x, 4), round(amx.z - amn.z, 4), round(amx.y - amn.y, 4)]},
        "headBounds": {"min": gl(Vector((hmn.x, hmx.y, hmn.z))), "max": gl(Vector((hmx.x, hmn.y, hmx.z)))},
        "foldAxisSign": 1,
        "foldConvention": "FlexPivot.rotation.x = +fold folds the handheld forward (toward head front, +Z); MultiFLEX pivot is on the front face, latch at rear",
        "pitchConvention": "runtime sets NeckPivot.rotation.x = -pitch (positive pitch leans wand back toward -Z); rest rotations are identity",
        "nozzleDefinition": "intakeWidth = inner span between side caps; intakeZ = rear brushroll back edge .. front roller front edge; shell = FloorHead mesh bbox incl. wheels",
    }


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    tier = "all"
    do_export = True
    if "--tier" in argv:
        tier = argv[argv.index("--tier") + 1]
    if "--no-export" in argv:
        do_export = False
    tiers = ["high", "balanced"] if tier == "all" else [tier]
    report = {"tiers": {}}
    rig = None
    for t in tiers:
        reset_scene()
        ctx = build(t)
        if t == "high":
            bpy.context.view_layer.update()
            src = os.path.join(ROOT, "assets", "source", "powerdetect.blend")
            os.makedirs(os.path.dirname(src), exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=src, compress=True)
        if not do_export:
            continue
        finalize_for_export(ctx)
        bpy.context.view_layer.update()
        total, per = tri_count()
        if t == "high" or rig is None:
            rig = measure_rig(ctx)
        out = os.path.join(ROOT, "public", "models", f"powerdetect-{t}.glb")
        export_glb(out)
        report["tiers"][t] = {"triangles": total, "perObject": per, "file": os.path.relpath(out, ROOT), "bytes": os.path.getsize(out), "materials": sorted(m.name for m in bpy.data.materials if m.users)}
        print(f"[build] {t}: {total} tris -> {out} ({os.path.getsize(out)} bytes)")
    if do_export and rig:
        rig["generatedBy"] = "scripts/blender/build_powerdetect.py"
        with open(os.path.join(ROOT, "public", "models", "rig.json"), "w") as f:
            json.dump(rig, f, indent=2)
        report["rig"] = rig
        report["ledger"] = P.LEDGER
        with open(os.path.join(ROOT, "assets", "source", "build_report.json"), "w") as f:
            json.dump(report, f, indent=2)
    print("[build] done")


if __name__ == "__main__":
    main()
