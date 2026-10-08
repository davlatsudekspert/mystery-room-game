"""desk.glb — Dr. Leyla Rahimova's antique walnut pedestal writing desk (hero prop, Lab 7).

1.50 w x 0.78 h x 0.72 d. Origin = floor centre of the footprint. Front faces Blender -Y (Godot +Z).
East side = model +X (Godot +X): carved rosette, secret panel, keyhole, hidden compartment.

Interactive parts (separate objects, origin at the pivot):
  IA_drawer_top        centre drawer; origin at its front-bottom-centre (drawer-front face, bottom
                       edge); slides out along -Y Blender / +Z Godot.
  IA_drawer_wheel_0..3 4 brass digit wheels (left -> right), CHILDREN of IA_drawer_top. Axle = local X,
                       origin at the axle centre. Digit 0 faces the viewer at rest; rotation.x = +k*36deg
                       (Godot and Blender alike) shows digit k.
  IA_rosette           carved rosette on the east side, upper rear; origin at the centre of its base
                       (on the side surface); press = move along -X.
  IA_compartment       hidden drawer in the east pedestal; origin at its outer-face centre; slides +X.
  IA_secret_panel      inlaid mahogany slip on the compartment face, CHILD of IA_compartment; origin at
                       its centre; slides 0.06 m down (-Z Blender / -Y Godot) to reveal the keyhole.
  IA_keyhole           brass escutcheon under the secret panel, CHILD of IA_compartment; origin at the
                       keyhole centre on the escutcheon face.

    blender -b --factory-startup -P tools/blender/models/desk.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "desk"
TOP_Z0 = 0.745           # underside of the top
TOP_Z1 = 0.78            # writing surface
CX = 0.725               # carcass half width (top overhangs 0.025)
FY, BY = -0.335, 0.335   # carcass front / back
PIN = 0.305              # pedestal inner face |x|
PL_H = 0.085             # plinth height
DF_T = 0.018             # drawer-front thickness (lipped, proud of the carcass)
DFY = FY - DF_T          # drawer-front face  (-0.353)
WHEEL_Z = 0.678          # combination wheel axle height
WHEEL_R = 0.026
WHEEL_W = 0.016
WHEEL_PITCH = 0.022
FIELD_X = CX + 0.010     # face of the raised side fields (0.735)
COMP_Y = 0.1425          # centre (y) of the upper-rear side panel = compartment
SECRET_Z = 0.596         # keyhole / secret panel centre height

static = []


def S(o):
    static.append(o)
    return o


def rotate_to(obj, normal):
    """Rotate mesh data so local +Z points along `normal`."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(normal).normalized())
    obj.data.transform(q.to_matrix().to_4x4())
    return obj


# ------------------------------------------------------------------ top
def build_top():
    path = [(-0.75, -0.36, 0), (0.75, -0.36, 0), (0.75, 0.36, 0), (-0.75, 0.36, 0)]
    prof = [(0.11, TOP_Z0), (0.018, TOP_Z0)]
    prof += A.arc(0.018, TOP_Z0 + 0.008, 0.008, 270, 180, 3)[1:]
    prof += [(0.004, 0.756), (0.0, 0.758)]
    prof += A.arc(0.012, 0.768, 0.012, 180, 90, 4)
    prof += [(0.11, TOP_Z1)]
    S(A.sweep("top_band", prof, path, closed=True, mat="M_Wood_Walnut"))
    lz = TOP_Z1 - 0.0005
    S(A.box_minmax("leather", (-0.64, -0.25, TOP_Z0), (0.64, 0.25, lz), mat="M_Leather", bevel=0.0008))
    # gold-tooled border line on the leather
    p2 = [(-0.624, -0.234, 0), (0.624, -0.234, 0), (0.624, 0.234, 0), (-0.624, 0.234, 0)]
    S(A.sweep("tooling", [(-0.0011, lz - 0.0003), (0.0011, lz - 0.0003), (0.0011, lz + 0.0004),
                          (-0.0011, lz + 0.0004)], p2, closed=True, mat="M_Brass_Polished"))


# ------------------------------------------------------------------ small hardware
def bail_pull(name, x, z, y=DFY):
    parts = []
    plate = A.rounded_rect(0.084, 0.026, 0.012, seg=2)
    parts.append(M.extrude_profile(name + "_plate", plate, 0.0018, loc=(x, y, z), rot=(math.pi / 2, 0, 0),
                                   mat="M_Brass_Aged", bevel=0.0))
    for sx in (-0.031, 0.031):
        parts.append(M.cylinder(name + "_post", 0.0032, 0.013, loc=(x + sx, y - 0.0018 - 0.0065, z + 0.004),
                                rot=(math.pi / 2, 0, 0), verts=6, mat="M_Brass_Aged", bevel=0.0))
    pts = []
    for i in range(7):
        t = math.pi + math.pi * i / 6
        pts.append((x + 0.031 * math.cos(t), y - 0.0125, z + 0.004 + 0.021 * math.sin(t)))
    parts.append(A.tube(name + "_bail", pts, 0.0032, sides=6, mat="M_Brass_Aged"))
    return parts


def knob(name, loc, normal=(0, -1, 0), scale=1.0):
    s = scale
    prof = [(0.0, 0.0), (0.0095 * s, 0.0), (0.0095 * s, 0.002 * s), (0.0048 * s, 0.006 * s),
            (0.0052 * s, 0.011 * s), (0.0115 * s, 0.017 * s), (0.0118 * s, 0.022 * s),
            (0.0085 * s, 0.0255 * s), (0.0, 0.0265 * s)]
    o = M.lathe(name, prof, segments=10, mat="M_Brass_Aged")
    rotate_to(o, normal)
    o.location = loc
    return o


def escutcheon(name, loc, normal=(0, -1, 0), w=0.018, h=0.03, mat="M_Brass_Aged"):
    """Brass keyhole plate + black keyhole, lying on a surface with the given outward normal.
    Returns (plate, hole); local frame: plate extruded along +Z then rotated to `normal`."""
    # plate outline in (h=horizontal, v=vertical)
    out = A.rounded_rect(w, h, w * 0.45, seg=3)
    hole = []
    cv, rr, sw = 0.003, 0.0027, 0.0011
    a0 = math.degrees(math.acos(sw / rr))
    hole += [(0.0017, -0.0075), (sw, cv - rr * math.sin(math.radians(a0)))]
    hole += A.arc(0.0, cv, rr, -a0, 180 + a0, 10)[1:-1]
    hole += [(-sw, cv - rr * math.sin(math.radians(a0))), (-0.0017, -0.0075)]
    hole = A.ccw(hole)
    plate = M.extrude_profile(name, out, 0.0012, mat=mat, bevel=0.0003)
    keyh = M.extrude_profile(name + "_hole", hole, 0.0016, mat="M_Bakelite", bevel=0.0)
    n = Vector(normal).normalized()
    # local frame: X = horizontal along the surface, Y = up (Z world), Z = normal
    up = Vector((0, 0, 1))
    right = up.cross(n).normalized()       # viewer's right when facing the surface
    rmat = Matrix((right, up, n)).transposed().to_4x4()
    for o in (plate, keyh):
        o.data.transform(rmat)
        o.location = loc
    return plate, keyh


def rosette(name, loc, normal, r=0.025, petals=6):
    prof = [(r, 0.0), (r, 0.0028), (r * 0.86, 0.0068), (r * 0.62, 0.0086), (r * 0.44, 0.0066),
            (r * 0.30, 0.0092), (r * 0.13, 0.0125), (0.0, 0.0132)]
    o = M.lathe(name, prof, segments=24, mat="M_Wood_Walnut")
    for v in o.data.vertices:
        rr = math.hypot(v.co.x, v.co.y)
        if rr < 1e-6:
            continue
        a = math.atan2(v.co.y, v.co.x)
        c = math.cos(petals * a)
        if rr > r * 0.5:
            f = 1.0 + 0.09 * c
            v.co.x *= f
            v.co.y *= f
            if v.co.z > 0.004:
                v.co.z *= 1.0 + 0.22 * c
        elif rr > r * 0.2:
            v.co.z *= 1.0 - 0.18 * math.cos(petals * a + math.pi / petals)
    rotate_to(o, normal)
    o.location = loc
    return o


# ------------------------------------------------------------------ pedestals
DRAWERS = [(0.130, 0.360), (0.364, 0.549), (0.553, 0.728)]   # bottom, middle, top (z ranges)


def column(name, x, y):
    z0 = PL_H + 0.008
    prof = [(0.0, z0), (0.025, z0), (0.025, z0 + 0.011), (0.0225, z0 + 0.016), (0.0232, z0 + 0.021),
            (0.0185, z0 + 0.028), (0.0172, z0 + 0.045), (0.0162, 0.40), (0.0172, 0.655),
            (0.0215, 0.664), (0.0178, 0.672), (0.0200, 0.690), (0.0255, 0.708), (0.027, 0.716),
            (0.027, TOP_Z0), (0.0, TOP_Z0)]
    o = M.lathe(name, prof, segments=10, mat="M_Wood_Walnut")
    o.location = (x, y, 0)
    return o


def side_panels(side, compartment=False):
    """Frame-and-panel relief on a pedestal's outer side (side=+1 east, -1 west)."""
    xf = side * CX
    up = (side, 0, 0)
    panels = [(-0.265, 0.265, 0.150, 0.405), (-0.265, -0.020, 0.450, 0.660), (0.020, 0.265, 0.450, 0.660)]
    fields = []
    for i, (y0, y1, z0, z1) in enumerate(panels):
        if side > 0:
            path = [(xf, y0, z0), (xf, y1, z0), (xf, y1, z1), (xf, y0, z1)]
        else:
            path = [(xf, y1, z0), (xf, y0, z0), (xf, y0, z1), (xf, y1, z1)]
        S(A.sweep(f"side_mould_{side}_{i}", A.profile_panel_mould(0.020, 0.010), path, up=up, closed=True,
                  mat="M_Wood_Walnut"))
        fy0, fy1, fz0, fz1 = y0 + 0.022, y1 - 0.022, z0 + 0.022, z1 - 0.022
        is_comp = compartment and i == 2
        if not is_comp:
            f = M.box(f"side_field_{side}_{i}", (0.014, fy1 - fy0, fz1 - fz0),
                      loc=(xf + side * 0.003, (fy0 + fy1) / 2, (fz0 + fz1) / 2), mat="M_Wood_Walnut",
                      bevel=0.009, segments=1)
            S(f)
            if i > 0:   # inlaid mahogany slip (matches the secret panel, so it does not stand out)
                S(M.box(f"inlay_{side}_{i}", (0.003, 0.085, 0.046),
                        loc=(side * (FIELD_X + 0.0015), (fy0 + fy1) / 2, SECRET_Z), mat="M_Wood_Mahogany",
                        bevel=0.0009, segments=1))
        fields.append((fy0, fy1, fz0, fz1))
    return fields


def pedestal(side):
    x_in, x_out = side * PIN, side * CX
    xmin, xmax = min(x_in, x_out), max(x_in, x_out)
    S(A.box_minmax(f"plinth_{side}", (xmin - 0.016, FY - 0.016, 0.0), (xmax + 0.016, BY, PL_H),
                   mat="M_Wood_Walnut", bevel=0.004, segments=2))
    base_prof = [(0.0, PL_H), (-0.013, PL_H)] + A.arc(-0.005, PL_H, 0.008, 180, 90, 3)[1:] + [(0.0, PL_H + 0.009)]
    S(A.sweep(f"base_mould_{side}", base_prof,
              [(xmin, FY, 0), (xmax, FY, 0), (xmax, BY, 0), (xmin, BY, 0)], closed=True, mat="M_Wood_Walnut"))
    carcass = A.box_minmax(f"carcass_{side}", (xmin, FY, PL_H), (xmax, BY, TOP_Z0), mat="M_Wood_Walnut",
                           bevel=0.003, segments=1)
    if side > 0:
        # pocket for the hidden compartment (upper rear panel of the east side)
        cutter = A.box_minmax("cutter", (CX - 0.285, 0.040, 0.470), (CX + 0.05, 0.245, 0.640), bevel=0.0)
        M.boolean(carcass, cutter)
        # the pocket walls keep the carcass material; darken nothing (walnut inside is fine)
    S(carcass)
    for x in (x_in, x_out):
        S(column(f"column_{side}_{x:.2f}", x, FY))
    side_panels(side, compartment=(side > 0))
    # drawers
    dx0, dx1 = xmin + 0.030, xmax - 0.030
    cx = (dx0 + dx1) / 2
    for i, (z0, z1) in enumerate(DRAWERS):
        ajar = 0.012 if (side < 0 and i == 1) else 0.0      # one drawer left slightly open
        S(M.box(f"dfront_{side}_{i}", (dx1 - dx0, DF_T, z1 - z0), loc=(cx, FY - DF_T / 2 - ajar, (z0 + z1) / 2),
                mat="M_Wood_Walnut", bevel=0.006, segments=2))
        if ajar:
            # visible drawer sides behind the ajar front
            for sx in (dx0 + 0.012, dx1 - 0.012):
                S(A.box_minmax(f"dside_{side}_{i}", (sx - 0.006, FY - ajar, z0 + 0.012), (sx + 0.006, FY + 0.01, z1 - 0.03),
                               mat="M_Wood_Panel", bevel=0.001))
        zc = (z0 + z1) / 2 - (0.012 if i == 2 else 0.0)
        for o in bail_pull(f"pull_{side}_{i}", cx, zc, y=DFY - ajar):
            S(o)
        if i == 2:
            for o in escutcheon(f"esc_{side}", (cx, DFY - ajar, (z0 + z1) / 2 + 0.040), (0, -1, 0), w=0.014, h=0.024):
                S(o)


# ------------------------------------------------------------------ kneehole & centre
def kneehole():
    xw = PIN - 0.026
    S(A.box_minmax("top_rail", (-xw, FY - 0.010, 0.731), (xw, FY + 0.015, TOP_Z0), mat="M_Wood_Walnut",
                   bevel=0.002))
    S(A.box_minmax("dust_board", (-PIN, FY + 0.008, 0.610), (PIN, 0.300, 0.624), mat="M_Wood_Panel", bevel=0.0015))
    # shaped apron under the centre drawer (cove brackets at both ends)
    pts = [(xw, 0.624), (-xw, 0.624), (-xw, 0.548)]
    pts += A.arc(-xw + 0.040, 0.548, 0.040, 180, 90, 5)[1:]
    pts += A.arc(xw - 0.040, 0.548, 0.040, 90, 0, 5)
    S(M.extrude_profile("apron", A.dedupe(pts), 0.018, loc=(0, FY + 0.008, 0), rot=(math.pi / 2, 0, 0),
                        mat="M_Wood_Walnut", bevel=0.002))
    # modesty / back panel with a raised field
    S(A.box_minmax("back_panel", (-PIN, 0.300, PL_H), (PIN, 0.318, 0.610), mat="M_Wood_Walnut", bevel=0.002))
    S(M.box("back_field", (0.46, 0.012, 0.38), loc=(0, 0.300, 0.35), mat="M_Wood_Walnut", bevel=0.009, segments=1))


def centre_drawer():
    parts = []
    fz0, fz1 = 0.628, 0.728
    xw = 0.276
    parts.append(M.box("cd_front", (2 * xw, DF_T, fz1 - fz0), loc=(0, FY - DF_T / 2, (fz0 + fz1) / 2),
                       mat="M_Wood_Walnut", bevel=0.006, segments=2))
    # drawer box
    parts.append(A.box_minmax("cd_side_l", (-0.270, FY, 0.634), (-0.258, 0.165, 0.716), mat="M_Wood_Panel", bevel=0.0015))
    parts.append(A.box_minmax("cd_side_r", (0.258, FY, 0.634), (0.270, 0.165, 0.716), mat="M_Wood_Panel", bevel=0.0015))
    parts.append(A.box_minmax("cd_back", (-0.258, 0.153, 0.634), (0.258, 0.165, 0.716), mat="M_Wood_Panel", bevel=0.0015))
    parts.append(A.box_minmax("cd_bottom", (-0.258, FY, 0.631), (0.258, 0.153, 0.638), mat="M_Wood_Panel", bevel=0.0))
    # lock housing behind the front (hides the wheel backs inside the drawer)
    parts.append(A.box_minmax("cd_lockbox", (-0.054, FY, 0.646), (0.054, FY + 0.032, 0.710), mat="M_Steel_Dark",
                              bevel=0.002))
    # brass lock plate with a slot window (frame swept round the slot)
    sx, sz = 0.049, 0.0185
    path = [(-sx, DFY, WHEEL_Z - sz), (sx, DFY, WHEEL_Z - sz), (sx, DFY, WHEEL_Z + sz), (-sx, DFY, WHEEL_Z + sz)]
    prof = [(0.0, 0.0), (0.0, 0.0022), (-0.0025, 0.0035), (-0.019, 0.0035), (-0.021, 0.0022), (-0.021, 0.0)]
    parts.append(A.sweep("cd_lockplate", prof, path, up=(0, -1, 0), closed=True, mat="M_Brass_Aged"))
    parts.append(M.box("cd_slot_back", (2 * sx, 0.002, 2 * sz), loc=(0, DFY - 0.0004, WHEEL_Z), mat="M_Steel_Dark",
                       bevel=0.0))
    # index chevrons at the reading line
    for s in (-1, 1):
        tri = [(0.0, 0.0), (0.008, -0.0045), (0.008, 0.0045)]
        o = M.extrude_profile("cd_index", tri, 0.0008, loc=(0, DFY - 0.0035, 0), rot=(math.pi / 2, 0, 0),
                              mat="M_Brass_Polished", bevel=0.0)
        o.data.transform(Matrix.Diagonal((s, 1, 1, 1)))
        if s < 0:
            o.data.flip_normals()
        o.location = (s * (sx + 0.0035), DFY - 0.0035, WHEEL_Z)
        parts.append(o)
    for (px, pz) in ((-0.0595, 0.0285), (0.0595, 0.0285), (-0.0595, -0.0285), (0.0595, -0.0285)):
        parts.append(A.screw("cd_screw", 0.0026, (px, DFY - 0.0035, WHEEL_Z + pz), (0, -1, 0), "M_Brass_Aged",
                             slot_angle=37 * (px + pz) * 100, segs=8))
    for s in (-1, 1):
        parts.append(knob("cd_knob", (s * 0.185, DFY, WHEEL_Z), (0, -1, 0), 0.9))
    drawer = M.join(parts, "IA_drawer_top")
    M.set_origin(drawer, (0, DFY, fz0))
    wheels = []
    y_axle = DFY - 0.0035 - 0.009 + WHEEL_R          # wheel front 9 mm proud of the plate
    for k in range(4):
        w = A.combo_wheel(f"IA_drawer_wheel_{k}", WHEEL_R, WHEEL_W, chamfer=0.0016, segments=30)
        w.location = ((k - 1.5) * WHEEL_PITCH, y_axle, WHEEL_Z)
        w["digit_step_deg"] = 36.0
        w["rotation_axis"] = "local X; rotation = +digit*36deg shows that digit"
        wheels.append(w)
    M.refresh()
    for w in wheels:
        M.set_parent(w, drawer)
    return drawer, wheels


def compartment():
    yc, zc = COMP_Y, 0.555
    parts = []
    parts.append(M.box("comp_face", (0.014, 0.203, 0.166), loc=(CX + 0.003, yc, zc), mat="M_Wood_Walnut",
                       bevel=0.009, segments=1))
    parts.append(A.box_minmax("comp_bottom", (CX - 0.255, 0.046, 0.474), (CX - 0.004, 0.239, 0.482), mat="M_Wood_Panel", bevel=0.0))
    parts.append(A.box_minmax("comp_wall_a", (CX - 0.255, 0.046, 0.482), (CX - 0.004, 0.054, 0.585), mat="M_Wood_Panel", bevel=0.001))
    parts.append(A.box_minmax("comp_wall_b", (CX - 0.255, 0.231, 0.482), (CX - 0.004, 0.239, 0.585), mat="M_Wood_Panel", bevel=0.001))
    parts.append(A.box_minmax("comp_wall_c", (CX - 0.255, 0.054, 0.482), (CX - 0.247, 0.231, 0.585), mat="M_Wood_Panel", bevel=0.001))
    comp = M.join(parts, "IA_compartment")
    M.set_origin(comp, (FIELD_X, yc, zc))
    # keyhole escutcheon (on the compartment face) + the sliding secret panel over it
    plate, hole = escutcheon("IA_keyhole", (FIELD_X, yc, SECRET_Z), (1, 0, 0), w=0.018, h=0.03)
    key = M.join([plate, hole], "IA_keyhole")
    M.set_origin(key, (FIELD_X + 0.0012, yc, SECRET_Z))
    sp = M.box("IA_secret_panel", (0.003, 0.085, 0.046), loc=(FIELD_X + 0.0018 + 0.0015, yc, SECRET_Z),
               mat="M_Wood_Mahogany", bevel=0.0009, segments=1)
    M.refresh()
    M.set_parent(key, comp)
    M.set_parent(sp, comp)
    return comp, key, sp


# ------------------------------------------------------------------ build
def build():
    M.reset_scene()
    A.prepare_materials()
    static.clear()
    build_top()
    pedestal(-1)
    pedestal(1)
    kneehole()
    # decorative rosette on the west side (matches the interactive one on the east side)
    S(rosette("rosette_west", (-CX, COMP_Y, 0.7025), (-1, 0, 0)))
    ia_ros = rosette("IA_rosette", (CX, COMP_Y, 0.7025), (1, 0, 0))
    drawer, wheels = centre_drawer()
    comp, key, sp = compartment()
    body = M.join(static, "desk_body")
    M.finalize()
    print(f"[{NAME}] tris: body={A.tris(body)} drawer={A.tris(drawer)} wheels={sum(A.tris(w) for w in wheels)} "
          f"rosette={A.tris(ia_ros)} compartment={A.tris(comp)} keyhole={A.tris(key)} panel={A.tris(sp)} "
          f"TOTAL={M.tri_count()}")
    return dict(body=body, drawer=drawer, wheels=wheels, rosette=ia_ros, comp=comp, key=key, panel=sp)


def main():
    args = M.main_guard()
    parts = build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(64)
    M.render_preview(NAME, (1.55, -1.85, 1.35), (0.0, 0.0, 0.42), lens=38, res=(1000, 700), samples=64,
                     world_strength=0.35, lights=A.STUDIO)
    # close-up of the combination wheels at rest (digit 0 must face the viewer, upright)
    M.render_preview(NAME + "_2", (0.02, -0.62, 0.80), (0.0, -0.35, WHEEL_Z), lens=85, res=(900, 520),
                     samples=64, world_strength=0.35, lights=A.STUDIO)
    # east side: rosette, inlaid secret panel, compartment
    M.render_preview(NAME + "_3", (1.45, -0.35, 0.95), (0.70, 0.08, 0.52), lens=45, res=(900, 700), samples=64,
                     world_strength=0.35, lights=A.STUDIO)
    # solved state: wheels 0-3-1-7, drawer open, secret panel down, compartment out
    for k, d in enumerate((0, 3, 1, 7)):
        parts["wheels"][k].rotation_euler.x = math.radians(36 * d)
    M.render_preview(NAME + "_4", (0.02, -0.62, 0.80), (0.0, -0.35, WHEEL_Z), lens=85, res=(900, 520),
                     samples=64, world_strength=0.35, lights=A.STUDIO)
    parts["drawer"].location.y -= 0.26
    parts["panel"].location.z -= 0.06
    parts["comp"].location.x += 0.20
    M.render_preview(NAME + "_5", (1.65, -1.25, 1.45), (0.25, -0.05, 0.55), lens=40, res=(1000, 700), samples=64,
                     world_strength=0.35, lights=A.STUDIO)


main()
