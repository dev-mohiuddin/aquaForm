// Soap Dish Recycler + Recycled Soap Holder - Prototype 1A
// Parametric OpenSCAD model based on handwritten sketches.
// Units: millimeters.
// Render in OpenSCAD, then export STL.
// Safety: heater/batteries are visual placeholders only, not real electrical design.

$fn = 48;

// -----------------------------
// Parameters
// -----------------------------
body_w = 180;
body_d = 78;
body_h = 235;
wall = 3;
corner_r = 8;

upper_z = 126;
shelf_z = 116;
lower_chamber_z = 22;

basket_w = 150;
basket_d = 55;
basket_h = 42;
basket_wall = 2.4;
drain_hole_d = 3.2;

soap_bar_w = 82;
soap_bar_d = 48;
soap_bar_h = 24;
mold_wall = 3;

heater_w = 95;
heater_d = 58;
heater_h = 3;

battery_drawer_w = 154;
battery_drawer_d = 48;
battery_drawer_h = 42;
d_cell_diameter = 33.5;
d_cell_length = 61.5;

hook_w = 20;
hook_thick = 6;
hook_drop = 52;
hook_lip = 28;
hinge_radius = 3;

// -----------------------------
// Basic modules
// -----------------------------
module rounded_box(w, d, h, r=3) {
    // rounded only in XY, base at z=0, centered on X/Y
    linear_extrude(height=h)
        offset(r=r)
            square([w-2*r, d-2*r], center=true);
}

module open_box(w, d, h, t, r=4) {
    difference() {
        rounded_box(w, d, h, r);
        translate([0,0,t]) rounded_box(w-2*t, d-2*t, h+2, max(0.1, r-t));
    }
}

module perforated_plate(w, d, h, hole_d=3, nx=8, ny=4, r=3, margin=12) {
    difference() {
        rounded_box(w, d, h, r);
        for (i=[0:nx-1]) {
            for (j=[0:ny-1]) {
                x = -w/2 + margin + (nx==1 ? 0 : i*(w-2*margin)/(nx-1));
                y = -d/2 + margin + (ny==1 ? 0 : j*(d-2*margin)/(ny-1));
                translate([x,y,-1]) cylinder(h=h+2, d=hole_d);
            }
        }
    }
}

module vertical_perforated_panel(w, thick, h, hole_d=5, nx=5, nz=2, r=3, margin_x=25, margin_z=22) {
    difference() {
        rounded_box(w, thick, h, r);
        for (i=[0:nx-1]) {
            for (k=[0:nz-1]) {
                x = -w/2 + margin_x + (nx==1 ? 0 : i*(w-2*margin_x)/(nx-1));
                z = margin_z + (nz==1 ? 0 : k*(h-2*margin_z)/(nz-1));
                translate([x, -thick/2-1, z]) rotate([-90,0,0]) cylinder(h=thick+2, d=hole_d);
            }
        }
    }
}

module cyl_x(r, len) {
    rotate([0,90,0]) cylinder(h=len, r=r, center=true);
}

module simple_hook() {
    // U-hook for bathtub lip / shower rail. Local origin near lower back.
    union() {
        translate([0,0,0]) rounded_box(hook_w, hook_thick, hook_drop, 1.5);
        translate([0, -hook_lip/2 + hook_thick/2, hook_drop-hook_thick]) rounded_box(hook_w, hook_lip, hook_thick, 1.5);
        translate([0, -hook_lip + hook_thick, hook_drop*0.35]) rounded_box(hook_w, hook_thick, hook_drop*0.55, 1.5);
    }
}

module heater_trace(width=82, depth=44, trace_w=2.2, trace_h=1.2) {
    y1 = -depth/2 + 6;
    y2 = -depth/6;
    y3 = depth/6;
    y4 = depth/2 - 6;
    union() {
        translate([0,y1,0]) rounded_box(width-14, trace_w, trace_h, .3);
        translate([width/2-9,(y1+y2)/2,0]) rounded_box(trace_w, abs(y2-y1), trace_h, .3);
        translate([0,y2,0]) rounded_box(width-14, trace_w, trace_h, .3);
        translate([-width/2+9,(y2+y3)/2,0]) rounded_box(trace_w, abs(y3-y2), trace_h, .3);
        translate([0,y3,0]) rounded_box(width-14, trace_w, trace_h, .3);
        translate([width/2-9,(y3+y4)/2,0]) rounded_box(trace_w, abs(y4-y3), trace_h, .3);
        translate([0,y4,0]) rounded_box(width-14, trace_w, trace_h, .3);
    }
}

// -----------------------------
// Model
// -----------------------------
module soap_recycler_prototype_1A() {
    // Main open-front housing
    color([0.92,0.90,0.82]) union() {
        translate([0, body_d/2-wall/2, 0]) rounded_box(body_w, wall, body_h, corner_r);
        translate([-body_w/2+wall/2, 0, 0]) rounded_box(wall, body_d, body_h, 1.5);
        translate([ body_w/2-wall/2, 0, 0]) rounded_box(wall, body_d, body_h, 1.5);
        translate([0,0,body_h-wall]) rounded_box(body_w, body_d, wall, corner_r);
        translate([0,0,0]) rounded_box(body_w, body_d, wall, corner_r);
        translate([0,0,shelf_z]) perforated_plate(body_w-2*wall, body_d-2*wall, wall, 4, 9, 3, 4);
    }

    // Hinged perforated front cover / soap dish cover
    color([0.80,0.78,0.70]) translate([0, -body_d/2-2, upper_z+8])
        vertical_perforated_panel(body_w-18, 4, 95, 5, 5, 2, 5, 25, 24);
    color([0.55,0.52,0.45]) translate([0, -body_d/2-8, upper_z+18])
        rounded_box(62, 8, 8, 3);

    // Hinge rods
    color([0.35,0.35,0.35]) translate([0, -body_d/2-4, upper_z+105]) cyl_x(hinge_radius, body_w-20);
    color([0.35,0.35,0.35]) translate([0, -body_d/2-4, upper_z+6]) cyl_x(hinge_radius, body_w-20);

    // Upper removable wet-soap basket / dish holder
    color([0.88,0.88,0.83]) translate([0, -3, upper_z+30]) open_box(basket_w, basket_d, basket_h, basket_wall, 6);
    color([0.72,0.72,0.68]) translate([0, -3, upper_z+31])
        perforated_plate(basket_w-9, basket_d-9, 1.2, drain_hole_d, 8, 4, 4, 10);
    color([0.70,0.68,0.60]) translate([0, -3, upper_z+basket_h+30])
        rounded_box(basket_w+8, basket_d+8, 3, 6);

    // Drip channel from wet basket toward lower mold chamber
    color([0.68,0.68,0.62]) translate([0, -body_d/2+18, shelf_z+5])
        perforated_plate(65, 24, 2, 2.4, 4, 2, 4, 8);

    // Lower recycled soap mold
    mold_outer_w = soap_bar_w + 2*mold_wall + 10;
    mold_outer_d = soap_bar_d + 2*mold_wall + 8;
    mold_outer_h = soap_bar_h + mold_wall + 6;
    color([0.75,0.75,0.70]) translate([0, -5, lower_chamber_z+18])
        open_box(mold_outer_w, mold_outer_d, mold_outer_h, mold_wall, 7);
    color([0.45,0.43,0.38]) translate([0, -body_d/2-8, lower_chamber_z+26])
        rounded_box(58, 10, 9, 4);

    // Heater placeholder + insulation spacer
    color([0.20,0.20,0.20]) translate([0, -5, lower_chamber_z+7])
        rounded_box(heater_w+8, heater_d+8, 2, 4);
    color([0.95,0.35,0.20]) translate([0, -5, lower_chamber_z+10])
        rounded_box(heater_w, heater_d, heater_h, 4);
    color([1.00,0.10,0.05]) translate([0, -5, lower_chamber_z+13.1])
        heater_trace();

    // Pull-out battery drawer / handle
    color([0.62,0.58,0.50]) translate([0, -body_d/2-26, 4])
        open_box(battery_drawer_w, battery_drawer_d, battery_drawer_h, 2.4, 6);
    color([0.50,0.47,0.40]) translate([0, -body_d/2-52, 2])
        rounded_box(battery_drawer_w+8, 6, battery_drawer_h+4, 5);
    color([0.30,0.30,0.28]) translate([0, -body_d/2-60, 18])
        rounded_box(70, 12, 10, 4);

    // Four D-cell placeholders, two-by-two
    color([0.20,0.20,0.20]) for (yy=[-10,10]) for (zz=[13,31])
        translate([0, -body_d/2-26+yy, 4+zz]) cyl_x(d_cell_diameter/2, d_cell_length);

    // Two rear hooks
    color([0.66,0.63,0.55]) translate([-48, body_d/2+8, body_h-56]) simple_hook();
    color([0.66,0.63,0.55]) translate([ 48, body_d/2+8, body_h-56]) simple_hook();

    // Wall mount bosses
    color([0.50,0.50,0.46]) translate([-55, body_d/2+1, 166]) rotate([90,0,0]) cylinder(h=3, r=7);
    color([0.50,0.50,0.46]) translate([ 55, body_d/2+1, 166]) rotate([90,0,0]) cylinder(h=3, r=7);
}

soap_recycler_prototype_1A();
