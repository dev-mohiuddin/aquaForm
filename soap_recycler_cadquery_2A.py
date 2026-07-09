"""
Soap Recycler + Recycled Soap Holder - Prototype 2A Premium Process Concept

This is a polished parametric CadQuery model based on the handwritten
prototype notes. It keeps the original functional idea, but presents it as a
more client-ready product concept with a clear collection-to-reforming journey:
draining basket, removable MoldPod, isolated heater/press area, side service
pod, and bathtub/shower hooks.

Run:
    ./.venv/bin/python soap_recycler_cadquery_2A.py

Outputs:
    soap_recycler_prototype_2A.step
    soap_recycler_prototype_2A.stl
    soap_recycler_demo_2A.html

Coordinate system:
    X = width left/right
    Y = depth front/back; back/wall side is +Y, user/front side is -Y
    Z = height from bottom upward

Concept workflow:
    1. Collect scraps in the perforated upper basket.
    2. Let water drain back into the tub/shower; this basket is a drying stage.
    3. Remove the basket and manually load dry scraps into the lower MoldPod.
    4. A sealed low-voltage thermal plate softens the batch, then a press cap
       consolidates it. Cool, pull out the MoldPod, and release the new bar.

Safety note:
    Heating, batteries, wiring, and wet-area sealing are visual placeholders.
    The D-cell side service pod is shown as a control-power concept, not a claim
    that four D cells can safely heat a wet soap batch. A real product needs a
    certified isolated power system, thermal cutoffs, waterproofing, food-safe
    materials, cleaning validation, and product certification.
"""

import cadquery as cq
import json
from pathlib import Path


# -----------------------------
# Parametric dimensions, in mm
# -----------------------------
P = {
    "body_w": 188.0,
    "body_d": 86.0,
    "body_h": 242.0,
    "wall": 3.2,
    "corner_r": 12.0,
    "front_frame_w": 12.0,
    "shelf_z": 118.0,
    "upper_z": 128.0,
    "lower_z": 20.0,
    "basket_w": 152.0,
    "basket_d": 58.0,
    "basket_h": 44.0,
    "basket_wall": 2.4,
    "drain_hole_d": 3.2,
    "soap_bar_w": 84.0,
    "soap_bar_d": 50.0,
    "soap_bar_h": 24.0,
    "mold_wall": 3.0,
    "mold_pod_liner": 2.2,
    "press_plate_h": 7.0,
    "press_clearance": 2.5,
    "heater_w": 100.0,
    "heater_d": 62.0,
    "heater_h": 3.0,
    "drawer_w": 158.0,
    "drawer_d": 52.0,
    "drawer_h": 44.0,
    "service_pod_w": 48.0,
    "service_pod_d": 76.0,
    "service_pod_h": 158.0,
    "d_cell_diameter": 33.5,
    "d_cell_length": 61.5,
    "hook_w": 22.0,
    "hook_thick": 6.0,
    "hook_drop": 56.0,
    "hook_lip": 31.0,
    "hook_spacing": 104.0,
    "hinge_radius": 3.0,
    "gasket_thick": 2.0,
    "drain_tray_h": 12.0,
    "drain_spout_d": 7.0,
    "status_diameter": 18.0,
}


# -----------------------------
# CAD helpers
# -----------------------------
def box(w, d, h, r=0.0):
    """Box centered on X/Y, base at Z=0, with optional rounded vertical edges."""
    obj = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))
    if r and min(w, d) > 2 * r and h > 0:
        obj = obj.edges("|Z").fillet(r)
    return obj


def open_box(w, d, h, wall, r=4.0):
    outer = box(w, d, h, r)
    inner = box(w - 2 * wall, d - 2 * wall, h + 1.0, max(0.1, r - wall)).translate((0, 0, wall))
    return outer.cut(inner)


def rounded_plate_with_holes(w, d, h, hole_d=3.0, nx=6, ny=3, r=4.0, margin_x=12.0, margin_y=10.0):
    plate = box(w, d, h, r)
    pts = []
    sx = (w - 2 * margin_x) / (nx - 1) if nx > 1 else 0
    sy = (d - 2 * margin_y) / (ny - 1) if ny > 1 else 0
    for i in range(nx):
        for j in range(ny):
            pts.append((-w / 2 + margin_x + i * sx, -d / 2 + margin_y + j * sy))
    return plate.faces(">Z").workplane().pushPoints(pts).circle(hole_d / 2).cutThruAll()


def vent_panel(w, thick, h, r=7.0, slot_w=28.0, slot_h=5.0, cols=4, rows=3):
    panel = box(w, thick, h, r)
    cutters = None
    x_gap = w / (cols + 1)
    z_gap = h / (rows + 1)
    for c in range(cols):
        for row in range(rows):
            x = -w / 2 + x_gap * (c + 1)
            z = z_gap * (row + 1)
            slot = box(slot_w, thick + 2, slot_h, 2.0).translate((x, 0, z - slot_h / 2))
            cutters = slot if cutters is None else cutters.union(slot)
    return panel.cut(cutters)


def cyl_x(radius, length):
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((-length / 2, 0, 0))


def cyl_y(radius, length):
    return cq.Workplane("XZ").circle(radius).extrude(length).translate((0, -length / 2, 0))


def cyl_z(radius, height):
    return cq.Workplane("XY").circle(radius).extrude(height)


def rounded_ring(outer_r, inner_r, height):
    return cyl_z(outer_r, height).cut(cyl_z(inner_r, height + 1.0).translate((0, 0, -0.5)))


def oval_solid(w, d, h, r=1.5):
    obj = cq.Workplane("XY").ellipse(w / 2, d / 2).extrude(h)
    if r and h > 2 * r:
        try:
            obj = obj.edges("|Z").fillet(r)
        except Exception:
            pass
    return obj


def make_hook():
    th = P["hook_thick"]
    w = P["hook_w"]
    lip = P["hook_lip"]
    drop = P["hook_drop"]
    vertical = box(w, th, drop, 1.8)
    top_lip = box(w, lip, th, 1.8).translate((0, -lip / 2 + th / 2, drop - th))
    return_leg = box(w, th, drop * 0.58, 1.8).translate((0, -lip + th, drop * 0.33))
    soft_pad = box(w + 4, 2.2, drop * 0.38, 1.0).translate((0, -lip + th - 2.5, drop * 0.36))
    return vertical.union(top_lip).union(return_leg).union(soft_pad)


def heater_trace(width=86.0, depth=48.0, trace_w=2.1, trace_h=1.1):
    y_positions = [-depth / 2 + 5.5, -depth / 6, depth / 6, depth / 2 - 5.5]
    obj = None
    for idx, y in enumerate(y_positions):
        seg = box(width - 10, trace_w, trace_h, 0.3).translate((0, y, 0))
        obj = seg if obj is None else obj.union(seg)
        if idx < len(y_positions) - 1:
            x = (width / 2 - 7) * (1 if idx % 2 == 0 else -1)
            conn = box(trace_w, abs(y_positions[idx + 1] - y), trace_h, 0.3).translate(
                (x, (y + y_positions[idx + 1]) / 2, 0)
            )
            obj = obj.union(conn)
    return obj


def mesh_insert(w, d, z_thick=1.2, bar=1.1, gap=11.0):
    frame = box(w, d, z_thick, 3.5)
    bars = frame
    count_x = int(w // gap)
    count_y = int(d // gap)
    for i in range(count_x + 1):
        x = -w / 2 + i * gap
        bars = bars.union(box(bar, d - 7, z_thick + 0.2, 0.2).translate((x, 0, 0)))
    for j in range(count_y + 1):
        y = -d / 2 + j * gap
        bars = bars.union(box(w - 7, bar, z_thick + 0.2, 0.2).translate((0, y, 0)))
    return bars


def soap_scraps():
    specs = [
        (-44, -8, 0, 24, 13, 5, 7),
        (-8, 10, 0, 30, 16, 6, -8),
        (38, -5, 0, 22, 15, 5, 16),
        (18, 17, 0, 17, 11, 4, 28),
    ]
    obj = None
    for x, y, z, w, d, h, rot in specs:
        scrap = oval_solid(w, d, h, 1.2).rotate((0, 0, 0), (0, 0, 1), rot).translate((x, y, z))
        obj = scrap if obj is None else obj.union(scrap)
    return obj


def water_flow_path():
    drops = None
    # The drain path stays at the side of the unit so drain water never enters
    # the lower thermal MoldPod compartment.
    for x, y, z, h in [(-68, 17, 142, 12), (-68, 17, 112, 16), (-68, 17, 78, 17), (-68, 17, 44, 14)]:
        drop = cyl_y(2.0, 2.2).translate((x, y, z)).union(oval_solid(5.0, 3.0, h, 1.0).translate((x, y, z)))
        drops = drop if drops is None else drops.union(drop)
    gutter = box(18, 54, 2.0, 5.0).translate((-68, 4, P["shelf_z"] + 5))
    outlet = cyl_z(P["drain_spout_d"] / 2, 13).translate((-68, 17, -11))
    return gutter.union(drops).union(outlet)


# -----------------------------
# Main parts
# -----------------------------
body_w = P["body_w"]
body_d = P["body_d"]
body_h = P["body_h"]
t = P["wall"]

# Premium open-front housing
back_panel = box(body_w, t, body_h, P["corner_r"]).translate((0, body_d / 2 - t / 2, 0))
left_wall = box(t, body_d, body_h, 2.0).translate((-body_w / 2 + t / 2, 0, 0))
right_wall = box(t, body_d, body_h, 2.0).translate((body_w / 2 - t / 2, 0, 0))
top_panel = box(body_w, body_d, t, P["corner_r"]).translate((0, 0, body_h - t))
bottom_panel = box(body_w, body_d, t, P["corner_r"])
front_left_rail = box(P["front_frame_w"], 8, body_h - 10, 4).translate((-body_w / 2 + 10, -body_d / 2 - 2, 5))
front_right_rail = box(P["front_frame_w"], 8, body_h - 10, 4).translate((body_w / 2 - 10, -body_d / 2 - 2, 5))
mid_shelf = rounded_plate_with_holes(body_w - 2 * t, body_d - 2 * t, t, 4.2, 10, 3, 5).translate((0, 0, P["shelf_z"]))
lower_rail = box(body_w - 26, 8, 8, 4).translate((0, -body_d / 2 - 2, 103))
upper_badge = box(86, 3.0, 14, 5).translate((0, -body_d / 2 - 4, body_h - 28))
main_housing = (
    back_panel.union(left_wall)
    .union(right_wall)
    .union(top_panel)
    .union(bottom_panel)
    .union(front_left_rail)
    .union(front_right_rail)
    .union(mid_shelf)
    .union(lower_rail)
    .union(upper_badge)
)

# Hinged front cover
front_cover_h = 102.0
front_cover = vent_panel(body_w - 28, 4.0, front_cover_h, 8, 30, 5, 4, 3).translate(
    (0, -body_d / 2 - 5.0, P["upper_z"] + 6)
)
cover_window = box(body_w - 68, 2.0, 46, 5).translate((0, -body_d / 2 - 7.2, P["upper_z"] + 34))
cover_handle = box(76, 10, 9, 4).translate((0, -body_d / 2 - 13.0, P["upper_z"] + 18))
# Soft gasket and status ring make the wet upper chamber read as a sealed product,
# not an open electronics enclosure.
cover_gasket = box(body_w - 42, 2.2, front_cover_h - 16, 9).cut(
    box(body_w - 56, 3.2, front_cover_h - 30, 7)
).translate((0, -body_d / 2 - 8.8, P["upper_z"] + 14))
status_ring = rounded_ring(P["status_diameter"] / 2, P["status_diameter"] / 2 - 2.4, 3.0).rotate(
    (0, 0, 0), (1, 0, 0), 90
).translate((body_w / 2 - 30, -body_d / 2 - 10.5, P["upper_z"] + 78))
status_core = cyl_y(4.0, 3.3).translate((body_w / 2 - 30, -body_d / 2 - 10.7, P["upper_z"] + 78))
hinge_upper = cyl_x(P["hinge_radius"], body_w - 24).translate((0, -body_d / 2 - 6.0, P["upper_z"] + front_cover_h + 8))
hinge_lower = cyl_x(P["hinge_radius"], body_w - 24).translate((0, -body_d / 2 - 6.0, P["upper_z"] + 4))

# Wet soap basket and mesh insert
basket_body = open_box(P["basket_w"], P["basket_d"], P["basket_h"], P["basket_wall"], 8).translate(
    (0, -3, P["upper_z"] + 30)
)
basket_mesh = mesh_insert(P["basket_w"] - 14, P["basket_d"] - 14).translate((0, -3, P["upper_z"] + 32))
basket_lip = box(P["basket_w"] + 10, P["basket_d"] + 10, 4, 8).translate((0, -3, P["upper_z"] + P["basket_h"] + 30))
soap_scrap_visuals = soap_scraps().translate((0, -3, P["upper_z"] + 36))

# Drip channel and lower mold/heater
drip_visuals = water_flow_path()
drain_tray = open_box(42, 58, P["drain_tray_h"], 2.2, 5).translate((-68, 10, P["shelf_z"] + 5))
drain_grille = rounded_plate_with_holes(30, 46, 1.6, 3.0, 3, 4, 3, 7, 7).translate(
    (-68, 10, P["shelf_z"] + P["drain_tray_h"] + 5)
)
mold_outer_w = P["soap_bar_w"] + 2 * P["mold_wall"] + 14
mold_outer_d = P["soap_bar_d"] + 2 * P["mold_wall"] + 10
mold_outer_h = P["soap_bar_h"] + P["mold_wall"] + 7
soap_mold = open_box(mold_outer_w, mold_outer_d, mold_outer_h, P["mold_wall"], 8).translate((0, -6, P["lower_z"] + 21))
mold_lip = box(mold_outer_w + 10, mold_outer_d + 10, 4, 7).translate((0, -6, P["lower_z"] + mold_outer_h + 21))
mold_pull = box(66, 12, 10, 4).translate((0, -body_d / 2 - 12, P["lower_z"] + 30))
recycled_bar = oval_solid(P["soap_bar_w"], P["soap_bar_d"], P["soap_bar_h"], 2).translate((0, -6, P["lower_z"] + 26))
thermal_gap = box(P["heater_w"] + 12, P["heater_d"] + 12, 2.4, 5).translate((0, -6, P["lower_z"] + 10))
heater_plate = box(P["heater_w"], P["heater_d"], P["heater_h"], 5).translate((0, -6, P["lower_z"] + 13))
heater_line = heater_trace().translate((0, -6, P["lower_z"] + 16.2))
safety_channel = box(18, 6, 72, 3).translate((body_w / 2 - 18, -body_d / 2 + 18, 28))
# The MoldPod is a removable, silicone-lined micro-batch cartridge. The press
# cap is parked above it in the static CAD view and moves only in the demo.
mold_liner = open_box(P["soap_bar_w"] + 2 * P["mold_pod_liner"], P["soap_bar_d"] + 2 * P["mold_pod_liner"], P["soap_bar_h"] + 5, P["mold_pod_liner"], 7).translate(
    (0, -6, P["lower_z"] + 25)
)
press_plate = box(P["soap_bar_w"] + 4, P["soap_bar_d"] + 4, P["press_plate_h"], 6).translate(
    (0, -6, P["lower_z"] + mold_outer_h + 31)
)
press_stem = cyl_z(7.0, 24).translate((0, -6, P["lower_z"] + mold_outer_h + 38))
thermal_lid = box(mold_outer_w + 16, mold_outer_d + 16, 5.0, 8).translate(
    (0, -6, P["lower_z"] + mold_outer_h + 57)
)
cooling_vents = vent_panel(60, 3.0, 22, 5, 11, 3, 4, 2).translate((0, body_d / 2 - 2, P["lower_z"] + 73))

# Battery/service pod and cells. Four D cells cannot physically coexist with the
# MoldPod in a shallow lower drawer, so this is an isolated side-mounted cassette.
# Its 2 x 2 vertical grid fits the stated four-D-cell requirement without sharing
# the wet or thermal volume.
service_x = body_w / 2 + P["service_pod_w"] / 2 + 6
battery_shell = open_box(P["service_pod_w"], P["service_pod_d"], P["service_pod_h"], 2.4, 7).translate((service_x, 0, 15))
battery_face = box(P["service_pod_w"] + 4, 7, P["service_pod_h"] + 6, 6).translate((service_x, -42, 12))
battery_handle = box(30, 12, 11, 5).translate((service_x, -52, 84))
battery_cells = []
battery_contacts = []
for cell_index, (yy, zz) in enumerate([(-20, 25), (-20, 96), (20, 25), (20, 96)], start=1):
    cell = cyl_z(P["d_cell_diameter"] / 2, P["d_cell_length"]).translate((service_x, yy, zz))
    contact_l = cyl_z(4.5, 2.5).translate((service_x, yy, zz - 2.5))
    contact_r = cyl_z(4.5, 2.5).translate((service_x, yy, zz + P["d_cell_length"]))
    battery_cells.append(cell)
    battery_contacts.append(contact_l.union(contact_r))
electronics_bulkhead = box(P["service_pod_w"] - 10, 4, 30, 4).translate((service_x, 34, 18))
power_seal = box(P["service_pod_w"] + 2, 2.0, P["service_pod_h"] + 2, 5).translate((service_x, -39, 14))

# Hooks and ghost bathtub rim
hook_left = make_hook().translate((-P["hook_spacing"] / 2, body_d / 2 + 9, body_h - 58))
hook_right = make_hook().translate((P["hook_spacing"] / 2, body_d / 2 + 9, body_h - 58))
hooks = hook_left.union(hook_right)
tub_rim = box(body_w + 55, 32, 12, 6).translate((0, body_d / 2 + 22, body_h - 16))
mount_bosses = (
    cyl_y(7, 3).translate((-56, body_d / 2 + 2, 168))
    .union(cyl_y(7, 3).translate((56, body_d / 2 + 2, 168)))
    .union(cyl_y(5, 3.5).translate((0, body_d / 2 + 2, 202)))
)


# -----------------------------
# Assembly and exports
# -----------------------------
assy = cq.Assembly(name="Soap_Recycler_Prototype_2A_Premium")
assy.add(main_housing, name="premium_open_front_housing", color=cq.Color(0.92, 0.94, 0.90, 1))
assy.add(front_cover, name="lift_front_vented_cover", color=cq.Color(0.20, 0.42, 0.47, 1))
assy.add(cover_window, name="smoke_translucent_cover_window_visual", color=cq.Color(0.36, 0.62, 0.66, 0.45))
assy.add(cover_handle, name="front_cover_pull_handle", color=cq.Color(0.09, 0.12, 0.12, 1))
assy.add(cover_gasket, name="wet_chamber_silicone_gasket", color=cq.Color(0.06, 0.09, 0.09, 1))
assy.add(status_ring, name="front_cycle_status_ring", color=cq.Color(0.78, 0.61, 0.29, 1))
assy.add(status_core, name="front_cycle_status_light", color=cq.Color(0.17, 0.76, 0.64, 1))
assy.add(hinge_upper, name="upper_hinge_pin", color=cq.Color(0.1, 0.1, 0.1, 1))
assy.add(hinge_lower, name="lower_hinge_pin", color=cq.Color(0.1, 0.1, 0.1, 1))
assy.add(basket_body, name="removable_wet_soap_basket", color=cq.Color(0.82, 0.83, 0.76, 1))
assy.add(basket_mesh, name="durable_mesh_basket_insert_visual", color=cq.Color(0.52, 0.56, 0.52, 1))
assy.add(basket_lip, name="basket_grip_lip", color=cq.Color(0.25, 0.44, 0.42, 1))
assy.add(soap_scrap_visuals, name="soap_scraps_placeholder", color=cq.Color(0.86, 0.68, 0.42, 1))
assy.add(drip_visuals, name="drain_chute_and_water_path_visual", color=cq.Color(0.22, 0.63, 0.85, 0.55))
assy.add(drain_tray, name="side_drain_collection_tray", color=cq.Color(0.30, 0.44, 0.42, 1))
assy.add(drain_grille, name="side_drain_grille", color=cq.Color(0.68, 0.70, 0.65, 1))
assy.add(soap_mold, name="pull_out_recycled_soap_mold", color=cq.Color(0.77, 0.78, 0.72, 1))
assy.add(mold_lip, name="mold_grip_lip", color=cq.Color(0.30, 0.39, 0.35, 1))
assy.add(mold_pull, name="mold_pull_tab", color=cq.Color(0.10, 0.13, 0.12, 1))
assy.add(recycled_bar, name="finished_recycled_soap_bar_visual", color=cq.Color(0.94, 0.78, 0.52, 1))
assy.add(thermal_gap, name="thermal_insulation_separator", color=cq.Color(0.13, 0.14, 0.14, 1))
assy.add(heater_plate, name="sealed_low_voltage_heater_plate_visual", color=cq.Color(0.90, 0.32, 0.18, 1))
assy.add(heater_line, name="heater_trace_visual", color=cq.Color(1.00, 0.14, 0.06, 1))
assy.add(safety_channel, name="sealed_wire_channel_visual", color=cq.Color(0.08, 0.10, 0.10, 1))
assy.add(mold_liner, name="removable_silicone_moldpod_liner", color=cq.Color(0.20, 0.57, 0.55, 1))
assy.add(press_plate, name="moldpod_press_cap", color=cq.Color(0.64, 0.54, 0.38, 1))
assy.add(press_stem, name="press_cap_stem", color=cq.Color(0.24, 0.29, 0.27, 1))
assy.add(thermal_lid, name="insulated_moldpod_thermal_lid", color=cq.Color(0.18, 0.28, 0.27, 1))
assy.add(cooling_vents, name="rear_cooling_vents", color=cq.Color(0.22, 0.33, 0.31, 1))
assy.add(battery_shell, name="pull_out_four_d_cell_battery_drawer", color=cq.Color(0.62, 0.60, 0.54, 1))
assy.add(battery_face, name="battery_drawer_face", color=cq.Color(0.22, 0.29, 0.28, 1))
assy.add(battery_handle, name="battery_drawer_handle", color=cq.Color(0.08, 0.10, 0.10, 1))
for cell_index, cell in enumerate(battery_cells, start=1):
    assy.add(cell, name=f"d_cell_{cell_index}_control_power_placeholder", color=cq.Color(0.16, 0.19, 0.18, 1))
for contact_index, contact in enumerate(battery_contacts, start=1):
    assy.add(contact, name=f"d_cell_{contact_index}_end_contacts", color=cq.Color(0.78, 0.68, 0.46, 1))
assy.add(electronics_bulkhead, name="dry_bay_electronics_bulkhead", color=cq.Color(0.11, 0.18, 0.18, 1))
assy.add(power_seal, name="battery_drawer_perimeter_seal", color=cq.Color(0.12, 0.45, 0.42, 1))
assy.add(hooks, name="dual_bathtub_or_shower_hooks", color=cq.Color(0.46, 0.52, 0.46, 1))
assy.add(tub_rim, name="ghost_bathtub_rim_context_visual", color=cq.Color(0.80, 0.86, 0.87, 0.28))
assy.add(mount_bosses, name="optional_wall_mount_bosses", color=cq.Color(0.45, 0.48, 0.46, 1))


DEMO_PARTS = [
    {"id": "housing", "group": "housing", "shape": main_housing, "color": [0.86, 0.89, 0.85], "alpha": 1.0},
    {"id": "front_cover", "group": "cover", "shape": front_cover, "color": [0.08, 0.30, 0.31], "alpha": 1.0},
    {"id": "cover_window", "group": "cover", "shape": cover_window, "color": [0.20, 0.55, 0.56], "alpha": 0.48},
    {"id": "cover_handle", "group": "cover", "shape": cover_handle, "color": [0.05, 0.08, 0.08], "alpha": 1.0},
    {"id": "cover_gasket", "group": "cover", "shape": cover_gasket, "color": [0.04, 0.06, 0.06], "alpha": 1.0},
    {"id": "status_ring", "group": "status", "shape": status_ring, "color": [0.85, 0.61, 0.25], "alpha": 1.0},
    {"id": "status_core", "group": "status", "shape": status_core, "color": [0.12, 0.86, 0.68], "alpha": 1.0},
    {"id": "hinge_upper", "group": "hinge", "shape": hinge_upper, "color": [0.08, 0.09, 0.09], "alpha": 1.0},
    {"id": "hinge_lower", "group": "hinge", "shape": hinge_lower, "color": [0.08, 0.09, 0.09], "alpha": 1.0},
    {"id": "basket_body", "group": "basket", "shape": basket_body, "color": [0.75, 0.78, 0.72], "alpha": 1.0},
    {"id": "basket_mesh", "group": "basket", "shape": basket_mesh, "color": [0.37, 0.46, 0.42], "alpha": 1.0},
    {"id": "basket_lip", "group": "basket", "shape": basket_lip, "color": [0.10, 0.37, 0.35], "alpha": 1.0},
    {"id": "soap_scraps", "group": "scraps", "shape": soap_scrap_visuals, "color": [0.90, 0.57, 0.27], "alpha": 1.0},
    {"id": "drain_path", "group": "water", "shape": drip_visuals, "color": [0.12, 0.62, 0.88], "alpha": 0.16},
    {"id": "drain_tray", "group": "drain", "shape": drain_tray, "color": [0.18, 0.40, 0.39], "alpha": 1.0},
    {"id": "drain_grille", "group": "drain", "shape": drain_grille, "color": [0.66, 0.69, 0.63], "alpha": 1.0},
    {"id": "soap_mold", "group": "mold", "shape": soap_mold, "color": [0.63, 0.68, 0.62], "alpha": 1.0},
    {"id": "mold_lip", "group": "mold", "shape": mold_lip, "color": [0.18, 0.30, 0.27], "alpha": 1.0},
    {"id": "mold_pull", "group": "mold", "shape": mold_pull, "color": [0.05, 0.07, 0.07], "alpha": 1.0},
    {"id": "mold_liner", "group": "mold", "shape": mold_liner, "color": [0.12, 0.57, 0.54], "alpha": 1.0},
    {"id": "recycled_bar", "group": "bar", "shape": recycled_bar, "color": [0.94, 0.66, 0.34], "alpha": 1.0},
    {"id": "thermal_gap", "group": "heater", "shape": thermal_gap, "color": [0.08, 0.10, 0.10], "alpha": 1.0},
    {"id": "heater_plate", "group": "heater", "shape": heater_plate, "color": [0.76, 0.22, 0.10], "alpha": 1.0},
    {"id": "heater_line", "group": "heater", "shape": heater_line, "color": [1.00, 0.16, 0.05], "alpha": 1.0},
    {"id": "safety_channel", "group": "heater", "shape": safety_channel, "color": [0.05, 0.07, 0.07], "alpha": 1.0},
    {"id": "press_plate", "group": "press", "shape": press_plate, "color": [0.63, 0.49, 0.27], "alpha": 1.0},
    {"id": "press_stem", "group": "press", "shape": press_stem, "color": [0.16, 0.23, 0.22], "alpha": 1.0},
    {"id": "thermal_lid", "group": "press", "shape": thermal_lid, "color": [0.09, 0.22, 0.22], "alpha": 1.0},
    {"id": "cooling_vents", "group": "press", "shape": cooling_vents, "color": [0.16, 0.29, 0.27], "alpha": 1.0},
    {"id": "battery_shell", "group": "battery", "shape": battery_shell, "color": [0.38, 0.42, 0.37], "alpha": 1.0},
    {"id": "battery_face", "group": "battery", "shape": battery_face, "color": [0.08, 0.17, 0.17], "alpha": 1.0},
    {"id": "battery_handle", "group": "battery", "shape": battery_handle, "color": [0.03, 0.05, 0.05], "alpha": 1.0},
    {"id": "electronics_bulkhead", "group": "battery", "shape": electronics_bulkhead, "color": [0.05, 0.13, 0.13], "alpha": 1.0},
    {"id": "power_seal", "group": "battery", "shape": power_seal, "color": [0.08, 0.52, 0.49], "alpha": 1.0},
    {"id": "hooks", "group": "hooks", "shape": hooks, "color": [0.33, 0.42, 0.36], "alpha": 1.0},
    {"id": "tub_rim", "group": "context", "shape": tub_rim, "color": [0.68, 0.80, 0.80], "alpha": 0.20},
    {"id": "mount_bosses", "group": "housing", "shape": mount_bosses, "color": [0.36, 0.41, 0.39], "alpha": 1.0},
]

for cell_index, cell in enumerate(battery_cells, start=1):
    DEMO_PARTS.append({"id": f"battery_cell_{cell_index}", "group": "battery", "shape": cell, "color": [0.16, 0.19, 0.18], "alpha": 1.0})
for contact_index, contact in enumerate(battery_contacts, start=1):
    DEMO_PARTS.append({"id": f"battery_contact_{contact_index}", "group": "battery", "shape": contact, "color": [0.84, 0.67, 0.32], "alpha": 1.0})


PROCESS_STEPS = [
    {
        "id": "collect",
        "number": "01",
        "label": "Collect",
        "title": "Add the small soap pieces",
        "body": "Place leftover bars and fragments in the upper removable mesh basket. The basket keeps the pieces visible and easy to rinse.",
        "detail": "No grinding or heat yet. This is the daily collection stage.",
    },
    {
        "id": "drain",
        "number": "02",
        "label": "Drain",
        "title": "Separate water from the soap",
        "body": "After use, water falls through the mesh, enters the isolated side gutter, and returns to the bath or shower. It never enters the thermal bay.",
        "detail": "A drier batch is cleaner, more consistent, and less likely to create foam during reforming.",
    },
    {
        "id": "load",
        "number": "03",
        "label": "Load MoldPod",
        "title": "Move dry scraps into the sealed lower cartridge",
        "body": "When the basket is full, lift it out and pour the dry pieces into the silicone-lined MoldPod below. This intentional handoff prevents clogs and keeps the wet and heated zones separate.",
        "detail": "The demo moves the same CAD soap-scrap mesh into the MoldPod to make this handoff clear.",
    },
    {
        "id": "fuse",
        "number": "04",
        "label": "Fuse",
        "title": "Softly fuse the soap batch",
        "body": "The insulated thermal plate evenly softens a small batch inside the closed MoldPod. The red trace is a visual placeholder for a temperature-controlled heating zone.",
        "detail": "A production version needs a certified isolated low-voltage power system and thermal cutoff.",
    },
    {
        "id": "press",
        "number": "05",
        "label": "Press and cool",
        "title": "Consolidate the softened batch",
        "body": "The press cap descends onto the lined mold, removing voids and giving the bar a repeatable shape. Rear vents represent the cooling phase.",
        "detail": "The heating chamber and dry service bay are shown as physically separated CAD regions.",
    },
    {
        "id": "release",
        "number": "06",
        "label": "Release",
        "title": "Pull out a new usable soap bar",
        "body": "After cooling, pull the MoldPod forward and flex the silicone liner to release the re-formed bar. The cycle can then begin again with new scraps.",
        "detail": "The finished bar in the demo is the same CAD mesh included in the STEP export.",
    },
]


CALLOUTS = [
    {"part": "basket_body", "steps": ["collect", "drain", "load"], "title": "Removable mesh basket", "body": "Daily soap-scrap collector and draining surface.", "offset": [36, 16, -4]},
    {"part": "drain_path", "steps": ["drain"], "title": "Isolated side drain", "body": "Drain water bypasses the thermal MoldPod bay.", "offset": [34, 12, 5]},
    {"part": "mold_liner", "steps": ["load", "fuse", "press", "release"], "title": "Silicone-lined MoldPod", "body": "A removable batch cartridge for reforming and release.", "offset": [37, 18, 11]},
    {"part": "heater_plate", "steps": ["fuse", "press"], "title": "Sealed thermal zone", "body": "Illustrative temperature-controlled heater and insulation stack.", "offset": [36, 10, 9]},
    {"part": "battery_shell", "steps": ["power"], "title": "Dry side service pod", "body": "Four D-cell placeholders remain visible with copper contacts; the isolated pod does not wash out to white.", "offset": [34, -4, 18]},
    {"part": "hooks", "steps": ["mount"], "title": "Tub / shower hooks", "body": "Rear hooks support a tool-free hanging concept.", "offset": [34, 14, -10]},
]


# ---------------------------------------------------------------------------
# Compact AquaForm kit override
# ---------------------------------------------------------------------------
# The earlier all-in-one study remains above as design history. These objects
# replace its export assembly with a compact two-piece product: wet collector
# plus a dry USB-C ReForm Base. All HTML meshes are made from this assembly.
C = {
    "collector_w": 154.0, "collector_d": 90.0, "collector_h": 182.0,
    "base_w": 128.0, "base_d": 94.0, "base_h": 48.0,
    "wall": 3.2, "basket_w": 126.0, "basket_d": 56.0, "basket_h": 38.0,
    "bar_w": 78.0, "bar_d": 48.0, "bar_h": 22.0,
    "mini_w": 58.0, "mini_d": 36.0, "mini_h": 18.0,
}
collector_x, base_x = -92.0, 108.0
cw, cd, ch, ct = C["collector_w"], C["collector_d"], C["collector_h"], C["wall"]

# Wet Shower Collector
compact_back = box(cw, ct, ch, 11).translate((collector_x, cd / 2 - ct / 2, 0))
compact_left = box(ct, cd, ch, 2).translate((collector_x - cw / 2 + ct / 2, 0, 0))
compact_right = box(ct, cd, ch, 2).translate((collector_x + cw / 2 - ct / 2, 0, 0))
compact_top = box(cw, cd, ct, 11).translate((collector_x, 0, ch - ct))
compact_bottom = box(cw, cd, ct, 11)
compact_shelf = rounded_plate_with_holes(cw - 2 * ct, cd - 2 * ct, ct, 3.6, 9, 4, 5).translate((collector_x, 0, 78))
compact_rail_l = box(9, 7, ch - 14, 3).translate((collector_x - cw / 2 + 9, -cd / 2 - 2, 7))
compact_rail_r = box(9, 7, ch - 14, 3).translate((collector_x + cw / 2 - 9, -cd / 2 - 2, 7))
compact_collector = compact_back.union(compact_left).union(compact_right).union(compact_top).union(compact_bottom).union(compact_shelf).union(compact_rail_l).union(compact_rail_r)

compact_cover = box(cw - 26, 4, 72, 8).translate((collector_x, -cd / 2 - 5, 98))
for slot_x in [-42, -14, 14, 42]:
    for slot_z in [112, 132, 152]:
        compact_cover = compact_cover.cut(box(18, 6, 4.5, 2).translate((collector_x + slot_x, -cd / 2 - 5, slot_z)))
compact_window = box(cw - 58, 2, 30, 5).translate((collector_x, -cd / 2 - 7, 121))
compact_handle = box(58, 10, 8, 4).translate((collector_x, -cd / 2 - 12, 104))
compact_hinge = cyl_x(3, cw - 26).translate((collector_x, -cd / 2 - 6, 96))
compact_gasket = box(cw - 36, 2, 64, 9).cut(box(cw - 50, 3, 50, 7)).translate((collector_x, -cd / 2 - 8, 101))
compact_status_ring = cyl_y(8, 3).cut(cyl_y(5.3, 4)).translate((collector_x + 51, -cd / 2 - 10, 148))
compact_status_light = cyl_y(4, 3.3).translate((collector_x + 51, -cd / 2 - 10.5, 148))

compact_basket = open_box(C["basket_w"], C["basket_d"], C["basket_h"], 2.4, 7).translate((collector_x, -2, 108))
compact_mesh = mesh_insert(C["basket_w"] - 12, C["basket_d"] - 12).translate((collector_x, -2, 110))
compact_basket_lip = box(C["basket_w"] + 8, C["basket_d"] + 8, 4, 7).translate((collector_x, -2, 146))
compact_scraps = soap_scraps().translate((collector_x, -2, 114))
compact_gutter = open_box(24, 52, 12, 2.2, 4).translate((collector_x - 55, 13, 82))
compact_grille = rounded_plate_with_holes(17, 39, 1.4, 3.0, 2, 4, 3, 5, 5).translate((collector_x - 55, 13, 93))
compact_water = None
for drop_z, drop_h in [(118, 12), (94, 14), (66, 13), (38, 11)]:
    drop = oval_solid(5, 3, drop_h, 1).translate((collector_x - 55, 13, drop_z))
    compact_water = drop if compact_water is None else compact_water.union(drop)
compact_nozzle = cyl_z(4.5, 12).translate((collector_x - 55, 13, -10))
compact_hooks = make_hook().translate((collector_x - 46, cd / 2 + 9, ch - 53)).union(make_hook().translate((collector_x + 46, cd / 2 + 9, ch - 53)))
compact_tub = box(cw + 42, 30, 11, 5).translate((collector_x, cd / 2 + 22, ch - 15))

# Dry USB-C ReForm Base and two removable MoldPods
bw, bd, bh = C["base_w"], C["base_d"], C["base_h"]
compact_base = box(bw, bd, bh, 13).translate((base_x, 0, 0))
compact_base_inset = open_box(bw - 18, bd - 18, 17, 2.5, 8).translate((base_x, 0, bh - 2))
compact_feet = box(35, 16, 5, 2).translate((base_x - 38, 0, -5)).union(box(35, 16, 5, 2).translate((base_x + 38, 0, -5)))
compact_usb = box(15, 3, 6, 1.5).translate((base_x, bd / 2 + 1, 17))
compact_usb_ring = box(35, 2, 13, 4).translate((base_x, bd / 2 + 1, 13))
compact_heater = box(90, 60, 3, 5).translate((base_x, 0, bh + 10))
compact_trace = None
for trace_y in [-20, -7, 7, 20]:
    trace = box(70, 1.8, 1, .2).translate((base_x, trace_y, bh + 13.2))
    compact_trace = trace if compact_trace is None else compact_trace.union(trace)

regular_outer = open_box(C["bar_w"] + 10, C["bar_d"] + 10, C["bar_h"] + 10, 3, 7).translate((base_x, 0, bh + 16))
regular_liner = open_box(C["bar_w"] + 4, C["bar_d"] + 4, C["bar_h"] + 5, 2, 6).translate((base_x, 0, bh + 19))
regular_lip = box(C["bar_w"] + 18, C["bar_d"] + 18, 4, 7).translate((base_x, 0, bh + 42))
regular_bar = oval_solid(C["bar_w"], C["bar_d"], C["bar_h"], 2).translate((base_x, 0, bh + 23))
mini_x, mini_y = base_x + 42, -57
mini_outer = open_box(C["mini_w"] + 10, C["mini_d"] + 10, C["mini_h"] + 9, 3, 6).translate((mini_x, mini_y, bh + 5))
mini_liner = open_box(C["mini_w"] + 4, C["mini_d"] + 4, C["mini_h"] + 5, 2, 5).translate((mini_x, mini_y, bh + 8))
mini_bar = oval_solid(C["mini_w"], C["mini_d"], C["mini_h"], 2).translate((mini_x, mini_y, bh + 11))
press_yoke = box(7, 12, 33, 3).translate((base_x - 48, 0, bh + 38)).union(box(7, 12, 33, 3).translate((base_x + 48, 0, bh + 38))).union(box(104, 14, 8, 4).translate((base_x, 0, bh + 68)))
press_cap = box(C["bar_w"] + 5, C["bar_d"] + 5, 6, 6).translate((base_x, 0, bh + 58))
press_stem = cyl_z(7, 17).translate((base_x, 0, bh + 64))
thermal_lid = box(C["bar_w"] + 22, C["bar_d"] + 22, 5, 8).translate((base_x, 0, bh + 83))
cooling_slots = rounded_plate_with_holes(52, 3, 18, 3, 3, 2, 3, 6, 1).translate((base_x, bd / 2 - 1, 20))

compact_assy = cq.Assembly(name="AquaForm_Compact_Premium")
def compact_add(shape, name, color):
    compact_assy.add(shape, name=name, color=cq.Color(*color))

TI = (0.78, 0.77, 0.73, 1)
G = (0.12, 0.14, 0.14, 1)
SAND = (0.66, 0.48, 0.30, 1)
SAGE = (0.36, 0.52, 0.46, 1)
SOAP = (0.89, 0.66, 0.42, 1)
CLAY = (0.72, 0.35, 0.22, 1)
for shape, name, color in [
    (compact_collector, "shower_collector_titanium_shell", TI), (compact_cover, "hinged_vented_cover", G), (compact_window, "smoke_window", (0.56, 0.68, 0.67, .45)),
    (compact_handle, "cover_pull", G), (compact_hinge, "cover_hinge", G), (compact_gasket, "wet_zone_gasket", G), (compact_status_ring, "status_ring", SAND), (compact_status_light, "status_light", SAGE),
    (compact_basket, "removable_mesh_basket", TI), (compact_mesh, "basket_mesh", SAGE), (compact_basket_lip, "basket_grip", G), (compact_scraps, "soap_scraps", SOAP),
    (compact_gutter, "isolated_drain_gutter", G), (compact_grille, "drain_grille", TI), (compact_water, "water_path_visual", (0.18, 0.58, 0.76, .45)), (compact_nozzle, "tub_drain_nozzle", G), (compact_hooks, "tub_shower_hooks", TI), (compact_tub, "tub_rim_context", (.78, .82, .80, .25)),
    (compact_base, "dry_reform_base", TI), (compact_base_inset, "base_pod_inset", G), (compact_feet, "non_slip_feet", G), (compact_usb, "usb_c_port", G), (compact_usb_ring, "usb_c_port_ring", SAND), (compact_heater, "sealed_low_voltage_heater", CLAY), (compact_trace, "heater_trace", (1, .26, .08, 1)),
    (regular_outer, "regular_moldpod", TI), (regular_liner, "regular_silicone_liner", SAGE), (regular_lip, "regular_moldpod_lip", G), (regular_bar, "regular_reformed_bar", SOAP), (mini_outer, "mini_moldpod", TI), (mini_liner, "mini_silicone_liner", SAGE), (mini_bar, "mini_reformed_bar", SOAP),
    (press_yoke, "press_yoke", TI), (press_cap, "press_cap", SAND), (press_stem, "press_stem", G), (thermal_lid, "thermal_lid", G), (cooling_slots, "cooling_slots", G),
]:
    compact_add(shape, name, color)

assy = compact_assy
DEMO_PARTS = [
    {"id":"collector","group":"collector","shape":compact_collector,"color":[.78,.77,.73],"alpha":1}, {"id":"cover","group":"cover","shape":compact_cover,"color":[.12,.14,.14],"alpha":1}, {"id":"window","group":"cover","shape":compact_window,"color":[.56,.68,.67],"alpha":.42}, {"id":"handle","group":"cover","shape":compact_handle.union(compact_hinge).union(compact_gasket),"color":[.1,.12,.12],"alpha":1}, {"id":"status","group":"status","shape":compact_status_ring.union(compact_status_light),"color":[.72,.47,.25],"alpha":1},
    {"id":"basket","group":"basket","shape":compact_basket.union(compact_basket_lip),"color":[.76,.75,.70],"alpha":1}, {"id":"mesh","group":"basket","shape":compact_mesh,"color":[.36,.52,.46],"alpha":1}, {"id":"scraps","group":"scraps","shape":compact_scraps,"color":[.89,.56,.28],"alpha":1}, {"id":"gutter","group":"drain","shape":compact_gutter.union(compact_grille).union(compact_nozzle),"color":[.14,.17,.16],"alpha":1}, {"id":"water","group":"water","shape":compact_water,"color":[.18,.58,.76],"alpha":.12}, {"id":"hooks","group":"hooks","shape":compact_hooks,"color":[.70,.70,.67],"alpha":1}, {"id":"tub","group":"context","shape":compact_tub,"color":[.76,.81,.79],"alpha":.16},
    {"id":"base","group":"base","shape":compact_base.union(compact_base_inset).union(compact_feet).union(compact_usb).union(compact_usb_ring).union(cooling_slots),"color":[.78,.77,.73],"alpha":1}, {"id":"heater","group":"heater","shape":compact_heater.union(compact_trace),"color":[.78,.24,.11],"alpha":1}, {"id":"regular_pod","group":"pod","shape":regular_outer.union(regular_liner).union(regular_lip),"color":[.70,.72,.68],"alpha":1}, {"id":"regular_bar","group":"bar","shape":regular_bar,"color":[.92,.67,.38],"alpha":1}, {"id":"mini_pod","group":"mini","shape":mini_outer.union(mini_liner),"color":[.70,.72,.68],"alpha":1}, {"id":"mini_bar","group":"mini","shape":mini_bar,"color":[.91,.64,.37],"alpha":1}, {"id":"press","group":"press","shape":press_yoke.union(press_cap).union(press_stem).union(thermal_lid),"color":[.55,.47,.36],"alpha":1},
]
PROCESS_STEPS = [
    {"id":"collect","number":"01","label":"Collect","title":"Save every small soap piece","body":"Place unusable fragments in the removable mesh basket instead of throwing them away.","detail":"The basket keeps everyday scraps visible and ready for the next batch.","next":"Use the collector normally; water drains away after each wash.","sound":"collect"},
    {"id":"drain","number":"02","label":"Drain","title":"Send excess water back to the tub","body":"Water passes through the mesh and isolated gutter, then leaves through the bottom nozzle.","detail":"Wet drainage never enters the dry reforming base.","next":"Leave the basket in place after bathing.","sound":"drain"},
    {"id":"dry","number":"03","label":"Air dry","title":"Let the soap pieces firm up","body":"The vented cover and mesh improve air exposure while the collector remains hooked on the tub or shower.","detail":"A drier batch produces a cleaner, more consistent re-formed bar.","next":"When the basket is full, open the cover.","sound":"dry"},
    {"id":"remove","number":"04","label":"Remove","title":"Lift out the collection basket","body":"Open the hinged cover and lift the basket by its wide grip lip.","detail":"Manual removal is simple to wash and avoids an unreliable wet-soap chute.","next":"Carry the basket to the dry ReForm Base.","sound":"remove"},
    {"id":"load","number":"05","label":"Load","title":"Fill the selected MoldPod","body":"Pour the dry pieces into the regular or kids/travel silicone-lined MoldPod.","detail":"Interchangeable pod sizes make the kit useful for households and small bars.","next":"Seat the MoldPod on the dry base.","sound":"load"},
    {"id":"dock","number":"06","label":"Dock","title":"Use the dry low-voltage base","body":"Dock the filled MoldPod on the USB-C ReForm Base, away from the wet bath area.","detail":"Separating wet collection from heat keeps the hanging collector compact.","next":"Close the thermal lid to begin a controlled softening cycle.","sound":"dock"},
    {"id":"form","number":"07","label":"Form","title":"Soften, press, and cool","body":"The illustrated thermal plate softens the batch; the press cap consolidates it while the base cools.","detail":"A consistent press reduces voids and gives the soap a usable bar shape.","next":"After cooling, lift the MoldPod from the base.","sound":"form"},
    {"id":"release","number":"08","label":"Release","title":"Release a new soap bar","body":"Flex the silicone liner and remove the finished recycled bar. Start the collection cycle again.","detail":"Discarded scraps return as a usable household soap bar.","next":"Rinse the basket and reuse both parts.","sound":"release"},
]
CALLOUTS = [
    {"part":"basket","steps":["collect","drain","dry","remove"],"title":"Mesh collection basket","body":"Holds small soap pieces while water drains through.","offset":[28,14,-6]}, {"part":"water","steps":["drain"],"title":"Isolated drain path","body":"Water returns to the tub and never enters the dry base.","offset":[28,8,4]}, {"part":"regular_pod","steps":["load","dock","form","release"],"title":"Regular MoldPod","body":"Removable silicone-lined cartridge for a standard bar.","offset":[28,12,8]}, {"part":"mini_pod","steps":["load"],"title":"Mini MoldPod","body":"Kids or travel-size recycled bar option.","offset":[24,12,8]}, {"part":"heater","steps":["dock","form"],"title":"Dry ReForm Base","body":"USB-C low-voltage heat concept, kept away from the wet collector.","offset":[28,10,8]}, {"part":"hooks","steps":["mount"],"title":"Tub / shower hooks","body":"Tool-free wet-zone mounting with soft protective pads.","offset":[25,12,-8]},
]


# ---------------------------------------------------------------------------
# Final single-machine AquaForm assembly
# ---------------------------------------------------------------------------
S = {
    "w": 154.0, "d": 90.0, "h": 216.0, "wall": 3.2,
    "basket_w": 126.0, "basket_d": 56.0, "basket_h": 38.0,
    "bar_w": 78.0, "bar_d": 48.0, "bar_h": 22.0,
    "mini_w": 58.0, "mini_d": 36.0, "mini_h": 18.0,
}
sx, sd, sh, sw = 0.0, S["d"], S["h"], S["wall"]

# One integrated rounded housing.
single_back = box(S["w"], sw, sh, 11).translate((0, sd / 2 - sw / 2, 0))
single_left = box(sw, sd, sh, 2).translate((-S["w"] / 2 + sw / 2, 0, 0))
single_right = box(sw, sd, sh, 2).translate((S["w"] / 2 - sw / 2, 0, 0))
single_top = box(S["w"], sd, sw, 11).translate((0, 0, sh - sw))
single_bottom = box(S["w"], sd, sw, 11)
single_shelf = rounded_plate_with_holes(S["w"] - 2 * sw, sd - 2 * sw, sw, 3.6, 9, 4, 5).translate((0, 0, 122))
single_shell = single_back.union(single_left).union(single_right).union(single_top).union(single_bottom).union(single_shelf)

# Upper input cover, basket, grip, and drain.
single_cover = box(S["w"] - 26, 4, 72, 8).translate((0, -sd / 2 - 5, 112))
for slot_x in [-42, -14, 14, 42]:
    for slot_z in [126, 146, 166]:
        single_cover = single_cover.cut(box(18, 6, 4.5, 2).translate((slot_x, -sd / 2 - 5, slot_z)))
single_cover_window = box(S["w"] - 58, 2, 30, 5).translate((0, -sd / 2 - 7, 135))
single_cover_handle = box(58, 10, 8, 4).translate((0, -sd / 2 - 12, 118))
single_hinge = cyl_x(3, S["w"] - 26).translate((0, -sd / 2 - 6, 110))
single_gasket = box(S["w"] - 36, 2, 64, 9).cut(box(S["w"] - 50, 3, 50, 7)).translate((0, -sd / 2 - 8, 115))
single_basket = open_box(S["basket_w"], S["basket_d"], S["basket_h"], 2.4, 7).translate((0, -2, 134))
single_mesh = mesh_insert(S["basket_w"] - 12, S["basket_d"] - 12).translate((0, -2, 136))
single_basket_lip = box(S["basket_w"] + 8, S["basket_d"] + 8, 4, 7).translate((0, -2, 172))
single_scraps = soap_scraps().translate((0, -2, 140))
single_gutter = open_box(24, 52, 12, 2.2, 4).translate((-55, 13, 124))
single_grille = rounded_plate_with_holes(17, 39, 1.4, 3, 2, 4, 3, 5, 5).translate((-55, 13, 135))
single_nozzle = cyl_z(4.5, 12).translate((-55, 13, -10))
single_water = None
for drop_z, drop_h in [(155, 12), (128, 14), (100, 13), (72, 11), (44, 10)]:
    drop = oval_solid(5, 3, drop_h, 1).translate((-55, 13, drop_z))
    single_water = drop if single_water is None else single_water.union(drop)

# Demo-only airflow guides use CadQuery geometry too, so the browser animation
# stays tied to the same source model rather than drawing a separate CSS scene.
single_airflow = None
for flow_x in [-34, 0, 34]:
    flow = cyl_z(1.2, 28).translate((flow_x, -8, 143)).union(cyl_z(3.4, 2.5).translate((flow_x, -8, 170)))
    single_airflow = flow if single_airflow is None else single_airflow.union(flow)

# Internal transfer chute, lower forming chamber, heater, and output drawer.
single_transfer_gate = box(30, 18, 8, 4).translate((0, -14, 115))
single_transfer_chute = box(22, 20, 47, 5).translate((0, 8, 91))
single_transfer_stream = soap_scraps().translate((0, 0, 101))
single_firewall = box(136, 3, 84, 1).translate((0, 36, 43))
single_heater = box(94, 58, 3, 5).translate((0, 0, 38))
single_trace = None
for trace_y in [-19, -7, 7, 19]:
    trace = box(74, 1.8, 1, .2).translate((0, trace_y, 41.2))
    single_trace = trace if single_trace is None else single_trace.union(trace)
single_mold_outer = open_box(S["bar_w"] + 10, S["bar_d"] + 10, S["bar_h"] + 10, 3, 7).translate((0, -2, 46))
single_mold_liner = open_box(S["bar_w"] + 4, S["bar_d"] + 4, S["bar_h"] + 5, 2, 6).translate((0, -2, 49))
single_mold_lip = box(S["bar_w"] + 18, S["bar_d"] + 18, 4, 7).translate((0, -2, 72))
single_soft_mass = oval_solid(S["bar_w"] - 8, S["bar_d"] - 8, 10, 2).translate((0, -2, 53))
single_bar = oval_solid(S["bar_w"], S["bar_d"], S["bar_h"], 2).translate((0, -2, 52))
single_mini_pod = open_box(S["mini_w"] + 10, S["mini_d"] + 10, S["mini_h"] + 9, 3, 6).translate((48, 21, 48))
single_mini_liner = open_box(S["mini_w"] + 4, S["mini_d"] + 4, S["mini_h"] + 5, 2, 5).translate((48, 21, 51))
single_mini_bar = oval_solid(S["mini_w"], S["mini_d"], S["mini_h"], 2).translate((48, 21, 54))
single_press_yoke = box(7, 12, 42, 3).translate((-48, 0, 70)).union(box(7, 12, 42, 3).translate((48, 0, 70))).union(box(104, 14, 8, 4).translate((0, 0, 108)))
single_press_cap = box(S["bar_w"] + 5, S["bar_d"] + 5, 6, 6).translate((0, -2, 93))
single_press_stem = cyl_z(7, 20).translate((0, -2, 98))
single_thermal_lid = box(S["bar_w"] + 22, S["bar_d"] + 22, 5, 8).translate((0, -2, 119))
single_output_drawer = box(112, 7, 39, 5).translate((0, -sd / 2 - 4, 22))
single_output_handle = box(58, 10, 7, 4).translate((0, -sd / 2 - 12, 37))
single_output_bar = oval_solid(S["bar_w"], S["bar_d"], S["bar_h"], 2).translate((0, -sd / 2 - 28, 28))
single_cooling_slots = rounded_plate_with_holes(56, 3, 20, 3, 3, 2, 3, 6, 1).translate((0, sd / 2 - 1, 25))

# Integrated battery bay: four cells sit behind the firewall, not beside the machine.
single_battery_cells = []
for cell_x, cell_z in [(-42, 16), (42, 16), (-42, 55), (42, 55)]:
    single_battery_cells.append(cyl_y(16.75, 61.5).translate((cell_x, 30, cell_z)))
single_battery_contacts = []
for cell_x, cell_z in [(-42, 16), (42, 16), (-42, 55), (42, 55)]:
    single_battery_contacts.append(cyl_y(4.5, 3).translate((cell_x, 61, cell_z)).union(cyl_y(4.5, 3).translate((cell_x, -1, cell_z))))
single_battery_cover = box(112, 4, 78, 5).translate((0, sd / 2 + 1, 43))
single_usb_port = box(14, 4, 7, 1.5).translate((56, -sd / 2 - 1, 75))
single_status_ring = cyl_y(8, 3).cut(cyl_y(5.3, 4)).translate((51, -sd / 2 - 10, 180))
single_status_light = cyl_y(4, 3.3).translate((51, -sd / 2 - 10.5, 180))
single_hooks = make_hook().translate((-46, sd / 2 + 9, sh - 53)).union(make_hook().translate((46, sd / 2 + 9, sh - 53)))
single_tub = box(S["w"] + 42, 30, 11, 5).translate((0, sd / 2 + 22, sh - 15))

single_assy = cq.Assembly(name="AquaForm_Single_Integrated_Machine")
def single_add(shape, name, color):
    single_assy.add(shape, name=name, color=cq.Color(*color))

TI = (.78, .77, .73, 1)
GRAPHITE = (.12, .14, .14, 1)
SANDSTONE = (.66, .48, .30, 1)
SAGE = (.36, .52, .46, 1)
SOAP_COLOR = (.89, .66, .42, 1)
HEAT = (.78, .24, .11, 1)
COPPER = (.84, .56, .28, 1)
for shape, name, color in [
    (single_shell, "integrated_rounded_housing", TI), (single_cover, "hinged_vented_cover", GRAPHITE), (single_cover_window, "cover_window", (.56, .68, .67, .45)), (single_cover_handle, "cover_handle", GRAPHITE), (single_hinge, "cover_hinge", GRAPHITE), (single_gasket, "wet_zone_gasket", GRAPHITE), (single_status_ring, "status_ring", SANDSTONE), (single_status_light, "status_light", SAGE),
    (single_basket, "removable_mesh_basket", TI), (single_mesh, "basket_mesh", SAGE), (single_basket_lip, "basket_grip_lip", GRAPHITE), (single_scraps, "soap_scraps", SOAP_COLOR), (single_gutter, "isolated_water_gutter", GRAPHITE), (single_grille, "drain_perforations", TI), (single_water, "water_droplets_visual", (.18, .58, .76, .45)), (single_nozzle, "bottom_drain_nozzle", GRAPHITE), (single_hooks, "bathtub_shower_hooks", TI),
    (single_transfer_gate, "transfer_gate", SANDSTONE), (single_transfer_chute, "internal_transfer_chute", GRAPHITE), (single_firewall, "dry_battery_firewall", GRAPHITE), (single_heater, "sealed_low_voltage_heater", HEAT), (single_trace, "heater_trace", (1, .26, .08, 1)), (single_mold_outer, "regular_moldpod", TI), (single_mold_liner, "regular_silicone_liner", SAGE), (single_mold_lip, "moldpod_lip", GRAPHITE), (single_soft_mass, "softened_soap_mass_visual", (.80, .45, .20, .78)), (single_bar, "reformed_soap_bar", SOAP_COLOR), (single_mini_pod, "mini_moldpod_cartridge", TI), (single_mini_liner, "mini_silicone_liner", SAGE), (single_mini_bar, "mini_reformed_bar", SOAP_COLOR),
    (single_press_yoke, "press_yoke", TI), (single_press_cap, "press_plate", SANDSTONE), (single_press_stem, "press_stem", GRAPHITE), (single_thermal_lid, "thermal_lid", GRAPHITE), (single_output_drawer, "bottom_output_drawer", TI), (single_output_handle, "output_drawer_handle", GRAPHITE), (single_output_bar, "output_soap_bar", SOAP_COLOR), (single_cooling_slots, "cooling_vents", GRAPHITE), (single_battery_cover, "battery_service_cover", GRAPHITE), (single_usb_port, "usb_c_low_voltage_port", GRAPHITE), (single_tub, "bathtub_context_only", (.78, .82, .80, .25)),
]:
    single_add(shape, name, color)
for index, cell in enumerate(single_battery_cells, 1):
    single_add(cell, f"d_cell_{index}_control_placeholder", GRAPHITE)
for index, contact in enumerate(single_battery_contacts, 1):
    single_add(contact, f"d_cell_{index}_copper_contacts", COPPER)

assy = single_assy
DEMO_PARTS = [
    {"id":"housing","group":"housing","shape":single_shell,"color":[.78,.77,.73],"alpha":1}, {"id":"cover","group":"cover","shape":single_cover,"color":[.12,.14,.14],"alpha":1}, {"id":"window","group":"cover","shape":single_cover_window,"color":[.56,.68,.67],"alpha":.42}, {"id":"cover_mechanics","group":"cover","shape":single_cover_handle.union(single_hinge).union(single_gasket),"color":[.1,.12,.12],"alpha":1}, {"id":"status","group":"status","shape":single_status_ring.union(single_status_light),"color":[.72,.47,.25],"alpha":1},
    {"id":"basket","group":"basket","shape":single_basket.union(single_basket_lip),"color":[.76,.75,.70],"alpha":1}, {"id":"mesh","group":"basket","shape":single_mesh,"color":[.36,.52,.46],"alpha":1}, {"id":"scraps","group":"scraps","shape":single_scraps,"color":[.89,.56,.28],"alpha":1}, {"id":"drain","group":"drain","shape":single_gutter.union(single_grille).union(single_nozzle),"color":[.14,.17,.16],"alpha":1}, {"id":"water","group":"water","shape":single_water,"color":[.18,.58,.76],"alpha":.12}, {"id":"airflow","group":"airflow","shape":single_airflow,"color":[.46,.72,.68],"alpha":.08}, {"id":"transfer","group":"transfer","shape":single_transfer_gate.union(single_transfer_chute).union(single_transfer_stream),"color":[.60,.43,.27],"alpha":1}, {"id":"heater","group":"heater","shape":single_heater.union(single_trace),"color":[.78,.24,.11],"alpha":1}, {"id":"firewall","group":"battery","shape":single_firewall,"color":[.08,.10,.10],"alpha":1},
    {"id":"mold","group":"mold","shape":single_mold_outer.union(single_mold_liner).union(single_mold_lip),"color":[.48,.61,.52],"alpha":1}, {"id":"soft_mass","group":"soft_mass","shape":single_soft_mass,"color":[.80,.45,.20],"alpha":.12}, {"id":"bar","group":"bar","shape":single_bar,"color":[.92,.67,.38],"alpha":1}, {"id":"mini_mold","group":"mold","shape":single_mini_pod.union(single_mini_liner).union(single_mini_bar),"color":[.46,.59,.50],"alpha":.72}, {"id":"press","group":"press","shape":single_press_yoke.union(single_press_cap).union(single_press_stem).union(single_thermal_lid),"color":[.55,.47,.36],"alpha":1}, {"id":"output","group":"output","shape":single_output_drawer.union(single_output_handle).union(single_output_bar),"color":[.72,.69,.62],"alpha":1}, {"id":"battery","group":"battery","shape":single_battery_cover,"color":[.10,.12,.12],"alpha":1},
]
for index, cell in enumerate(single_battery_cells, 1):
    DEMO_PARTS.append({"id":f"battery_cell_{index}","group":"battery","shape":cell,"color":[.12,.14,.14],"alpha":1})
for index, contact in enumerate(single_battery_contacts, 1):
    DEMO_PARTS.append({"id":f"battery_contact_{index}","group":"battery","shape":contact,"color":[.84,.56,.28],"alpha":1})
DEMO_PARTS.append({"id":"hooks","group":"hooks","shape":single_hooks,"color":[.70,.70,.67],"alpha":1})
DEMO_PARTS.append({"id":"tub","group":"context","shape":single_tub,"color":[.76,.81,.79],"alpha":.16})

PROCESS_STEPS = [
    {"id":"collect","number":"01","label":"Collect","title":"Add unused soap pieces","body":"Small leftover pieces visibly drop through the top opening and settle in the mesh basket.","why":"The basket stores the batch above the dry forming chamber.","detail":"The basket stores the batch above the dry forming chamber.","next":"Let excess water leave the wet zone.","sound":"collect","duration_ms":4000,"camera":[-.53,.20,620],"visible_groups":["housing","cover","basket","scraps","drain"],"focus_groups":["basket","scraps"]},
    {"id":"drain","number":"02","label":"Drain","title":"Drain the wet zone","body":"Water drops pass through the basket, follow the isolated side gutter, and exit at the bottom nozzle.","why":"The gutter keeps water completely away from the heater, battery, and mold.","detail":"The gutter keeps water completely away from the heater, battery, and mold.","next":"Allow air to circulate around the scraps.","sound":"drain","duration_ms":4500,"camera":[-.78,.12,540],"visible_groups":["housing","cover","basket","scraps","drain","water"],"focus_groups":["water","drain"]},
    {"id":"dry","number":"03","label":"Air dry","title":"Airflow firms the scraps","body":"Air moves through the vented cover and around the basket while the scraps stay safely in the upper chamber.","why":"Dry, firm soap reforms more predictably than wet soap.","detail":"Dry, firm soap reforms more predictably than wet soap.","next":"Check that the batch is ready to transfer.","sound":"dry","duration_ms":4500,"camera":[-.42,.30,610],"visible_groups":["housing","cover","basket","scraps","airflow","drain"],"focus_groups":["airflow","basket","scraps"]},
    {"id":"ready","number":"04","label":"Ready check","title":"Confirm a dry batch","body":"The status ring confirms the basket remains in the dry zone before the internal transfer gate is opened.","why":"This pause separates drainage and reforming for hygiene and safer operation.","detail":"This pause separates drainage and reforming for hygiene and safer operation.","next":"Open the transfer gate.","sound":"dry","duration_ms":3000,"camera":[-.36,.20,550],"visible_groups":["housing","cover","basket","scraps","airflow","status","transfer"],"focus_groups":["status","transfer"]},
    {"id":"transfer","number":"05","label":"Transfer","title":"Guide the dry batch inward","body":"The cover opens, the basket slides toward the gate, and the scraps travel down the short controlled chute.","why":"The transfer is deliberately visible and contained, not an unrealistic instant teleport.","detail":"The transfer is deliberately visible and contained, not an unrealistic instant teleport.","next":"Seat the internal silicone MoldPod.","sound":"transfer","duration_ms":5500,"camera":[-.35,.05,500],"visible_groups":["housing","cover","basket","scraps","transfer","mold"],"focus_groups":["transfer","scraps"]},
    {"id":"load","number":"06","label":"Load mold","title":"Fill the internal MoldPod","body":"The dry batch enters the silicone-lined regular or mini cartridge inside the same machine.","why":"The two mold sizes are interchangeable components, not a second appliance.","detail":"The two mold sizes are interchangeable components, not a second appliance.","next":"Close the insulated thermal chamber.","sound":"load","duration_ms":4500,"camera":[-.18,.04,490],"visible_groups":["housing","transfer","scraps","mold","press"],"focus_groups":["mold","scraps"]},
    {"id":"soften","number":"07","label":"Soften","title":"Warm the sealed MoldPod","body":"A low-temperature heater concept glows below the MoldPod as the individual scraps become one softened soap mass.","why":"The thermal firewall keeps this conceptually separate from the wet and battery zones.","detail":"The thermal firewall keeps this conceptually separate from the wet and battery zones.","next":"Press the softened mass to the bar shape.","sound":"dock","duration_ms":5500,"camera":[.08,.08,500],"visible_groups":["housing","heater","firewall","battery","mold","scraps","soft_mass","press"],"focus_groups":["heater","soft_mass","mold"]},
    {"id":"press","number":"08","label":"Press","title":"Consolidate the soap","body":"The press plate descends to consolidate the softened soap against the MoldPod walls.","why":"The controlled stroke creates a consistent bar shape before cooling.","detail":"The controlled stroke creates a consistent bar shape before cooling.","next":"Cool the formed bar before release.","sound":"form","duration_ms":4500,"camera":[-.10,.02,465],"visible_groups":["housing","heater","mold","soft_mass","press","bar"],"focus_groups":["press","soft_mass","mold"]},
    {"id":"cool","number":"09","label":"Cool / set","title":"Cool the finished form","body":"The heater glow eases away while airflow through the lower vents helps the pressed bar set safely in the MoldPod.","why":"Cooling protects the bar shape before the drawer is opened.","detail":"Cooling protects the bar shape before the drawer is opened.","next":"Pull the bottom output drawer.","sound":"dry","duration_ms":5000,"camera":[-.16,-.02,485],"visible_groups":["housing","mold","bar","press","airflow","output"],"focus_groups":["bar","airflow","output"]},
    {"id":"release","number":"10","label":"Release","title":"Release a new soap bar","body":"The lower drawer slides forward and the silicone liner presents one complete recycled soap bar from the same machine.","why":"The cycle is complete and the upper collector can begin gathering the next batch.","detail":"The cycle is complete and the upper collector can begin gathering the next batch.","next":"Rinse the basket and repeat.","sound":"release","duration_ms":5500,"camera":[-.36,-.04,500],"visible_groups":["housing","mold","output","bar","hooks"],"focus_groups":["output","bar"]},
]
CALLOUTS = [
    {"part":"basket","steps":["collect","drain","dry","ready","transfer"],"title":"Mesh input basket","body":"Small soap scraps enter here while water leaves below.","offset":[27,12,-5]}, {"part":"water","steps":["drain"],"title":"Water-only path","body":"The isolated gutter sends water out of the bottom nozzle.","offset":[28,8,5]}, {"part":"airflow","steps":["dry","ready","cool"],"title":"Vented airflow","body":"Air helps scraps firm up and assists the final cooling phase.","offset":[28,10,5]}, {"part":"transfer","steps":["ready","transfer","load"],"title":"Internal transfer gate","body":"A short controlled guide moves dry scraps toward the MoldPod.","offset":[28,8,4]}, {"part":"heater","steps":["soften","press"],"title":"Sealed heater plate","body":"Low-voltage heater concept under the internal MoldPod.","offset":[29,9,8]}, {"part":"battery","steps":["soften"],"title":"Integrated dry battery bay","body":"Four D-cell placeholders sit behind a dry firewall.","offset":[29,12,5]}, {"part":"press","steps":["press","cool"],"title":"Press and thermal lid","body":"Press plate descends, then cooling completes the bar.","offset":[27,13,7]}, {"part":"output","steps":["cool","release"],"title":"Bottom output drawer","body":"The finished recycled soap bar exits from the same machine.","offset":[29,6,5]}, {"part":"hooks","steps":["mount"],"title":"Tub / shower hooks","body":"The single machine hangs beside the bath or shower.","offset":[25,10,-8]},
]


def _shape_from(obj):
    return obj.val() if hasattr(obj, "val") else obj


def _display_point(v):
    return [float(v.x), float(v.z), float(-v.y)]


def _part_meshes(tolerance=2.0):
    raw_parts = []
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]

    for spec in DEMO_PARTS:
        verts, faces = _shape_from(spec["shape"]).tessellate(tolerance)
        points = [_display_point(v) for v in verts]
        for p in points:
            for axis in range(3):
                mins[axis] = min(mins[axis], p[axis])
                maxs[axis] = max(maxs[axis], p[axis])
        raw_parts.append({**spec, "points": points, "faces": faces})

    center = [(mins[i] + maxs[i]) / 2 for i in range(3)]
    parts = []
    bboxes = {}
    total_triangles = 0

    for raw in raw_parts:
        local_mins = [float("inf"), float("inf"), float("inf")]
        local_maxs = [float("-inf"), float("-inf"), float("-inf")]
        qverts = []
        for p in raw["points"]:
            shifted = [p[i] - center[i] for i in range(3)]
            for axis in range(3):
                local_mins[axis] = min(local_mins[axis], shifted[axis])
                local_maxs[axis] = max(local_maxs[axis], shifted[axis])
            qverts.extend([int(round(value * 10)) for value in shifted])
        flat_faces = [idx for face in raw["faces"] for idx in face]
        total_triangles += len(raw["faces"])
        bboxes[raw["id"]] = {"min": local_mins, "max": local_maxs}
        parts.append(
            {
                "id": raw["id"],
                "group": raw["group"],
                "color": raw["color"],
                "alpha": raw["alpha"],
                "v": qverts,
                "f": flat_faces,
            }
        )

    callouts = []
    for item in CALLOUTS:
        bbox = bboxes[item["part"]]
        anchor = [(bbox["min"][i] + bbox["max"][i]) / 2 + item["offset"][i] for i in range(3)]
        callouts.append({**item, "anchor": anchor})
        del callouts[-1]["offset"]

    return {
        "version": "AquaForm Compact Premium",
        "units": "mm",
        "source": "soap_recycler_cadquery_2A.py",
        "triangleCount": total_triangles,
        "bounds": {"min": mins, "max": maxs, "center": center},
        "parts": parts,
        "callouts": callouts,
        "process": PROCESS_STEPS,
        "dimensions": {"single_machine_mm": [154, 90, 216]},
    }


def write_demo_html_legacy(path="soap_recycler_demo_2A.html"):
    data = json.dumps(_part_meshes(), separators=(",", ":"))
    template = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Soap Recycler Prototype 2A - CAD Matched Demo</title>
  <style>
    :root {
      --bg: #ece9df;
      --ink: #17201f;
      --muted: #66716d;
      --panel: rgba(250, 249, 244, .78);
      --line: rgba(23, 32, 31, .14);
      --teal: #1f686c;
      --copper: #c96d3e;
      --cream: #f8f6ef;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 14%, rgba(31,104,108,.18), transparent 32%),
        radial-gradient(circle at 86% 20%, rgba(201,109,62,.16), transparent 30%),
        linear-gradient(145deg, #f6f4ec, #deddd5 48%, #edf0eb);
      font-family: ui-sans-serif, "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      overflow: hidden;
    }
    .app { display: grid; grid-template-columns: 330px 1fr; height: 100%; }
    .panel {
      display: flex;
      flex-direction: column;
      gap: 18px;
      padding: 22px;
      border-right: 1px solid var(--line);
      background: var(--panel);
      backdrop-filter: blur(18px);
      box-shadow: 18px 0 45px rgba(23,32,31,.08);
      z-index: 5;
    }
    .brand { display: grid; gap: 7px; }
    .eyebrow {
      color: var(--teal);
      font-size: 12px;
      font-weight: 850;
      letter-spacing: .12em;
      text-transform: uppercase;
    }
    h1 { margin: 0; font-size: 28px; line-height: 1.05; letter-spacing: 0; }
    .body-copy { margin: 0; color: var(--muted); font-size: 14px; line-height: 1.45; }
    .stat-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .stat {
      padding: 11px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.52);
    }
    .stat b { display: block; font-size: 18px; }
    .stat span { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
    .section-title {
      color: var(--muted);
      font-size: 12px;
      font-weight: 850;
      letter-spacing: .10em;
      text-transform: uppercase;
    }
    .modes { display: grid; gap: 8px; }
    button {
      width: 100%;
      min-height: 42px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      background: rgba(255,255,255,.64);
      font: inherit;
      font-weight: 780;
      text-align: left;
      cursor: pointer;
      transition: transform .16s ease, background .16s ease, border-color .16s ease;
    }
    button:hover { transform: translateY(-1px); border-color: rgba(31,104,108,.46); }
    button.active { color: #fbfdf9; background: #163c3f; border-color: #163c3f; }
    .tools { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .toggle {
      display: flex;
      align-items: center;
      gap: 9px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255,255,255,.50);
      color: var(--muted);
      font-size: 13px;
      font-weight: 720;
    }
    input[type="checkbox"] { accent-color: var(--teal); }
    .hint { margin-top: auto; color: var(--muted); font-size: 12px; line-height: 1.5; }
    .stage {
      position: relative;
      min-width: 0;
      overflow: hidden;
    }
    canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
    .watermark {
      position: absolute;
      right: 20px;
      bottom: 18px;
      padding: 9px 11px;
      border: 1px solid rgba(255,255,255,.45);
      border-radius: 8px;
      color: rgba(23,32,31,.62);
      background: rgba(255,255,255,.42);
      backdrop-filter: blur(14px);
      font-size: 12px;
      font-weight: 820;
      letter-spacing: .08em;
      text-transform: uppercase;
    }
    .callout {
      position: absolute;
      width: min(250px, 28vw);
      padding: 11px 12px;
      border: 1px solid rgba(23,32,31,.15);
      border-radius: 8px;
      background: rgba(255,255,255,.82);
      box-shadow: 0 18px 42px rgba(23,32,31,.14);
      backdrop-filter: blur(14px);
      pointer-events: none;
      opacity: 0;
      transform: translate(12px, -50%) scale(.98);
      transition: opacity .2s ease, transform .2s ease;
    }
    .callout.visible { opacity: 1; transform: translate(12px, -50%) scale(1); }
    .callout::before {
      content: "";
      position: absolute;
      left: -30px;
      top: 50%;
      width: 30px;
      height: 1px;
      background: rgba(23,32,31,.35);
    }
    .callout b { display: block; margin-bottom: 5px; font-size: 13px; }
    .callout span { display: block; color: var(--muted); font-size: 12px; line-height: 1.35; }
    .toast {
      position: absolute;
      left: 22px;
      bottom: 18px;
      max-width: 430px;
      padding: 12px 14px;
      border: 1px solid rgba(23,32,31,.13);
      border-radius: 8px;
      color: var(--muted);
      background: rgba(255,255,255,.62);
      backdrop-filter: blur(14px);
      font-size: 13px;
      line-height: 1.45;
    }
    @media (max-width: 860px) {
      body { overflow: auto; }
      .app { grid-template-columns: 1fr; grid-template-rows: auto 680px; min-height: 100%; }
      .panel { border-right: 0; border-bottom: 1px solid var(--line); }
      .modes { grid-template-columns: 1fr 1fr; }
      .callout { width: 220px; }
    }
    @media (max-width: 540px) {
      .modes, .tools, .stat-row { grid-template-columns: 1fr; }
      .app { grid-template-rows: auto 570px; }
      .callout { display: none; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="panel">
      <div class="brand">
        <div class="eyebrow">CAD-Matched Viewer</div>
        <h1>Soap Recycler Prototype 2A</h1>
        <p class="body-copy" id="modeText">Actual mesh generated from the same CadQuery source as the STEP file.</p>
      </div>
      <div class="stat-row">
        <div class="stat"><b id="partCount">0</b><span>CAD parts</span></div>
        <div class="stat"><b id="triCount">0</b><span>triangles</span></div>
      </div>
      <div>
        <div class="section-title">Presentation mode</div>
        <div class="modes" id="modes"></div>
      </div>
      <div>
        <div class="section-title">Controls</div>
        <div class="tools">
          <button type="button" id="reset">Reset View</button>
          <button type="button" id="autoplay">Autoplay</button>
        </div>
      </div>
      <label class="toggle"><input type="checkbox" id="labels" checked> Floating labels</label>
      <p class="hint">Drag the model to orbit. Scroll or pinch to zoom. STEP Match mode shows the actual CAD layout without exploded offsets.</p>
    </aside>
    <main class="stage" id="stage">
      <canvas id="canvas"></canvas>
      <div id="callouts"></div>
      <div class="toast">This browser demo renders real triangle meshes tessellated from <b>soap_recycler_cadquery_2A.py</b>, the same source used to export the Shapr3D STEP file.</div>
      <div class="watermark">Real CAD Mesh</div>
    </main>
  </div>
  <script id="model-data" type="application/json">__MODEL_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById("model-data").textContent);
    const canvas = document.getElementById("canvas");
    const stage = document.getElementById("stage");
    const modeText = document.getElementById("modeText");
    const modesEl = document.getElementById("modes");
    const calloutsEl = document.getElementById("callouts");
    const labelToggle = document.getElementById("labels");
    const gl = canvas.getContext("webgl", { antialias: true, alpha: true });

    document.getElementById("partCount").textContent = data.parts.length;
    document.getElementById("triCount").textContent = Math.round(data.triangleCount / 1000) + "k";

    const MODES = {
      step: "STEP Match: exact CAD layout used for the exported STEP/STL files.",
      exploded: "Exploded view: the same CAD components move apart for client explanation.",
      flow: "Drain path: highlights basket, drain chute, and soap/water movement placeholders.",
      heating: "Heat and mold: highlights the lower mold tray, heater plate, and recycled soap bar.",
      battery: "Battery drawer: pulls out the actual drawer and battery placeholder geometry.",
      hook: "Tub hook view: focuses on rear hooks and bathtub/shower mounting context.",
      xray: "X-Ray: fades the outer shell so the internal feature layout is easier to explain."
    };

    for (const [id, text] of Object.entries(MODES)) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.mode = id;
      button.textContent = id === "step" ? "STEP Match" : id[0].toUpperCase() + id.slice(1);
      button.addEventListener("click", () => setMode(id));
      modesEl.appendChild(button);
    }

    if (!gl) {
      stage.innerHTML = "<div class='toast'>WebGL is not available in this browser.</div>";
      throw new Error("WebGL unavailable");
    }

    const vertexShader = `
      attribute vec3 aPosition;
      attribute vec3 aNormal;
      uniform mat4 uMvp;
      uniform mat4 uModel;
      varying vec3 vNormal;
      varying vec3 vWorld;
      void main() {
        vec4 world = uModel * vec4(aPosition, 1.0);
        vWorld = world.xyz;
        vNormal = mat3(uModel) * aNormal;
        gl_Position = uMvp * vec4(aPosition, 1.0);
      }
    `;
    const fragmentShader = `
      precision mediump float;
      varying vec3 vNormal;
      varying vec3 vWorld;
      uniform vec3 uColor;
      uniform float uAlpha;
      uniform float uGlow;
      void main() {
        vec3 n = normalize(vNormal);
        vec3 key = normalize(vec3(-0.42, 0.72, 0.52));
        vec3 fill = normalize(vec3(0.55, 0.35, -0.65));
        float diffuse = max(dot(n, key), 0.0);
        float bounce = max(dot(n, fill), 0.0) * 0.22;
        float rim = pow(1.0 - max(dot(n, normalize(vec3(0.0, 0.2, 1.0))), 0.0), 2.2) * 0.20;
        vec3 color = uColor * (0.34 + diffuse * 0.68 + bounce) + vec3(1.0, 0.92, 0.78) * rim;
        color += vec3(1.0, 0.44, 0.18) * uGlow * 0.22;
        gl_FragColor = vec4(color, uAlpha);
      }
    `;

    function shader(type, source) {
      const s = gl.createShader(type);
      gl.shaderSource(s, source);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    }

    const program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, vertexShader));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, fragmentShader));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
    gl.useProgram(program);

    const loc = {
      position: gl.getAttribLocation(program, "aPosition"),
      normal: gl.getAttribLocation(program, "aNormal"),
      mvp: gl.getUniformLocation(program, "uMvp"),
      model: gl.getUniformLocation(program, "uModel"),
      color: gl.getUniformLocation(program, "uColor"),
      alpha: gl.getUniformLocation(program, "uAlpha"),
      glow: gl.getUniformLocation(program, "uGlow")
    };

    function decodeMesh(part) {
      const positions = [];
      const normals = [];
      const verts = part.v;
      const faces = part.f;
      const point = (idx) => {
        const o = idx * 3;
        return [verts[o] / 10, verts[o + 1] / 10, verts[o + 2] / 10];
      };
      const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
      const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
      const norm = (v) => {
        const d = Math.hypot(v[0], v[1], v[2]) || 1;
        return [v[0]/d, v[1]/d, v[2]/d];
      };
      for (let i = 0; i < faces.length; i += 3) {
        const p0 = point(faces[i]);
        const p1 = point(faces[i + 1]);
        const p2 = point(faces[i + 2]);
        const n = norm(cross(sub(p1, p0), sub(p2, p0)));
        positions.push(...p0, ...p1, ...p2);
        normals.push(...n, ...n, ...n);
      }
      return { positions: new Float32Array(positions), normals: new Float32Array(normals), count: positions.length / 3 };
    }

    const parts = data.parts.map((part) => {
      const mesh = decodeMesh(part);
      const positionBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, mesh.positions, gl.STATIC_DRAW);
      const normalBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, normalBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, mesh.normals, gl.STATIC_DRAW);
      return {
        ...part,
        mesh,
        positionBuffer,
        normalBuffer,
        state: { offset: [0, 0, 0], alpha: part.alpha, glow: 0 },
        target: { offset: [0, 0, 0], alpha: part.alpha, glow: 0 }
      };
    });

    const labels = data.callouts.map((callout) => {
      const el = document.createElement("div");
      el.className = "callout";
      el.innerHTML = `<b>${callout.title}</b><span>${callout.body}</span>`;
      calloutsEl.appendChild(el);
      return { ...callout, el };
    });

    let mode = "step";
    let yaw = -0.58;
    let pitch = 0.25;
    let distance = 480;
    let autoplay = false;
    let autoplayAt = 0;
    const modeKeys = Object.keys(MODES);

    function groupOffset(group, activeMode) {
      if (activeMode === "exploded") {
        if (group === "cover") return [130, 32, 20];
        if (group === "basket" || group === "soap") return [-132, 54, 16];
        if (group === "mold") return [-120, -18, 24];
        if (group === "heater") return [-72, -42, -6];
        if (group === "battery") return [132, -36, 34];
        if (group === "hooks" || group === "context") return [0, 72, -82];
      }
      if (activeMode === "battery" && group === "battery") return [138, -12, 36];
      if (activeMode === "hook" && (group === "hooks" || group === "context")) return [0, 18, -18];
      return [0, 0, 0];
    }

    function groupAlpha(part, activeMode) {
      if (activeMode === "xray") {
        if (part.group === "housing" || part.group === "cover") return Math.min(part.alpha, 0.22);
        return part.alpha;
      }
      if (activeMode === "flow") {
        return ["flow", "basket", "soap", "mold", "housing"].includes(part.group) ? part.alpha : Math.min(part.alpha, 0.18);
      }
      if (activeMode === "heating") {
        return ["heater", "mold", "soap", "housing"].includes(part.group) ? part.alpha : Math.min(part.alpha, 0.20);
      }
      if (activeMode === "battery") {
        return ["battery", "housing"].includes(part.group) ? part.alpha : Math.min(part.alpha, 0.24);
      }
      if (activeMode === "hook") {
        return ["hooks", "context", "housing", "cover"].includes(part.group) ? part.alpha : Math.min(part.alpha, 0.22);
      }
      return part.alpha;
    }

    function groupGlow(group, activeMode) {
      if (activeMode === "flow" && group === "flow") return 1;
      if (activeMode === "heating" && group === "heater") return 1;
      if (activeMode === "battery" && group === "battery") return .5;
      return 0;
    }

    function setMode(nextMode) {
      mode = nextMode;
      modeText.textContent = MODES[mode];
      document.querySelectorAll("[data-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === mode);
      });
      for (const part of parts) {
        part.target.offset = groupOffset(part.group, mode);
        part.target.alpha = groupAlpha(part, mode);
        part.target.glow = groupGlow(part.group, mode);
      }
    }

    document.getElementById("reset").addEventListener("click", () => {
      yaw = -0.58;
      pitch = 0.25;
      distance = 480;
    });
    document.getElementById("autoplay").addEventListener("click", (event) => {
      autoplay = !autoplay;
      event.currentTarget.classList.toggle("active", autoplay);
      autoplayAt = 0;
    });

    function m4Identity() {
      return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
    }
    function m4Translate(x, y, z) {
      return [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1];
    }
    function m4Multiply(a, b) {
      const out = new Array(16);
      for (let c = 0; c < 4; c++) {
        for (let r = 0; r < 4; r++) {
          out[c * 4 + r] = a[0 * 4 + r] * b[c * 4 + 0] + a[1 * 4 + r] * b[c * 4 + 1] + a[2 * 4 + r] * b[c * 4 + 2] + a[3 * 4 + r] * b[c * 4 + 3];
        }
      }
      return out;
    }
    function m4Perspective(fovy, aspect, near, far) {
      const f = 1 / Math.tan(fovy / 2);
      return [f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)/(near-far),-1, 0,0,(2*far*near)/(near-far),0];
    }
    function normalize(v) {
      const d = Math.hypot(v[0], v[1], v[2]) || 1;
      return [v[0]/d, v[1]/d, v[2]/d];
    }
    function cross(a, b) {
      return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
    }
    function dot(a, b) {
      return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
    }
    function m4LookAt(eye, target, up) {
      const z = normalize([eye[0]-target[0], eye[1]-target[1], eye[2]-target[2]]);
      const x = normalize(cross(up, z));
      const y = cross(z, x);
      return [x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0, -dot(x,eye),-dot(y,eye),-dot(z,eye),1];
    }
    function transformPoint(m, p) {
      const x = p[0], y = p[1], z = p[2], w = 1;
      return [
        m[0]*x + m[4]*y + m[8]*z + m[12]*w,
        m[1]*x + m[5]*y + m[9]*z + m[13]*w,
        m[2]*x + m[6]*y + m[10]*z + m[14]*w,
        m[3]*x + m[7]*y + m[11]*z + m[15]*w
      ];
    }

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.floor(canvas.clientWidth * dpr);
      const h = Math.floor(canvas.clientHeight * dpr);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
    window.addEventListener("resize", resize);

    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    canvas.addEventListener("pointerdown", (event) => {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      const dx = event.clientX - lastX;
      const dy = event.clientY - lastY;
      lastX = event.clientX;
      lastY = event.clientY;
      yaw += dx * 0.007;
      pitch = Math.max(-1.05, Math.min(1.05, pitch + dy * 0.006));
    });
    canvas.addEventListener("pointerup", (event) => {
      dragging = false;
      canvas.releasePointerCapture(event.pointerId);
    });
    canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      distance = Math.max(250, Math.min(850, distance + event.deltaY * 0.45));
    }, { passive: false });

    function draw(now) {
      resize();
      if (autoplay && (!autoplayAt || now - autoplayAt > 3600)) {
        const next = modeKeys[(modeKeys.indexOf(mode) + 1) % modeKeys.length];
        setMode(next);
        autoplayAt = now;
      }

      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.enable(gl.DEPTH_TEST);
      gl.enable(gl.CULL_FACE);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      const aspect = canvas.width / Math.max(canvas.height, 1);
      const projection = m4Perspective(Math.PI / 4.3, aspect, 1, 2200);
      const eye = [
        Math.sin(yaw) * Math.cos(pitch) * distance,
        Math.sin(pitch) * distance + 30,
        Math.cos(yaw) * Math.cos(pitch) * distance
      ];
      const view = m4LookAt(eye, [0, 14, 0], [0, 1, 0]);
      const viewProjection = m4Multiply(projection, view);

      for (const part of parts) {
        for (let i = 0; i < 3; i++) part.state.offset[i] += (part.target.offset[i] - part.state.offset[i]) * 0.12;
        part.state.alpha += (part.target.alpha - part.state.alpha) * 0.12;
        part.state.glow += (part.target.glow - part.state.glow) * 0.12;
      }

      const drawList = [...parts].sort((a, b) => (b.state.alpha >= .98) - (a.state.alpha >= .98));
      for (const part of drawList) {
        const model = m4Translate(part.state.offset[0], part.state.offset[1], part.state.offset[2]);
        const mvp = m4Multiply(viewProjection, model);
        gl.uniformMatrix4fv(loc.model, false, new Float32Array(model));
        gl.uniformMatrix4fv(loc.mvp, false, new Float32Array(mvp));
        gl.uniform3fv(loc.color, new Float32Array(part.color));
        gl.uniform1f(loc.alpha, part.state.alpha);
        gl.uniform1f(loc.glow, part.state.glow);
        gl.depthMask(part.state.alpha > .94);

        gl.bindBuffer(gl.ARRAY_BUFFER, part.positionBuffer);
        gl.enableVertexAttribArray(loc.position);
        gl.vertexAttribPointer(loc.position, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, part.normalBuffer);
        gl.enableVertexAttribArray(loc.normal);
        gl.vertexAttribPointer(loc.normal, 3, gl.FLOAT, false, 0, 0);
        gl.drawArrays(gl.TRIANGLES, 0, part.mesh.count);
      }
      gl.depthMask(true);

      updateLabels(viewProjection, canvas.clientWidth, canvas.clientHeight);
      requestAnimationFrame(draw);
    }

    function updateLabels(viewProjection, width, height) {
      const showLabels = labelToggle.checked;
      for (const label of labels) {
        const active = showLabels && label.modes.includes(mode);
        if (!active) {
          label.el.classList.remove("visible");
          continue;
        }
        const part = parts.find((p) => p.id === label.id || p.group === label.id || label.id === "flow" && p.group === "flow");
        const offset = part ? part.state.offset : [0, 0, 0];
        const point = [label.anchor[0] + offset[0], label.anchor[1] + offset[1], label.anchor[2] + offset[2]];
        const clip = transformPoint(viewProjection, point);
        if (clip[3] <= 0.1) {
          label.el.classList.remove("visible");
          continue;
        }
        const ndcX = clip[0] / clip[3];
        const ndcY = clip[1] / clip[3];
        const x = (ndcX * .5 + .5) * width;
        const y = (-ndcY * .5 + .5) * height;
        if (x < -80 || x > width + 80 || y < -80 || y > height + 80) {
          label.el.classList.remove("visible");
          continue;
        }
        label.el.style.left = `${x}px`;
        label.el.style.top = `${y}px`;
        label.el.classList.add("visible");
      }
    }

    setMode("step");
    requestAnimationFrame(draw);
  </script>
</body>
</html>'''
    Path(path).write_text(template.replace("__MODEL_DATA__", data), encoding="ascii")


def write_demo_html_process_legacy(path="soap_recycler_demo_2A.html"):
    """Write the premium process-film viewer from the same part meshes as STEP."""
    data = json.dumps(_part_meshes(), separators=(",", ":"))
    template = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AquaForm Soap Recycler - CAD Process Film</title>
  <style>
    :root {
      --ink: #e9f0e9;
      --muted: #aab9ae;
      --line: rgba(222, 239, 225, .16);
      --panel: rgba(12, 31, 28, .82);
      --panel-solid: #102923;
      --teal: #75d8bd;
      --copper: #e6a262;
      --coral: #ff825a;
      --canvas: #071512;
    }
    * { box-sizing: border-box; }
    html, body { min-height: 100%; }
    body {
      min-width: 320px;
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(900px 680px at 12% 4%, rgba(42, 116, 97, .34), transparent 62%),
        radial-gradient(780px 550px at 97% 82%, rgba(211, 115, 66, .22), transparent 60%),
        linear-gradient(140deg, #06130f, #102b25 55%, #071a17);
      font-family: "Avenir Next", "Futura", "Trebuchet MS", sans-serif;
      overflow: hidden;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: .28;
      background-image: radial-gradient(rgba(238,245,235,.23) .55px, transparent .6px);
      background-size: 5px 5px;
      mix-blend-mode: soft-light;
    }
    .app { display: grid; grid-template-columns: 348px minmax(0, 1fr); min-height: 100vh; }
    .sidebar {
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding: 26px 22px 20px;
      background: linear-gradient(180deg, rgba(17,43,37,.95), rgba(7,23,20,.95));
      border-right: 1px solid var(--line);
      box-shadow: 22px 0 70px rgba(0,0,0,.22);
      z-index: 4;
    }
    .brand { display: grid; gap: 9px; }
    .eyebrow, .section-kicker {
      color: var(--teal);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: .18em;
      text-transform: uppercase;
    }
    h1 {
      max-width: 260px;
      margin: 0;
      color: #f4f6ee;
      font-family: "Iowan Old Style", "Baskerville", Georgia, serif;
      font-size: 38px;
      font-weight: 500;
      line-height: .94;
      letter-spacing: -.055em;
    }
    .subhead { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.55; }
    .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .metric { padding: 11px 12px; border: 1px solid var(--line); border-radius: 13px; background: rgba(255,255,255,.045); }
    .metric b { display: block; font-size: 17px; letter-spacing: -.03em; }
    .metric span { color: var(--muted); font-size: 9px; font-weight: 800; letter-spacing: .11em; text-transform: uppercase; }
    .sidebar-section { display: grid; gap: 9px; }
    .view-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
    button {
      min-height: 39px;
      border: 1px solid var(--line);
      border-radius: 11px;
      color: #dce8dd;
      background: rgba(255,255,255,.045);
      font: inherit;
      font-size: 12px;
      font-weight: 750;
      cursor: pointer;
      transition: color .2s ease, background .2s ease, border-color .2s ease, transform .2s ease;
    }
    button:hover { transform: translateY(-1px); border-color: rgba(117,216,189,.55); }
    button.active { color: #09221c; border-color: var(--teal); background: var(--teal); }
    .play-button { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 48px; color: #10251f; border-color: var(--copper); background: linear-gradient(135deg, #f5bf7d, #dd9360); }
    .play-button.active { color: #fbf4e7; border-color: #ffb07b; background: #9f4d39; }
    .play-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; box-shadow: 0 0 16px currentColor; }
    .sidebar-note { margin-top: auto; color: #91a69b; font-size: 11px; line-height: 1.55; }
    .stage { position: relative; min-width: 0; min-height: 100vh; overflow: hidden; }
    .stage::before, .stage::after { content: ""; position: absolute; pointer-events: none; z-index: 1; }
    .stage::before { inset: 0; background: radial-gradient(ellipse at 48% 46%, rgba(91,184,150,.12), transparent 41%); }
    .stage::after { inset: 20px; border: 1px solid rgba(218,244,224,.12); border-radius: 22px; }
    canvas { position: absolute; inset: 0; display: block; width: 100%; height: 100%; }
    .topbar { position: absolute; top: 28px; left: 36px; right: 36px; display: flex; align-items: center; justify-content: space-between; z-index: 2; pointer-events: none; }
    .topbar .brand-mark { display: flex; gap: 9px; align-items: center; color: #dbe8dd; font-size: 10px; font-weight: 850; letter-spacing: .15em; text-transform: uppercase; }
    .brand-mark i { width: 9px; height: 9px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 18px rgba(117,216,189,.8); }
    .cad-badge { padding: 8px 10px; border: 1px solid rgba(117,216,189,.34); border-radius: 99px; color: var(--teal); background: rgba(7,21,18,.46); font-size: 10px; font-weight: 800; letter-spacing: .11em; text-transform: uppercase; backdrop-filter: blur(10px); }
    .story-card {
      position: absolute;
      left: 36px;
      bottom: 128px;
      width: min(408px, calc(100% - 72px));
      padding: 18px 19px 17px;
      border: 1px solid rgba(222,239,225,.18);
      border-radius: 17px;
      background: linear-gradient(135deg, rgba(16,43,36,.88), rgba(8,25,22,.68));
      box-shadow: 0 22px 55px rgba(0,0,0,.20);
      backdrop-filter: blur(16px);
      z-index: 3;
    }
    .story-card .step-number { color: var(--copper); font-size: 10px; font-weight: 850; letter-spacing: .16em; }
    .story-card h2 { margin: 7px 0 8px; color: #f5f7ef; font-family: "Iowan Old Style", Georgia, serif; font-size: 24px; font-weight: 500; line-height: 1; letter-spacing: -.035em; }
    .story-card p { margin: 0; color: #c0cfc3; font-size: 12px; line-height: 1.5; }
    .story-card .detail { margin-top: 10px; color: var(--teal); font-size: 10px; font-weight: 700; line-height: 1.45; }
    .story-card.product-card h2 { font-size: 22px; }
    .tip { position: absolute; right: 35px; bottom: 130px; max-width: 225px; color: rgba(218,235,221,.72); font-size: 11px; line-height: 1.5; text-align: right; z-index: 2; pointer-events: none; }
    .timeline-wrap { position: absolute; right: 30px; bottom: 26px; left: 30px; z-index: 4; }
    .timeline { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 7px; padding: 9px; border: 1px solid rgba(222,239,225,.17); border-radius: 17px; background: rgba(9,29,25,.73); box-shadow: 0 18px 48px rgba(0,0,0,.25); backdrop-filter: blur(18px); }
    .step-button { position: relative; min-height: 62px; padding: 9px 10px 8px; overflow: hidden; text-align: left; }
    .step-button::after { content: ""; position: absolute; right: 10px; bottom: 9px; left: 10px; height: 2px; border-radius: 2px; background: rgba(117,216,189,.22); transform: scaleX(0); transform-origin: left; transition: transform .35s ease; }
    .step-button.active { color: #f3fbf2; border-color: rgba(117,216,189,.62); background: rgba(88,178,146,.18); }
    .step-button.active::after { background: var(--teal); transform: scaleX(1); }
    .step-button strong, .step-button span { display: block; pointer-events: none; }
    .step-button strong { color: var(--copper); font-size: 9px; letter-spacing: .1em; }
    .step-button span { margin-top: 4px; font-size: 11px; }
    .callout { position: absolute; width: min(230px, 25vw); padding: 11px 12px; border: 1px solid rgba(222,239,225,.22); border-radius: 12px; color: #edf5ec; background: rgba(10,35,30,.86); box-shadow: 0 16px 42px rgba(0,0,0,.22); backdrop-filter: blur(16px); opacity: 0; pointer-events: none; transform: translate(14px, -50%) scale(.96); transition: opacity .23s ease, transform .23s ease; z-index: 3; }
    .callout.visible { opacity: 1; transform: translate(14px, -50%) scale(1); }
    .callout::before { content: ""; position: absolute; top: 50%; left: -32px; width: 32px; height: 1px; background: rgba(117,216,189,.68); }
    .callout b { display: block; margin-bottom: 4px; color: var(--teal); font-size: 11px; }
    .callout span { display: block; color: #c7d5ca; font-size: 10px; line-height: 1.42; }
    @media (max-width: 930px) {
      body { overflow: auto; }
      .app { grid-template-columns: 1fr; }
      .sidebar { min-height: 0; padding: 20px; border-right: 0; border-bottom: 1px solid var(--line); }
      .brand { grid-template-columns: 1fr; }
      h1 { font-size: 32px; }
      .sidebar-note { margin-top: 0; }
      .stage { min-height: 760px; }
    }
    @media (max-width: 620px) {
      .view-buttons { grid-template-columns: 1fr 1fr; }
      .timeline-wrap { right: 12px; bottom: 12px; left: 12px; overflow-x: auto; }
      .timeline { min-width: 620px; }
      .topbar { top: 18px; right: 20px; left: 20px; }
      .story-card { bottom: 114px; left: 18px; width: calc(100% - 36px); }
      .tip, .callout { display: none; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="eyebrow">AquaForm / 2A premium concept</div>
        <h1>Soap, given a second life.</h1>
        <p class="subhead">A CAD-matched product story for a bath-side soap recycler. The process view explains the human handoff, isolated drain, MoldPod, thermal fuse, press, and release cycle.</p>
      </div>
      <div class="metrics">
        <div class="metric"><b id="partCount">0</b><span>CAD parts</span></div>
        <div class="metric"><b id="triCount">0</b><span>mesh triangles</span></div>
      </div>
      <div class="sidebar-section">
        <div class="section-kicker">CAD views</div>
        <div class="view-buttons" id="viewButtons"></div>
      </div>
      <button class="play-button" id="playCycle" type="button" title="Play the complete six-step recycling explanation"><i class="play-dot"></i><span>Play full recycle cycle</span></button>
      <div class="sidebar-section">
        <div class="section-kicker">Camera</div>
        <div class="view-buttons">
          <button id="resetView" type="button" title="Restore the premium product camera">Reset view</button>
          <button id="labelsToggle" type="button" class="active" title="Show or hide feature labels">Labels on</button>
        </div>
      </div>
      <p class="sidebar-note">Drag to orbit. Scroll or pinch to zoom. <b>STEP Match</b> is zero-offset geometry: it renders the exact triangle meshes tessellated from the same CadQuery source that exports the STEP and STL files.</p>
    </aside>
    <main class="stage" id="stage">
      <canvas id="canvas"></canvas>
      <div class="topbar"><div class="brand-mark"><i></i> Purpose-built circular care</div><div class="cad-badge" id="cadBadge">STEP match active</div></div>
      <section class="story-card product-card" id="storyCard"><div class="step-number">CAD PRODUCT VIEW</div><h2 id="storyTitle">The complete premium concept</h2><p id="storyBody">The static view matches the exported CAD layout: basket and scraps above, completed bar in MoldPod below, an isolated drain, a sealed thermal zone, dry side service pod, and tub hooks.</p><div class="detail" id="storyDetail">Select a process card below, or play the full cycle.</div></section>
      <div class="tip" id="tip">This is a concept animation. The heating and electrical systems require engineering, waterproofing, thermal-safety, and certification work before manufacture.</div>
      <div id="callouts"></div>
      <div class="timeline-wrap"><nav class="timeline" id="timeline" aria-label="Soap recycling process"></nav></div>
    </main>
  </div>
  <script id="model-data" type="application/json">__MODEL_DATA__</script>
  <script>
    const data = JSON.parse(document.getElementById("model-data").textContent);
    const canvas = document.getElementById("canvas");
    const stage = document.getElementById("stage");
    const gl = canvas.getContext("webgl", { antialias: true, alpha: true });
    const storyCard = document.getElementById("storyCard");
    const storyTitle = document.getElementById("storyTitle");
    const storyBody = document.getElementById("storyBody");
    const storyDetail = document.getElementById("storyDetail");
    const cadBadge = document.getElementById("cadBadge");
    const calloutsEl = document.getElementById("callouts");
    document.getElementById("partCount").textContent = data.parts.length;
    document.getElementById("triCount").textContent = Math.round(data.triangleCount / 1000) + "k";

    if (!gl) {
      stage.innerHTML = "<div class='story-card'><div class='step-number'>Browser support</div><h2>WebGL is unavailable</h2><p>Open this file in a modern desktop browser to see the CAD process animation.</p></div>";
      throw new Error("WebGL unavailable");
    }

    const VIEWS = {
      product: { label: "STEP Match", summary: "Zero-offset CAD geometry, matching the exported STEP/STL layout.", camera: [-.58, .24, 470] },
      exploded: { label: "Exploded", summary: "The exact CAD parts separate for a clean client explanation.", camera: [-.62, .24, 555] },
      power: { label: "Service power", summary: "Dry side service pod. D-cell bodies and copper contacts remain visible, never washed out by the housing.", camera: [-.82, -.08, 435] },
      mount: { label: "Tub mount", summary: "Rear hooks and the tub rim context show the hanging concept.", camera: [.56, .26, 465] }
    };
    const stepById = Object.fromEntries(data.process.map((step) => [step.id, step]));
    const viewButtons = document.getElementById("viewButtons");
    const timeline = document.getElementById("timeline");
    let activeView = "product";
    let activeStep = null;
    let labelsEnabled = true;
    let playing = false;
    let nextStepAt = 0;
    let yaw = -.58, pitch = .24, distance = 470;
    let yawTarget = yaw, pitchTarget = pitch, distanceTarget = distance;

    for (const [id, view] of Object.entries(VIEWS)) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.view = id;
      button.textContent = view.label;
      button.title = view.summary;
      button.addEventListener("click", () => setView(id));
      viewButtons.appendChild(button);
    }
    for (const step of data.process) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "step-button";
      button.dataset.step = step.id;
      button.title = step.title + ": " + step.body;
      button.innerHTML = `<strong>${step.number}</strong><span>${step.label}</span>`;
      button.addEventListener("click", () => setStep(step.id));
      timeline.appendChild(button);
    }

    const vertexShader = `
      attribute vec3 aPosition; attribute vec3 aNormal;
      uniform mat4 uMvp; uniform mat4 uModel;
      varying vec3 vNormal; varying vec3 vWorld;
      void main() { vec4 world = uModel * vec4(aPosition, 1.0); vWorld = world.xyz; vNormal = mat3(uModel) * aNormal; gl_Position = uMvp * vec4(aPosition, 1.0); }
    `;
    const fragmentShader = `
      precision mediump float;
      varying vec3 vNormal; varying vec3 vWorld;
      uniform vec3 uColor; uniform float uAlpha; uniform float uGlow;
      void main() {
        vec3 n = normalize(vNormal);
        vec3 key = normalize(vec3(-.55, .72, .48));
        vec3 fill = normalize(vec3(.48, .16, -.78));
        float diffuse = max(dot(n, key), .0);
        float bounce = max(dot(n, fill), .0) * .25;
        float rim = pow(1.0 - max(dot(n, normalize(vec3(.0, .20, 1.0))), .0), 2.5) * .26;
        vec3 color = uColor * (.28 + diffuse * .78 + bounce) + vec3(.92, .99, .90) * rim;
        color += vec3(1.0, .25, .08) * uGlow * .38;
        gl_FragColor = vec4(color, uAlpha);
      }
    `;
    function compile(type, source) { const shader = gl.createShader(type); gl.shaderSource(shader, source); gl.compileShader(shader); if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader)); return shader; }
    const program = gl.createProgram();
    gl.attachShader(program, compile(gl.VERTEX_SHADER, vertexShader)); gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fragmentShader)); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
    gl.useProgram(program);
    const loc = { position: gl.getAttribLocation(program, "aPosition"), normal: gl.getAttribLocation(program, "aNormal"), mvp: gl.getUniformLocation(program, "uMvp"), model: gl.getUniformLocation(program, "uModel"), color: gl.getUniformLocation(program, "uColor"), alpha: gl.getUniformLocation(program, "uAlpha"), glow: gl.getUniformLocation(program, "uGlow") };

    function decodeMesh(part) {
      const positions = [], normals = [], verts = part.v, faces = part.f;
      const point = (index) => { const o = index * 3; return [verts[o] / 10, verts[o + 1] / 10, verts[o + 2] / 10]; };
      const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
      const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
      const norm = (v) => { const d = Math.hypot(...v) || 1; return [v[0]/d, v[1]/d, v[2]/d]; };
      for (let i = 0; i < faces.length; i += 3) { const p0 = point(faces[i]), p1 = point(faces[i+1]), p2 = point(faces[i+2]), n = norm(cross(sub(p1,p0),sub(p2,p0))); positions.push(...p0,...p1,...p2); normals.push(...n,...n,...n); }
      return { positions: new Float32Array(positions), normals: new Float32Array(normals), count: positions.length / 3 };
    }
    const parts = data.parts.map((part) => {
      const mesh = decodeMesh(part); const positionBuffer = gl.createBuffer(); const normalBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer); gl.bufferData(gl.ARRAY_BUFFER, mesh.positions, gl.STATIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, normalBuffer); gl.bufferData(gl.ARRAY_BUFFER, mesh.normals, gl.STATIC_DRAW);
      return { ...part, mesh, positionBuffer, normalBuffer, state: { offset:[0,0,0], alpha:part.alpha, glow:0, pulse:0 }, target: { offset:[0,0,0], alpha:part.alpha, glow:0, pulse:0 } };
    });
    const partById = Object.fromEntries(parts.map((part) => [part.id, part]));
    const labels = data.callouts.map((callout) => { const el = document.createElement("div"); el.className = "callout"; el.innerHTML = `<b>${callout.title}</b><span>${callout.body}</span>`; calloutsEl.appendChild(el); return { ...callout, el }; });

    function cameraFor(values) { [yawTarget, pitchTarget, distanceTarget] = values; }
    function setView(viewId) {
      activeView = viewId; activeStep = null; playing = false;
      const view = VIEWS[viewId]; cameraFor(view.camera);
      storyCard.classList.add("product-card"); storyTitle.textContent = view.label; storyBody.textContent = view.summary; storyDetail.textContent = viewId === "product" ? "Static mode is an exact CAD layout match. Select the six cards below for the animated explanation." : "The underlying triangle geometry is still the same CAD mesh; this view only changes presentation offsets and transparency.";
      cadBadge.textContent = viewId === "product" ? "STEP match active" : "CAD mesh presentation";
      refreshButtons();
    }
    function setStep(stepId) {
      activeView = "process"; activeStep = stepId; playing = false;
      const step = stepById[stepId]; cameraFor([-.56, .18, stepId === "release" ? 470 : 445]);
      storyCard.classList.remove("product-card"); storyTitle.textContent = step.title; storyBody.textContent = step.body; storyDetail.textContent = step.detail; cadBadge.textContent = "PROCESS " + step.number + " / CAD MESH";
      refreshButtons();
    }
    function refreshButtons() {
      document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === activeView));
      document.querySelectorAll("[data-step]").forEach((button) => button.classList.toggle("active", button.dataset.step === activeStep));
      const play = document.getElementById("playCycle"); play.classList.toggle("active", playing); play.querySelector("span").textContent = playing ? "Pause recycle cycle" : "Play full recycle cycle";
    }
    document.getElementById("playCycle").addEventListener("click", () => {
      playing = !playing;
      if (playing) { activeView = "process"; activeStep = activeStep || data.process[0].id; nextStepAt = 0; const step = stepById[activeStep]; storyCard.classList.remove("product-card"); storyTitle.textContent = step.title; storyBody.textContent = step.body; storyDetail.textContent = step.detail; cameraFor([-.56,.18,445]); }
      refreshButtons();
    });
    document.getElementById("resetView").addEventListener("click", () => { cameraFor(activeView === "mount" ? VIEWS.mount.camera : [-.58,.24,470]); });
    document.getElementById("labelsToggle").addEventListener("click", (event) => { labelsEnabled = !labelsEnabled; event.currentTarget.classList.toggle("active", labelsEnabled); event.currentTarget.textContent = labelsEnabled ? "Labels on" : "Labels off"; });

    function baseTarget(part) { return { offset:[0,0,0], alpha:part.alpha, glow:0, pulse:0 }; }
    function fadeOthers(part, keep, alpha=.08) { return keep.includes(part.group) ? part.alpha : Math.min(part.alpha, alpha); }
    function stateFor(part) {
      const t = baseTarget(part);
      if (activeView === "product") return t;
      if (activeView === "exploded") {
        const offsets = { cover:[0,28,82], basket:[-118,40,35], scraps:[-118,40,35], drain:[-86,-6,18], water:[-86,-6,18], mold:[-106,-18,54], bar:[-106,-18,54], heater:[-45,-54,22], press:[0,45,25], battery:[0,-20,118], hooks:[0,48,-70], context:[0,48,-70], status:[0,28,82] };
        t.offset = offsets[part.group] || [0,0,0]; return t;
      }
      if (activeView === "power") {
        if (part.group === "battery") { t.offset = [0,-6,110]; t.glow = .34; return t; }
        t.alpha = fadeOthers(part, ["battery"], .035); return t;
      }
      if (activeView === "mount") {
        if (part.group === "hooks" || part.group === "context") { t.offset = [0,12,-12]; t.glow = .18; return t; }
        t.alpha = fadeOthers(part, ["hooks","context","housing","cover"], .16); return t;
      }
      const step = activeStep || "collect";
      const inner = ["basket","scraps","drain","water","mold","bar","heater","press","status"];
      if (part.group === "housing" || part.group === "cover" || part.group === "hinge") t.alpha = Math.min(part.alpha, .16);
      if (!inner.includes(part.group) && part.group !== "housing" && part.group !== "cover" && part.group !== "hinge") t.alpha = Math.min(part.alpha, .05);
      if (step === "collect") {
        if (part.group === "basket" || part.group === "scraps") { t.glow = .16; t.pulse = .26; }
        if (part.group === "bar" || part.group === "heater" || part.group === "press") t.alpha = Math.min(part.alpha, .10);
        return t;
      }
      if (step === "drain") {
        if (part.group === "basket" || part.group === "drain") t.glow = .25;
        if (part.group === "water") { t.alpha = .92; t.glow = .52; t.pulse = .9; }
        if (part.group === "bar" || part.group === "heater" || part.group === "press") t.alpha = Math.min(part.alpha, .08);
        return t;
      }
      if (step === "load") {
        if (part.group === "basket") t.offset = [-102,34,58];
        if (part.group === "scraps") { t.offset = [0,-122,4]; t.glow = .34; t.pulse = .34; }
        if (part.group === "mold") t.glow = .28;
        if (part.group === "bar") t.alpha = Math.min(part.alpha, .10);
        if (part.group === "water") t.alpha = .04;
        return t;
      }
      if (step === "fuse") {
        if (part.group === "scraps") { t.offset = [0,-122,4]; t.alpha = .36; t.glow = .68; t.pulse = .5; }
        if (part.group === "heater") { t.glow = 1; t.pulse = .7; }
        if (part.group === "mold" || part.group === "bar") { t.glow = .34; }
        if (part.group === "water") t.alpha = .03;
        return t;
      }
      if (step === "press") {
        if (part.group === "scraps") { t.offset = [0,-122,4]; t.alpha = .04; }
        if (part.group === "press") { t.offset = [0,-28,0]; t.glow = .72; t.pulse = .34; }
        if (part.group === "heater") { t.glow = .72; t.pulse = .55; }
        if (part.group === "bar" || part.group === "mold") t.glow = .42;
        if (part.group === "water") t.alpha = .03;
        return t;
      }
      if (step === "release") {
        if (part.group === "mold" || part.group === "bar") { t.offset = [0,-8,108]; t.glow = part.group === "bar" ? .54 : .15; }
        if (part.group === "scraps" || part.group === "heater" || part.group === "press") t.alpha = Math.min(part.alpha, .08);
        if (part.group === "water") t.alpha = .03;
        return t;
      }
      return t;
    }

    function m4Multiply(a,b) { const o = new Array(16); for (let c=0;c<4;c++) for (let r=0;r<4;r++) o[c*4+r]=a[r]*b[c*4]+a[4+r]*b[c*4+1]+a[8+r]*b[c*4+2]+a[12+r]*b[c*4+3]; return o; }
    function m4Translate(x,y,z) { return [1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1]; }
    function m4Perspective(fovy,aspect,near,far) { const f=1/Math.tan(fovy/2); return [f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)/(near-far),-1, 0,0,(2*far*near)/(near-far),0]; }
    function norm(v) { const d=Math.hypot(...v)||1; return [v[0]/d,v[1]/d,v[2]/d]; }
    function cross(a,b) { return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]; }
    function dot(a,b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
    function m4LookAt(eye,target,up) { const z=norm([eye[0]-target[0],eye[1]-target[1],eye[2]-target[2]]), x=norm(cross(up,z)), y=cross(z,x); return [x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]; }
    function transformPoint(m,p) { const [x,y,z]=p; return [m[0]*x+m[4]*y+m[8]*z+m[12],m[1]*x+m[5]*y+m[9]*z+m[13],m[2]*x+m[6]*y+m[10]*z+m[14],m[3]*x+m[7]*y+m[11]*z+m[15]]; }
    function resize() { const dpr=Math.min(devicePixelRatio||1,2), w=Math.floor(canvas.clientWidth*dpr), h=Math.floor(canvas.clientHeight*dpr); if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;} gl.viewport(0,0,w,h); }
    addEventListener("resize", resize);
    let dragging=false,lastX=0,lastY=0;
    canvas.addEventListener("pointerdown",(event)=>{dragging=true;lastX=event.clientX;lastY=event.clientY;canvas.setPointerCapture(event.pointerId);});
    canvas.addEventListener("pointermove",(event)=>{if(!dragging)return;const dx=event.clientX-lastX,dy=event.clientY-lastY;lastX=event.clientX;lastY=event.clientY;yawTarget+=dx*.007;pitchTarget=Math.max(-1.05,Math.min(1.05,pitchTarget+dy*.006));});
    canvas.addEventListener("pointerup",(event)=>{dragging=false;canvas.releasePointerCapture(event.pointerId);});
    canvas.addEventListener("wheel",(event)=>{event.preventDefault();distanceTarget=Math.max(245,Math.min(860,distanceTarget+event.deltaY*.42));},{passive:false});

    function updateLabels(viewProjection,width,height) {
      for (const label of labels) {
        const visible = labelsEnabled && ((activeView === "process" && label.steps.includes(activeStep)) || (activeView === "power" && label.steps.includes("power")) || (activeView === "mount" && label.steps.includes("mount")));
        if (!visible) { label.el.classList.remove("visible"); continue; }
        const part=partById[label.part]; if(!part) { label.el.classList.remove("visible"); continue; }
        const clip=transformPoint(viewProjection,[label.anchor[0]+part.state.offset[0],label.anchor[1]+part.state.offset[1],label.anchor[2]+part.state.offset[2]]);
        if(clip[3] <= .1) { label.el.classList.remove("visible"); continue; }
        const x=(clip[0]/clip[3]*.5+.5)*width, y=(-clip[1]/clip[3]*.5+.5)*height;
        if(x < -80 || x > width+80 || y < -80 || y > height+80) { label.el.classList.remove("visible"); continue; }
        label.el.style.left=x+"px"; label.el.style.top=y+"px"; label.el.classList.add("visible");
      }
    }
    function draw(now) {
      resize();
      if (playing && (!nextStepAt || now >= nextStepAt)) {
        const current=data.process.findIndex((step)=>step.id===activeStep); activeStep=data.process[(current+1+data.process.length)%data.process.length].id; nextStepAt=now+4700;
        const step=stepById[activeStep]; storyTitle.textContent=step.title; storyBody.textContent=step.body; storyDetail.textContent=step.detail; cadBadge.textContent="PROCESS "+step.number+" / CAD MESH"; cameraFor([-.56,.18,activeStep==="release"?470:445]); refreshButtons();
      }
      yaw+=(yawTarget-yaw)*.1; pitch+=(pitchTarget-pitch)*.1; distance+=(distanceTarget-distance)*.1;
      for(const part of parts) { const target=stateFor(part); for(let i=0;i<3;i++)part.target.offset[i]=target.offset[i]; part.target.alpha=target.alpha;part.target.glow=target.glow;part.target.pulse=target.pulse; for(let i=0;i<3;i++)part.state.offset[i]+=(part.target.offset[i]-part.state.offset[i])*.095;part.state.alpha+=(part.target.alpha-part.state.alpha)*.095;part.state.glow+=(part.target.glow-part.state.glow)*.11;part.state.pulse+=(part.target.pulse-part.state.pulse)*.12; }
      gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
      const aspect=canvas.width/Math.max(canvas.height,1), projection=m4Perspective(Math.PI/4.25,aspect,1,2300), eye=[Math.sin(yaw)*Math.cos(pitch)*distance,Math.sin(pitch)*distance+27,Math.cos(yaw)*Math.cos(pitch)*distance], vp=m4Multiply(projection,m4LookAt(eye,[0,10,0],[0,1,0]));
      const drawList=[...parts].sort((a,b)=>b.state.alpha-a.state.alpha);
      for(const part of drawList) { if(part.state.alpha<.025) continue; const pulse=Math.sin(now*.008+part.mesh.count*.003)*part.state.pulse; const o=part.state.offset; const model=m4Translate(o[0],o[1]+pulse*1.6,o[2]+pulse*.8), mvp=m4Multiply(vp,model); gl.uniformMatrix4fv(loc.model,false,new Float32Array(model));gl.uniformMatrix4fv(loc.mvp,false,new Float32Array(mvp));gl.uniform3fv(loc.color,new Float32Array(part.color));gl.uniform1f(loc.alpha,part.state.alpha);gl.uniform1f(loc.glow,part.state.glow+Math.max(0,pulse)*.45);gl.depthMask(part.state.alpha>.94);gl.bindBuffer(gl.ARRAY_BUFFER,part.positionBuffer);gl.enableVertexAttribArray(loc.position);gl.vertexAttribPointer(loc.position,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,part.normalBuffer);gl.enableVertexAttribArray(loc.normal);gl.vertexAttribPointer(loc.normal,3,gl.FLOAT,false,0,0);gl.drawArrays(gl.TRIANGLES,0,part.mesh.count); }
      gl.depthMask(true); updateLabels(vp,canvas.clientWidth,canvas.clientHeight); requestAnimationFrame(draw);
    }
    window.__soapDemo = { setView, setStep, data };
    setView("product"); requestAnimationFrame(draw);
  </script>
</body>
</html>'''
    Path(path).write_text(template.replace("__MODEL_DATA__", data), encoding="ascii")


def write_demo_html(path="soap_recycler_demo_2A.html"):
    """Generate the compact white presentation from the same CAD mesh payload."""
    data = json.dumps(_part_meshes(), separators=(",", ":"))
    template = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AquaForm Compact - CAD Demo</title>
<style>
:root{--ink:#303331;--muted:#747873;--paper:#f7f3eb;--white:#fffdf9;--line:#dcd4c6;--sand:#c6aa82;--clay:#a95f40;--titanium:#737876}*{box-sizing:border-box}html,body{height:100%;margin:0}body{overflow:hidden;background:radial-gradient(circle at 15% 10%,#fff 0,transparent 32%),radial-gradient(circle at 87% 90%,#e9dac8 0,transparent 36%),var(--paper);color:var(--ink);font-family:"Avenir Next","Trebuchet MS",sans-serif}body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background-image:radial-gradient(#9e866955 .55px,transparent .7px);background-size:6px 6px}.stage{position:relative;height:100%;overflow:hidden}canvas{position:absolute;inset:0;width:100%;height:100%;display:block}.top{position:absolute;z-index:3;top:19px;left:25px;right:25px;display:flex;align-items:center;justify-content:space-between;pointer-events:none}.brand{font:500 25px/1 "Iowan Old Style",Georgia,serif;letter-spacing:-.045em}.brand small{margin-left:7px;color:var(--muted);font:800 9px/1 "Avenir Next",sans-serif;letter-spacing:.13em;text-transform:uppercase}.badge{padding:7px 10px;border:1px solid var(--line);border-radius:99px;background:#fffdf9cc;color:#655e55;font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;backdrop-filter:blur(9px)}.views{position:absolute;z-index:4;top:55px;right:24px;display:flex;gap:6px}.views button,.sound,.play,.step{border:1px solid var(--line);border-radius:9px;background:#fffdf9e8;color:var(--ink);font:750 11px/1 "Avenir Next",sans-serif;cursor:pointer;transition:transform .18s,background .18s,border-color .18s}.views button,.sound{padding:9px 10px}.views button:hover,.sound:hover,.play:hover,.step:hover{transform:translateY(-1px);border-color:var(--sand)}.views button.active,.sound.active{background:#505755;border-color:#505755;color:#fff}.card{position:absolute;z-index:3;left:24px;bottom:110px;width:min(290px,calc(100% - 48px));opacity:0;pointer-events:none;transform:translateY(6px);transition:opacity .22s,transform .22s}.card.show{opacity:1;transform:none}.card-inner{padding:13px 14px;border:1px solid var(--line);border-radius:13px;background:#fffdf9e9;box-shadow:0 14px 36px #5a4a351a;backdrop-filter:blur(10px)}.card b{display:block;color:var(--clay);font-size:10px;letter-spacing:.12em;text-transform:uppercase}.card h2{margin:6px 0;font:500 20px/1 "Iowan Old Style",Georgia,serif;letter-spacing:-.03em}.card p,.card em{display:block;margin:0;color:var(--muted);font-size:11px;line-height:1.45}.card em{margin-top:8px;color:#80664e;font-style:normal}.hint{position:absolute;z-index:2;right:24px;bottom:112px;width:210px;color:#77756f;font-size:10px;line-height:1.45;text-align:right}.callout{position:absolute;z-index:3;width:205px;padding:9px 10px;border:1px solid var(--line);border-radius:10px;background:#fffdf9e8;box-shadow:0 10px 26px #5a4a3518;opacity:0;pointer-events:none;transform:translate(11px,-50%) scale(.96);transition:.2s}.callout.show{opacity:1;transform:translate(11px,-50%) scale(1)}.callout:before{content:"";position:absolute;left:-27px;top:50%;width:27px;height:1px;background:var(--sand)}.callout b{display:block;color:var(--clay);font-size:10px}.callout span{display:block;margin-top:3px;color:var(--muted);font-size:10px;line-height:1.35}.bottom{position:absolute;z-index:4;right:18px;bottom:18px;left:18px;display:flex;gap:8px;align-items:center;padding:8px;border:1px solid var(--line);border-radius:14px;background:#fffdf9e5;box-shadow:0 16px 42px #5a4a351a;backdrop-filter:blur(12px)}.play{display:flex;align-items:center;gap:7px;min-width:126px;padding:11px 12px;background:#505755;border-color:#505755;color:#fff}.play i{width:7px;height:7px;border-radius:50%;background:#e5bd83;box-shadow:0 0 10px #e5bd83}.sound{padding:10px}.timeline{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:5px;flex:1}.step{min-height:39px;padding:6px;text-align:left}.step strong,.step span{display:block}.step strong{color:#a2714e;font-size:8px;letter-spacing:.08em}.step span{margin-top:3px;font-size:10px}.step.active{background:#dac19f;border-color:#c3a477}.step.active strong{color:#704b32}@media(max-width:800px){body{overflow:auto}.stage{min-height:680px}.bottom{overflow-x:auto}.timeline{min-width:640px}.hint{display:none}.top{left:15px;right:15px}.views{right:14px}.card{left:15px}}@media(max-width:520px){.brand small,.views button:nth-child(2){display:none}.bottom{left:8px;right:8px;bottom:8px}.play{min-width:104px;font-size:10px}.sound{font-size:0}.sound:after{content:"sound";font-size:10px}}
</style></head><body><main class="stage" id="stage"><canvas id="canvas"></canvas><header class="top"><div class="brand">AquaForm <small>compact circular care</small></div><div class="badge" id="badge">STEP Match</div></header><nav class="views" id="views"></nav><section class="card" id="card"><div class="card-inner"><b id="number">Process</b><h2 id="title"></h2><p id="description"></p><em id="next"></em></div></section><p class="hint" id="hint">Drag to orbit. Scroll to zoom. The initial view is deliberately zoomed out and uses zero-offset meshes from the same CadQuery source as the STEP and STL exports.</p><div id="callouts"></div><footer class="bottom"><button class="play" id="play"><i></i><span>Play cycle</span></button><button class="sound" id="sound">Sound off</button><div class="timeline" id="timeline"></div></footer></main><script id="model-data" type="application/json">__MODEL_DATA__</script><script>
const data=JSON.parse(document.getElementById('model-data').textContent),canvas=document.getElementById('canvas'),stage=document.getElementById('stage'),gl=canvas.getContext('webgl',{antialias:true,alpha:true});if(!gl){stage.innerHTML='<p style="padding:28px">WebGL is required for the AquaForm demo.</p>';throw Error('WebGL unavailable')}const $=id=>document.getElementById(id),badge=$('badge'),card=$('card'),title=$('title'),description=$('description'),next=$('next'),number=$('number'),views=$('views'),timeline=$('timeline'),calloutsEl=$('callouts'),soundButton=$('sound'),playButton=$('play');
const VIEWS={product:{label:'STEP Match',camera:[-.53,.20,650]},exploded:{label:'Exploded',camera:[-.58,.20,710]},section:{label:'Section View',camera:[-.42,.12,530]},battery:{label:'Battery',camera:[.12,.06,510]},heater:{label:'Heater',camera:[-.12,.10,500]},drain:{label:'Drain Path',camera:[-.72,.16,560]},mount:{label:'Tub mount',camera:[.62,.22,620]}};let view='product',step=null,playing=false,nextAt=0,audioOn=false,audio=null,yaw=-.53,pitch=.20,distance=650,yawT=yaw,pitchT=pitch,distanceT=distance;
for(const[id,item]of Object.entries(VIEWS)){const b=document.createElement('button');b.textContent=item.label;b.dataset.view=id;b.onclick=()=>setView(id);views.appendChild(b)}for(const item of data.process){const b=document.createElement('button');b.className='step';b.dataset.step=item.id;b.innerHTML=`<strong>${item.number}</strong><span>${item.label}</span>`;b.title=item.title;b.onclick=()=>setStep(item.id,true);timeline.appendChild(b)}
const vs='attribute vec3 p,n;uniform mat4 m,v;varying vec3 N;void main(){N=mat3(m)*n;gl_Position=v*m*vec4(p,1.);}';const fs='precision mediump float;varying vec3 N;uniform vec3 c;uniform float a,g;void main(){vec3 n=normalize(N),l=normalize(vec3(-.5,.75,.45));float d=max(dot(n,l),0.),r=pow(1.-max(dot(n,normalize(vec3(0.,.2,1.))),0.),2.);vec3 col=c*(.35+d*.72)+vec3(1.)*r*.16+vec3(1.,.25,.08)*g*.35;gl_FragColor=vec4(col,a);}';function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vs));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);gl.useProgram(program);const L={p:gl.getAttribLocation(program,'p'),n:gl.getAttribLocation(program,'n'),m:gl.getUniformLocation(program,'m'),v:gl.getUniformLocation(program,'v'),c:gl.getUniformLocation(program,'c'),a:gl.getUniformLocation(program,'a'),g:gl.getUniformLocation(program,'g')};
function decode(part){const pos=[],nor=[],pt=i=>[part.v[i*3]/10,part.v[i*3+1]/10,part.v[i*3+2]/10],sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]],cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm=x=>{const d=Math.hypot(...x)||1;return x.map(v=>v/d)};for(let i=0;i<part.f.length;i+=3){const a=pt(part.f[i]),b=pt(part.f[i+1]),c=pt(part.f[i+2]),n=norm(cross(sub(b,a),sub(c,a)));pos.push(...a,...b,...c);nor.push(...n,...n,...n)}return{p:new Float32Array(pos),n:new Float32Array(nor),count:pos.length/3}}const parts=data.parts.map(part=>{const mesh=decode(part),pb=gl.createBuffer(),nb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,pb);gl.bufferData(gl.ARRAY_BUFFER,mesh.p,gl.STATIC_DRAW);gl.bindBuffer(gl.ARRAY_BUFFER,nb);gl.bufferData(gl.ARRAY_BUFFER,mesh.n,gl.STATIC_DRAW);return{...part,mesh,pb,nb,s:{o:[0,0,0],a:part.alpha,g:0,p:0},t:{o:[0,0,0],a:part.alpha,g:0,p:0}}});const byId=Object.fromEntries(parts.map(p=>[p.id,p]));const labels=data.callouts.map(c=>{const el=document.createElement('div');el.className='callout';el.innerHTML=`<b>${c.title}</b><span>${c.body}</span>`;calloutsEl.appendChild(el);return{...c,el}});
function camera(x){[yawT,pitchT,distanceT]=x}function refresh(){document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));document.querySelectorAll('[data-step]').forEach(b=>b.classList.toggle('active',b.dataset.step===step));playButton.querySelector('span').textContent=playing?'Pause cycle':'Play cycle'}function showStep(id){const item=data.process.find(x=>x.id===id);number.textContent='Process '+item.number;title.textContent=item.title;description.textContent=item.body;next.textContent='Next: '+item.next;card.classList.add('show');badge.textContent='Process '+item.number}function setView(id){view=id;step=null;playing=false;camera(VIEWS[id].camera);card.classList.remove('show');badge.textContent=VIEWS[id].label;$('hint').textContent=id==='mount'?'The single machine stays fully colored; hooks and tub context are highlighted.':id==='section'?'Cutaway view reveals the real internal transfer, heater, battery, press, and output path.':'Drag to orbit. Scroll to zoom. STEP Match uses zero-offset geometry from the same CadQuery source as STEP/STL.';refresh()}function setStep(id,withSound){view='process';step=id;playing=false;showStep(id);const cameras={collect:[-.53,.20,620],drain:[-.78,.12,540],dry:[-.42,.30,610],transfer:[-.35,.05,500],load:[-.18,.04,490],dock:[.08,.08,500],form:[-.10,.02,465],release:[-.36,-.04,500]};camera(cameras[id]||[-.48,.16,570]);if(withSound)cue(data.process.find(x=>x.id===id).sound);refresh()}playButton.onclick=()=>{playing=!playing;if(playing){audioOn=true;enableAudio();soundButton.textContent='Sound on';soundButton.classList.add('active');if(!step)step=data.process[0].id;showStep(step);nextAt=0;cue(data.process.find(x=>x.id===step).sound)}refresh()};soundButton.onclick=()=>{audioOn=!audioOn;if(audioOn){enableAudio();cue('dock')}soundButton.textContent=audioOn?'Sound on':'Sound off';soundButton.classList.toggle('active',audioOn)};
function target(p){const t={o:[0,0,0],a:p.alpha,g:0,p:0};if(view==='product')return t;if(view==='exploded'){const o={cover:[0,25,48],basket:[-65,36,38],scraps:[-65,36,38],drain:[-52,-8,10],water:[-52,-8,10],base:[45,-8,30],heater:[45,-34,30],pod:[75,10,25],bar:[75,10,25],mini:[85,14,38],press:[45,42,30],hooks:[0,42,-56],context:[0,42,-56]};t.o=o[p.group]||[0,0,0];return t}if(view==='mount'){if(['hooks','context'].includes(p.group)){t.o=[0,10,-10];t.g=.2;return t}t.a=Math.min(p.alpha,.12);return t}if(['collector','cover'].includes(p.group))t.a=Math.min(p.alpha,.15);if(!['basket','scraps','drain','water','base','heater','pod','bar','mini','press','status','collector','cover'].includes(p.group))t.a=Math.min(p.alpha,.05);if(step==='collect'){if(['basket','scraps'].includes(p.group)){t.g=.2;t.p=.2}if(['bar','heater','press'].includes(p.group))t.a=Math.min(p.alpha,.1)}if(step==='drain'){if(p.group==='water'){t.a=.94;t.g=.55;t.p=.9}if(['basket','drain'].includes(p.group))t.g=.2;if(['bar','heater','press'].includes(p.group))t.a=Math.min(p.alpha,.08)}if(step==='dry'){if(['basket','scraps','cover'].includes(p.group)){t.g=.12;t.p=.3}if(p.group==='water')t.a=.03;if(['bar','heater','press'].includes(p.group))t.a=Math.min(p.alpha,.08)}if(step==='remove'){if(p.group==='cover')t.o=[0,24,40];if(['basket','scraps'].includes(p.group))t.o=[-46,34,47];if(['bar','heater','press'].includes(p.group))t.a=Math.min(p.alpha,.08)}if(step==='load'){if(p.group==='basket')t.o=[-64,36,55];if(p.group==='scraps'){t.o=[190,-72,10];t.g=.35;t.p=.28}if(p.group==='pod')t.g=.2;if(p.group==='bar')t.a=.08}if(step==='dock'){if(p.group==='scraps'){t.o=[190,-72,10];t.a=.42;t.g=.42}if(['base','pod','heater'].includes(p.group))t.g=.28;if(p.group==='bar')t.a=.15}if(step==='form'){if(p.group==='scraps'){t.o=[190,-72,10];t.a=.05}if(p.group==='heater'){t.g=1;t.p=.7}if(p.group==='press'){t.o=[0,-24,0];t.g=.7;t.p=.3}if(['pod','bar'].includes(p.group))t.g=.42}if(step==='release'){if(['pod','bar'].includes(p.group)){t.o=[0,-5,95];t.g=p.group==='bar'?.62:.18}if(['scraps','heater','press'].includes(p.group))t.a=Math.min(p.alpha,.08)}return t}
function target(p){const t={o:[0,0,0],a:p.alpha,g:0,p:0},keep=(groups,a=.92)=>groups.includes(p.group)?Math.min(p.alpha,a):Math.min(p.alpha,.06);if(view==='product')return t;if(view==='exploded'){const o={cover:[0,25,48],basket:[-48,35,38],scraps:[-48,35,38],drain:[-48,-8,10],water:[-48,-8,10],transfer:[0,-30,24],mold:[0,-30,35],soft_mass:[0,-30,35],bar:[0,-30,35],heater:[0,-52,20],press:[0,45,30],output:[0,-20,70],battery:[48,16,30],hooks:[0,42,-56],context:[0,42,-56]};t.o=o[p.group]||[0,0,0];return t}if(view==='mount'){if(['hooks','context'].includes(p.group)){t.g=.35;return t}return t}if(view==='section'){if(['housing','cover'].includes(p.group))t.a=.16;else if(['context','hooks'].includes(p.group))t.a=.05;return t}if(view==='battery'){t.a=keep(['battery','housing','cover'],.9);if(p.group==='battery')t.g=.48;return t}if(view==='heater'){t.a=keep(['heater','mold','soft_mass','bar','press','housing','cover'],.94);if(p.group==='heater')t.g=1;if(p.group==='press')t.g=.45;return t}if(view==='drain'){t.a=keep(['collector','cover','basket','drain','water','housing','hooks'],.94);if(p.group==='water')t.a=.95;if(['water','drain'].includes(p.group))t.g=.55;return t}if(['housing','cover'].includes(p.group))t.a=.14;if(['hooks','context','battery'].includes(p.group))t.a=.05;if(step==='collect'){if(['basket','scraps'].includes(p.group)){t.g=.25;t.p=.2}if(['transfer','mold','heater','press','output','bar','soft_mass'].includes(p.group))t.a=Math.min(p.alpha,.06)}if(step==='drain'){if(p.group==='water'){t.a=.95;t.g=.6;t.p=.9}if(['basket','drain'].includes(p.group))t.g=.25;if(['transfer','mold','heater','press','output','bar','soft_mass'].includes(p.group))t.a=Math.min(p.alpha,.06)}if(step==='dry'){if(['basket','scraps','cover'].includes(p.group)){t.g=.16;t.p=.35}if(p.group==='water')t.a=.03;if(['transfer','mold','heater','press','output','bar','soft_mass'].includes(p.group))t.a=Math.min(p.alpha,.06)}if(step==='transfer'){if(p.group==='cover')t.o=[0,25,40];if(p.group==='basket')t.o=[-42,30,42];if(p.group==='scraps')t.o=[0,-38,0];if(p.group==='transfer'){t.g=.4;t.p=.25}if(['heater','press','output','bar','soft_mass'].includes(p.group))t.a=Math.min(p.alpha,.08)}if(step==='load'){if(p.group==='scraps'){t.o=[0,-82,0];t.g=.4;t.p=.25}if(p.group==='transfer')t.g=.35;if(p.group==='mold')t.g=.3;if(p.group==='bar')t.a=.08;if(['heater','press','output'].includes(p.group))t.a=Math.min(p.alpha,.08)}if(step==='dock'){if(p.group==='scraps'){t.o=[0,-82,0];t.a=.3;t.g=.4}if(['heater','mold','press'].includes(p.group))t.g=.4;if(p.group==='battery')t.a=.24;if(p.group==='bar')t.a=.08}if(step==='form'){if(p.group==='scraps'){t.o=[0,-82,0];t.a=.03}if(p.group==='soft_mass'){t.a=.95;t.g=.75;t.p=.45}if(p.group==='heater'){t.g=1;t.p=.7}if(p.group==='press'){t.o=[0,-28,0];t.g=.75;t.p=.25}if(p.group==='bar')t.a=.22;if(p.group==='mold')t.g=.35}if(step==='release'){if(p.group==='output')t.o=[0,0,105];if(p.group==='bar'){t.o=[0,0,105];t.g=.6}if(p.group==='soft_mass')t.a=.04;if(['scraps','heater','press','transfer','mold'].includes(p.group))t.a=Math.min(p.alpha,.08)}return t}
function enableAudio(){if(!audio)audio=new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume()}function tone(f,d=.12,type='sine',gain=.04,delay=0){if(!audioOn||!audio)return;const o=audio.createOscillator(),g=audio.createGain(),at=audio.currentTime+delay;o.type=type;o.frequency.setValueAtTime(f,at);g.gain.setValueAtTime(.0001,at);g.gain.exponentialRampToValueAtTime(gain,at+.012);g.gain.exponentialRampToValueAtTime(.0001,at+d);o.connect(g).connect(audio.destination);o.start(at);o.stop(at+d+.02)}function cue(name){if(!audioOn)return;enableAudio();const map={collect:()=>{tone(640,.08,'sine',.035);tone(880,.07,'sine',.025,.1)},drain:()=>{tone(980,.06,'sine',.018);tone(760,.07,'sine',.014,.15);tone(920,.06,'sine',.012,.29)},dry:()=>tone(520,.22,'triangle',.012),transfer:()=>{tone(360,.12,'triangle',.035);tone(540,.08,'sine',.02,.12)},load:()=>{tone(320,.13,'triangle',.035);tone(470,.1,'sine',.02,.15)},dock:()=>{tone(210,.09,'square',.03);tone(630,.12,'sine',.018,.1)},form:()=>{tone(110,.38,'sine',.025);tone(180,.1,'triangle',.04,.28)},release:()=>{tone(390,.1,'triangle',.04);tone(650,.2,'sine',.025,.1)}};(map[name]||map.dock)()}
function mul(a,b){const o=new Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)o[c*4+r]=a[r]*b[c*4]+a[4+r]*b[c*4+1]+a[8+r]*b[c*4+2]+a[12+r]*b[c*4+3];return o}const tr=(x,y,z)=>[1,0,0,0,0,1,0,0,0,0,1,0,x,y,z,1],norm=v=>{const d=Math.hypot(...v)||1;return v.map(x=>x/d)},cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];function perspective(f,a,n,z){const q=1/Math.tan(f/2);return[q/a,0,0,0,0,q,0,0,0,0,(z+n)/(n-z),-1,0,0,2*z*n/(n-z),0]}function look(eye,target,up){const z=norm([eye[0]-target[0],eye[1]-target[1],eye[2]-target[2]]),x=norm(cross(up,z)),y=cross(z,x);return[x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]}function point(m,p){const[x,y,z]=p;return[m[0]*x+m[4]*y+m[8]*z+m[12],m[1]*x+m[5]*y+m[9]*z+m[13],m[2]*x+m[6]*y+m[10]*z+m[14],m[3]*x+m[7]*y+m[11]*z+m[15]]}function resize(){const d=Math.min(devicePixelRatio||1,2),w=Math.floor(canvas.clientWidth*d),h=Math.floor(canvas.clientHeight*d);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}gl.viewport(0,0,w,h)}addEventListener('resize',resize);let drag=false,lx=0,ly=0;canvas.onpointerdown=e=>{drag=true;lx=e.clientX;ly=e.clientY;canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;yawT+=(e.clientX-lx)*.007;pitchT=Math.max(-1.04,Math.min(1.04,pitchT+(e.clientY-ly)*.006));lx=e.clientX;ly=e.clientY};canvas.onpointerup=e=>{drag=false;canvas.releasePointerCapture(e.pointerId)};canvas.onwheel=e=>{e.preventDefault();distanceT=Math.max(360,Math.min(950,distanceT+e.deltaY*.45))};
function updateLabels(v,w,h){for(const label of labels){const show=(view==='process'&&label.steps.includes(step))||(view==='mount'&&label.steps.includes('mount'));if(!show){label.el.classList.remove('show');continue}const p=byId[label.part],q=point(v,[label.anchor[0]+p.s.o[0],label.anchor[1]+p.s.o[1],label.anchor[2]+p.s.o[2]]);if(q[3]<.1){label.el.classList.remove('show');continue}const x=(q[0]/q[3]*.5+.5)*w,y=(-q[1]/q[3]*.5+.5)*h;if(x<0||x>w||y<0||y>h){label.el.classList.remove('show');continue}label.el.style.left=x+'px';label.el.style.top=y+'px';label.el.classList.add('show')}}
function draw(now){resize();if(playing&&(!nextAt||now>=nextAt)){const i=data.process.findIndex(x=>x.id===step);step=data.process[(i+1)%data.process.length].id;showStep(step);cue(data.process.find(x=>x.id===step).sound);nextAt=now+4400;refresh()}yaw+=(yawT-yaw)*.1;pitch+=(pitchT-pitch)*.1;distance+=(distanceT-distance)*.1;for(const p of parts){const t=target(p);for(let i=0;i<3;i++)p.t.o[i]=t.o[i];p.t.a=t.a;p.t.g=t.g;p.t.p=t.p;for(let i=0;i<3;i++)p.s.o[i]+=(p.t.o[i]-p.s.o[i])*.09;p.s.a+=(p.t.a-p.s.a)*.09;p.s.g+=(p.t.g-p.s.g)*.1;p.s.p+=(p.t.p-p.s.p)*.1}gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);const vp=mul(perspective(Math.PI/4.25,canvas.width/Math.max(canvas.height,1),1,2200),look([Math.sin(yaw)*Math.cos(pitch)*distance,Math.sin(pitch)*distance+20,Math.cos(yaw)*Math.cos(pitch)*distance],[0,5,0],[0,1,0]));for(const p of [...parts].sort((a,b)=>b.s.a-a.s.a)){if(p.s.a<.02)continue;const u=Math.sin(now*.008+p.mesh.count*.002)*p.s.p,o=p.s.o,m=tr(o[0],o[1]+u*1.5,o[2]+u*.7);gl.uniformMatrix4fv(L.m,false,new Float32Array(m));gl.uniformMatrix4fv(L.v,false,new Float32Array(mul(vp,m)));gl.uniform3fv(L.c,new Float32Array(p.color));gl.uniform1f(L.a,p.s.a);gl.uniform1f(L.g,p.s.g+Math.max(0,u)*.35);gl.depthMask(p.s.a>.94);gl.bindBuffer(gl.ARRAY_BUFFER,p.pb);gl.enableVertexAttribArray(L.p);gl.vertexAttribPointer(L.p,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,p.nb);gl.enableVertexAttribArray(L.n);gl.vertexAttribPointer(L.n,3,gl.FLOAT,false,0,0);gl.drawArrays(gl.TRIANGLES,0,p.mesh.count)}gl.depthMask(true);updateLabels(vp,canvas.clientWidth,canvas.clientHeight);requestAnimationFrame(draw)}window.__aquaFormDemo={setView,setStep,data};setView('product');requestAnimationFrame(draw);
</script></main></body></html>'''
    # Keep the presentation controls compact while adding explicit camera and label controls.
    template = template.replace(".views button,.sound,.play,.step{", ".views button,.sound,.play,.step,.tool{")
    template = template.replace("grid-template-columns:repeat(8,minmax(0,1fr))", "grid-template-columns:repeat(10,minmax(0,1fr))")
    template = template.replace(".views button,.sound{padding:9px 10px}", ".views button,.sound{padding:9px 10px}.tool{padding:9px 8px}")
    template = template.replace(".views button:hover,.sound:hover,.play:hover,.step:hover{", ".views button:hover,.sound:hover,.play:hover,.step:hover,.tool:hover{")
    template = template.replace('<button class="sound" id="sound">Sound off</button><div class="timeline"', '<button class="sound" id="sound">Sound off</button><button class="tool" id="zoomIn">Zoom +</button><button class="tool" id="zoomOut">Zoom -</button><button class="tool" id="resetView">Reset</button><button class="tool" id="labels">Labels on</button><div class="timeline"')
    template = template.replace("calloutsEl=$('callouts'),soundButton=$('sound'),playButton=$('play');", "calloutsEl=$('callouts'),soundButton=$('sound'),playButton=$('play'),zoomIn=$('zoomIn'),zoomOut=$('zoomOut'),resetButton=$('resetView'),labelsButton=$('labels');")
    template = template.replace("let view='product',step=null,playing=false,nextAt=0,audioOn=false,audio=null,yaw=-.53,pitch=.20,distance=650", "let view='product',step=null,playing=false,nextAt=0,audioOn=false,audio=null,labelsOn=true,stageStartedAt=0,yaw=-.53,pitch=.20,distance=650")
    template = template.replace("number.textContent='Process '+item.number;", "number.textContent='Process '+item.number+' / '+String(data.process.length);")
    template = template.replace("const cameras={collect:[-.53,.20,620],drain:[-.78,.12,540],dry:[-.42,.30,610],transfer:[-.35,.05,500],load:[-.18,.04,490],dock:[.08,.08,500],form:[-.10,.02,465],release:[-.36,-.04,500]};camera(cameras[id]||[-.48,.16,570]);", "const item=data.process.find(x=>x.id===id);stageStartedAt=performance.now();camera(item.camera||[-.48,.16,570]);")
    template = template.replace("nextAt=0;cue(data.process.find(x=>x.id===step).sound)", "stageStartedAt=performance.now();nextAt=stageStartedAt+data.process.find(x=>x.id===step).duration_ms;camera(data.process.find(x=>x.id===step).camera);cue(data.process.find(x=>x.id===step).sound)")
    template = template.replace("nextAt=now+4400;refresh()", "const item=data.process.find(x=>x.id===step);stageStartedAt=now;camera(item.camera);nextAt=now+item.duration_ms;refresh()")
    template = template.replace("soundButton.classList.toggle('active',audioOn)};\nfunction target", "soundButton.classList.toggle('active',audioOn)};labelsButton.onclick=()=>{labelsOn=!labelsOn;labelsButton.textContent=labelsOn?'Labels on':'Labels off'};zoomIn.onclick=()=>{distanceT=Math.max(360,distanceT-60)};zoomOut.onclick=()=>{distanceT=Math.min(950,distanceT+60)};resetButton.onclick=()=>setView('product');\nfunction target")
    template = template.replace("next.textContent='Next: '+item.next;", "next.textContent='Why: '+item.why+' Next: '+item.next;")
    template = template.replace("const show=(view==='process'&&label.steps.includes(step))||(view==='mount'&&label.steps.includes('mount'))", "const show=labelsOn&&((view==='process'&&label.steps.includes(step))||(view==='mount'&&label.steps.includes('mount')))")
    video_target = r"""function target(p,now){const t={o:[0,0,0],a:p.alpha,g:0,p:0},keep=(g,a=.92)=>g.includes(p.group)?Math.min(p.alpha,a):Math.min(p.alpha,.06),item=step&&data.process.find(x=>x.id===step),q=item?Math.max(0,Math.min(1,(now-stageStartedAt)/item.duration_ms)):0;if(view==='product')return t;if(view==='exploded'){const o={cover:[0,25,48],basket:[-48,35,38],scraps:[-48,35,38],drain:[-48,-8,10],water:[-48,-8,10],airflow:[0,25,0],transfer:[0,-30,24],mold:[0,-30,35],soft_mass:[0,-30,35],bar:[0,-30,35],heater:[0,-52,20],press:[0,45,30],output:[0,-20,70],battery:[48,16,30],hooks:[0,42,-56],context:[0,42,-56]};t.o=o[p.group]||[0,0,0];return t}if(view==='mount'){if(['hooks','context'].includes(p.group))t.g=.35;return t}if(view==='section'){if(['housing','cover'].includes(p.group))t.a=.16;else if(['context','hooks'].includes(p.group))t.a=.05;return t}if(view==='battery'){t.a=keep(['battery','housing','cover'],.9);if(p.group==='battery')t.g=.48;return t}if(view==='heater'){t.a=keep(['heater','mold','soft_mass','bar','press','housing','cover'],.94);if(p.group==='heater')t.g=1;if(p.group==='press')t.g=.45;return t}if(view==='drain'){t.a=keep(['cover','basket','drain','water','housing','hooks'],.94);if(p.group==='water')t.a=.95;if(['water','drain'].includes(p.group))t.g=.55;return t}if(['housing','cover'].includes(p.group))t.a=.15;if(['hooks','context','battery'].includes(p.group))t.a=.05;if(step==='collect'){if(p.group==='scraps'){t.o=[0,38*(1-q),-8*(1-q)];t.g=.3;t.p=.45}if(p.group==='basket')t.g=.18;if(['transfer','mold','heater','press','output','bar','soft_mass','airflow'].includes(p.group))t.a=Math.min(p.alpha,.05)}if(step==='drain'){if(p.group==='water'){t.a=.96;t.o=[0,-98*q,0];t.g=.7;t.p=1}if(['basket','drain'].includes(p.group))t.g=.28;if(['transfer','mold','heater','press','output','bar','soft_mass','airflow'].includes(p.group))t.a=Math.min(p.alpha,.05)}if(step==='dry'){if(p.group==='airflow'){t.a=.92;t.o=[0,22*(q-.5),0];t.g=.55;t.p=1}if(['basket','scraps','cover'].includes(p.group)){t.g=.18;t.p=.28}if(p.group==='water')t.a=.02;if(['transfer','mold','heater','press','output','bar','soft_mass'].includes(p.group))t.a=Math.min(p.alpha,.05)}if(step==='ready'){if(p.group==='airflow'){t.a=.62;t.o=[0,12*(q-.5),0];t.g=.38;t.p=.7}if(p.group==='status')t.g=.7;if(p.group==='transfer')t.g=.25;if(['heater','press','output','bar','soft_mass'].includes(p.group))t.a=Math.min(p.alpha,.05)}if(step==='transfer'){if(p.group==='cover')t.o=[0,25*q,40*q];if(p.group==='basket')t.o=[-42*q,30*q,42*q];if(p.group==='scraps'){t.o=[-10*q,-48*q,7*q];t.g=.45;t.p=.5}if(p.group==='transfer'){t.g=.55;t.p=.35}if(['heater','press','output','bar','soft_mass','airflow'].includes(p.group))t.a=Math.min(p.alpha,.06)}if(step==='load'){if(p.group==='scraps'){t.o=[0,-88*q,0];t.g=.45;t.p=.42}if(p.group==='transfer')t.g=.38;if(p.group==='mold')t.g=.42;if(p.group==='press')t.o=[0,0,-12*q];if(['heater','output','bar','soft_mass','airflow'].includes(p.group))t.a=Math.min(p.alpha,.07)}if(step==='soften'){if(p.group==='scraps'){t.o=[0,-88,0];t.a=Math.max(.03,1-q);t.g=.35}if(p.group==='soft_mass'){t.a=.08+.86*q;t.g=.72*q;t.p=.45}if(p.group==='heater'){t.g=.4+.6*q;t.p=.7}if(p.group==='mold')t.g=.35;if(p.group==='battery')t.a=.22;if(p.group==='bar')t.a=.08}if(step==='press'){if(p.group==='scraps')t.a=.02;if(p.group==='soft_mass'){t.a=.92-.5*q;t.g=.58;t.p=.28}if(p.group==='press'){t.o=[0,-34*q,0];t.g=.8;t.p=.25}if(p.group==='heater'){t.g=.8-.45*q;t.p=.5}if(p.group==='bar'){t.a=.15+.72*q;t.g=.25*q}if(p.group==='mold')t.g=.36}if(step==='cool'){if(p.group==='heater')t.a=.10;if(p.group==='soft_mass')t.a=.03;if(p.group==='bar'){t.a=.95;t.g=.2}if(p.group==='press')t.o=[0,-34*(1-q),0];if(p.group==='airflow'){t.a=.82;t.o=[0,18*(q-.5),-10];t.g=.45;t.p=.9}if(p.group==='output')t.g=.2}if(step==='release'){if(p.group==='output')t.o=[0,0,112*q];if(p.group==='bar'){t.o=[0,0,112*q];t.a=.98;t.g=.68}if(p.group==='soft_mass')t.a=.03;if(['scraps','heater','press','transfer','mold','airflow'].includes(p.group))t.a=Math.min(p.alpha,.07)}return t}"""
    template = template.replace("function enableAudio()", video_target + "function enableAudio()")
    template = template.replace("const t=target(p);", "const t=target(p,now);")
    api_script = "<script>window.__aquaFormDemo={setView:setView,setStep:setStep,playCycle:()=>playButton.click(),pauseCycle:()=>{playing=false;refresh()},toggleSound:()=>soundButton.click(),resetView:()=>setView('product'),data:data}</script>"
    output = template.replace("__MODEL_DATA__", data).replace("</script></main>", "</script>" + api_script + "</main>")
    Path(path).write_text(output, encoding="ascii")


if __name__ == "__main__":
    assy.save("soap_recycler_prototype_2A.step")
    cq.exporters.export(assy.toCompound(), "soap_recycler_prototype_2A.stl")
    write_demo_html()

    print("Exported: soap_recycler_prototype_2A.step")
    print("Exported: soap_recycler_prototype_2A.stl")
    print("Exported: soap_recycler_demo_2A.html")
