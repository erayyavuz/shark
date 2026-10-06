"""
Central parameters + measurement ledger for the Shark PowerDetect (IP1251EUT assumption) reconstruction.

Units: meters. All values are in PRODUCT coordinates (rest pose, wand vertical):
    x   = lateral, +x = viewer's right when the product faces the viewer (== glTF +X)
    up  = height above floor (== glTF +Y)
    fwd = toward the floorhead front (== glTF +Z, == Blender -Y)
Origin = VacuumRoot = floor point midway between the two roller contact lines, centered in x.

Measurement method (see LEDGER):
  * Overall assembled envelope H 1.158 / W 0.263 / D 0.393 from P1 (official TR product page).
  * Axial lengths, widths and colours follow PRODUCT_REFERENCE.md v1.0 (reference-director), primarily the
    official straight front view V7 (k7 = 0.634 mm/px) cross-checked against V2 (folded side view).
  * My own V2 pass (folded stack 4400 px == 1.158 m, 0.263 mm/px) gave the same purple wand (0.29-0.30 m),
    cap (0.053) and handle rear extent (0.209 m behind the wand axis region) within a few mm.
  * Fore-aft: head front = wand axis + 0.150; handle rear = motor axis - 0.208; motor axis = wand axis - 0.035
    -> overall depth 0.392 m vs. P1 0.393 m (independent consistency check).
  * Colors are art-direction estimates (PRODUCT_REFERENCE §6 medians), not official specifications.
Status values: measured (pixel-measured in a matched view), derived (computed from measured values),
inferred (not directly visible / estimated from product family logic), official (P1 field).
"""

LEDGER = []


def m(key, value, source, status):
    LEDGER.append({"key": key, "value": value, "source": source, "status": status})
    return value


S_V2 = m("scale_v2_m_per_px", 0.000263, "own V2 stack (PRODUCT_REFERENCE k2=0.2747 mm/px uses a different landmark set)", "derived")
S_V7 = m("scale_v7_m_per_px", 0.000634, "PRODUCT_REFERENCE.md v1.0 §3: V7 alpha bbox 1826 px == 1.158 m", "derived")

# ---------------------------------------------------------------- overall
OVERALL_H = m("overall.height", 1.158, "P1 assembled dims", "official")
OVERALL_W = m("overall.width", 0.263, "P1 assembled dims (== head width incl. side caps)", "official")
OVERALL_D = m("overall.depth", 0.393, "P1 assembled dims", "official")

# ---------------------------------------------------------------- floorhead (FloorHead-local == root-local)
HEAD_HALF_W = m("head.half_width", OVERALL_W / 2, "P1 width", "official")
SIDE_THICK = m("head.side_cap_thickness", 0.0315, "V7: roller visible length 0.200 inside 0.263 -> ~0.031 per side", "measured")
HEAD_INNER_HALF = HEAD_HALF_W - SIDE_THICK  # 0.100
HEAD_FRONT = m("head.front_fwd", 0.069, "wand axis->head front 0.150 (PRODUCT_REFERENCE) and P1 D 0.393", "derived")
HEAD_DEPTH = m("head.body_depth", 0.132, "PRODUCT_REFERENCE V5 ratio 0.503 x 0.263", "measured")
HEAD_REAR = HEAD_FRONT - HEAD_DEPTH  # -0.063
HEAD_TOP = m("head.cover_top_up", 0.076, "PRODUCT_REFERENCE V7 front face 130 px x 0.588 mm/px", "measured")

ROLLER_F_R = m("roller.front.radius", 0.0275, "PRODUCT_REFERENCE: dia ~0.055", "inferred")
ROLLER_F_FWD = m("roller.front.center_fwd", 0.035, "set so origin is midway between contact lines; front edge 6.5 mm behind bumper", "derived")
ROLLER_F_LEN = m("roller.front.length", 0.196, "V7 visible length 0.200 incl. end gaps", "measured")
ROLLER_R_R = m("roller.rear.radius", 0.020, "PRODUCT_REFERENCE: dia ~0.040 (no underside view)", "inferred")
ROLLER_R_CORE = m("roller.rear.core_radius", 0.0105, "inferred", "inferred")
ROLLER_R_FWD = m("roller.rear.center_fwd", -0.035, "must sit under the 0.132 body; mirrored about origin", "inferred")
ROLLER_R_LEN = m("roller.rear.length", 0.190, "inferred", "inferred")

WAND_AXIS_FWD = m("wand.axis_fwd", HEAD_FRONT - 0.150, "PRODUCT_REFERENCE: wand axis -> head front ~0.150", "inferred")
NECK_PIVOT = m("neck.pivot(x,up,fwd)", (0.0, 0.100, WAND_AXIS_FWD), "PRODUCT_REFERENCE §9: pitch axis ~0.095-0.10", "inferred")
NECK_DISC_UP = m("neck.purple_disc_up", 0.112, "PRODUCT_REFERENCE chosen 0.112 (V7); V2 0.094 conflicting", "conflicting")
WHEEL_R = m("wheel.radius", 0.0235, "PRODUCT_REFERENCE: dia 0.047 (V2 172 px)", "measured")
WHEEL_FWD = m("wheel.center_fwd", -0.088, "V2/V5: directly behind body; footprint depth ~0.18", "measured")
WHEEL_X_IN = m("wheel.x_inner", 0.051, "V5 top view: wheels at the rear corners of the neck plate (~±0.061 centre)", "measured")
WHEEL_W = m("wheel.width", 0.019, "PRODUCT_REFERENCE ~0.020", "inferred")
YOKE_HALF_W = m("neck.yoke_half_width", 0.024, "V7 75 px -> 0.048", "measured")

# ---------------------------------------------------------------- wand (heights 'up', rest pose; floor up)
COLLAR = m("collar.up_range", (0.124, 0.263), "neck connector 0.151 above disc", "measured")
COLLAR_W = m("collar.width(bottom,top)", (0.046, 0.036), "V7 72 -> 57 px", "measured")
COLLAR_D = m("collar.depth", 0.050, "V2", "measured")
COLLAR_BTN_UP = m("collar.button_up", NECK_DISC_UP + 0.079, "V7 light-grey oval release button", "measured")
CUFF = m("cuff.up_range", (0.263, 0.283), "V7 grey bottom cuff of wand 0.020", "measured")
WAND = m("wand.up_range", (0.283, 0.581), "V7/V2 purple length 0.298", "measured")
WAND_SEC = m("wand.section(w,d)", (0.035, 0.046), "V7 55 px lateral; fore-aft conflicting 0.039-0.051", "conflicting")
FOLD_PIVOT = m("fold.pivot(x,up,fwd)", (0.0, 0.663, WAND_AXIS_FWD + 0.025), "top of purple + 0.082; front face 0.025 ahead of axis", "measured")
FOLD_W = m("fold.housing_width(w, with caps)", (0.051, 0.063), "V7 81 / 99 px", "measured")
FOLD_CAP_R = m("fold.pivot_cap_radius", 0.0115, "V2 85 px -> 0.023 dia", "measured")
HANDHELD_BOTTOM = m("upper.handheld_bottom_up", 0.812, "hinge + 0.149", "measured")
UPPER_W = m("upper.width", 0.045, "V7 71 px", "measured")
UPPER_BTN_UP = m("upper.button_up", HANDHELD_BOTTOM - 0.032, "V7 dark oval release button", "measured")

# ---------------------------------------------------------------- handheld (motor/bin axis)
BODY_FWD = m("body.axis_fwd", WAND_AXIS_FWD - 0.035, "PRODUCT_REFERENCE ~0.035 behind wand axis", "inferred")
BODY_R = m("body.radius", 0.045, "V7 body width 0.090", "measured")
BASE = m("bin.grey_base_up_range", (0.812, 0.847), "V7 0.035", "measured")
SHROUD = m("bin.silver_shroud_up_range", (0.847, 0.897), "V7 0.050", "measured")
BIN = m("bin.clear_up_range", (0.847, 0.997), "clear shell spans shroud + window (0.150)", "measured")
BIN_R = m("bin.outer_radius", 0.0440, "V7 0.090 width incl. frame", "measured")
BIN_WALL = m("bin.wall", 0.0022, "inferred molded PC wall", "inferred")
PURPLE_RING = m("bin.purple_ring_up_range", (0.997, 1.027), "V7 0.030", "measured")
SILVER_BAND = m("body.silver_band_up_range", (1.027, 1.049), "V7 'Shark' band (blank)", "measured")
MOTOR = m("motor.up_range", (1.049, 1.104), "V7 motor+band 0.076", "measured")
MOTOR_R = m("motor.radius", 0.0440, "V7", "measured")
CAP = m("filter_cap.up_range", (1.104, 1.157), "V7/V2 0.053; cap top is the highest point (V7)", "measured")
CAP_R = m("filter_cap.radius", 0.0450, "V7 0.090 dia", "measured")
CAP_RIBS = m("filter_cap.rib_count", 22, "V2/V4/V7: ~11 flutes per visible half", "measured")
SCREEN_R = m("screen.radius", 0.029, "PRODUCT_REFERENCE ~0.060 dia control screen", "inferred")
FRAME_FRONT = m("frame.front_fwd", BODY_FWD + 0.059, "body depth 0.104 = bin rear wall -> front frame", "measured")
FRAME_WIN = m("frame.window(half_w, up0, up1)", (0.031, 0.849, 1.025), "V7", "measured")

# handle (fwd values absolute)
HANDLE_REAR = m("handle.rear_fwd", BODY_FWD - 0.208, "V2 757 px behind motor axis", "measured")
GRIP_A = m("grip.front(up,fwd)", (1.112, BODY_FWD - 0.030), "attach 0.035-0.050 below cap top", "measured")
GRIP_B = m("grip.rear(up,fwd)", (1.132, HANDLE_REAR + 0.024), "rises ~7 deg: V7 shows nothing above the cap, so the loop stays below 1.157", "conflicting")
GRIP_SEC = m("grip.section(w,h)", (0.031, 0.030), "ref thickness ~0.028", "measured")
BATT_A = m("battery.front(up,fwd)", (1.028, BODY_FWD - 0.028), "attach 0.107-0.148 below cap top", "measured")
BATT_B = m("battery.rear(up,fwd)", (1.032, HANDLE_REAR + 0.024), "V2", "measured")
BATT_SEC = m("battery.section(w,h)", (0.058, 0.040), "ref 0.152 x 0.040", "measured")
POST = m("handle.rear_post(up0,up1,depth,width)", (0.990, 1.148, 0.044, 0.058), "ref outer height 0.162 -> 0.158 (kept below cap top)", "measured")

# ---------------------------------------------------------------- colors (sRGB 0-255) — PRODUCT_REFERENCE §6 medians, art direction
COLORS = {
    "M_Housing": ((125, 123, 118), 0.42, 0.0),
    "M_HousingDark": ((62, 63, 66), 0.48, 0.0),
    "M_Purple": ((90, 60, 126), 0.38, 0.0),
    "M_PurpleMatte": ((88, 58, 124), 0.32, 0.12),
    "M_Silver": ((186, 188, 192), 0.30, 0.85),
    "M_Rubber": ((34, 34, 36), 0.78, 0.0),
    "M_Bristle": ((30, 30, 32), 0.85, 0.0),
    "M_Turquoise": ((111, 211, 198), 0.35, 0.0),
    "M_Hose": ((21, 22, 23), 0.55, 0.0),
    "M_Label": ((201, 202, 203), 0.38, 0.0),
    "M_LED": ((245, 248, 255), 0.2, 0.0),
    "M_Screen": ((14, 15, 17), 0.08, 0.0),
    "M_LightStrip": ((122, 91, 163), 0.3, 0.0),
    "M_Dust": ((120, 108, 96), 0.95, 0.0),
}
ROLLER_STRIPE = m("roller.stripe_srgb", (66, 150, 136), "ref #3A7F74 brightened toward V5 minty close-ups", "inferred")

# ---------------------------------------------------------------- detail tiers
DETAIL = {
    "high": {"lathe": 200, "corner": 9, "bevel_seg": 5, "roller_rings": 110, "roller_segs": 160, "path": 2.5},
    "balanced": {"lathe": 96, "corner": 5, "bevel_seg": 3, "roller_rings": 44, "roller_segs": 80, "path": 1.2},
}
