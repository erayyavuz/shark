"""
handheld part (v2, IA3246GN Sagewood) — hand vacuum (motor housing, front cyclone module, rear dust bin, handle
loop, battery, top UI screen). Owned by the handheld agent. See ../PARTS_CONTRACT.md.

Local frame: everything is authored in millimetres as (x, h, r):
  x  = product x (right when looking at the front), h = height above the floor, r = depth BEHIND the column front
  face (positive toward the handle / rear).  Column front face fwd = F_FRONT (metres).

Dimension ledger (mm).  Sources:
  [H1]   sn-gn-hero.png, Sagewood front, 1.559 px/mm, floor y=1886 (zoomed cap crop 6.236 px/mm)
  [SP13] IA3000 Luxe social-proof video, t=12.5 s: pure left-side elevation of the docked handheld (2.98 px/mm,
         anchored on the POWERDETECT band bottom = 1047)
  [H1V]  IA3241 Highlight1 video t=0.3 s (right side, slight 3/4)       [GAL1] sn-gal1.jpg (Sagewood handle/battery)
  [M6]   owner's guide p.6 handheld line drawing (side)  [M12] p.12 UI screen (power / mode / LED ring / icons)
  [F075] luxemoe frame 075 (Sagewood, top of the column: dark UI screen on the cap top)
  [inf]  inferred
"""
import math

import bpy
import bmesh
from mathutils import Vector

import lib
from lib import V, mk, bevel, fillet, ring_mesh, TAU

G = "MotorAssembly"

# ------------------------------------------------------------------ ledger (mm unless noted)
TOP = 1140.0            # cap top, docked [spec]
BOT = 835.0             # handheld bottom plane [params]
COL_W = 90.0            # column width [H1 140 px]
COL_D = 42.0            # column depth at bin level [SP13 r 0..42]
BODY_BEV = 11.0         # x-edge roundover of the main shell [H1 cap corner ~12 mm]
AXIS_R = 21.0           # wand axis sits under the column centre [SP13 dark neck r 0..42]
# front module (Shark plate / POWERDETECT band / copper shroud / cyclone window) [H1 zoom]
MOD_W, MOD_D, MOD_RF, MOD_RB = 76.0, 36.0, 15.0, 3.0
PLATE_H0, PLATE_H1, PLATE_TOPR = 1061.0, 1107.0, 10.0
BAND_H0, BAND_H1 = 1043.6, 1060.4
COP_H0, COP_H1 = 1008.0, 1043.0
COP_ROWS = ((1009.6, 1029.6), (1035.6, 1041.8))   # lower / upper rib rows [H1 zoom]
RIB_PITCH, RIB_DEPTH = 1.9, 1.4
WIN_H0, WIN_H1, WIN_BOTR, WIN_WALL = 860.0, 1007.4, 14.0, 1.8
CHEEK_TRIM = 12.0       # cheeks recede so the module wraps the front corners [SP13 clear visible r 2..17]
# rear dust bin [SP13]
BIN_X, BIN_R0, BIN_R1 = 37.0, 44.0, 124.0
BIN_WALL = 2.0
HOUSE_BOT_SLOPE = 24.0 / 84.0      # housing bottom / bin top line (42,980) -> (126,1004)
BIN_BOT_SLOPE = 0.25               # bin floor rises toward the rear ~14 deg [M6, SP13 cradle]
# battery (pill, axis tilted 16 deg) [SP13, H1V, GAL1]
BAT_F = (125.0, 1035.5)     # front end centre; front tip butts the housing rear face at r ~111 [SP13]
BAT_B = (237.0, 1068.5)
BAT_T, BAT_W = 28.0, 80.0   # XIABTR540 flat-lay ~151 x 82 [TECH ref]
# grip [SP13, H1V]
GRIP_F = (80.0, 1107.0)
GRIP_B = (206.0, 1121.0)
GRIP_W, GRIP_T = 36.0, 30.0
# UI screen on the cap top [F075, M12]


def _P():
    import params
    return params


F_FRONT = 0.0   # set in build()


def W(x, h, r):
    """local mm (x, h, r) -> Blender vector"""
    return V(x / 1000.0, h / 1000.0, F_FRONT - r / 1000.0)


def Pp(x, h, r):
    """local mm -> product coords tuple (m)"""
    return (x / 1000.0, h / 1000.0, F_FRONT - r / 1000.0)


SIDE = lambda u, v, w: W(w, v, u)        # side profile (u=r, v=h) extruded along x=w
PLAN = lambda u, v, w: W(u, w, v)        # plan (u=x, v=r) extruded along h=w
FRONT = lambda u, v, w: W(u, v, w)       # front (u=x, v=h) extruded along r=w


# ------------------------------------------------------------------ generic helpers
def arc(cx, cy, R, a0, a1, n):
    return [(cx + R * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + R * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def plan_poly(w, d, rf, rb, n=12):
    """rounded rect in (x, r): front edge r=0 (corner radius rf), back edge r=d (radius rb). Starts at front centre."""
    pts = [(0.0, 0.0)]
    pts += arc(w / 2 - rf, rf, rf, -90, 0, n)
    pts += arc(w / 2 - rb, d - rb, rb, 0, 90, max(2, n // 3))
    pts += arc(-w / 2 + rb, d - rb, rb, 90, 180, max(2, n // 3))
    pts += arc(-w / 2 + rf, rf, rf, 180, 270, n)
    out = []
    for p in pts:
        if not out or (Vector(p) - Vector(out[-1])).length > 1e-6:
            out.append(p)
    if (Vector(out[0]) - Vector(out[-1])).length < 1e-6:
        out.pop()
    return out


def resample(pts, M):
    P = [Vector(p) for p in pts]
    N = len(P)
    seg = [(P[(i + 1) % N] - P[i]).length for i in range(N)]
    L = sum(seg)
    out = []
    i, acc = 0, 0.0
    for k in range(M):
        s = L * k / M
        while acc + seg[i] < s and i < N - 1:
            acc += seg[i]
            i += 1
        t = (s - acc) / max(seg[i], 1e-9)
        q = P[i].lerp(P[(i + 1) % N], t)
        out.append((q.x, q.y))
    return out, L


def normals2d(pts, centre):
    N = len(pts)
    out = []
    for i in range(N):
        a = Vector(pts[i - 1])
        b = Vector(pts[(i + 1) % N])
        t = (b - a).normalized()
        n = Vector((t.y, -t.x))
        if n.dot(Vector(pts[i]) - Vector(centre)) < 0:
            n = -n
        out.append(n)
    return out


def offset2d(pts, d, centre):
    ns = normals2d(pts, centre)
    return [(p[0] + n.x * d, p[1] + n.y * d) for p, n in zip(pts, ns)]


def loft(name, rings, mat, cap0=True, cap1=True, recalc=True, smooth=True):
    """rings: list of lists of Blender vectors"""
    verts, faces = ring_mesh(rings, cap0, cap1)
    return mk(name, verts, faces, mat, G, smooth=smooth, recalc=recalc)


def shell_tube(name, outer, inner, mat, top_open=False, smooth=True):
    """closed thin-walled tube from outer/inner ring stacks (same counts): outer + inner surfaces + end annuli"""
    n = len(outer[0])
    R = len(outer)
    verts = [v for r in outer for v in r] + [v for r in inner for v in r]
    off = R * n
    faces = []
    for i in range(R - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j))
            faces.append((off + i * n + j, off + (i + 1) * n + j, off + (i + 1) * n + j2, off + i * n + j2))
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((j, off + j, off + j2, j2))
        a, b = (R - 1) * n, off + (R - 1) * n
        faces.append((a + j, a + j2, b + j2, b + j))
    return mk(name, verts, faces, mat, G, smooth=smooth)


def boolean_cut(ob, cutters, union=False):
    for c in cutters:
        md = ob.modifiers.new("Cut", "BOOLEAN")
        md.operation = "UNION" if union else "DIFFERENCE"
        md.solver = "EXACT"
        md.object = c
        try:
            md.material_mode = "TRANSFER"
        except Exception:
            pass
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


def box(name, x0, x1, h0, h1, r0, r1, mat, bev=None, seg=2):
    verts = [W(x, h, r) for x in (x0, x1) for h in (h0, h1) for r in (r0, r1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mk(name, verts, faces, mat, G, smooth=False)
    if bev:
        bevel(ob, bev / 1000.0, seg)
    return ob


def prism(name, pts, mapf, w0, w1, mat, bev=None, seg=None, smooth=True):
    """2-D polygon (mm) extruded between w0..w1 (mm) through mapf; optional bevel (mm)"""
    ob = lib.extrude(name, pts, mapf, w0, w1, mat, G, smooth=smooth)
    if bev:
        bevel(ob, bev / 1000.0, seg)
    return ob


def stadium(cx, cy, length, h, n=10):
    """horizontal stadium centred at (cx,cy): total length incl. round ends, height h"""
    r = h / 2
    a = length / 2 - r
    return arc(cx + a, cy, r, -90, 90, n) + arc(cx - a, cy, r, 90, 270, n)


def tomb_scale(h, h_end, R, W_, upward=True):
    """x-scale for a front-view rounded corner of radius R at the end h_end of a part of width W_"""
    dh = (h - (h_end - R)) if upward else ((h_end + R) - h)
    if dh <= 0:
        return 1.0
    dh = min(dh, R)
    return (W_ - 2 * (R - math.sqrt(max(R * R - dh * dh, 0.0)))) / W_


# ------------------------------------------------------------------ module plan
def mod_front_r(x):
    """front surface depth r(x) of the module plan (mm)"""
    flat = MOD_W / 2 - MOD_RF
    ax = abs(x)
    if ax <= flat:
        return 0.0
    dx = min(ax - flat, MOD_RF - 1e-6)
    return MOD_RF - math.sqrt(MOD_RF ** 2 - dx * dx)


def mod_plan(step, grow=0.0, w=MOD_W, d=MOD_D):
    base = plan_poly(w + 2 * grow, d + grow, MOD_RF + grow, MOD_RB + grow, 24)
    base = [(x, r - grow) for x, r in base]
    _, L = resample(base, 64)
    M = max(48, int(round(L / step)))
    M += M % 4 and (4 - M % 4)
    pts, L = resample(base, M)
    return pts, L


def ring_at(pts, h, xs=1.0, off=None, centre=(0.0, MOD_D / 2)):
    if off is not None:
        ns = normals2d(pts, centre)
        return [W(p[0] * xs + n.x * o, h, p[1] + n.y * o) for p, n, o in zip(pts, ns, off)]
    return [W(p[0] * xs, h, p[1]) for p in pts]


def offs(pts, d):
    return [d] * len(pts)


# ======================================================================== parts
# side-profile rear boundary r_max(h) of the main shell (front is r = 0) [SP13, H1V, M6]
REAR_CHAIN = [(COL_D, BOT), (COL_D, 980), (112, 1000), (112, 1094), (92, 1103), (88, 1122), (86, 1131)]
REAR_RAD = [0, 4, 6, 8, 6, 6, 0]
SH_RF, SH_RB = 40.0, 9.0      # plan corner radii: front (D-shaped end face, rt-controls photo / F075), rear
TOP_R, BOT_R = 13.0, 3.0      # roundover of the top end face / bottom


def rear_chain(q):
    pts = fillet(REAR_CHAIN, REAR_RAD, q["corner"])
    # fillet() treats the list as closed: drop wrap-around artefacts at both ends
    pts = [p for p in pts if BOT <= p[1] <= REAR_CHAIN[-1][1] + 1e-6]
    out = []
    for p in pts:
        if not out or p[1] > out[-1][1] + 1e-4:
            out.append(p)
    return out


def r_max(chain, h):
    if h <= chain[0][1]:
        return chain[0][0]
    for (r0, h0), (r1, h1) in zip(chain, chain[1:]):
        if h0 <= h <= h1:
            t = (h - h0) / max(h1 - h0, 1e-9)
            return r0 + (r1 - r0) * t
    return chain[-1][0]


def shell_plan(D, inset, M):
    i = inset
    rf = max(min(SH_RF, D - SH_RB - 1.0) - i, 0.8)
    rb = max(SH_RB - i, 0.8)
    pts = plan_poly(COL_W - 2 * i, D - 2 * i, rf, rb, 16)
    pts = [(x, r + i) for x, r in pts]
    out, _ = resample(pts, M)
    return out


def top_flat_D(q):
    return r_max(rear_chain(q), TOP - TOP_R)


def build_shell(q):
    """main Sagewood shell: column + motor housing + lower lobe around the battery front. Lofted along h from plan
    sections (x +-45, r 0..r_max(h)) with a D-shaped front, rounded top end face (UI screen) and bottom; pockets,
    vents, seams and the screen recess cut with exact booleans."""
    chain = rear_chain(q)
    M = q["shell_m"]
    hs = set(round(p[1], 3) for p in chain)
    h = BOT + BOT_R
    while h < TOP - TOP_R:
        hs.add(round(h, 3))
        h += q["shell_dh"]
    hs = sorted(x for x in hs if BOT + BOT_R <= x <= TOP - TOP_R)
    rings = []
    nb = 3
    for k in range(nb):  # bottom roundover
        ph = (math.pi / 2) * k / nb
        hh = BOT + BOT_R - BOT_R * math.cos(ph)
        rings.append([W(x, hh, r) for x, r in shell_plan(r_max(chain, hh), BOT_R * (1 - math.sin(ph)), M)])
    for hh in hs:
        rings.append([W(x, hh, r) for x, r in shell_plan(r_max(chain, hh), 0.0, M)])
    nt = q["top_n"]
    Dt = r_max(chain, TOP - TOP_R)
    for k in range(1, nt + 1):  # top roundover
        ph = (math.pi / 2) * k / nt
        hh = TOP - TOP_R + TOP_R * math.sin(ph)
        rings.append([W(x, hh, r) for x, r in shell_plan(Dt, TOP_R * (1 - math.cos(ph)), M)])
    sh = loft("HH_Shell", rings, "M_Sage")

    cutters = []
    gap = 0.6
    # 1. front module pocket (module plan grown by the seam gap), tombstone top corners
    pp, _ = mod_plan(1.5, grow=gap, d=MOD_D + 4)
    hs2 = [WIN_H0 - gap] + [PLATE_H1 + gap - PLATE_TOPR * (1 - k / 6) for k in range(7)]
    rr = []
    for h in hs2:
        xs = tomb_scale(h, PLATE_H1 + gap, PLATE_TOPR + gap, MOD_W + 2 * gap)
        rr.append([W(x * xs, h, r if r > 1 else r - 8) for x, r in pp])
    cutters.append(loft("cut_pocket", rr, "M_Sage"))  # diffuse light inner walls seen through the window [H1]
    # 2. cheek trim: the column sides recede behind the module so it wraps the front corners [SP13]
    cutters.append(box("cut_cheek", -60, 60, WIN_H0 - gap, PLATE_H1 - PLATE_TOPR, -10, CHEEK_TRIM, "M_Sage"))
    # 3. wand socket under the column (dark): the wand neck plugs in here
    sock = [(x, r + AXIS_R) for x, r in lib.rrect(50, 32, 9)]
    cutters.append(prism("cut_socket", sock, PLAN, BOT - 5, BOT + 4, "M_Graphite"))
    boolean_cut(sh, cutters)

    # 4. side vents: recessed louvre panel + 2 x 12 slots each side [rt-controls, H1V, SP13, M6]
    cut2 = []
    for s in (-1, 1):
        x0, x1 = (COL_W / 2 - 0.7, COL_W / 2 + 5) if s > 0 else (-COL_W / 2 - 5, -COL_W / 2 + 0.7)
        panel = fillet([(39, 1079), (65, 1079), (65, 1127), (39, 1127)], 3, q["corner"])
        cut2.append(prism(f"cut_ventpanel{s}", panel, SIDE, x0, x1, "M_Sage"))
    boolean_cut(sh, cut2)
    cut3 = []
    for s in (-1, 1):
        x0, x1 = (COL_W / 2 - 3.2, COL_W / 2 + 5) if s > 0 else (-COL_W / 2 - 5, -COL_W / 2 + 3.2)
        for col in ((41.0, 51.5), (53.0, 63.5)):
            for k in range(12):
                hc = 1082.4 + k * 3.8
                st = stadium((col[0] + col[1]) / 2, hc, col[1] - col[0], 2.0, 4)
                cut3.append(prism(f"cut_slot{s}{col[0]}{k}", st, SIDE, x0, x1, "M_Graphite", smooth=False))
        # seam between the column shell and the motor housing [SP13 r ~42]
        x0s, x1s = (COL_W / 2 - 0.8, COL_W / 2 + 5) if s > 0 else (-COL_W / 2 - 5, -COL_W / 2 + 0.8)
        cut3.append(box(f"cut_seam{s}", x0s, x1s, 983, 1076, 39.6, 40.3, "M_SageDeep"))
    boolean_cut(sh, [join(cut3, "cut_slots")])
    # 5. UI screen well in the top end face
    cut4 = prism("cut_screen", screen_outline(q, 0.0), PLAN, TOP - 1.4, TOP + 5, "M_Graphite")
    boolean_cut(sh, [cut4])
    return sh


# ------------------------------------------------------------------ UI screen [rt-ia3241-controls, M12, F075]
def screen_outline(q, inset):
    """outline (x, r) of the top end face's flat area shrunk by `inset` mm"""
    Dt = top_flat_D(q)
    i = TOP_R + inset
    pts = plan_poly(COL_W - 2 * i, Dt - 2 * i, max(SH_RF - i, 1.0), max(SH_RB - i, 1.0), 16)
    pts = [(x, r + i) for x, r in pts]
    out, _ = resample(pts, 160)
    return out


def outline_r_at(outline, x, rear=True):
    """r of the outline at abs(x) on the rear (or front) side"""
    best = None
    for (x0, r0), (x1, r1) in zip(outline, outline[1:] + outline[:1]):
        if (x0 - x) * (x1 - x) <= 0 and abs(x1 - x0) > 1e-9:
            r = r0 + (r1 - r0) * (x - x0) / (x1 - x0)
            if best is None or (rear and r > best) or (not rear and r < best):
                best = r
    return best


def build_screen(q, display, decals):
    import materials
    objs = []
    bez_o = screen_outline(q, 0.3)
    bez_i = screen_outline(q, 3.3)
    glass = screen_outline(q, 3.6)
    # brushed-silver bezel ring (raised 0.4 mm over the end face)
    hb0, hb1 = TOP - 1.4, TOP + 0.0
    outer = [[W(x, h, r) for x, r in bez_o] for h in (hb0, hb1 - 0.5)] + [[W(x, hb1, r) for x, r in screen_outline(q, 0.8)]]
    inner = [[W(x, h, r) for x, r in bez_i] for h in (hb0, hb1 - 0.5)] + [[W(x, hb1, r) for x, r in screen_outline(q, 2.8)]]
    objs.append(shell_tube("HH_ScreenBezel", outer, inner, "M_SilverBrush"))
    glass_h = TOP - 0.35
    gl = prism("HH_ScreenGlass", glass, PLAN, TOP - 1.4, glass_h, "M_Screen", bev=0.2, seg=2)
    objs.append(gl)
    rs = [r for _, r in glass]
    g_r0, g_r1 = min(rs), max(rs)
    g_w = 2 * max(abs(x) for x, _ in glass)
    g_d = g_r1 - g_r0
    # decal (icons + bar + battery/F0 icons). Owner's-guide layout: ink top at 15.5 % of the screen depth,
    # ink height 59 % / width 57 %; viewer stands behind the handle: viewer's right = product -x, glyph up = front.
    # atlas sub-rect (px in the 512x512 display slot): x 92..420, y 30..415 — tighter than the slot's 'ink' box, which
    # clips a stray glyph at its bottom edge. Icons span 59 % of the screen depth starting 15.5 % from its front.
    U0, U1 = 0.75 + 92 / 2048, 0.75 + 420 / 2048
    V1, V0 = 0.5625 - 30 / 1024, 0.5625 - 415 / 1024
    ih = 0.614 * g_d
    iw = ih * 328.0 / 385.0
    r_top = g_r0 + 0.142 * g_d
    nx = ny = 2
    verts, faces, uvs = [], [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            s_, t = i / nx, j / ny
            verts.append(W(iw / 2 - iw * s_, glass_h + 0.2, r_top + ih * (1 - t)))
            uvs.append((U0 + (U1 - U0) * s_, V0 + (V1 - V0) * t))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    dec = mk("HH_DisplayIcons", verts, faces, "M_Decal", G, smooth=False, uvs=uvs, recalc=False)
    _face_up(dec)
    decals.append(dec)
    objs.append(dec)
    # LED indicator ring: strip 2.0..3.6 mm inside the glass edge over the front half and down both sides
    r_lim = g_r0 + 0.62 * g_d
    o = screen_outline(q, 3.6 + 1.8)
    ii = screen_outline(q, 3.6 + 3.5)
    keep = [k for k, (x, r) in enumerate(o) if r < r_lim]
    # make the kept run contiguous around the front (outline starts at the front centre)
    n = len(o)
    run = []
    k = 0
    while (k % n) in keep and len(run) < n:
        run.append(k % n)
        k += 1
    k = n - 1
    left = []
    while k in keep and k not in run:
        left.append(k)
        k -= 1
    idx = left[::-1] + run
    verts = [W(o[k][0], glass_h + 0.25, o[k][1]) for k in idx] + [W(ii[k][0], glass_h + 0.25, ii[k][1]) for k in idx]
    m = len(idx)
    faces = [(i, i + 1, m + i + 1, m + i) for i in range(m - 1)]
    led = mk("HH_LEDRing", verts, faces, "M_LEDRing", G, smooth=False, recalc=False)
    _face_up(led)
    display.append(led)
    objs.append(led)
    # battery light bar, laid exactly over the atlas bar (px x 100..396, y 310..330 in the slot)
    bw = iw * 296.0 / 328.0
    bx = iw / 2 - iw * ((248.0 - 92.0) / 328.0)
    br = r_top + ih * ((320.0 - 30.0) / 385.0)
    bh = ih * 20.0 / 385.0
    bar = [(x + bx, r + br) for x, r in lib.rrect(bw, bh, bh / 2 - 0.01, 4)]
    lb = mk("HH_LightBar", [W(x, glass_h + 0.3, r) for x, r in bar], [tuple(range(len(bar)))], "M_LEDRing", G,
            smooth=False, recalc=False)
    _face_up(lb)
    display.append(lb)
    objs.append(lb)
    # POWER (viewer's left = +x) and MODE touch keys forming the rear edge of the screen [rt-controls, M12]
    k_r0 = g_r0 + 0.76 * g_d
    rear_o = screen_outline(q, 4.6)
    keys_c = {}
    for side, name in ((1, "Power"), (-1, "Mode")):
        poly = [(0.45 * side, k_r0)]
        xt = 0.29 * g_w
        poly.append((xt * side, k_r0))
        for t in range(1, 9):
            x = xt + (0.43 * g_w - xt) * t / 8
            rr_ = outline_r_at(rear_o, x * side)
            rk = min(k_r0 + (x - xt) * 1.1, rr_ if rr_ else k_r0 + 9)
            poly.append((x * side, rk))
        rr_ = outline_r_at(rear_o, 0.45 * side)
        poly.append((0.45 * side, rr_))
        if side < 0:
            poly = poly[::-1]
        kp = prism(f"HH_Key{name}", poly, PLAN, glass_h - 0.05, glass_h + 0.3, "M_Graphite", bev=0.15, seg=1)
        objs.append(kp)
        xs_ = [x for x, _ in poly]
        rs_ = [r for _, r in poly]
        keys_c[name] = ((min(xs_) + max(xs_)) / 2, (min(rs_) + max(rs_)) / 2)
    # key icons (printed light grey): power = ring with gap + stem, mode = 4-blade fan [rt-controls]
    ic = []
    cxp, crp = keys_c["Power"]
    hz = glass_h + 0.35
    pr = [math.radians(-55 + 290 * i / 28) - math.pi / 2 for i in range(29)]
    o_ = [(cxp + 2.6 * math.cos(t), crp - 2.6 * math.sin(t)) for t in pr]
    i_ = [(cxp + 2.0 * math.cos(t), crp - 2.0 * math.sin(t)) for t in pr]
    m = len(o_)
    ic.append(mk("HH_IconPower", [W(x, hz, r) for x, r in o_] + [W(x, hz, r) for x, r in i_],
                 [(i, i + 1, m + i + 1, m + i) for i in range(m - 1)], "M_SilverBrush", G, smooth=False, recalc=False))
    st = [(cxp - 0.3, crp - 3.1), (cxp + 0.3, crp - 3.1), (cxp + 0.3, crp - 0.3), (cxp - 0.3, crp - 0.3)]
    ic.append(mk("HH_IconPowerStem", [W(x, hz, r) for x, r in st], [(0, 1, 2, 3)], "M_SilverBrush", G, smooth=False,
                 recalc=False))
    cxm, crm = keys_c["Mode"]
    for b in range(4):
        a0 = b * TAU / 4 + 0.4
        bl = [(cxm, crm)]
        for i in range(7):
            t = a0 + 1.0 * i / 6
            rr_ = 3.0 * (0.25 + 0.75 * math.sin(math.pi * i / 6) ** 0.6)
            bl.append((cxm + rr_ * math.cos(t), crm + rr_ * math.sin(t)))
        ic.append(mk(f"HH_IconFan{b}", [W(x, hz, r) for x, r in bl], [tuple(range(len(bl)))], "M_SilverBrush", G,
                     smooth=False, recalc=False))
    for ob in ic:
        _face_up(ob)
    objs.extend(ic)
    return objs, Pp(cxp, TOP - 0.05, crp)


def _face_up(ob):
    """make a flat horizontal mesh face +up (Blender +Z)"""
    me = ob.data
    for p in me.polygons:
        if p.normal.z < 0:
            p.flip()
    me.update()


def _face_dir(ob, d):
    me = ob.data
    for p in me.polygons:
        if p.normal.dot(d) < 0:
            p.flip()
    me.update()


# ------------------------------------------------------------------ front module
def build_module(q, decals, objs):
    import materials
    gapz = 0.3
    # --- label plate (brushed grey 'Shark' plate) with tombstone top + 0.4 mm edge break
    pp, _ = mod_plan(q["plan_step"])
    hs = [PLATE_H0, PLATE_H0 + 0.4]
    top = PLATE_H1
    nk = 7
    hs += [top - PLATE_TOPR + PLATE_TOPR * math.sin(math.pi / 2 * k / nk) for k in range(nk + 1)]
    rings = []
    for h in hs:
        xs = tomb_scale(h, top, PLATE_TOPR, MOD_W)
        o = -0.4 if h in (PLATE_H0,) else 0.0
        rings.append(ring_at(pp, h, xs, offs(pp, o)))
    plate = loft("HH_SharkPlate", rings, "M_PlateGrey")
    objs.append(plate)
    # --- brushed silver POWERDETECT band
    hs = [BAND_H0, BAND_H0 + 0.4, BAND_H1 - 0.4, BAND_H1]
    rings = [ring_at(pp, h, 1.0, offs(pp, -0.4 if h in (BAND_H0, BAND_H1) else 0.0)) for h in hs]
    band = loft("HH_PDSBand", rings, "M_SilverBrush")
    objs.append(band)
    # thin dark separating line between plate and band [H1 zoom]
    rings = [ring_at(pp, h, 1.0, offs(pp, -0.35)) for h in (BAND_H1, PLATE_H0)]
    objs.append(loft("HH_PlateSeam", rings, "M_Graphite"))

    # --- decals: conform to the module front surface
    def decal(name, slot, wid, hc, hgt, nx=16):
        verts, faces, uvs = [], [], []
        for j in range(2):
            for i in range(nx + 1):
                s, t = i / nx, j
                x = -wid / 2 + wid * s
                h = hc - hgt / 2 + hgt * t
                rr = mod_front_r(x) - 0.25
                # push along the plan normal so the plate stays parallel to the surface around the corners
                verts.append(W(x, h, rr))
                uvs.append(materials.decal_uv(slot, s, t))
        for i in range(nx):
            faces.append((i, i + 1, nx + 2 + i, nx + 1 + i))
        ob = mk(name, verts, faces, "M_Decal", G, smooth=True, uvs=uvs, recalc=False)
        _face_dir(ob, Vector((0, -1, 0)))
        decals.append(ob)
        objs.append(ob)

    decal("HH_DecalShark", "shark_white", 46.0, 1078.5, 46.0 / 3.7957)
    decal("HH_DecalPDS", "pds_band_dark", 59.0, 1050.8, 59.0 / 14.1654, nx=20)

    # --- copper cyclone shroud: two rows of vertical fins on a satin copper ring [H1 zoom]
    cp, L = mod_plan(q["rib_step"])
    M = len(cp)
    per = max(2, int(round(RIB_PITCH / (L / M))))
    pat = []
    for i in range(M):
        x, r = cp[i]
        if r > 26:
            pat.append(-RIB_DEPTH)
            continue
        k = i % per
        pat.append(0.0 if (per >= 4 and k in (1,)) or (per < 4 and k == 0) else -RIB_DEPTH)
    flush = offs(cp, 0.0)
    core = offs(cp, -RIB_DEPTH)
    edge = offs(cp, -0.45)
    spec = [(COP_H0, edge), (COP_H0 + 0.45, flush)]
    for (a, b) in COP_ROWS:
        spec += [(a - 0.25, flush), (a, core), (a + 0.12, pat), (b - 0.12, pat), (b, core), (b + 0.25, flush)]
    spec += [(COP_H1 - 0.45, flush), (COP_H1, edge)]
    rings = [ring_at(cp, h, 1.0, o) for h, o in spec]
    cop = loft("HH_CopperShroud", rings, "M_Copper", smooth=True)
    cop.data.set_sharp_from_angle(angle=math.radians(50))
    # groove floors + groove side walls in the darker brushed copper so the fine ribs read at hero scale [H1]
    me = cop.data
    me.materials.append(lib.MATS["M_CopperBrush"])
    nring = len(cp)
    deep = set()
    for i, (_, o) in enumerate(spec):
        for j in range(nring):
            if o[j] <= -RIB_DEPTH + 1e-6:
                deep.add(i * nring + j)
    for poly in me.polygons:
        vs = list(poly.vertices)
        if sum(1 for v in vs if v in deep) >= 2:
            poly.material_index = 1
    me.update()
    objs.append(cop)

    # --- clear cyclone window (thin wall), rounded bottom corners in front view
    wp, _ = mod_plan(q["plan_step"])
    hs = []
    nb = 7
    hs += [WIN_H0 + WIN_BOTR - WIN_BOTR * math.sin(math.pi / 2 * (nb - k) / nb) for k in range(nb + 1)]
    hs += [WIN_H1]
    outer, inner = [], []
    wn = normals2d(wp, (0, MOD_D / 2))
    for h in hs:
        xs = tomb_scale(h, WIN_H0, WIN_BOTR, MOD_W, upward=False)
        outer.append(ring_at(wp, h, xs))
        hi = min(h + WIN_WALL, WIN_H1)
        xs_i = tomb_scale(hi, WIN_H0 + WIN_WALL, WIN_BOTR - WIN_WALL, MOD_W - 2 * WIN_WALL, upward=False)
        inner.append([W(p[0] * xs_i - n.x * WIN_WALL, hi, p[1] - n.y * WIN_WALL) for p, n in zip(wp, wn)])
    # open-back C section (front + wrapped sides to r=WIN_BACK): one clear wall = 2 interfaces on any camera path
    # (a closed sleeve + thin-walled duct exceeded Cycles' transmission bounce budget and rendered the window black)
    WIN_BACK = 26.0
    n = len(wp)
    right = []
    for k in range(n):
        if wp[k][1] > WIN_BACK:
            break
        right.append(k)
    left = []
    for k in range(n - 1, 0, -1):
        if wp[k][1] > WIN_BACK:
            break
        left.append(k)
    idx = list(reversed(right)) + left  # +x back -> front centre -> -x back
    m = len(idx)
    R = len(hs)
    verts = []
    for i in range(R):
        verts += [outer[i][k] for k in idx]
    for i in range(R):
        verts += [inner[i][k] for k in idx]
    off = R * m
    faces = []
    for i in range(R - 1):
        for j in range(m - 1):
            faces.append((i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j))
            faces.append((off + i * m + j, off + (i + 1) * m + j, off + (i + 1) * m + j + 1, off + i * m + j + 1))
        for j in (0, m - 1):  # vertical side edges of the C
            faces.append((i * m + j, (i + 1) * m + j, off + (i + 1) * m + j, off + i * m + j))
    for i in (0, R - 1):      # bottom / top edges
        for j in range(m - 1):
            faces.append((i * m + j, off + i * m + j, off + i * m + j + 1, i * m + j + 1))
    win = mk("HH_CycloneWindow", verts, faces, "M_ClearBin", G)
    objs.append(win)
    return win


def build_cyclone_internals(q, objs):
    """what is seen through the front window [H1]: round clear cyclone chamber with a perforated chrome dome,
    curved inlet duct rising from the wand port, bottom rosette, two vertical inner ribs, frosted back plate."""
    hc, xc = 950.0, 0.0
    # frosted back plate
    # chamber ring (axis = depth)
    prof = [(29.6, 0.0), (31.2, 0.0), (31.2, 21.0), (29.6, 21.0)]
    ring = lib.lathe("HH_CycChamber", [(a / 1000, b / 1000) for a, b in prof], Pp(xc, hc, 7.0), (0, 0, -1), (0, 1, 0),
                     "M_ClearBin", G, segs=q["lathe"], closed=True)
    objs.append(ring)
    # chamber back disc (smoked) and front lip
    disc = lib.lathe("HH_CycDisc", [(0.0, 0.0), (0.0306, 0.0), (0.0306, 0.0012), (0.0, 0.0012)], Pp(xc, hc, 27.0),
                     (0, 0, -1), (0, 1, 0), "M_ClearBin", G, segs=q["lathe"], closed=True)
    objs.append(disc)
    # perforated chrome dome (star-corrugated mesh cone) [H1]
    dprof = []
    for i in range(13):
        t = i / 12
        dprof.append((16.0 * math.cos(t * math.pi / 2) / 1000, (5.5 * math.sin(t * math.pi / 2)) / 1000))
    dome = lib.lathe("HH_CycMeshDome", dprof, Pp(xc + 1.0, hc + 4.0, 20.0), (0, 0, 1), (0, 1, 0), "M_Chrome", G,
                     segs=q["lathe"], cap0=True, cap1=False,
                     rmod=lambda th, h, r: r * (1.0 + 0.06 * math.cos(24 * th)))
    objs.append(dome)
    # vortex finder collar around the dome
    vf = [(16.2, 0.0), (19.0, 0.0), (19.0, 9.0), (16.2, 9.0)]
    objs.append(lib.lathe("HH_CycCollar", [(a / 1000, b / 1000) for a, b in vf], Pp(xc + 1.0, hc + 4.0, 13.0),
                          (0, 0, -1), (0, 1, 0), "M_ClearBin", G, segs=q["lathe"] // 2, closed=True))
    # inlet duct: thin-walled tube rising from the wand port and turning into the chamber tangentially
    path = lib.bezier_path(Vector((2.0, 866.0, 16.0)), Vector((2.0, 910.0, 16.0)), Vector((-6.0, 930.0, 15.0)),
                           Vector((-22.0, 955.0, 15.0)), q["duct_n"])
    path = path + [Vector((-27.0, 963.0, 15.0))]
    secn = q["duct_secn"]

    def tube_rings(rad):
        rings = []
        N = len(path)
        for i, c in enumerate(path):
            a = path[max(i - 1, 0)]
            b = path[min(i + 1, N - 1)]
            T = (b - a).normalized()
            B = Vector((0, 0, 1))
            Nn = T.cross(B).normalized()
            B2 = Nn.cross(T).normalized()
            rings.append([W(*(c + (Nn * math.cos(TAU * j / secn) + B2 * math.sin(TAU * j / secn)) * rad))
                          for j in range(secn)])
        return rings

    duct = loft("HH_CycDuct", tube_rings(9.5), "M_ClearBin")   # solid acrylic look: 2 interfaces (Cycles bounce budget)
    objs.append(duct)
    # bottom port rosette (smoked) with 8 radial fins
    # bottom inlet cone + rosette (vortex outlet seen at the window bottom) [H1]
    cone = [(0.0, 0.8605), (0.0135, 0.8605), (0.0135, 0.8635), (0.0110, 0.8665), (0.0062, 0.8770), (0.0050, 0.8790),
            (0.0, 0.8790)]
    objs.append(lib.lathe_up("HH_CycCone", cone, F_FRONT - 0.016, "M_ClearBin", G, segs=q["lathe"] // 2))
    rose = [(0.0, 0.8790), (0.0052, 0.8790), (0.0052, 0.8810), (0.0035, 0.8830), (0.0, 0.8835)]
    objs.append(lib.lathe_up("HH_CycRosette", rose, F_FRONT - 0.016, "M_Chrome", G, segs=q["lathe"] // 2,
                             rmod=lambda th, h, r: r * (1.0 + 0.12 * math.cos(8 * th))))
    fins = []
    for k in range(8):
        a_ = TAU * k / 8
        pts = []
        for (rad, hh) in ((6.0, 877.0), (13.0, 864.0)):
            pts.append((rad, hh))
        cx0, cr0 = 6.0 * math.cos(a_), 16.0 + 6.0 * math.sin(a_)
        cx1, cr1 = 13.0 * math.cos(a_), 16.0 + 13.0 * math.sin(a_)
        nx, nr = -math.sin(a_) * 0.45, math.cos(a_) * 0.45
        vv = [W(cx0 + nx, 877.5, cr0 + nr), W(cx0 - nx, 877.5, cr0 - nr), W(cx1 - nx, 863.5, cr1 - nr),
              W(cx1 + nx, 863.5, cr1 + nr), W(cx0 + nx, 870.0, cr0 + nr), W(cx0 - nx, 870.0, cr0 - nr),
              W(cx1 - nx, 860.6, cr1 - nr), W(cx1 + nx, 860.6, cr1 + nr)]
        ff = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        fins.append(mk(f"HH_CycFin{k}", vv, ff, "M_ClearBin", G, smooth=False))
    objs.append(join(fins, "HH_CycFins"))
    # vertical inner ribs [H1 lines at x ~ +-25]
    for s in (-1, 1):
        objs.append(box(f"HH_CycRib{s}", s * 25.0 - 0.6, s * 25.0 + 0.6, 862.0, 925.0, 8.0, 30.0, "M_ClearBin"))


# ------------------------------------------------------------------ rear dust bin
def bin_bottom(r):
    return 848.0 + (r - BIN_R0) * BIN_BOT_SLOPE


def bin_top(r):
    return 980.0 + (r - 42.0) * HOUSE_BOT_SLOPE + 3.0


def build_bin(q, objs):
    plan = plan_poly(2 * BIN_X, BIN_R1 - BIN_R0, 3.0, 12.0, q["corner"])
    plan = [(x, r + BIN_R0) for x, r in plan]
    pts, _ = resample(plan, q["bin_n"])
    cen = (0.0, (BIN_R0 + BIN_R1) / 2)
    ipts = offset2d(pts, -BIN_WALL, cen)
    ts = [0.0, 0.02, 0.5, 1.0]

    def stack(pp, inset_bot):
        rings = []
        for t in ts:
            ring = []
            for x, r in pp:
                hb = bin_bottom(r) + inset_bot
                h = hb + t * (bin_top(r) - hb)
                ring.append(W(x, h, r))
            rings.append(ring)
        return rings

    shell = shell_tube("HH_DustbinShell", stack(pts, 0.0), stack(ipts, 0.0), "M_ClearBin")
    objs.append(shell)
    # smoked inner separator: stepped wall (upper filter chamber + lower channel) [SP13]
    wall = [(78, 1001), (78, 942), (60, 942), (60, 896), (46.5, 896), (46.5, 897.6), (58.4, 897.6), (58.4, 943.6),
            (76.4, 943.6), (76.4, 1001)]
    sep = prism("HH_BinSeparator", wall, SIDE, -BIN_X + BIN_WALL + 0.3, BIN_X - BIN_WALL - 0.3, "M_ClearBin")
    objs.append(sep)
    # copper pre-filter mesh cone in the upper chamber [GAL1]
    prof = [(0.0, 0.0)]
    for i in range(9):
        t = i / 8
        prof.append(((11.0 - 4.0 * t) / 1000, (18.0 * t) / 1000))
    prof.append((0.0, 0.018))
    cone = lib.lathe("HH_BinMeshCone", prof, Pp(0.0, 965.0, 76.0), (0, 0, 1), (0, 1, 0), "M_CopperSatin", G,
                     segs=q["lathe"] // 2, cap0=False, cap1=False,
                     rmod=lambda th, h, r: r * (1.0 + 0.05 * math.cos(30 * th)))
    objs.append(cone)
    # bottom door (opens for auto-empty) + front hinge + rear latch [M p.16, SP13]
    dplan = offset2d(pts, 0.4, cen)
    rings = []
    for dz in (-3.6, -3.1, -0.4, 0.0):
        rings.append([W(x, bin_bottom(r) + dz, r) for x, r in dplan])
    door = loft("HH_BinDoor", rings, "M_SageDeep")
    objs.append(door)
    for s in (-1, 1):
        objs.append(lib.lathe_x("HH_BinHinge%d" % s, [(0.0, s * 0.020), (0.0024, s * 0.020), (0.0024, s * 0.032),
                                                    (0.0, s * 0.032)], (bin_bottom(46) - 3.0) / 1000,
                                F_FRONT - 0.0455, "M_SageDeep", G, segs=24))
    latch = [(BIN_R1 - 1.0, bin_bottom(BIN_R1) - 3.5), (BIN_R1 + 3.2, bin_bottom(BIN_R1) - 3.5),
             (BIN_R1 + 3.2, bin_bottom(BIN_R1) + 26.0), (BIN_R1 + 1.5, bin_bottom(BIN_R1) + 28.0),
             (BIN_R1 - 1.0, bin_bottom(BIN_R1) + 28.0)]
    objs.append(prism("HH_BinLatch", fillet(latch, [0.4, 1.0, 1.0, 1.0, 0.4], 3), SIDE, -11.0, 11.0, "M_SageDeep",
                      bev=0.6, seg=2))
    return shell


def build_contents(q):
    plan = plan_poly(2 * BIN_X - 2 * BIN_WALL - 1.0, BIN_R1 - BIN_R0 - 2 * BIN_WALL - 1.0, 2.0, 10.0, 6)
    plan = [(x, r + BIN_R0 + BIN_WALL + 0.5) for x, r in plan]
    pts, _ = resample(plan, 64)
    top_h = 120.0
    rings = []
    for t in (0.0, 0.5, 0.9, 1.0):
        ring = []
        for x, r in pts:
            hb = bin_bottom(r) + 0.3
            bump = 0.0
            if t >= 0.9:
                bump = (3.0 * math.sin(x * 0.21) * math.cos(r * 0.17) - 4.0 * ((x / BIN_X) ** 2)) * (1.0 if t == 1.0 else 0.4)
            ring.append(W(x, hb + t * top_h + bump, r))
        rings.append(ring)
    ob = loft("DustbinContents", rings, "M_Dust")
    rc = (BIN_R0 + BIN_R1) / 2
    lib.set_origin(ob, W(0.0, bin_bottom(rc) + 0.3, rc))
    return ob


# ------------------------------------------------------------------ handle loop + battery
def bat_map(a, b):
    """battery local (a along the axis from the front end centre, b up-normal) -> (r, h)"""
    th = math.atan2(BAT_B[1] - BAT_F[1], BAT_B[0] - BAT_F[0])
    return (BAT_F[0] + a * math.cos(th) - b * math.sin(th), BAT_F[1] + a * math.sin(th) + b * math.cos(th))


def bat_len():
    return math.hypot(BAT_B[0] - BAT_F[0], BAT_B[1] - BAT_F[1])


def build_battery(q, decals, objs):
    import materials
    L = bat_len()
    R = BAT_T / 2
    pill = arc(L, 0, R, -90, 90, q["corner"] + 4) + arc(0, 0, R, 90, 270, q["corner"] + 4)
    prof = [bat_map(a, b) for a, b in pill]
    body = prism("HH_Battery", prof, SIDE, -BAT_W / 2, BAT_W / 2, "M_Graphite", bev=2.2, seg=q["small_seg"])
    objs.append(body)
    # raised side plates: main grey plate (Shark) + lighter rear end cap with the release button [SP13, GAL1]
    split = L - 10.0
    for s in (-1, 1):
        x0, x1 = (BAT_W / 2 - 0.3, BAT_W / 2 + 0.9) if s > 0 else (-BAT_W / 2 - 0.9, -BAT_W / 2 + 0.3)
        ri = R - 3.0
        main = arc(split - 0.5, 0, 0.01, -90, -90, 1)[:1]
        main = [(split - 0.4, -ri), (split - 0.4, ri)] + arc(8.0, 0, ri, 90, 270, q["corner"] + 2)
        p = prism(f"HH_BatPlate{s}", [bat_map(a, b) for a, b in main], SIDE, x0, x1, "M_PlateGrey", bev=0.45, seg=2)
        objs.append(p)
        endc = arc(L, 0, ri, -90, 90, q["corner"] + 2) + [(split + 0.4, ri), (split + 0.4, -ri)]
        e = prism(f"HH_BatEnd{s}", [bat_map(a, b) for a, b in endc], SIDE, x0, x1, "M_SilverBrush", bev=0.45, seg=2)
        objs.append(e)
        # round button / indicator: dark ring with a dark-glass centre
        cx = bat_map(L + 2.0, 0.0)
        xs = x1 if s > 0 else x0
        btn = lib.lathe_x(f"HH_BatButton{s}", [(0.0, 0.0), (0.0052, 0.0), (0.0052, 0.0009), (0.0040, 0.0013), (0.0, 0.0013)],
                          cx[1] / 1000, F_FRONT - cx[0] / 1000, "M_Graphite", G, segs=32)
        # lathe_x revolves about +x through x=0: shift it to the plate face
        for v in btn.data.vertices:
            v.co.x = v.co.x * s + xs / 1000.0
        btn.data.update()
        objs.append(btn)
        glass = lib.lathe_x(f"HH_BatLens{s}", [(0.0, 0.0), (0.0031, 0.0), (0.0031, 0.0006), (0.0, 0.0008)],
                            cx[1] / 1000, F_FRONT - cx[0] / 1000, "M_Screen", G, segs=24)
        for v in glass.data.vertices:
            v.co.x = v.co.x * s + (xs + s * 1.15) / 1000.0
        glass.data.update()
        objs.append(glass)
        # 'Shark' on the battery plate (reads left-to-right for a viewer on that side, glyph up = +h)
        wid, hgt = 28.0, 28.0 / 3.7957
        ac = 46.0
        verts, faces, uvs = [], [], []
        for j in range(2):
            for i in range(2):
                a = ac - wid / 2 + wid * i
                b = -hgt / 2 + hgt * j
                r_, h_ = bat_map(a, b)
                # viewer on +x side looks toward -x: their right = toward the front (smaller r); on -x: toward rear
                if s < 0:
                    r_, h_ = bat_map(ac + wid / 2 - wid * i, b)
                verts.append(W(xs + s * 0.25, h_, r_))
                uvs.append(materials.decal_uv("shark_white", i, j))
        faces = [(0, 1, 3, 2)]
        dec = mk(f"HH_DecalBatShark{s}", verts, faces, "M_Decal", G, smooth=False, uvs=uvs, recalc=False)
        _face_dir(dec, Vector((s, 0, 0)))
        decals.append(dec)
        objs.append(dec)
    # charging-contact / release block under the battery (dock charging-post saddle) [SP13 dark tab r 143..175]
    blk = []
    for a, b in ((19, -10), (48, -10), (48, -17.5), (45, -20.5), (22, -20.5), (19, -17.5)):
        blk.append(bat_map(a, b))
    objs.append(prism("HH_ContactBlock", fillet(blk, [0.5, 0.5, 1.5, 1.5, 1.5, 1.5], 3), SIDE, -15.0, 15.0,
                      "M_Graphite", bev=0.7, seg=2))
    for s in (-1, 1):
        c0 = bat_map(26, -20.4)
        c1 = bat_map(40, -20.4)
        pts = [c0, c1, bat_map(40, -21.0), bat_map(26, -21.0)]
        objs.append(prism(f"HH_Contact{s}", pts, SIDE, s * 7.0 - 2.5, s * 7.0 + 2.5, "M_Chrome", bev=0.3, seg=1))
    # Sagewood lobe under the battery front (part of the housing) [SP13 sage under the battery r 110..143]
    lob = [(100.0, 997.0), (125.0, 1003.0), (143.0, 1009.0), (146.0, 1016.0)]
    ua = (146.0 - BAT_F[0]) / math.cos(bat_theta())
    ub = (104.0 - BAT_F[0]) / math.cos(bat_theta())
    lob += [bat_map(ua, -BAT_T / 2 + 2.0), bat_map(ub, -BAT_T / 2 + 2.0)]
    objs.append(prism("HH_BatteryLobe", fillet(lob, [2, 6, 6, 4, 2, 1], q["corner"]), SIDE, -40.0, 40.0, "M_Sage",
                      bev=7.0, seg=q["round_seg"] - 2))
    return body


def bat_theta():
    return math.atan2(BAT_B[1] - BAT_F[1], BAT_B[0] - BAT_F[0])


def build_handle(q, objs):
    # black soft-touch grip (top bar of the handle loop)
    a = Vector(Pp(0, GRIP_F[1], GRIP_F[0]))
    b = Vector(Pp(0, GRIP_B[1], GRIP_B[0]))
    n = q["grip_n"]
    path = [a.lerp(b, i / n) for i in range(n + 1)]

    def sec(t):
        bulge = math.sin(math.pi * min(1.0, max(0.0, (t - 0.1) / 0.8)))
        return ((GRIP_W + 2.0 * bulge) / 1000, (GRIP_T + 1.5 * bulge) / 1000, 13.0 / 1000)

    grip = lib.sweep("HH_Grip", path, sec, "M_Rubber", G, cap_round=0.004)
    objs.append(grip)
    # finger rest bump under the front of the grip [M6, H1V]
    fb = []
    for i in range(9):
        t = i / 8
        fb.append((86.0 + 22.0 * t, GRIP_F[1] + (GRIP_B[1] - GRIP_F[1]) * (16.0 + 22.0 * t) / (GRIP_B[0] - GRIP_F[0])
                   - GRIP_T / 2 + 1.0 - 3.2 * math.sin(math.pi * t)))
    fb = fb + [(108.0, 1104.0), (86.0, 1104.0)]
    objs.append(prism("HH_GripBump", fb, SIDE, -12.0, 12.0, "M_Rubber", bev=2.0, seg=3))
    # rear bend (Sagewood): the handle loop curves down from the grip end onto the battery's rear half [H1V, SP13, AE3]
    bt = bat_map((228.0 - BAT_F[0]) / math.cos(bat_theta()), BAT_T / 2)
    bp = lib.bezier_path(Vector(Pp(0, 1121.5, 196.0)), Vector(Pp(0, 1125.0, 226.0)), Vector(Pp(0, 1114.0, 231.0)),
                         Vector(Pp(0, bt[1] - 3.0, 228.0)), q["grip_n"])

    def bsec(t):
        return (40.0 / 1000, (GRIP_T + 2.0 + 3.0 * t) / 1000, 13.0 / 1000)

    post = lib.sweep("HH_RearBend", bp, bsec, "M_Sage", G, cap_round=0.003)
    objs.append(post)
    return grip


# ======================================================================== build
def build(ctx):
    global F_FRONT
    P = ctx["P"]
    tier = ctx["tier"]
    F_FRONT = P.WAND_FWD + AXIS_R / 1000.0
    hi = tier == "high"
    q = {
        "corner": lib.D["corner"],
        "round_seg": 8 if hi else 5,
        "small_seg": 3 if hi else 2,
        "plan_step": 1.2 if hi else 2.4,
        "rib_step": 0.5 if hi else 1.0,
        "lathe": 96 if hi else 48,
        "bin_n": 128 if hi else 72,
        "duct_n": 20 if hi else 10,
        "duct_secn": 28 if hi else 16,
        "grip_n": 14 if hi else 8,
        "shell_m": 168 if hi else 96,
        "shell_dh": 6.0 if hi else 12.0,
        "top_n": 6 if hi else 3,
    }
    objs, decals, display = [], [], []
    shell = build_shell(q)
    objs.append(shell)
    scr, power_anchor = build_screen(q, display, decals)
    objs.extend(scr)
    build_module(q, decals, objs)
    build_cyclone_internals(q, objs)
    bin_shell = build_bin(q, objs)
    build_battery(q, decals, objs)
    build_handle(q, objs)
    contents = build_contents(q)
    for o in objs + [contents]:
        o["grp"] = G
    # dedupe (module helpers append into objs)
    seen, uniq = set(), []
    for o in objs:
        if o.name not in seen:
            seen.add(o.name)
            uniq.append(o)
    notes = (
        "Handheld IA3246GN. Local frame: column front face fwd = WAND_FWD + 0.021; wand axis under the column centre. "
        "UI screen is on the cap top (F075 + guide p.12), read from behind the handle; PowerControlAnchor = power key. "
        "Battery pill (76 W x 28 T, axis 16 deg) forms the handle-loop bottom; rear end at fwd = F - 0.251. "
        "Charging-contact block under the battery at r 156..185 mm behind the column front, h ~1.02 m (dock post saddle). "
        "Rear dust bin = DustbinShell (x +-37, r 44..124, floor slanted 848->868 mm); DustbinContents origin at bin floor "
        "centre, full-height scale = 120 mm. Front latch release button (handheld<->wand) is below 0.835 (wand agent)."
    )
    return {
        "groups": {G: uniq + [contents]},
        "special": {"DustbinShell": bin_shell, "DustbinContents": contents, "Display": display},
        "anchors": {
            "PowerControlAnchor": power_anchor,
            "MotorAssembly": (0.0, P.HANDHELD_BOTTOM_UP, P.WAND_FWD),
        },
        "notes": notes,
    }
