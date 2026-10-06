"""
wand part (v2, IA3246GN Sagewood). Owned by the wand agent. See ../PARTS_CONTRACT.md.

Builds, in the upright docked rest pose along the wand axis (x = 0, fwd = P.WAND_FWD):
  LowerWand: lower collar (nozzle-release button, double seam, small wand button), copper anodized tube with the
             POWERDETECT SPEED marking strip (M_Decal, UV 0..1), lower MultiFLEX housing, outer hinge knuckles +
             copper pivot caps, side catch buttons, the internal flex hose (rigid arc about the pivot - see below).
  UpperWand: centre hinge knuckle, upper MultiFLEX housing with rear fold latch, side clip tabs, seam at ~0.780 with
             the oval handheld-release button, dark neck up to P.HANDHELD_BOTTOM_UP.

Fold mechanics: pivot axis = product X through FlexPivot (10 mm proud of the housing front, barrel on cheeks).
The housings are split through the pivot: inside HEEL_R by a plane HEEL_BETA below the rear horizontal, outside it by
a plane CUT_BETA; the upper half owns a rounded heel (r < HEEL_R) seated in a concentric cup of the lower half, so a
positive rotation of UpperWand (handheld towards the head front) opens a wedge at the rear and never intersects the
lower half (checked 0..95 deg; the manual's ~180 deg storage fold is NOT supported). The flex hose is a corrugated torus segment about the pivot axis owned by LowerWand: at rest the
part above the cut lies inside the upper housing; at fold angle t exactly the arc [-beta, -beta + t] is exposed,
which is the wedge between the two housings - so no morph targets are needed.

Local ledger (H1 = sn-gn-hero.png, 1.559 px/mm; near-floor heights corrected with the lead's perspective fix:
true = 0.647 - (0.647 - h_H1) * 1.0766, anchored at the hinge and at the 0.155 head/wand seam):
  copper tube face 36 mm (56 px) [H1]; tube visible 0.241..0.553 [H1 0.270..0.560, corrected]
  lower collar 47 mm wide [H1], seam 0.155 [lead, manual Fig.2], nozzle-release oval 29 x 42 mm ring [H1]
  hinge band 52 mm wide x 26 mm (41 px) high, 3 knuckles 17/19/17 mm + ~2.5 mm copper caps [H1, sn-3241laa-01]
  pivot up 0.647 [H1 y 857..898]; upper housing 45 mm wide, flares to 55 mm at the seam 0.780 [H1]
  release button ring 27 x 42 mm centred 0.7755, button 21 x 34 mm [H1]
  tube 36 x 44 mm, housings 47 mm deep flush with the tube front, barrel 27 mm dia 10 mm proud [us_og_p-03 side view
  @1.41 px/mm, sn-gal1]; rear pill unlock latch + 3 marks [us_og_p-06, tech ref 6.3]; hose, side catch, keyhole
  windows [sn-gal1 (Sagewood, folded ~100 deg), sn-3241laa-01]
"""
import math

import bmesh
from mathutils import Vector

G_LO = "LowerWand"
G_UP = "UpperWand"

# ---------------------------------------------------------------- ledger (relative to the wand axis fwd A)
TUBE_W, TUBE_D, TUBE_R = 0.036, 0.044, 0.0085   # 36 [H1] x 44 deep [manual us_og_p-03 side view @1.41 px/mm, sn-gal1 tube/cap ratio]
TUBE_UP = (0.236, 0.560)          # tube length incl. the parts hidden inside collar / sleeve
TUBE_VIS = (0.241, 0.553)
COLLAR_W, COLLAR_D = 0.047, 0.048
HOUSE_D = 0.047                   # hinge housing depth, flush with the tube front [us_og_p-03: housing ~ tube depth]
FRONT_OFF = 0.0235                # housing front face relative to axis
PIVOT_OFF = 0.0335                # pivot 10 mm in front of the front face: barrel stands proud on cheeks [us_og_p-03]
BARREL_R = 0.0135
BARREL_W = 0.052
CUT_BETA = math.radians(12)        # outer split plane (outside the heel radius)
HEEL_BETA = math.radians(50)       # inner split plane (inside the heel radius)
HEEL_R = 0.049                     # radius of the upper housing's rounded heel about the pivot [sn-3241laa-01, sn-gal1]
CUT_GAP = 0.0003
HOSE_RC = 0.030                   # hose centreline radius about the pivot
HOSE_R = 0.0095
SEAM_UP = 0.7800                  # upper wand / neck seam
DECAL = {"up0": 0.333, "up1": 0.479, "x0": -0.0065, "x1": 0.0038}   # ink box: H1 y 1128..1340 (corrected), x -6.5..+3.8 mm, aspect 14.17


def build(ctx):
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

    def add(ob, g):
        made[g].append(ob)
        return ob

    def front_map(u, v, w):
        return V(u, v, w)

    def side_map(sign):
        # (fwd, up) plane extruded along +-x
        return lambda u, v, w: V(sign * w, v, u)

    def rear_map(u, v, w):
        return V(u, v, w)

    def oval(cx, cy, w, h, n=None):
        """stadium / rounded oval (w x h) in the (u, v) plane"""
        n = n or max(6, D["corner"] + 2)
        r = min(w, h) / 2 * 0.98
        return [(cx + px, cy + py) for px, py in L.rrect(w, h, r, n)]

    def ring_prism(name, outer, inner, mapf, w0, w1, mat, g, bev=None):
        """prism with a hole: outer/inner loops of equal count"""
        n = len(outer)
        verts = [mapf(u, v, w0) for u, v in outer] + [mapf(u, v, w1) for u, v in outer]
        verts += [mapf(u, v, w0) for u, v in inner] + [mapf(u, v, w1) for u, v in inner]
        faces = []
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((j, j2, n + j2, n + j))                       # outer wall
            faces.append((2 * n + j2, 2 * n + j, 3 * n + j, 3 * n + j2))  # inner wall
            faces.append((n + j, n + j2, 3 * n + j2, 3 * n + j))       # top
            faces.append((j2, j, 2 * n + j, 2 * n + j2))               # bottom
        ob = L.mk(name, verts, faces, mat, g)
        if bev:
            L.bevel(ob, bev, 2)
        return add(ob, g)

    def dished_button(name, cx, cy, w, h, z0, z1, depth, mat, g):
        """oval push button with a rounded rim and a thumb scoop in its lower half (H1 / sn-3241laa-01)"""
        base = oval(cx, cy, w, h, n=max(8, D["corner"] + 4))
        dc = (cx, cy - 0.18 * h)
        rings = []
        prof = [(1.0, z0), (1.0, z1 - 0.0009), (0.985, z1 - 0.0003), (0.95, z1)]
        prof += [(sv, z1 - depth * max(0.0, 1 - (sv / 0.86) ** 2)) for sv in (0.86, 0.72, 0.58, 0.44, 0.30, 0.16, 0.05)]
        for sv, z in prof:
            rings.append([V(dc[0] + sv * (u - dc[0]), dc[1] + sv * (v - dc[1]), z) for u, v in base])
        vv, ff = L.ring_mesh(rings, True, True)
        return add(L.mk(name, vv, ff, mat, g), g)

    def loft(name, st, mat, g, cap_round=0.0):
        return add(L.loft_up(name, st, mat, g, cap_round=cap_round), g)

    def bisect(ob, keep, gap, beta=CUT_BETA):
        """cut ob with a fold plane through the pivot; keep='below' (lower half) or 'above'. Fills the cut flat."""
        nb = Vector((0.0, math.sin(beta), math.cos(beta)))   # Blender-space normal (towards the upper half)
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

    def side_poly(pts):
        """closed 2D polygon in the (fwd, up) side plane, extruded across x (boolean cutter)"""
        return L.extrude("_cutter", pts, lambda u, v, w: V(w, v, u), -0.06, 0.06, "M_Hose", "_cut", smooth=False)

    def boolean(ob, cutter, op="DIFFERENCE"):
        import bpy
        md = ob.modifiers.new("Bool", "BOOLEAN")
        md.operation = op
        md.solver = "EXACT"
        md.object = cutter
        L.apply_modifiers(ob)
        bpy.data.objects.remove(cutter, do_unlink=True)
        ob.data.set_sharp_from_angle(angle=math.radians(40))
        return ob

    def arc_pts(r, b0, b1, n=24):
        """points at radius r about the pivot for angles b0..b1 measured downward from the rear horizontal"""
        return [(PF - r * math.cos(b0 + (b1 - b0) * k / n), PU - r * math.sin(b0 + (b1 - b0) * k / n)) for k in range(n + 1)]

    def band(name, up, h, w, d, r, cf, mat, g, grow=0.00012):
        """thin seam line wrapped around a rounded-rect section"""
        return loft(name, [(up - h / 2, w + 2 * grow, d + 2 * grow, r + grow, cf), (up + h / 2, w + 2 * grow, d + 2 * grow, r + grow, cf)], mat, g)

    # ================================================================= LOWER WAND
    # ---- lower collar: S0 .. tube; nozzle-release oval just above the seam, double seam, small wand button
    cc = A + 0.001
    c_top0, c_top1 = 0.214, 0.243
    collar = loft("LowerCollar", [
        (S0, COLLAR_W - 0.002, COLLAR_D - 0.002, 0.0115, cc),
        (S0 + 0.0025, COLLAR_W, COLLAR_D, 0.012, cc),
        (0.205, COLLAR_W, COLLAR_D, 0.012, cc),
        (c_top0, COLLAR_W - 0.0005, COLLAR_D - 0.0005, 0.012, cc),
        (0.228, 0.0425, 0.0425, 0.0105, A + 0.0005),
        (0.237, 0.0395, 0.0375, 0.0090, A + 0.0002),
        (c_top1, TUBE_W + 0.0025, TUBE_D + 0.0025, TUBE_R + 0.0012, A),
    ], "M_Graphite", G_LO)
    L.bevel(collar, 0.0008, 2)
    # bottom lip ring (meets the head neck) + double seam lines above it
    band("CollarSeamA", S0 + 0.0060, 0.0007, COLLAR_W, COLLAR_D, 0.012, cc, "M_Hose", G_LO)
    band("CollarSeamB", S0 + 0.0092, 0.0007, COLLAR_W, COLLAR_D, 0.012, cc, "M_Hose", G_LO)
    cfront = cc + COLLAR_D / 2
    # nozzle-release button: raised bezel + recess + domed oval cap (29 x 42 mm ring)
    nb_up = S0 + 0.023
    ring_prism("NozzleBtnBezel", oval(0, nb_up, 0.029, 0.042), oval(0, nb_up, 0.0235, 0.0365), front_map,
               cfront - 0.002, cfront + 0.0013, "M_Graphite", G_LO, bev=0.0005)
    add(L.extrude("NozzleBtnWell", oval(0, nb_up, 0.0240, 0.0370), front_map, cfront - 0.002, cfront + 0.0002, "M_Hose", G_LO), G_LO)
    dished_button("NozzleBtn", 0, nb_up, 0.0212, 0.0342, cfront - 0.001, cfront + 0.0026, 0.0011, "M_Graphite", G_LO)
    # small wand-release button on the collar taper just below the copper (dark pill, raised ~4 mm)
    wb_up = 0.2335
    pill = add(L.extrude("WandLockBtn", oval(0, wb_up, 0.026, 0.0085), front_map, A + 0.021, A + 0.0292, "M_Rubber", G_LO), G_LO)
    L.bevel(pill, 0.0012, 3)
    ring_prism("WandLockBtnRim", oval(0, wb_up, 0.0295, 0.0118), oval(0, wb_up, 0.0268, 0.0091), front_map,
               A + 0.020, A + 0.0268, "M_Graphite", G_LO, bev=0.0004)

    # ---- copper anodized tube (rounded rect) + end rings
    tube = loft("CopperTube", [(TUBE_UP[0], TUBE_W, TUBE_D, TUBE_R, A), (TUBE_UP[1], TUBE_W, TUBE_D, TUBE_R, A)], "M_Copper", G_LO)
    for k, u in enumerate((TUBE_VIS[0] + 0.0004, TUBE_VIS[1] - 0.0004)):
        band(f"TubeEndShadow{k}", u, 0.0008, TUBE_W, TUBE_D, TUBE_R, A, "M_Hose", G_LO, grow=0.00005)

    # ---- POWERDETECT SPEED marking plate on the flat copper front face (atlas slot pds_wand_white, ink rect)
    import materials as M
    fz = A + TUBE_D / 2 + 0.00025
    du0, du1, dx0, dx1 = DECAL["up0"], DECAL["up1"], DECAL["x0"], DECAL["x1"]
    nU = 4
    verts, uvs, faces = [], [], []
    for i in range(nU + 1):
        s_ = i / nU
        up = du1 + (du0 - du1) * s_              # s: reading direction = top -> bottom
        for t_, x in ((0.0, dx0), (1.0, dx1)):   # t: glyph up = +x (viewer's right in the front view)
            verts.append(V(x, up, fz))
            uvs.append(M.decal_uv("pds_wand_white", s_, t_))
    for i in range(nU):
        a_ = i * 2
        faces.append((a_, a_ + 2, a_ + 3, a_ + 1))
    add(L.mk("PowerDetectDecal", verts, faces, "M_Decal", G_LO, smooth=False, uvs=uvs, recalc=False), G_LO)

    # ---- lower MultiFLEX housing: sleeve over the tube, flares to 47 mm, cut by the fold plane
    hf = A + FRONT_OFF
    hc = hf - HOUSE_D / 2
    s0 = TUBE_VIS[1]
    low = loft("FlexLowerHousing", [
        (s0, TUBE_W + 0.0028, TUBE_D + 0.0028, TUBE_R + 0.0014, A),
        (s0 + 0.004, TUBE_W + 0.0040, TUBE_D + 0.0040, TUBE_R + 0.002, A),
        (0.5695, 0.044, 0.043, 0.0105, A + 0.0035),
        (0.592, 0.0465, 0.050, 0.012, hc + 0.0025),
        (0.612, 0.047, HOUSE_D, 0.0125, hc),
        (PU + 0.004, 0.047, HOUSE_D, 0.0125, hc),
    ], "M_Graphite", G_LO)
    bisect(low, "below", CUT_GAP)
    # rounded heel seat: remove the sector (r < HEEL_R) between the outer and the inner split planes
    eps = math.radians(4)
    hb = HEEL_BETA
    apex = (PF + CUT_GAP * math.sin(hb) - 0.0006 * math.cos(hb), PU - CUT_GAP * math.cos(hb) - 0.0006 * math.sin(hb))
    boolean(low, side_poly([apex] + arc_pts(HEEL_R + CUT_GAP, CUT_BETA - eps, hb)))
    L.bevel(low, 0.0022, 3)
    band("SleeveLip", s0 + 0.0009, 0.0008, TUBE_W + 0.0028, TUBE_D + 0.0028, TUBE_R + 0.0014, A, "M_Hose", G_LO, grow=0.0001)
    # side catch: small rectangular push button framed by a D-loop (sn-gal1), both sides, near the rear
    for s, tag in ((1, "R"), (-1, "L")):
        xs = s * 0.0235
        cu, cfw = 0.596, hc - 0.010
        btn_pts = [(cfw + px, cu + py) for px, py in L.rrect(0.0075, 0.0105, 0.0016)]
        add(L.extrude(f"FoldCatchBtn_{tag}", btn_pts, side_map(s), 0.0225, 0.0255, "M_Rubber", G_LO, bev=0.0005, bev_seg=2), G_LO)
        outer = [(cfw + px, cu + py) for px, py in L.rrect(0.0135, 0.0165, 0.0050)]
        inner = [(cfw + px, cu + py) for px, py in L.rrect(0.0099, 0.0129, 0.0032)]
        ring_prism(f"FoldCatchLoop_{tag}", outer, inner, side_map(s), 0.0228, 0.0250, "M_Graphite", G_LO, bev=0.0004)
        _ = xs

    # ---- hinge barrel: outer knuckles + copper pivot caps on LowerWand, centre knuckle on UpperWand
    segs = max(48, D["lathe"] // 2)
    half = BARREL_W / 2
    cap_t = 0.0024
    kn_gap = 0.0004
    xc = 0.0095                        # centre knuckle half width (19 mm)
    xo = half - cap_t - 0.0002         # outer knuckle end
    rb = BARREL_R
    e = 0.0007

    def knuckle(name, x0, x1, g):
        prof = [(rb - 0.004, x0), (rb - e, x0), (rb, x0 + e), (rb, x1 - e), (rb - e, x1), (rb - 0.004, x1)]
        return add(L.lathe_x(name, prof, PU, PF, "M_Graphite", g, segs=segs), g)

    knuckle("FlexKnuckle_R", xc + kn_gap, xo, G_LO)
    knuckle("FlexKnuckle_L", -xo, -(xc + kn_gap), G_LO)
    knuckle("FlexKnuckle_C", -xc, xc, G_UP)
    for s, tag in ((1, "R"), (-1, "L")):
        x0 = s * (xo + 0.0002)
        prof = [(0.0, x0), (rb - 0.0006, x0), (rb, x0 + s * 0.0006), (rb, x0 + s * (cap_t - 0.0008)),
                (rb - 0.0012, x0 + s * cap_t), (rb - 0.0035, x0 + s * (cap_t + 0.0003)), (0.0, x0 + s * (cap_t + 0.0004))]
        cap = L.lathe_x(f"FlexPivotCap_{tag}", prof if s > 0 else prof, PU, PF, "M_Copper", G_LO, segs=segs, cap0=False, cap1=False)
        add(cap, G_LO)
    # cheeks: webs carrying the proud barrel. outer pair on LowerWand (below the pivot), centre web on UpperWand
    def cheek_profile(sign):
        """side profile (fwd, up) of a web from the housing front up to the barrel, mirrored by sign (+1 up, -1 down)"""
        fr = hf - 0.003
        WH = 0.018                       # web height from the pivot (kept inside the barrel silhouette seen from the front)
        pts = [(fr, PU - sign * WH)]
        for k in range(1, 9):            # smooth S from the housing front out to the barrel tangent
            t = k / 8
            fwd = fr + (PF - fr) * (3 * t * t - 2 * t * t * t)
            pts.append((fwd, PU - sign * (WH - (WH - (rb - 0.001)) * t)))
        for k in range(1, 7):            # follow the barrel (inside its radius) back to the pivot level
            ang = -math.pi / 2 * sign + (math.pi / 2) * sign * k / 6 * (-1)
            pts.append((PF + (rb - 0.001) * math.cos(-math.pi / 2 - (math.pi / 2) * k / 6 if sign > 0 else math.pi / 2 + (math.pi / 2) * k / 6),
                        PU + (rb - 0.001) * math.sin(-math.pi / 2 - (math.pi / 2) * k / 6 if sign > 0 else math.pi / 2 + (math.pi / 2) * k / 6)))
            _ = ang
        pts.append((fr, PU))
        return pts if sign < 0 else pts[::-1]

    for s, tag in ((1, "R"), (-1, "L")):
        ch = add(L.extrude(f"FlexCheek_{tag}", cheek_profile(1), side_map(s), xc + kn_gap + 0.0006, xo - 0.0004, "M_Graphite", G_LO), G_LO)
        L.bevel(ch, 0.0008, 2)

    # ---- internal corrugated flex hose: torus segment about the pivot axis (see module doc)
    a0, a1 = -HEEL_BETA - math.radians(12), -HEEL_BETA + math.radians(94)
    nA = 150 if high else 70
    nC = 20 if high else 12
    pitch = 0.0034
    rings = []
    arc_len = HOSE_RC * (a1 - a0)
    for i in range(nA + 1):
        a = a0 + (a1 - a0) * i / nA
        sl = arc_len * i / nA
        rr = HOSE_R - 0.0011 * (0.5 - 0.5 * math.cos(math.tau * sl / pitch)) ** 1.5
        cu = PU + HOSE_RC * math.sin(a)
        cfw = PF - HOSE_RC * math.cos(a)
        rad = Vector((0.0, math.sin(a), -math.cos(a)))   # (x, up, fwd) radial outward
        ring = []
        for j in range(nC):
            t = math.tau * j / nC
            p = Vector((0.0, cu, cfw)) + Vector((math.cos(t) * rr, 0, 0)) + rad * (math.sin(t) * rr)
            ring.append(V(p.x, p.y, p.z))
        rings.append(ring)
    hv, hfc = L.ring_mesh(rings, True, True)
    add(L.mk("FlexHose", hv, hfc, "M_Hose", G_LO), G_LO)

    # ================================================================= UPPER WAND
    up = loft("FlexUpperHousing", [
        (PU - 0.048, 0.045, HOUSE_D, 0.012, hc),
        (0.700, 0.045, HOUSE_D, 0.012, hc),
        (0.735, 0.0455, HOUSE_D, 0.012, hc),
        (0.758, 0.0495, HOUSE_D, 0.0125, hc),
        (SEAM_UP - 0.0003, 0.0545, HOUSE_D, 0.013, hc),
    ], "M_Graphite", G_UP)
    bisect(up, "above", CUT_GAP, HEEL_BETA)
    # keep only the heel (r < HEEL_R) below the outer split plane
    boolean(up, side_poly(arc_pts(HEEL_R - CUT_GAP, CUT_BETA, HEEL_BETA + math.radians(6)) + arc_pts(0.13, HEEL_BETA + math.radians(6), CUT_BETA)))
    L.bevel(up, 0.0022, 3)
    ch = add(L.extrude("FlexCheek_C", cheek_profile(-1), side_map(1), -xc + 0.0004, xc - 0.0004, "M_Graphite", G_UP), G_UP)
    L.bevel(ch, 0.0008, 2)
    # rear fold-unlock latch: tall pill slider on the back (us_og_p-06 inset, us_og_p-03), three small marks above it
    hr = hc - HOUSE_D / 2
    lat_c = PU + 0.030
    lat = add(L.extrude("FoldLatch", oval(0, lat_c, 0.020, 0.070), rear_map, hr + 0.0015, hr - 0.0040, "M_Graphite", G_UP), G_UP)
    L.bevel(lat, 0.0012, 3)
    add(L.extrude("FoldLatchGrip", oval(0, lat_c - 0.012, 0.010, 0.026), rear_map, hr - 0.0035, hr - 0.0046, "M_Hose", G_UP, bev=0.0004, bev_seg=2), G_UP)
    for k in range(3):
        mk_pts = [(-0.0045 + 0.0045 * k + px, lat_c + 0.042 + py) for px, py in L.rrect(0.0022, 0.0022, 0.0004, 2)]
        add(L.extrude(f"FoldLatchMark{k}", mk_pts, rear_map, hr + 0.0005, hr - 0.0004, "M_Hose", G_UP), G_UP)
    # keyhole window on both sides of the upper housing (dark recess showing the hose, sn-3241laa-01 / us_og_p-03)
    for s, tag in ((1, "R"), (-1, "L")):
        kc = (hr + 0.012, PU + 0.002)
        circ = [(kc[0] + 0.0052 * math.cos(math.tau * k / 20), kc[1] + 0.0052 * math.sin(math.tau * k / 20)) for k in range(20)]
        add(L.extrude(f"KeyholeHole_{tag}", circ, side_map(s), 0.0215, 0.02275, "M_Hose", G_UP), G_UP)
        slot = [(kc[0] + px, kc[1] - 0.008 + py) for px, py in L.rrect(0.0052, 0.012, 0.0024)]
        add(L.extrude(f"KeyholeSlot_{tag}", slot, side_map(s), 0.0215, 0.02275, "M_Hose", G_UP), G_UP)
    # side clip tabs at the seam (rear edge, sn-gal1 / sn-3241laa-01)
    for s, tag in ((1, "R"), (-1, "L")):
        tpts = [(hr + 0.009 + px, SEAM_UP - 0.006 + py) for px, py in L.rrect(0.0075, 0.012, 0.0022)]
        add(L.extrude(f"SideClip_{tag}", tpts, side_map(s), 0.0255, 0.0290, "M_Rubber", G_UP, bev=0.0006, bev_seg=2), G_UP)

    # ---- seam 0.780 + dark neck to the handheld interface
    neck = loft("UpperNeck", [
        (SEAM_UP + 0.0003, 0.0548, HOUSE_D, 0.013, hc),
        (0.800, 0.0560, HOUSE_D, 0.013, hc),
        (TOP, 0.0580, HOUSE_D, 0.0135, hc),
    ], "M_Graphite", G_UP)
    L.bevel(neck, 0.0010, 2)
    loft("SeamFiller", [(SEAM_UP - 0.003, 0.053, HOUSE_D - 0.002, 0.012, hc), (SEAM_UP + 0.003, 0.053, HOUSE_D - 0.002, 0.012, hc)], "M_Hose", G_UP)
    band("SeamLine2", SEAM_UP + 0.0042, 0.0006, 0.0560, HOUSE_D, 0.013, hc, "M_Hose", G_UP)
    # handheld-release button straddling the seam: bezel (27 x 42), recess, button (21 x 34) with thumb dish
    rb_up = 0.7755
    ring_prism("ReleaseBtnBezel", oval(0, rb_up, 0.027, 0.042), oval(0, rb_up, 0.0222, 0.0368), front_map,
               hf - 0.002, hf + 0.0014, "M_Graphite", G_UP, bev=0.0005)
    add(L.extrude("ReleaseBtnWell", oval(0, rb_up, 0.0226, 0.0372), front_map, hf - 0.002, hf + 0.0003, "M_Hose", G_UP), G_UP)
    dished_button("ReleaseBtn", 0, rb_up, 0.0204, 0.0346, hf - 0.001, hf + 0.0028, 0.0011, "M_Graphite", G_UP)

    groups = {g: [o for o in objs] for g, objs in made.items()}
    notes = (
        f"FlexPivot=(0,{PU:.4f},{PF:.4f}) axis +X, positive = handheld forward, safe 0..95 deg. "
        f"Decal strip 'PowerDetectDecal' (M_Decal) on copper front face, x {DECAL['x0']}..{DECAL['x1']}, up {DECAL['up0']}..{DECAL['up1']}; "
        "UV u 0->1 = top->bottom (reading direction), v 0->1 = -x -> +x (letter tops face +x / image right in front view); "
        "atlas text should read left->right with tops at v=1, H1 text box = up 0.335..0.479, x -5.5..+2.9 mm."
    )
    return {"groups": groups, "special": {}, "anchors": {"FlexPivot": pivot}, "notes": notes}
