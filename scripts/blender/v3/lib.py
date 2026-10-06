"""
Shared geometry helpers for the v3 (IP3251) procedural build. Lead-owned; part agents import, never edit.
Product coordinates: (x right, up, fwd) in meters; floor at up = 0; VacuumRoot origin = centre of the floorhead
intake footprint; product front = +fwd. Blender authoring: Z-up, front = Blender -Y  (V(x, up, fwd) -> (x, -fwd, up)).
The glTF exporter maps Blender (x,y,z) -> glTF (x,z,-y): product +fwd becomes glTF +Z.

Detail level: call set_tier("high"|"balanced") before building. D[...] keys: corner, lathe, path, bevel_seg.
Materials: MATS is filled by materials.make_materials(); pass a material NAME (str) to mk/lathe/... .
"""
import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

TAU = math.tau
DETAIL = {
    "high": {"lathe": 200, "corner": 9, "bevel_seg": 5, "roller_rings": 110, "roller_segs": 160, "path": 2.5},
    "balanced": {"lathe": 96, "corner": 5, "bevel_seg": 3, "roller_rings": 44, "roller_segs": 80, "path": 1.2},
}
D = dict(DETAIL["high"])
MATS = {}


def set_tier(tier):
    D.clear()
    D.update(DETAIL[tier])


class _Coll:
    obj = None


def COLL_LINK(ob):
    (_Coll.obj or bpy.context.scene.collection).objects.link(ob)
    return ob

# =====================================================================================  coordinates
def V(x, up, fwd):
    """product coords (x, up, fwd) -> Blender vector"""
    return Vector((x, -fwd, up))


def PV(x, up, fwd):
    return Vector((x, up, fwd))


def toB(p):
    return Vector((p[0], -p[2], p[1]))


# =====================================================================================  mesh helpers


def link(ob):
    return COLL_LINK(ob)


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
    me.materials.append(MATS[mat] if isinstance(mat, str) else mat)
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


# ---------------------------------------------------------------- rig / scene utilities
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


