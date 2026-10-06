"""
Interface parameters for the v2 build (IA3246GN). Lead-owned. Product coords (x, up, fwd), meters.
Values marked [H1] are pixel-measured on the official Sagewood front hero (assets/references/ia3246/raw/sn-gn-hero.png,
1.559 px/mm, floor y=1886) by the reference-director (PRODUCT_REFERENCE_IA3246GN.md §1). [inf] = inferred placeholder;
part owners may supersede the pivots they own by returning them in `anchors` (NeckPivot: floorhead, FlexPivot: wand,
MotorAssembly origin: handheld) — tell the lead when you do.
"""

# overall (official spec: 375 L x 260 W x 1140 H mm, stick standing in dock)
OVERALL_H = 1.140          # floor -> top of handheld cap, docked [spec]
HEAD_W = 0.260             # floorhead width incl. bumper [spec, H1 265 +-3%]
OVERALL_L = 0.375          # head front -> dock rear [spec, interpretation in ref doc]

# wand axis (vertical in rest pose) — x = 0
WAND_FWD = -0.100          # wand axis fwd offset from the intake centre [manual p.21 Fig.2/3: axis above rear-wheel axle, 146 mm behind head front; intake centre 44 mm behind front] (rev 2026-10-05)

# interfaces along the wand axis (rest pose, heights above floor)
WAND_SOCKET_UP = 0.155     # head/wand split = seam just BELOW the oval nozzle-release button (button belongs to the wand's lower collar) [manual Fig.2 ~150; H1 reads ~20 mm high from perspective] (rev)
FOLD_UP = 0.647            # MultiFLEX pivot height [H1 barrel/copper caps y=857..898 px, wand agent] (rev)
HANDHELD_BOTTOM_UP = 0.835 # wand/handheld interface plane (bottom of handheld connector) [H1 ~836]

# pivots (defaults; owners may override via anchors)
NECK_PIVOT = (0.0, 0.045, WAND_FWD)          # wand pitch axis (along x) inside the floorhead neck [floorhead agent] (rev)
FOLD_PIVOT = (0.0, FOLD_UP, WAND_FWD + 0.020)  # MultiFLEX pivot on the wand's front face [wand agent]
HANDHELD_ORIGIN = (0.0, HANDHELD_BOTTOM_UP, WAND_FWD)  # MotorAssembly node origin

# cross-section guidance [H1]
WAND_FACE_W = 0.035        # copper wand visible face width
UPPER_WAND_W = 0.045       # dark upper wand above the hinge; flares to ~0.055 at the seam at up~0.780 [wand agent, H1]
HANDHELD_W = 0.090         # handheld body / cap width
BRUSHROLL_R = 0.024        # placeholder for rig.json until the floorhead part reports it

# head layout (floorhead agent, manual Fig.3): head front +0.044, end caps rear -0.065, neck plate rear -0.118,
# rear wheels x = +-0.053 (15 mm wide, D 48 mm, axle fwd -0.100, up 0.024), cap top 0.064
HEAD_FRONT_FWD = 0.044
