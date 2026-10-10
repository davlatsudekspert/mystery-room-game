"""Light echoes: the eight named foreground staff of the Night replay (Chapter 4 group I; docs/models/ch4.md section 9).

Eight DISTINCT silhouettes, each in three poses = 24 root-level closed meshes (M_Echo), origin on the floor between the
feet, facing Godot +Z. The staff are the 1979 people of Chapters 2 - 4 (the scientists, the technicians, the operator,
the welder, the archivist, the watch-room clerk). The room puts them at the eight ring positions nearest the catwalk and
draws the pose of the replay minute (the node name ends in the pose: `_a`, `_b`, `_c`).

Output: game/assets/models/echo_named.glb
  <who>_a   at work (the early minutes)           <who> = operator, welder, archivist, scientist_f, scientist_m,
  <who>_b   the next task (the middle minutes)            technician_f, technician_m, clerk
  <who>_c   03:17: shielding the eyes from the flash (the frozen minute)
Budget: <= 1,200 triangles per mesh (eight figures x three poses), <= 29,000 per file.

Run: blender -b --factory-startup -P tools/blender/models/echo_named.py [-- --no-render] [-- --only operator,clerk]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import lib_ch4_echo as C  # noqa: E402
from lib_ch4_echo import E, H, L, R, mrlib  # noqa: E402

NAME = "echo_named"
ARGS = mrlib.main_guard()
RENDER = "--no-render" not in ARGS
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
POSE_BUDGET, FILE_BUDGET = 1200, 29000
VOXEL = 0.0115


# ------------------------------------------------------------------ props (closed shells in build space)
def box(c, size, rot=(0.0, 0.0, 0.0), bevel=0.005):
    """A rounded box; c may be a callable(ctx) -> point. rot = Euler degrees about X, Y, Z (applied Z, Y, X)."""
    def make(ctx):
        cc = c(ctx) if callable(c) else c
        rm = Matrix.Rotation(math.radians(rot[2]), 3, "Z") @ Matrix.Rotation(math.radians(rot[1]), 3, "Y") @ \
            Matrix.Rotation(math.radians(rot[0]), 3, "X")
        return [L.rounded_box("prop_box", size, cc, rm, bevel=bevel, segments=1)]
    return make


def rod(a, b, r=0.016, r1=None):
    """A thin round shaft between two points (a tool, a pen); a, b may be callables(ctx)."""
    def make(ctx):
        pa = a(ctx) if callable(a) else a
        pb = b(ctx) if callable(b) else b
        return [E.limb("prop_rod", pa, pb, [r, r1 or r], seg=8, cap0=0.6, cap1=0.6)]
    return make


def at_wrist(side, off):
    """A point relative to a wrist (build axes)."""
    return lambda ctx: ctx["wr"][side] + Vector(off)


# ------------------------------------------------------------------ the shared 03:17 pose
def flash(zn, side=1, both=False, turn=-34.0, box_c=None, box_size=None):
    """Shielding the eyes: a forearm (or both) raised across the face, torso turned away, weight thrown back."""
    eye = zn + 0.135
    s = side
    w = {s: R(s * 0.070, 0.205, eye), -s: R(-s * 0.400, 0.060, zn - 0.45)}
    h = {s: (s * 0.60, 0.10, 0.25), -s: (-s * 0.40, -0.40, -0.20)}
    if both:
        w = {s: R(s * 0.055, 0.215, eye - 0.02), -s: R(-s * 0.070, 0.225, eye - 0.07)}
        h = {s: (s * 0.55, 0.10, 0.20), -s: (-s * 0.55, 0.10, 0.10)}
    return C.pose(hip_xy=(0.0, -0.040), neck_xy=(0.0, -0.040), yaw_hip=-turn * 0.3, yaw_chest=turn * s,
                  feet={1: (0.11, -0.150 if s == 1 else 0.100, -12.0), -1: (-0.10, 0.100 if s == 1 else -0.150, 18.0)},
                  wrist=w, hint=h, head=(turn * 0.8 * s, -8.0, 0.0), tilt=-4.0)


# ------------------------------------------------------------------ the eight figures
def fig_operator():
    zn = 1.52
    S = C.spec(z_hip=0.95, z_neck=zn, w=1.02, d=1.02, grow=0.010, hair="short", head=1.04, gear=("cap", "headphones"),
               hand=1.0, leg=(0.074, 0.058, 0.050), shoe=1.05)
    a = C.pose(neck_xy=(0.0, 0.012), yaw_chest=-8.0, head=(34.0, 24.0, 0.0), tilt=6.0,
               feet={1: (0.10, 0.02, -10.0), -1: (-0.11, -0.05, 12.0)},
               wrist={1: R(0.215, 0.080, 0.830), -1: None}, hint={1: (0.4, -0.55, -0.1)})
    b = C.pose(neck_xy=(0.0, 0.120), yaw_chest=6.0, head=(0.0, -14.0, 0.0), tilt=16.0, hip_xy=(0.0, -0.05),
               feet={1: (0.10, -0.05, -6.0), -1: (-0.11, 0.00, 10.0)},
               wrist={1: R(0.150, 0.470, 1.100), -1: R(-0.240, 0.300, 0.940)},
               hint={1: (0.35, -0.2, -0.45), -1: (-0.4, -0.2, -0.45)},
               props=[rod(lambda c: c["wr"][1] + Vector((0, 0.02, -0.02)), lambda c: c["wr"][1] + Vector((0.01, 0.17, 0.20)),
                          r=0.016)])
    return S, dict(a=a, b=b, c=flash(zn, 1, both=True, turn=-30.0))


def fig_welder():
    zn = 1.44
    S = C.spec(z_hip=0.90, z_neck=zn, w=1.16, d=1.12, grow=0.020, hem_dz=-0.30, hair="cropped", head=1.04,
               gear=("mask",), hand=1.28, boot=True, leg=(0.084, 0.066, 0.058), shoe=1.16, sleeve=(0.056, 0.052, 0.046))
    a = C.pose(neck_xy=(0.0, 0.020), yaw_chest=10.0, head=(-12.0, -8.0, 0.0), tilt=10.0,
               feet={1: (0.14, 0.02, -14.0), -1: (-0.14, -0.04, 14.0)},
               wrist={1: R(0.240, 0.210, 0.860), -1: R(-0.250, 0.060, 0.940)},
               hint={1: (0.5, -0.2, -0.4), -1: (-0.6, -0.1, 0.0)},
               props=[rod(lambda c: c["wr"][1] + Vector((0, -0.05, 0.04)), lambda c: c["wr"][1] + Vector((0.02, 0.33, -0.16)),
                          r=0.022, r1=0.014)])
    b = C.pose(neck_xy=(0.0, 0.015), yaw_chest=-6.0, head=(0.0, 6.0, 0.0), tilt=4.0,
               feet={1: (0.14, 0.0, -12.0), -1: (-0.14, 0.02, 12.0)},
               wrist={1: R(0.130, 0.190, 1.640), -1: R(-0.260, 0.080, 0.900)},
               hint={1: (0.75, 0.0, 0.25), -1: (-0.5, -0.3, -0.2)})
    return S, dict(a=a, b=b, c=flash(zn, -1, both=False, turn=-32.0))


def fig_archivist():
    zn = 1.40
    S = C.spec(z_hip=0.88, z_neck=zn, w=0.93, d=0.96, grow=0.004, hair="receding", head=1.02, gear=("glasses",),
               long_hem=(0.380, 0.220, 0.218, 0.160, 0.155, 2.2, 0.010, 0.020), hand=0.95,
               leg=(0.066, 0.052, 0.044), shoe=0.98, sleeve=(0.046, 0.042, 0.038))
    book = box(R(0.0, 0.250, 1.020), (0.22, 0.034, 0.30), (-10.0, 0.0, 0.0))
    a = C.pose(hip_xy=(0.0, -0.06), neck_xy=(0.0, 0.150), yaw_chest=0.0, head=(8.0, -34.0, 0.0), tilt=22.0,
               feet={1: (0.09, 0.0, -8.0), -1: (-0.10, 0.02, 10.0)},
               wrist={1: R(0.130, 0.230, 1.010), -1: R(-0.130, 0.230, 0.990)},
               hint={1: (0.4, -0.3, -0.4), -1: (-0.4, -0.3, -0.4)}, props=[book])
    b = C.pose(hip_xy=(0.0, -0.05), neck_xy=(0.0, 0.130), yaw_chest=8.0, head=(-6.0, -18.0, 0.0), tilt=20.0,
               feet={1: (0.09, 0.0, -6.0), -1: (-0.10, 0.03, 10.0)},
               wrist={1: R(0.100, 0.330, 1.330), -1: R(-0.150, 0.220, 0.960)},
               hint={1: (0.5, -0.15, -0.1), -1: (-0.4, -0.3, -0.4)},
               props=[box(R(0.115, 0.350, 1.370), (0.10, 0.012, 0.075), (-30.0, 0.0, 0.0), bevel=0.003)])
    c = flash(zn, 1, both=False, turn=-26.0)
    c.update(hip_xy=(0.0, -0.08), neck_xy=(0.0, 0.080), tilt=10.0)
    return S, dict(a=a, b=b, c=c)


def fig_scientist_f():
    zn = 1.43
    S = C.spec(sex="f", z_hip=0.87, z_neck=zn, w=0.95, d=0.96, hair="bob", head=1.04, hand=0.92,
               leg=(0.066, 0.052, 0.046), shoe=0.92, sleeve=(0.045, 0.041, 0.036))
    carton = box(R(0.255, 0.150, 0.960), (0.12, 0.34, 0.26), (0.0, 0.0, -8.0), bevel=0.01)
    a = C.pose(neck_xy=(0.0, 0.010), yaw_hip=14.0, yaw_chest=24.0, head=(30.0, -4.0, 0.0), tilt=6.0,
               feet={1: (0.095, -0.01, -6.0), -1: (-0.10, 0.04, 14.0)},
               wrist={1: R(0.250, 0.210, 0.930), -1: R(-0.220, 0.130, 0.800)},
               hint={1: (0.8, -0.15, -0.3), -1: (-0.4, -0.4, -0.2)}, props=[carton])
    c0 = R(0.0, 0.300, 1.190)
    b = C.pose(neck_xy=(0.0, 0.030), yaw_chest=-6.0, head=(0.0, -10.0, 0.0), tilt=10.0,
               feet={1: (0.095, 0.0, -4.0), -1: (-0.10, 0.03, 8.0)},
               wrist={1: R(0.200, 0.290, 1.180), -1: R(-0.200, 0.290, 1.180)},
               hint={1: (0.5, -0.2, -0.3), -1: (-0.5, -0.2, -0.3)},
               props=[box(c0, (0.12, 0.34, 0.26), (0.0, 0.0, 0.0), bevel=0.01)])
    c = flash(zn, -1, both=True, turn=-24.0)
    c.update(props=[box(R(0.0, 0.250, zn + 0.05), (0.34, 0.12, 0.26), (-6.0, 0.0, 0.0), bevel=0.01)],
             wrist={1: R(0.190, 0.200, zn + 0.00), -1: R(-0.190, 0.200, zn + 0.00)})
    return S, dict(a=a, b=b, c=c)


def fig_scientist_m():
    zn = 1.58
    S = C.spec(z_hip=0.98, z_neck=zn, w=0.97, d=0.97, hair="short", head=1.0, hand=1.04,
               leg=(0.072, 0.056, 0.048), shoe=1.08, sleeve=(0.049, 0.044, 0.038))
    ledger = box(R(-0.040, 0.260, 1.180), (0.30, 0.024, 0.22), (-24.0, 0.0, 0.0), bevel=0.004)
    a = C.pose(neck_xy=(0.0, 0.050), yaw_hip=-12.0, yaw_chest=-22.0, head=(-26.0, -30.0, 0.0), tilt=14.0,
               feet={1: (0.10, 0.0, -10.0), -1: (-0.11, 0.05, 12.0)},
               wrist={1: R(0.130, 0.270, 1.250), -1: R(-0.190, 0.240, 1.090)},
               hint={1: (0.4, -0.25, -0.3), -1: (-0.4, -0.3, -0.4)}, props=[ledger])
    b = C.pose(neck_xy=(0.0, 0.015), yaw_hip=6.0, yaw_chest=12.0, head=(14.0, 4.0, 0.0), tilt=6.0,
               feet={1: (0.10, 0.0, -8.0), -1: (-0.11, 0.04, 10.0)},
               wrist={1: R(0.150, 0.420, 1.290), -1: R(-0.215, 0.100, 0.900)},
               hint={1: (0.4, -0.1, -0.4), -1: (-0.5, -0.5, -0.1)})
    return S, dict(a=a, b=b, c=flash(zn, 1, both=True, turn=-28.0))


def fig_technician_f():
    zn = 1.33
    S = C.spec(sex="f", z_hip=0.81, z_neck=zn, w=0.92, d=0.94, hair="bun", head=1.05, hand=0.9,
               leg=(0.062, 0.049, 0.044), shoe=0.88, sleeve=(0.043, 0.039, 0.035))
    board = box(R(-0.010, 0.270, 1.050), (0.23, 0.020, 0.32), (-34.0, 0.0, 0.0), bevel=0.004)
    a = C.pose(neck_xy=(0.0, 0.030), yaw_chest=6.0, head=(4.0, -26.0, 0.0), tilt=12.0,
               feet={1: (0.09, -0.01, -6.0), -1: (-0.09, 0.04, 12.0)},
               wrist={1: R(0.110, 0.290, 1.020), -1: R(-0.130, 0.250, 0.960)},
               hint={1: (0.4, -0.2, -0.4), -1: (-0.4, -0.2, -0.4)}, props=[board])
    b = C.pose(neck_xy=(0.0, 0.0), yaw_chest=-10.0, head=(-12.0, 26.0, 0.0), tilt=2.0,
               feet={1: (0.09, 0.0, -8.0), -1: (-0.09, 0.03, 10.0)},
               wrist={1: R(0.200, 0.160, 1.610), -1: R(-0.190, 0.190, 0.930)},
               hint={1: (0.8, 0.0, 0.3), -1: (-0.4, -0.3, -0.4)},
               props=[box(R(-0.170, 0.215, 0.900), (0.23, 0.020, 0.32), (-8.0, 0.0, 12.0), bevel=0.004)])
    return S, dict(a=a, b=b, c=flash(zn, -1, both=False, turn=-30.0))


def fig_technician_m():
    zn = 1.43
    S = C.spec(z_hip=0.90, z_neck=zn, w=1.10, d=1.06, grow=0.004, hair="cropped", head=1.02, hand=1.1,
               leg=(0.078, 0.060, 0.050), shoe=1.08, sleeve=(0.053, 0.048, 0.042))
    a = C.pose(neck_xy=(0.0, 0.020), yaw_chest=-6.0, head=(-10.0, -6.0, 0.0), tilt=8.0,
               feet={1: (0.11, 0.0, -10.0), -1: (-0.11, 0.03, 12.0)},
               wrist={1: None, -1: R(-0.215, 0.090, 0.860)}, hint={-1: (-0.4, -0.6, -0.1)},
               props=[rod(lambda c: c["wr"][1] + Vector((0.0, 0.02, 0.05)), lambda c: c["wr"][1] + Vector((0.02, 0.02, -0.34)),
                          r=0.018)])
    b = C.pose(neck_xy=(0.0, 0.090), yaw_chest=8.0, head=(6.0, -22.0, 0.0), tilt=14.0, hip_xy=(0.0, -0.03),
               feet={1: (0.11, -0.03, -8.0), -1: (-0.11, 0.04, 10.0)},
               wrist={1: R(0.120, 0.360, 1.050), -1: R(-0.110, 0.330, 1.030)},
               hint={1: (0.4, -0.2, -0.4), -1: (-0.4, -0.2, -0.4)},
               props=[rod(lambda c: c["wr"][1] + Vector((-0.12, 0.02, 0.0)), lambda c: c["wr"][1] + Vector((0.20, 0.10, 0.10)),
                          r=0.018)])
    return S, dict(a=a, b=b, c=flash(zn, 1, both=False, turn=-32.0))


def fig_clerk():
    zn = 1.50
    S = C.spec(z_hip=0.94, z_neck=zn, w=0.88, d=0.92, hem_dz=-0.22, hair="short", head=1.0, gear=("visor",),
               hand=0.96, leg=(0.064, 0.050, 0.046), shoe=1.0, sleeve=(0.042, 0.038, 0.034))
    ledger = box(R(-0.215, 0.100, 1.120), (0.09, 0.30, 0.22), (0.0, 0.0, 0.0), bevel=0.006)
    a = C.pose(neck_xy=(0.0, 0.040), yaw_chest=6.0, head=(10.0, -12.0, 0.0), tilt=10.0,
               feet={1: (0.09, 0.0, -8.0), -1: (-0.10, 0.03, 10.0)},
               wrist={1: R(0.130, 0.280, 1.160), -1: R(-0.210, 0.110, 1.060)},
               hint={1: (0.4, -0.3, -0.3), -1: (-0.6, -0.3, -0.1)},
               props=[ledger, rod(lambda c: c["wr"][1] + Vector((0.01, 0.06, 0.0)), lambda c: c["wr"][1] + Vector((0.03, 0.16, 0.08)),
                                  r=0.009)])
    b = C.pose(neck_xy=(0.0, 0.100), yaw_chest=0.0, head=(0.0, -34.0, 0.0), tilt=20.0, hip_xy=(0.0, -0.04),
               feet={1: (0.09, -0.04, -6.0), -1: (-0.10, 0.0, 8.0)},
               wrist={1: R(0.120, 0.360, 1.020), -1: R(-0.150, 0.340, 1.000)},
               hint={1: (0.4, -0.2, -0.4), -1: (-0.4, -0.2, -0.4)},
               props=[box(R(-0.030, 0.360, 0.990), (0.30, 0.22, 0.020), (0.0, 0.0, 0.0), bevel=0.005)])
    return S, dict(a=a, b=b, c=flash(zn, -1, both=True, turn=-24.0))


FIGURES = {"operator": fig_operator, "welder": fig_welder, "archivist": fig_archivist,
           "scientist_f": fig_scientist_f, "scientist_m": fig_scientist_m, "technician_f": fig_technician_f,
           "technician_m": fig_technician_m, "clerk": fig_clerk}


# ------------------------------------------------------------------ QA
def renders(by):
    names = [n for n in FIGURES if f"{n}_a" in by]
    k = len(names)
    xs = [(i - (k - 1) / 2) * 0.95 for i in range(k)]
    for tag, suf in (("echo_named", "a"), ("echo_named_2", "c")):
        objs = [by[f"{n}_{suf}"] for n in names]
        C.ghost_row(tag, objs, xs, (0.0, -9.5, 1.45), (0.0, 0.0, 0.88), lens=34, res=(1600, 640), samples=18,
                    everything=list(by.values()))
    objs = [by[f"{n}_b"] for n in names]
    C.ghost_row("echo_named_3", objs, xs, (0.0, -9.5, 1.45), (0.0, 0.0, 0.88), lens=34, res=(1600, 640), samples=18,
                    everything=list(by.values()))


def main():
    mrlib.reset_scene()
    by = {}
    total = 0
    for who, fn in FIGURES.items():
        if ONLY and who not in ONLY:
            continue
        S, poses = fn()
        for p in ("a", "b", "c"):
            key = f"{who}_{p}"
            o, _ctx = C.lp_figure(key, S, poses[p], voxel=VOXEL, tris=POSE_BUDGET)
            H.turn(o)
            o.data.name = o.name
            by[key] = o
            rep = E.mesh_report(o)
            total += rep["tris"]
            print(f"[echo4] {key}: {rep['tris']} tris, shells {rep['shells']}, non-manifold {rep['non_manifold_edges']}, "
                  f"h {rep['bbox_max'][2]:.3f}")
    path = mrlib.export_glb(NAME)
    H.verify(path, {k: POSE_BUDGET for k in by}, file_budget=FILE_BUDGET)
    if RENDER:
        renders(by)


if __name__ == "__main__":
    main()
