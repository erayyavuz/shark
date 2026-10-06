"""
Interface parameters for the v3 build: Shark PowerDetect Clean & Empty IP3251 (TR IP3251EUT; user's own video frames
in assets/references/ip3251/user/). Lead-owned. Product coords (x, up, fwd), meters, upright rest pose, origin = centre
of the floorhead intake footprint on the floor (stick standing on the floor; the dock-raise is separate, see DOCKED_RAISE).

The IP3251 stick/wand/floorhead are the same hardware as the IP1251EUT (TECHNICAL_REFERENCE_IP3251.md §0/§4.2), so the
stack heights come from PRODUCT_REFERENCE.md §4 (V7 front / V2 side photo measurements of IP1251, agreement 1–3 mm).
[PR4] = that table; [inf] = inferred placeholder. Part owners may supersede the pivots they own via `anchors`
(NeckPivot: floorhead, FlexPivot: wand, MotorAssembly: handheld) — tell the lead.
"""

STICK_H = 1.158            # floor -> top of cap, stick standing on the floor [TR spec 115.8 cm, = IP1251EUT]
SYSTEM_H = 1.177           # docked, top of cap above floor [UK spec 117.7 cm] -> the dock raises the stick ~19 mm
DOCKED_RAISE = SYSTEM_H - STICK_H  # [inf] floorhead parked on the dock base plate; dock agent confirms the plate height
HEAD_W = 0.263             # floorhead width [official]
SYSTEM_D = 0.472           # head front -> rear-most point of the docked system [UK spec 47.19 cm]

WAND_FWD = -0.123          # wand axis fwd offset from the intake centre [floorhead agent: manual p-16 side (nose->axis ~167 mm), V5 top (163 mm), intake centre ~42 mm behind nose] (rev)

# stack heights on the wand axis (upright, stick on the floor) [PR4]
NECK_DISC_UP = 0.112       # centre of the neck joint disc (front-facing purple disc)
WAND_SOCKET_UP = 0.263     # top of the floorhead neck connector (with its oval release button) = bottom of the wand cuff
WAND_TUBE = (0.283, 0.581) # bronze wand tube visible span (0.020 grey cuff below)
FOLD_UP = 0.663            # MultiFLEX pivot height
HANDHELD_BOTTOM_UP = 0.812 # wand/handheld interface (bottom of the handheld socket)

NECK_PIVOT = (0.0, 0.042, WAND_FWD)              # lateral pitch barrel low in the rear neck cradle between the wheels [floorhead agent, V2 + manual p18] (rev)
FOLD_PIVOT = (0.0, FOLD_UP, WAND_FWD + 0.025)    # on the wand's FRONT face, fold closes toward the front [PR4]
HANDHELD_ORIGIN = (0.0, HANDHELD_BOTTOM_UP, WAND_FWD)

# cross-sections [PR4]
WAND_SECTION = (0.035, 0.046)   # lateral x fore-aft, rounded rectangle
UPPER_WAND_W = 0.045
HINGE_W = (0.051, 0.063)        # housing / with purple pivot caps (cap dia 0.023)
HANDHELD_W = 0.090              # body / cap / bin diameter
BRUSHROLL_R = 0.0275            # front soft roller radius placeholder for rig.json

# floorhead (floorhead agent): head nose at fwd = WAND_FWD + 0.165; RollerFront = black soft roller with turquoise helical
# stripes (behind the clear front lip); RollerRear = turquoise brushroll with yellow/tan chevron bristles (seen through the top window)
HEAD_NOSE_FWD = WAND_FWD + 0.165
