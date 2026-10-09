"""shell_gallery.glb — the Resonance Gallery shell in WORLD coordinates (place at the origin, yaw 0).
Contract: docs/models/ch3.md §3 shell_gallery (+ §1.1 layout, §1.4 portals, §1.5 lights, §2 views); results:
docs/models/ch3_a.md.

  gallery_drum       concrete drum wall, inner face r 4.0 (flat at x = ±3.70 for |z| <= 1.6: the door bays), y 0..4.5:
                     plinth, two pour-joint grooves, a cornice ring; openings for the two blast-door tunnels
                     (|z| <= 0.8, y <= 2.4) and the shutter tunnel (z -3.15 .. -2.05, y 0.30 .. 2.10). The memorial arc
                     (phi -30° .. 30°) is plain.
  gallery_ceiling    flat concrete at y 4.5, 12 radial ribs (phi = 15° + 30° k) and the ring beam r 1.45 .. 1.75
  gallery_floor      M_Stone ring r 1.62 .. the drum face
  IA_glass_floor     the glass disc r 1.5, y -0.08 .. 0 (M_Glass) — the look-down hotspot
  glass_rim          brass ring r 1.5 .. 1.62 with 24 rivets; it also carries every other static brass part of the
                     Gallery (floor inlay circles r 2.4 / 3.6, the five sconce bodies, the shutter-mouth frame, the brass
                     band under the ring beam) so the shell keeps one brass surface
  gallery_rail       brass tube handrail ring r 1.75, top y 1.0, lower rail, 12 posts at phi = 15° + 30° k
  IA_tunnel_shutter  the concrete lining of the shutter tunnel from the drum face to the camp wall x = 4.5
  lamp_glass_0..4    sconce glasses at y 2.7, phi 125°, 160°, 200°, 235°, 315° (code emission); empties light_gallery_0..4
  empties            echo_rail_mount, echo_strand_mount, echo_leyla_mount, portal_w_g, portal_e_g, portal_shutter_g

phi is measured from north (-Z) clockwise seen from above (toward +X).

    blender -b --factory-startup -P tools/blender/models/shell_gallery.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "shell_gallery"
TRI_BUDGET, SURF_BUDGET = 12000, 10
CONC, STONE, BRASS, GLASS = K.CONC, K.STONE, K.BRASS, K.GLASS
R_IN, H = 4.0, 4.5
BAY_X, BAY_Z, DOOR_Z, DOOR_H = 3.70, 1.6, 0.8, 2.4
SH_Z0, SH_Z1, SH_Y0, SH_Y1, CAMP_X = -3.15, -2.05, 0.30, 2.10, 4.5
RAIL_R, RAIL_TOP = 1.75, 1.0
SCONCES = [125.0, 160.0, 200.0, 235.0, 315.0]
SCONCE_Y = 2.7
# drum wall profile: (s = offset into the wall from the inner face, y)
PROFILE = [(-0.025, 0.0), (-0.025, 0.14), (0.0, 0.165), (0.0, SH_Y0), (0.0, 1.40), (0.012, 1.415), (0.012, 1.435),
           (0.0, 1.45), (0.0, SH_Y1), (0.0, DOOR_H), (0.0, 3.05), (0.012, 3.065), (0.012, 3.085), (0.0, 3.10),
           (0.0, 4.24), (-0.07, 4.30), (-0.14, 4.40), (-0.14, H)]


def phi_of(x, z):
    return math.degrees(math.atan2(x, -z)) % 360.0


def xc(z):
    return math.sqrt(R_IN * R_IN - z * z)


PHI_SH = (phi_of(xc(SH_Z0), SH_Z0), phi_of(xc(SH_Z1), SH_Z1))
PHI_BAY_E = (phi_of(xc(-BAY_Z), -BAY_Z), phi_of(xc(BAY_Z), BAY_Z))
PHI_BAY_W = (phi_of(-xc(BAY_Z), BAY_Z), phi_of(-xc(-BAY_Z), -BAY_Z))


def inner_path():
    """Closed inner-face polyline [(x, z)], phi increasing (clockwise from above), with the two flat door bays."""
    angles = sorted(set([5.0 * k for k in range(72)] + list(PHI_SH) + list(PHI_BAY_E) + list(PHI_BAY_W)))
    pts = []
    for a in angles:
        if PHI_BAY_E[0] + 1e-6 < a < PHI_BAY_E[1] - 1e-6 or PHI_BAY_W[0] + 1e-6 < a < PHI_BAY_W[1] - 1e-6:
            continue
        p = K.polar(R_IN, a)
        pts.append((p.x, p.z))
        if abs(a - PHI_BAY_E[0]) < 1e-6:
            pts += [(BAY_X, -BAY_Z), (BAY_X, -DOOR_Z), (BAY_X, DOOR_Z), (BAY_X, BAY_Z)]
        if abs(a - PHI_BAY_W[0]) < 1e-6:
            pts += [(-BAY_X, BAY_Z), (-BAY_X, DOOR_Z), (-BAY_X, -DOOR_Z), (-BAY_X, -BAY_Z)]
    return pts


def wall_sweep(name, path, profile, mat):
    """Sweep the open profile [(s, y)] along the closed path [(x, z)]; s > 0 goes into the wall. Faces face the room."""
    n = len(path)
    P = [Vector((x, 0.0, z)) for x, z in path]
    up = Vector((0, 1, 0))
    bm = bmesh.new()
    cols = []
    for i in range(n):
        t_in = (P[i] - P[i - 1]).normalized()
        t_out = (P[(i + 1) % n] - P[i]).normalized()
        n_in, n_out = up.cross(t_in), up.cross(t_out)
        m = (n_in + n_out)
        m = m.normalized() if m.length > 1e-6 else n_in
        k = 1.0 / max(0.25, m.dot(n_in))
        cols.append([bm.verts.new(P[i] + m * (s * k) + up * y) for (s, y) in profile])
    for i in range(n):
        a, b = cols[i], cols[(i + 1) % n]
        for r in range(len(profile) - 1):
            bm.faces.new((a[r], b[r], b[r + 1], a[r + 1]))
    return K.obj_from_bm(name, bm, mat)


def drum_wall():
    w = wall_sweep("drum", inner_path(), PROFILE, CONC)

    def opening(c, nrm):
        if abs(c.z) < DOOR_Z and c.y < DOOR_H and abs(c.x) > 3.5:
            return True
        r = math.hypot(c.x, c.z)
        ph = phi_of(c.x, c.z)
        return r > 3.5 and PHI_SH[0] < ph < PHI_SH[1] and SH_Y0 < c.y < SH_Y1
    K.delete_faces_where(w, opening)
    A.hint(w, 30.0)
    return K.part("gallery_drum", [w])


def flat_poly(name, outer, holes, y, mat, up=True):
    """Horizontal filled polygon (G-frame (x, z) loops) at height y, facing up or down."""
    if up:
        loops = [[(x, -z) for (x, z) in lp] for lp in [outer] + holes]
        o = L.flat_shape(name, loops, mat=mat)
        o.data.transform(Matrix.Translation((0, y, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    else:
        loops = [[(x, z) for (x, z) in lp] for lp in [outer] + holes]
        o = L.flat_shape(name, loops, mat=mat)
        o.data.transform(Matrix.Translation((0, y, 0)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    return o


def circle_xz(r, n):
    return [(K.polar(r, 360.0 * k / n).x, K.polar(r, 360.0 * k / n).z) for k in range(n)]


def floor():
    o = flat_poly("floor", inner_path(), [circle_xz(1.62, 64)], 0.0, STONE, up=True)
    return K.part("gallery_floor", [o])


def ceiling():
    parts = [flat_poly("ceil", inner_path(), [], H, CONC, up=False)]
    # ring beam over the shaft
    beam = K.revolve("beam", [(1.45, H), (1.45, 4.12), (1.75, 4.12), (1.75, H)], 0.0, 360.0, 48, CONC)
    K._orient(beam, inward=False)
    bm = bmesh.new()
    bm.from_mesh(beam.data)
    for f in bm.faces:          # inner face looks at the axis, bottom looks down, outer face looks out
        c = f.calc_center_median()
        r = math.hypot(c.x, c.z)
        want = Vector((-c.x, 0, -c.z)).normalized() if r < 1.47 else (Vector((0, -1, 0)) if abs(c.y - 4.12) < 1e-4 else Vector((c.x, 0, c.z)).normalized())
        if f.normal.dot(want) < 0:
            f.normal_flip()
    bm.to_mesh(beam.data)
    bm.free()
    A.hint(beam, 30.0)
    parts.append(beam)
    # 12 radial ribs from the ring beam to the cornice
    for k in range(12):
        a = 15.0 + 30.0 * k
        r1 = rib_end(a)
        p0, p1 = K.polar(1.74, a, 0.0), K.polar(r1, a, 0.0)
        d = p1 - p0
        rib = K.gbox("rib", (-d.length / 2, 4.20, -0.09), (d.length / 2, H, 0.09), CONC, 0.012)
        rib.data.transform(Matrix.Translation(((p0 + p1) / 2).to_3d()) @ Matrix.Rotation(-math.atan2(d.z, d.x), 4, "Y"))
        parts.append(rib)
        # corbel under the rib end
        c = K.polar(r1 - 0.12, a, 0.0)
        cb = K.gbox("corbel", (-0.12, 3.95, -0.11), (0.12, 4.20, 0.11), CONC, 0.01)
        cb.data.transform(Matrix.Translation((c.x, 0, c.z)) @ Matrix.Rotation(-math.atan2(d.z, d.x), 4, "Y"))
        parts.append(cb)
    return K.part("gallery_ceiling", parts)


def rib_end(a):
    """Radius where a radial line at phi meets the cornice face (inner face - 0.14)."""
    p = K.polar(1.0, a)
    best = R_IN
    if abs(p.x) > 1e-6:
        r_bay = BAY_X / abs(p.x)
        z = p.z * r_bay
        if abs(z) <= BAY_Z and r_bay < best:
            best = r_bay
    return best - 0.14


def glass_floor():
    o = K.glathe("glass", [(0.0, -0.08), (1.5, -0.08), (1.5, 0.0), (0.0, 0.0)], (0, 0, 0), (0, 1, 0), 64, GLASS,
                 smooth=30.0)
    return K.part("IA_glass_floor", [o], pivot=(0.0, 0.0, 0.0))


def sconce(k, a):
    """Brass wall sconce (uplight) at phi a: back plate, arm, cup; returns (brass parts, glass, light empty pos)."""
    w = K.polar(R_IN, a)
    d = -w.normalized()                                     # into the room
    ex = Vector((0, 1, 0)).cross(d).normalized()
    mtx = Matrix(((ex.x, 0, d.x, w.x), (ex.y, 1, d.y, 0.0), (ex.z, 0, d.z, w.z), (0, 0, 0, 1)))
    y = SCONCE_Y
    parts = []
    bp = K.plate("sc_plate", [L.rounded_rect(0.13, 0.30, 0.06, 4)], 0.012, mat=BRASS, bevel=0.0)
    bp.data.transform(Matrix.Translation((0, y - 0.10, 0.0)))
    parts.append(bp)
    arm = K.V.tube("sc_arm", [(0, y - 0.18, 0.01), (0, y - 0.18, 0.12), (0, y - 0.14, 0.20), (0, y - 0.07, 0.24)], 0.013,
                   sides=6, mat=BRASS, fillet=0.04)
    parts.append(arm)
    cup = K.glathe("sc_cup", [(0.0, -0.075), (0.03, -0.075), (0.05, -0.06), (0.075, -0.03), (0.088, 0.0), (0.084, 0.006),
                              (0.072, -0.012), (0.0, -0.012)], (0, y, 0.25), (0, 1, 0), 12, BRASS, smooth=50.0)
    parts.append(cup)
    parts.append(K.glathe("sc_finial", [(0.0, 0.0), (0.014, 0.0), (0.008, -0.03), (0.0, -0.04)], (0, y - 0.075, 0.25),
                          (0, 1, 0), 8, BRASS, smooth=60.0))
    for o in parts:
        o.data.transform(mtx)
    gl = K.glathe("sc_glass", [(0.0, -0.01), (0.068, -0.01), (0.074, 0.10), (0.066, 0.165), (0.0, 0.165)], (0, y, 0.25),
                  (0, 1, 0), 16, GLASS, smooth=50.0)
    gl.data.transform(mtx)
    bulb = mtx @ Vector((0, y + 0.06, 0.25))
    return parts, K.part(f"lamp_glass_{k}", [gl], pivot=tuple(bulb)), bulb


def shutter_frame():
    """Brass frame around the shutter tunnel's Gallery mouth (on the drum face) + threshold plate."""
    out = []
    r = R_IN - 0.012
    da = math.degrees(0.07 / R_IN)
    a0, a1 = PHI_SH
    out.append(K.ring_wall("sf_l", r, SH_Y0 - 0.07, SH_Y1 + 0.07, a0 - da, a0, 1, BRASS))
    out.append(K.ring_wall("sf_r", r, SH_Y0 - 0.07, SH_Y1 + 0.07, a1, a1 + da, 1, BRASS))
    out.append(K.ring_wall("sf_t", r, SH_Y1, SH_Y1 + 0.07, a0, a1, 6, BRASS))
    out.append(K.ring_wall("sf_b", r, SH_Y0 - 0.07, SH_Y0, a0, a1, 6, BRASS))
    # threshold plate on the tunnel floor at the mouth
    pts = [(xc(z), z) for z in [SH_Z0 + (SH_Z1 - SH_Z0) * t / 6 for t in range(7)]]
    inner = [(x + 0.10, z) for (x, z) in reversed(pts)]
    out.append(flat_poly("sf_sill", pts + inner, [], SH_Y0 + 0.004, BRASS, up=True))
    return out


def rim_and_brass():
    parts = []
    rim = K.revolve("rim", [(1.49, -0.11), (1.49, -0.082), (1.50, -0.082), (1.50, 0.0), (1.506, 0.006), (1.614, 0.006),
                            (1.62, 0.0), (1.62, -0.11)], 0.0, 360.0, 64, BRASS)
    A.hint(rim, 40.0)
    parts.append(rim)
    for k in range(24):
        p = K.polar(1.56, 7.5 + 15.0 * k, 0.006)
        parts.append(K.rivet("rimrv", 0.012, tuple(p), normal=(0, 1, 0), mat=BRASS, segs=5))
    for r in (2.4, 3.6):
        parts.append(flat_poly("inlay", circle_xz(r + 0.02, 96), [circle_xz(r - 0.02, 96)], 0.0015, BRASS, up=True))
    parts.append(flat_poly("beamband", circle_xz(1.68, 48), [circle_xz(1.52, 48)], 4.119, BRASS, up=False))
    parts += shutter_frame()
    return parts


def rail():
    parts = []
    top = M.torus("rail", RAIL_R, 0.025, major_seg=56, minor_seg=8, mat=BRASS)
    top.data.transform(Matrix.Translation((0, RAIL_TOP - 0.025, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    low = M.torus("rail2", RAIL_R, 0.014, major_seg=56, minor_seg=6, mat=BRASS)
    low.data.transform(Matrix.Translation((0, 0.45, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    A.hint(top, 70.0)
    A.hint(low, 70.0)
    parts += [top, low]
    for k in range(12):
        p = K.polar(RAIL_R, 15.0 + 30.0 * k, 0.0)
        parts.append(K.glathe("post", [(0.06, 0.0), (0.06, 0.012), (0.03, 0.024), (0.018, 0.06), (0.018, 0.975)],
                              (p.x, 0.0, p.z), (0, 1, 0), 8, BRASS, smooth=50.0, cap_bottom=False, cap_top=False))
    return K.part("gallery_rail", parts)


def tunnel_lining():
    zs = [SH_Z0 + (SH_Z1 - SH_Z0) * t / 6 for t in range(7)]
    arc = [(xc(z), z) for z in zs]
    poly = arc + [(CAMP_X, SH_Z1), (CAMP_X, SH_Z0)]
    parts = [flat_poly("tfloor", poly, [], SH_Y0, CONC, up=True), flat_poly("tceil", poly, [], SH_Y1, CONC, up=False)]
    x0 = xc(SH_Z0)
    parts.append(K.quad("twall_n", ((x0 + CAMP_X) / 2, (SH_Y0 + SH_Y1) / 2, SH_Z0), (1, 0, 0), (0, 1, 0), CAMP_X - x0,
                        SH_Y1 - SH_Y0, CONC))                       # faces +Z (into the tunnel)
    x1 = xc(SH_Z1)
    parts.append(K.quad("twall_s", ((x1 + CAMP_X) / 2, (SH_Y0 + SH_Y1) / 2, SH_Z1), (-1, 0, 0), (0, 1, 0), CAMP_X - x1,
                        SH_Y1 - SH_Y0, CONC))                       # faces -Z
    # board-form lift lines (shallow ribs) along the tunnel walls
    for y in (0.90, 1.50):
        parts.append(K.gbox("tlift", (x0, y - 0.01, SH_Z0), (CAMP_X, y + 0.01, SH_Z0 + 0.008), CONC, 0.0))
        parts.append(K.gbox("tlift", (x1, y - 0.01, SH_Z1 - 0.008), (CAMP_X, y + 0.01, SH_Z1), CONC, 0.0))
    return K.part("IA_tunnel_shutter", parts, pivot=(4.0, SH_Y0, (SH_Z0 + SH_Z1) / 2))


def build():
    M.reset_scene()
    K.ensure_materials()
    out = dict(drum=drum_wall(), ceiling=ceiling(), floor=floor(), glass=glass_floor(), rail=rail(),
               tunnel=tunnel_lining())
    brass = rim_and_brass()
    lamps, bulbs = [], []
    for k, a in enumerate(SCONCES):
        bp, gl, bulb = sconce(k, a)
        brass += bp
        lamps.append(gl)
        bulbs.append(bulb)
    out["rim"] = K.part("glass_rim", brass)
    out["lamps"] = lamps
    for k, b in enumerate(bulbs):
        K.empty(f"light_gallery_{k}", tuple(b))
    K.empty("echo_rail_mount", (-2.05, 0.0, -0.40), (0, 79, 0))
    K.empty("echo_strand_mount", (-2.30, 0.0, 1.00), (0, 40, 0))
    K.empty("echo_leyla_mount", (2.30, 0.0, 1.00), (0, -40, 0))
    K.empty("portal_w_g", (-4.45, 1.2, 0.0), (0, -90, 0))
    K.empty("portal_e_g", (4.45, 1.2, 0.0), (0, 90, 0))
    K.empty("portal_shutter_g", (4.40, 1.2, -2.6), (0, 90, 0))
    K.to_blender()
    A.finalize_uv()
    return out


def verify(path):
    mounts = {"echo_rail_mount": ((-2.05, 0, -0.40), (0, 79, 0)), "echo_strand_mount": ((-2.30, 0, 1.00), (0, 40, 0)),
              "echo_leyla_mount": ((2.30, 0, 1.00), (0, -40, 0)), "portal_w_g": ((-4.45, 1.2, 0), (0, -90, 0)),
              "portal_e_g": ((4.45, 1.2, 0), (0, 90, 0)), "portal_shutter_g": ((4.40, 1.2, -2.6), (0, 90, 0))}
    meshes = ["gallery_floor", "IA_glass_floor", "glass_rim", "gallery_rail", "gallery_drum", "gallery_ceiling",
              "IA_tunnel_shutter"] + [f"lamp_glass_{k}" for k in range(5)]
    req = meshes + list(mounts) + [f"light_gallery_{k}" for k in range(5)]
    expect = {k: v[0] for k, v in mounts.items()}
    expect["IA_glass_floor"] = (0, 0, 0)
    for k, a in enumerate(SCONCES):
        p = K.polar(R_IN, a)
        print(f"{K.TAG} sconce {k} phi {a}: wall point ({p.x:+.3f}, {SCONCE_Y}, {p.z:+.3f})")
    errs = K.V.verify_glb(path, required=req, identity=meshes + [f"light_gallery_{k}" for k in range(5)], expect=expect,
                          rot_expect={k: v[1] for k, v in mounts.items()}, show=req)
    errs += K.facts(path, TRI_BUDGET, 12)
    print(f"{K.TAG} shutter mouth phi {PHI_SH[0]:.2f}..{PHI_SH[1]:.2f}, east bay phi {PHI_BAY_E[0]:.2f}..{PHI_BAY_E[1]:.2f}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    K.qa_begin(bounces=6)
    K.qa_import("blast_door", (-3.70, 0, 0), 90.0, prefix="qa_dw_")
    K.qa_import("blast_door", (3.70, 0, 0), -90.0, prefix="qa_de_")
    arr = K.qa_import("array_below", (0, 0, 0), 0.0, prefix="qa_ar_")
    from lib_ch3_symbols import DECAL_FILE, DRUM_ORDER, DECALS3
    target = [1, 3, 2, 4]
    for o in list(bpy.data.objects):
        if o.name.startswith("qa_ar_ring_sym_"):
            i = int(o.name.split("_")[-1].split(".")[0])
            K.override(o, K.image_emitter(f"qa_sym_{i}", os.path.join(DECALS3, DECAL_FILE[DRUM_ORDER[target[i]]]), 6.0,
                                          (0.85, 0.98, 1.0)))
        elif o.name.startswith("qa_ar_ring_") and o.type == "MESH":
            K.override(o, K.glow("qa_lumen_dorm", "7FC8D8", 1.1))
        elif o.name.startswith(("qa_dw_drum_lamp", "qa_de_drum_lamp")):
            K.override(o, K.glow("qa_lamp_amber", "FFA030", 5.0))
    glass = parts["glass"]
    glass.visible_shadow = False                     # Godot: glass casts no shadow; let the Array light come up
    lamp_glow = K.glow("qa_sconce", "FFD9A0", 5.0)
    for gl in parts["lamps"]:
        K.override(gl, lamp_glow)

    def lights(cam=None):
        K.clear_lights()
        K.light("key_gallery", "SPOT", (0.0, 4.4, 2.2), 900.0, "D6E6F2", radius=0.2, target=(0.0, 0.0, -1.4), spot_deg=60)
        K.light("array_up", "SPOT", (0.0, -6.0, 0.0), 9000.0, "CFF6FF", radius=1.2, target=(0.0, 5.0, 0.0), spot_deg=40)
        sg = K.light("shaft_glow", "AREA", (0.0, -0.4, 0.0), 160.0, "CFF6FF", radius=2.6, target=(0.0, 5.0, 0.0))
        sg.visible_camera = sg.visible_glossy = sg.visible_transmission = False
        for k in (0, 3):
            p = bpy.data.objects[f"light_gallery_{k}"].matrix_world.translation
            K.light(f"sconce_{k}", "POINT", (p.x, p.z, -p.y), 70.0, "FFCF94", radius=0.06)
        for k in (1, 2, 4):
            p = bpy.data.objects[f"light_gallery_{k}"].matrix_world.translation
            K.light(f"sconce_{k}", "POINT", (p.x, p.z, -p.y), 25.0, "FFCF94", radius=0.06)
        if cam:
            K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), 10.0, "FFE2C2", radius=0.2)

    if K.want(args, "1"):    # 'gallery' root view
        lights()
        K.shoot(NAME, (-2.7, 1.65, 2.2), (1.8, 1.0, -2.2), vfov=62)
    if K.want(args, "2"):    # 'gallery_w' root view
        lights()
        K.shoot(NAME + "_2", (2.7, 1.65, 2.2), (-1.8, 1.0, -2.2), vfov=62)
    if K.want(args, "3"):    # 'glass_floor' view: the Array 30 m below through the glass
        lights((0.0, 1.55, 1.1))
        K.shoot(NAME + "_3", (0.0, 1.55, 1.1), (0.0, -30.0, -0.6), vfov=32)
    if K.want(args, "4"):    # hero: high three-quarter over the shaft
        lights()
        K.shoot(NAME + "_4", (2.3, 3.5, 2.5), (-0.7, 0.5, -0.9), vfov=66)
    if K.want(args, "5"):    # 'finale' view (console absent: group F)
        lights()
        K.shoot(NAME + "_5", (0.0, 1.85, 3.75), (0.0, 1.15, 0.4), vfov=66)
    if K.want(args, "6"):    # 'blast_east' view
        lights((1.95, 1.6, -0.7))
        K.shoot(NAME + "_6", (1.95, 1.6, -0.7), (3.7, 1.3, 0.0), vfov=56)
    if K.want(args, "7"):    # 'secret' view toward the shutter mouth / memorial corner
        lights((0.6, 1.5, -1.8))
        K.shoot(NAME + "_7", (0.6, 1.5, -1.8), (2.6, 1.2, -2.6), vfov=52)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = K.export(NAME)
    errs = verify(path)
    print(f"{K.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(parts, args)


main()
