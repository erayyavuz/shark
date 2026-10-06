"""
wand part (v3, IP3251 / IP3251EUT; stick hardware = IP1251). Owned by the wand agent. See ../PARTS_CONTRACT.md.

Builds, in the upright rest pose along the wand axis (x = 0, fwd = P.WAND_FWD = A), from P.WAND_SOCKET_UP to
P.HANDHELD_BOTTOM_UP:
  LowerWand: grey cuff (mates the floorhead neck connector at 0.263) with the dark lock-tab pill in its slot and the
             'D' lock mark, bronze anodized tube (chamfered rounded-rect, 'soft facets'), the vertical
             "Shark POWERDETECT" decal plate (M_Decal), grey taper into the lower MultiFLEX housing (deepens toward the
             rear, front lobe toward the barrel), side windows with the black fold catch, centre hinge knuckle,
             lower flex-hose piece + port ring.
  UpperWand: upper MultiFLEX housing (deep box, front recedes upward), outer hinge knuckles + purple pivot caps,
             rear fold latch rail (tall dark pill, hangs over the lower housing's back), handheld-release button
             (dark stadium with thumb dish, side lugs) centred 0.034 below the handheld, top spigot, upper hose piece.

Fold mechanics: pivot axis = product X through FlexPivot (A + 0.025, barrel r 10.8 mm half embedded in both housings).
The housings are split by the horizontal plane through the pivot. All upper material lies behind the pivot, so a
positive rotation (handheld forward) only lifts it away from the lower half: the rear opens as a wedge and nothing
intersects (BVH-checked 0..180 deg; V2 shows the 180 deg storage fold with both mating faces flat on top, which is
exactly this split). Knuckles are coaxial cylinders -> invariant under rotation.
Flex hose = two rigid corrugated torus pieces about the pivot axis (radius HOSE_RC): LowerWand owns phi in
[-20, 47] deg, UpperWand owns phi_local in [-47, 20] deg (phi from the rear horizontal, upward). At fold t the union
covers [-20, t + 20], so the exposed wedge [0, t] is bridged for t <= 94 deg; at rest both pieces are hidden inside
the housings. The hose passes through dark port rings on both mating faces. (Beyond ~94 deg - the manual's storage
fold - the two stubs separate; a flexible hose would need a deform rig.)

Local ledger (relative to the wand axis A; [V7] = IP1251 front ortho 1.587 px/mm, [EUT] = cl-eut-01 1.555 px/mm minus
the 19 mm dock raise, [V2] = IP1251 side photo 3.62 px/mm (storage fold, pivot y 315), [PR4] = PRODUCT_REFERENCE §4):
  tube 35 x 46 [PR4/V7 34.7]; visible 0.2885..0.581 [V7 0.288..0.590, EUT 0.271..0.578, V2 0.287..0.578];
    chamfer 6 mm facets [crop-tr01-hinge-wand]
  cuff 0.263..0.288: 43 -> 37 wide [V7 0.250 44.7 / 0.266 42.2 / 0.282 37.2], dark lock pill at 0.2745 [V7 0.274]
  lower housing: flush with the tube at 0.581, front lobe +0.0235 -> +0.0265 at the pivot plane, rear -0.0233 ->
    -0.0402 [V2 depth 63 mm at the plane], width 36 -> 45 (0.628) -> 51 (0.652) [V7]; side window 17.5 x 27 mm with
    black catch at f -0.021..-0.004 [V2 hinge crop, user-1663]
  pivot 0.663 [PR4; EUT barrel centre 0.667]; barrel 51 wide + purple caps Ø23 x 5.3 -> 61.7 [V7 61.7, PR4 63]
  upper housing 51 wide to 0.680, 44.7 above [V7]; depth -0.041 -> -0.046 rear, front +0.023 receding to +0.011
    [V2 storage: arch inner edge f 0.008 at 0.726, rear f -0.046]
  release button stadium 33 x 48 bezel centred 0.778 [EUT/V7 0.760..0.805], side lugs -> 51 [V7 0.778 51.0];
  rear latch rail -0.029..+0.074 about the pivot plane [V2]
  decal text box [EUT]: up 0.362..0.537, x -5.5 (baseline) .. +7.4 mm (cap tops), reads top -> bottom
"""
import math

import bmesh
from mathutils import Vector

G_LO = "LowerWand"
G_UP = "UpperWand"

TUBE_W, TUBE_D = 0.035, 0.046
TUBE_CH = 0.0060          # facet chamfer
TUBE_FR = 0.0042          # fillet on the chamfer edges
TUBE_UP = (0.276, 0.592)  # incl. parts hidden in cuff / housing
TUBE_VIS = (0.2885, 0.581)
FRONT = 0.0235            # housing front face (rel. A)
PIVOT_OFF = 0.025
RB = 0.0114               # knuckle radius (barrel ~Ø23-25 in EUT/V7)
CAP_R = 0.0115            # purple cap radius (Ø23)
HALF_W = 0.0224           # knuckle half width; + caps = 51 overall [EUT 53, V7 50.7 incl. caps]
CAP_T = 0.0030
XC = 0.0074               # centre knuckle half width
CUT_GAP = 0.0003
HOSE_RC = 0.030
HOSE_R = 0.0092
REL_UP = 0.7735           # handheld-release button centre [EUT bezel 0.747..0.798]
SEAM2_UP = 0.7895         # seam line with side lugs across the upper wand [EUT/V7]
DECAL_SLOT = "wand_shark_powerdetect"
DECAL = {"up0": 0.3625, "up1": 0.5365, "x0": -0.0055, "x1": 0.0074}   # ink box 174 x 12.9 mm (baseline .. cap tops) [EUT]


def build(ctx):
    import bpy
    P, L = ctx["P"], ctx["lib"]
    D = L.D
    V = L.V
    A = P.WAND_FWD
    S0 = P.WAND_SOCKET_UP
    TOP = P.HANDHELD_BOTTOM_UP
    PU = P.FOLD_UP
    PF = A + PIVOT_OFF
    pivot = (0.0, PU, PF)
    high = ctx["tier"] == "high"
    made = {G_LO: [], G_UP: []}
    segs = 64 if high else 32

    def add(ob, g):
        made[g].append(ob)
        return ob

    def front_map(u, v, w):
        return V(u, v, w)

    def side_map(sign):
        return lambda u, v, w: V(sign * w, v, u)

    def oval(cx, cy, w, h, n=None):
        n = n or max(6, D["corner"] + 2)
        r = min(w, h) / 2 * 0.98
        return [(cx + px, cy + py) for px, py in L.rrect(w, h, r, n)]

    def circle(cx, cy, r, n=20):
        return [(cx + r * math.cos(math.tau * k / n), cy + r * math.sin(math.tau * k / n)) for k in range(n)]

    def ring_prism(name, outer, inner, mapf, w0, w1, mat, g, bev=None):
        n = len(outer)
        verts = [mapf(u, v, w0) for u, v in outer] + [mapf(u, v, w1) for u, v in outer]
        verts += [mapf(u, v, w0) for u, v in inner] + [mapf(u, v, w1) for u, v in inner]
        faces = []
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((j, j2, n + j2, n + j))
            faces.append((2 * n + j2, 2 * n + j, 3 * n + j, 3 * n + j2))
            faces.append((n + j, n + j2, 3 * n + j2, 3 * n + j))
            faces.append((j2, j, 2 * n + j, 2 * n + j2))
        ob = L.mk(name, verts, faces, mat, g)
        if bev:
            L.bevel(ob, bev, 2)
        return add(ob, g)

    def dished_button(name, cx, cy, w, h, z0, z1, depth, mat, g, dish_dy=-0.15):
        base = oval(cx, cy, w, h, n=max(8, D["corner"] + 4))
        dc = (cx, cy + dish_dy * h)
        rings = []
        prof = [(1.0, z0), (1.0, z1 - 0.0009), (0.985, z1 - 0.0003), (0.95, z1)]
        prof += [(sv, z1 - depth * max(0.0, 1 - (sv / 0.86) ** 2)) for sv in (0.86, 0.70, 0.54, 0.38, 0.22, 0.06)]
        for sv, z in prof:
            rings.append([V(dc[0] + sv * (u - dc[0]), dc[1] + sv * (v - dc[1]), z) for u, v in base])
        vv, ff = L.ring_mesh(rings, True, True)
        return add(L.mk(name, vv, ff, mat, g), g)

    def st(up, w, fr, rr, r):
        """loft station from front / rear offsets (rel. A)"""
        return (up, w, fr - rr, r, A + (fr + rr) / 2)

    def loft(name, stations, mat, g, sec=None):
        return add(L.loft_up(name, stations, mat, g, sec=sec), g)

    def bisect(ob, keep, gap):
        nb = Vector((0.0, 0.0, 1.0))
        co = V(*pivot) + nb * (gap if keep == "above" else -gap)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=nb,
                                     clear_outer=(keep == "below"), clear_inner=(keep == "above"))
        cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        bmesh.ops.holes_fill(bm, edges=cut, sides=0)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.set_sharp_from_angle(angle=math.radians(40))
        return ob

    def boolean(ob, cutter, op="DIFFERENCE"):
        md = ob.modifiers.new("Bool", "BOOLEAN")
        md.operation = op
        md.solver = "EXACT"
        md.object = cutter
        L.apply_modifiers(ob)
        bpy.data.objects.remove(cutter, do_unlink=True)
        ob.data.set_sharp_from_angle(angle=math.radians(40))
        return ob

    def band(name, up, h, w, fr, rr, r, mat, g, grow=0.00012):
        s0 = st(up - h / 2, w + 2 * grow, fr + grow, rr - grow, r + grow)
        s1 = st(up + h / 2, w + 2 * grow, fr + grow, rr - grow, r + grow)
        return loft(name, [s0, s1], mat, g)

    def tube_sec(w, d):
        c = TUBE_CH
        pts = [(w / 2, -d / 2 + c), (w / 2, d / 2 - c), (w / 2 - c, d / 2), (-w / 2 + c, d / 2),
               (-w / 2, d / 2 - c), (-w / 2, -d / 2 + c), (-w / 2 + c, -d / 2), (w / 2 - c, -d / 2)]
        return L.fillet(pts, TUBE_FR, max(3, D["corner"] - 3))

    def hose(name, phi0, phi1, g):
        nA = 80 if high else 40
        nC = 18 if high else 10
        pitch = 0.0034
        a0, a1 = math.radians(phi0), math.radians(phi1)
        arc_len = HOSE_RC * (a1 - a0)
        rings = []
        for i in range(nA + 1):
            a = a0 + (a1 - a0) * i / nA
            sl = arc_len * i / nA
            rr = HOSE_R - 0.0011 * (0.5 - 0.5 * math.cos(math.tau * sl / pitch)) ** 1.5
            cu = PU + HOSE_RC * math.sin(a)
            cf = PF - HOSE_RC * math.cos(a)
            rad = Vector((0.0, math.sin(a), -math.cos(a)))
            ring = []
            for j in range(nC):
                t = math.tau * j / nC
                p = Vector((0.0, cu, cf)) + Vector((math.cos(t) * rr, 0, 0)) + rad * (math.sin(t) * rr)
                ring.append(V(p.x, p.y, p.z))
            rings.append(ring)
        hv, hf = L.ring_mesh(rings, True, True)
        return add(L.mk(name, hv, hf, "M_Hose", g), g)

    def port_ring(name, g, sign):
        """dark annulus on a mating face around the hose passage (phi = 0)"""
        h0, h1 = (PU - 0.0009, PU - CUT_GAP + 0.00012) if sign < 0 else (PU + CUT_GAP - 0.00012, PU + 0.0009)
        prof = [(HOSE_R + 0.0004, h0), (HOSE_R + 0.0004, h1), (HOSE_R + 0.0028, h1), (HOSE_R + 0.0028, h0)]
        if sign > 0:
            prof = prof[::-1]
        return add(L.lathe_up(name, prof, PF - HOSE_RC, "M_Charcoal", g, segs=segs, closed=True), g)

    # ================================================================= LOWER WAND
    # ---- cuff: S0 .. tube (mates the floorhead neck connector top at S0)
    cuff = loft("WandCuff", [
        st(S0, 0.0428, 0.0255, -0.0255, 0.0115),
        st(S0 + 0.0030, 0.0430, 0.0258, -0.0258, 0.0118),
        st(0.2700, 0.0412, 0.0255, -0.0255, 0.0112),
        st(0.2800, 0.0386, 0.0247, -0.0247, 0.0102),
        st(0.2870, 0.0374, 0.0243, -0.0243, 0.0098),
        st(0.2890, 0.0366, 0.0238, -0.0238, 0.0094),
    ], "M_Gunmetal", G_LO)
    L.bevel(cuff, 0.0007, 2)
    band("CuffSeam", S0 + 0.0060, 0.0006, 0.0426, 0.0254, -0.0254, 0.0114, "M_Charcoal", G_LO)
    # lock-tab pill in its slot (front, just under the bronze) [V7 0.274, EUT, tr-part-flex]
    pu = 0.2748
    ring_prism("LockTabSlot", oval(0, pu, 0.0255, 0.0100), oval(0, pu, 0.0228, 0.0076), front_map,
               A + 0.0205, A + 0.0262, "M_Charcoal", G_LO, bev=0.0003)
    pill = add(L.extrude("LockTabPill", oval(0, pu, 0.0222, 0.0070), front_map, A + 0.0200, A + 0.0292, "M_Charcoal", G_LO), G_LO)
    L.bevel(pill, 0.0011, 3)
    # 'D' lock mark, right side near the bottom of the cuff [tr-part-flex]
    arc = [math.pi / 2 + math.pi * k / 10 for k in range(11)]
    dc_ = (A + 0.004, S0 + 0.0115)
    dpts = [(dc_[0] + 0.0032 * math.cos(a), dc_[1] + 0.0032 * math.sin(a)) for a in arc]
    dpts += [(A + 0.0052, S0 + 0.0083), (A + 0.0052, S0 + 0.0147)]
    dpts_in = [(dc_[0] + 0.0021 * math.cos(a), dc_[1] + 0.0021 * math.sin(a)) for a in arc]
    dpts_in += [(A + 0.0043, S0 + 0.0094), (A + 0.0043, S0 + 0.0136)]
    ring_prism("CuffDMark", dpts, dpts_in, side_map(1), 0.0206, 0.0219, "M_Charcoal", G_LO)

    # ---- bronze anodized tube (chamfered 'soft facet' section)
    loft("BronzeTube", [(TUBE_UP[0], TUBE_W, TUBE_D, 0.004, A), (TUBE_UP[1], TUBE_W, TUBE_D, 0.004, A)],
         "M_Bronze", G_LO, sec=tube_sec)

    # ---- "Shark POWERDETECT" plate on the flat front face (atlas slot wand_shark_powerdetect)
    import materials as M
    fz = A + TUBE_D / 2 + 0.00025
    du0, du1, dx0, dx1 = DECAL["up0"], DECAL["up1"], DECAL["x0"], DECAL["x1"]
    nU = 6
    verts, uvs, faces = [], [], []
    for i in range(nU + 1):
        s_ = i / nU
        up = du1 + (du0 - du1) * s_                     # s (reading direction) = top -> bottom [EUT]
        for t_, x in ((0.0, dx0), (1.0, dx1)):   # t (glyph up) = +x = viewer's right in the front view [EUT]
            verts.append(V(x, up, fz))
            uvs.append(M.decal_uv(DECAL_SLOT, s_, t_))
    for i in range(nU):
        a_ = i * 2
        faces.append((a_, a_ + 2, a_ + 3, a_ + 1))
    add(L.mk("WandDecal", verts, faces, "M_Decal", G_LO, smooth=False, uvs=uvs, recalc=False), G_LO)

    # ---- lower MultiFLEX housing: flush with the tube -> taper -> 51 mm hinge block, rear deepens, front lobe
    F = FRONT
    low = loft("FlexLowerHousing", [
        st(0.5790, 0.0356, 0.0233, -0.0233, 0.0092),
        st(0.5840, 0.0358, 0.0234, -0.0236, 0.0093),
        st(0.5900, 0.0364, F, -0.0250, 0.0095),
        st(0.5980, 0.0384, F, -0.0282, 0.0100),
        st(0.6080, 0.0414, F, -0.0322, 0.0106),
        st(0.6180, 0.0436, F + 0.0002, -0.0352, 0.0110),
        st(0.6280, 0.0446, F + 0.0006, -0.0375, 0.0112),
        st(0.6360, 0.0456, F + 0.0012, -0.0388, 0.0114),
        st(0.6440, 0.0466, F + 0.0020, -0.0396, 0.0116),
        st(0.6520, 0.0470, F + 0.0027, -0.0400, 0.0118),
        st(PU + 0.004, 0.0470, F + 0.0030, -0.0402, 0.0118),
    ], "M_Gunmetal", G_LO)
    bisect(low, "below", CUT_GAP)
    # side windows (recess) with the black fold catch inside [V2 hinge, user-1663, crop-tr01]
    for s, tag in ((1, "R"), (-1, "L")):
        wpts = [(A - 0.0125 + px, 0.6445 + py) for px, py in L.rrect(0.0175, 0.0270, 0.0045)]
        cut = L.extrude("_cutter", wpts, side_map(s), 0.0222, 0.040, "M_Hose", "_cut", smooth=False)
        boolean(low, cut)
        add(L.extrude(f"FlexWindowFloor_{tag}", wpts, side_map(s), 0.0207, 0.02235, "M_Hose", G_LO), G_LO)
        cpts = [(A - 0.0125 + px, 0.6530 + py) for px, py in L.rrect(0.0110, 0.0085, 0.0018)]
        add(L.extrude(f"FlexCatch_{tag}", cpts, side_map(s), 0.0212, 0.0233, "M_Charcoal", G_LO, bev=0.0004, bev_seg=2), G_LO)
        hpts = [(A - 0.0125 + px, 0.6475 + py) for px, py in L.rrect(0.0040, 0.0050, 0.0012)]
        add(L.extrude(f"FlexCatchHinge_{tag}", hpts, side_map(s), 0.0212, 0.0229, "M_Charcoal", G_LO), G_LO)
    L.bevel(low, 0.0020, 3)
    port_ring("HosePortLower", G_LO, -1)
    hose("FlexHoseLower", -20, 47, G_LO)

    # ---- hinge barrel: centre knuckle (LowerWand), outer knuckles + purple caps (UpperWand)
    e = 0.0007
    gapk = 0.0004

    def knuckle(name, x0, x1, g):
        prof = [(RB - 0.004, x0), (RB - e, x0), (RB, x0 + e), (RB, x1 - e), (RB - e, x1), (RB - 0.004, x1)]
        return add(L.lathe_x(name, prof, PU, PF, "M_Gunmetal", g, segs=segs), g)

    knuckle("FlexKnuckle_C", -XC, XC, G_LO)

    # ================================================================= UPPER WAND
    U0 = PU - 0.004
    up = loft("FlexUpperHousing", [
        st(U0, 0.0470, 0.0230, -0.0402, 0.0118),
        st(PU + 0.0100, 0.0470, 0.0228, -0.0410, 0.0118),
        st(0.6800, 0.0466, 0.0205, -0.0440, 0.0117),
        st(0.6900, 0.0450, 0.0180, -0.0455, 0.0113),
        st(0.7000, 0.0447, 0.0160, -0.0460, 0.0111),
        st(0.7200, 0.0447, 0.0130, -0.0460, 0.0110),
        st(0.7450, 0.0447, 0.0112, -0.0460, 0.0110),
        st(0.7950, 0.0447, 0.0110, -0.0460, 0.0110),
        st(0.8060, 0.0455, 0.0112, -0.0460, 0.0112),
        st(TOP, 0.0462, 0.0114, -0.0460, 0.0114),
    ], "M_Gunmetal", G_UP)
    bisect(up, "above", CUT_GAP)
    L.bevel(up, 0.0020, 3)
    band("UpperTopSeam", TOP - 0.0045, 0.0006, 0.0452, 0.0111, -0.0460, 0.0111, "M_Charcoal", G_UP)
    port_ring("HosePortUpper", G_UP, 1)
    hose("FlexHoseUpper", -47, 20, G_UP)
    knuckle("FlexKnuckle_R", XC + gapk, HALF_W, G_UP)
    knuckle("FlexKnuckle_L", -HALF_W, -(XC + gapk), G_UP)
    for s, tag in ((1, "R"), (-1, "L")):
        x0 = s * (HALF_W + 0.0002)
        prof = [(0.0, x0), (CAP_R - 0.0008, x0), (CAP_R, x0 + s * 0.0007), (CAP_R, x0 + s * (CAP_T - 0.0012)),
                (CAP_R - 0.0010, x0 + s * CAP_T), (CAP_R - 0.0032, x0 + s * (CAP_T + 0.0002)),
                (0.0, x0 + s * (CAP_T + 0.0003))]
        add(L.lathe_x(f"FlexPivotCap_{tag}", prof, PU, PF, "M_Purple", G_UP, segs=segs, cap0=False, cap1=False), G_UP)

    # rear fold latch rail: frame + tall dark pill + round indicator, spans the joint [V2, manual p-12 inset]
    rb_ = -0.0440
    r0, r1 = PU - 0.029, PU + 0.074
    rc = (r0 + r1) / 2
    rail = add(L.extrude("FoldLatchRail", oval(0, rc, 0.0170, r1 - r0), front_map, A + rb_ + 0.0038, A + rb_ - 0.0070,
                         "M_Gunmetal", G_UP), G_UP)
    L.bevel(rail, 0.0012, 3)
    pill2 = add(L.extrude("FoldLatchPill", oval(0, rc + 0.004, 0.0100, 0.084), front_map, A + rb_ - 0.0065, A + rb_ - 0.0082,
                          "M_Charcoal", G_UP), G_UP)
    L.bevel(pill2, 0.0008, 2)
    add(L.extrude("FoldLatchDot", circle(0, PU + 0.060, 0.0035), front_map, A + rb_ - 0.0078, A + rb_ - 0.0086, "M_Gunmetal", G_UP), G_UP)

    # handheld-release button: vertical stadium bezel, dark recess, dark button with a thumb dish in its lower half,
    # small side lugs with pins (V7 51 mm bulge, V2 side) [EUT, V7]
    hf = A + 0.0110
    ring_prism("ReleaseBtnBezel", oval(0, REL_UP, 0.0320, 0.0500), oval(0, REL_UP, 0.0262, 0.0442), front_map,
               hf - 0.0040, hf + 0.0026, "M_Gunmetal", G_UP, bev=0.0006)
    add(L.extrude("ReleaseBtnWell", oval(0, REL_UP, 0.0268, 0.0448), front_map, hf - 0.003, hf + 0.0004, "M_Hose", G_UP), G_UP)
    dished_button("ReleaseBtn", 0, REL_UP, 0.0246, 0.0426, hf - 0.002, hf + 0.0030, 0.0013, "M_Charcoal", G_UP, dish_dy=-0.18)
    for s, tag in ((1, "R"), (-1, "L")):
        lug = [(A + 0.0040 + px, SEAM2_UP + py) for px, py in L.rrect(0.0120, 0.0070, 0.0025)]
        add(L.extrude(f"ReleaseLug_{tag}", lug, side_map(s), 0.0200, 0.0254, "M_Gunmetal", G_UP, bev=0.0008, bev_seg=2), G_UP)
        add(L.extrude(f"ReleasePin_{tag}", circle(A + 0.0040, SEAM2_UP, 0.0010, 12), side_map(s), 0.0250, 0.02575,
                      "M_Charcoal", G_UP), G_UP)
    band("UpperSeam", SEAM2_UP, 0.0006, 0.0447, 0.0110, -0.0460, 0.0110, "M_Charcoal", G_UP)
    # spigot into the handheld socket (hidden by the handheld)
    loft("HandheldSpigot", [st(TOP - 0.002, 0.030, 0.006, -0.030, 0.008), st(TOP + 0.012, 0.030, 0.006, -0.030, 0.008)],
         "M_Charcoal", G_UP)

    groups = {g: list(objs) for g, objs in made.items()}
    notes = (
        f"FlexPivot=(0,{PU:.4f},{PF:.4f}) axis +X, positive = handheld forward; housings clean 0..180 deg, hose bridged 0..94 deg. "
        f"Decal 'WandDecal' (M_Decal, slot {DECAL_SLOT}) on the flat bronze front face, up {du0}..{du1}, x {dx0}..{dx1} "
        "(plate = the slot's INK rect; measured ink box 174 x 12.9 mm, aspect 13.5 - the atlas ink is 23.3:1, i.e. drawn ~1.7x too wide). UV s 0->1 = top->bottom (reading direction), t 0->1 = -x->+x: glyph tops face +x = viewer's RIGHT in the front "
        "view (measured on cl-eut-01: 'Shark' at the top, ascenders on the right). "
    )
    return {"groups": groups, "special": {}, "anchors": {"FlexPivot": pivot}, "notes": notes}
