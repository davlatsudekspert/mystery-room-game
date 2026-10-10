"""MYSTERY ROOM — Chapter 4 helpers (the Array Hall). Contract: docs/models/ch4.md; measured results:
docs/models/ch4_<group>.md.

Builds on lib_ch3_a (K), lib_ch3_d (D), lib_ch3_bc (B), lib_ch3_ef (E) and the older libraries (never edits them).
G-FRAME as in Chapter 3: every script builds in Godot axes inside Blender (x, y, z = Godot x, y, z), then calls
`to_blender()` before parenting and export.

  constants          the hall's fixed numbers (radii, deck height, the bay, the mark azimuths)
  polar / yaw_mesh   polar placement (azimuth from north, clockwise seen from above) and rotating mesh data
  orient             make the faces of an open surface look toward / away from a point
  arc_strip          a wall / strip following a polyline of (x, z) points
  ensure_materials   every slot Chapter 4 uses
  VIEWS / view       the camera proposals of docs/models/ch4.md section 2
  qa_hall / lights   QA scene: the hall shell + the neighbouring GLBs, the hall's lights, Godot-FOV cameras
"""
from __future__ import annotations

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
import lib_ch3_d as D  # noqa: E402
import lib_ch3_ef as E  # noqa: E402
import lib_ch3_symbols as S  # noqa: E402
import lib_ch4_numerals as N  # noqa: E402

K.QA_SUB = "ch4"
TAG = "[ch4]"
ROOT = M.ROOT
PREVIEW_DIR = os.path.join(ROOT, "qa", "blender", "ch4", "preview")

# ---------------------------------------------------------------------- materials (library slots only)
CONC, GREEN, STEEL, BRASS = "M_Concrete", "M_Paint_Green", "M_Steel_Dark", "M_Brass_Aged"
PAINT, CHEQ, CHROME, GLASS = "M_Steel_Painted", "M_Chequer", "M_Chrome", "M_Glass"
GDARK, FROST, BAKE, CREAM = "M_Glass_Dark", "M_Glass_Frosted", "M_Bakelite", "M_Enamel_Cream"
VELVET, CRYSTAL, LUMEN, CHALK = "M_Velvet", "M_Crystal", "M_Emissive_Lumen", "M_Chalk"
BRASS_P, SHQ, WALNUT, PAPER = "M_Brass_Polished", "M_Shader_Quad", "M_Wood_Walnut", "M_Paper"

# ---------------------------------------------------------------------- the hall's numbers (ch4.md section 1)
R_HALL = 14.0
WALL_TOP = 7.0
VAULT_APEX = 12.0
OCULUS_R = 1.5
SHAFT_TOP = 14.6
RING_R = (10.5, 8.5, 6.5, 4.5)
DECK_Y = 2.5
BRIDGE_X = 5.9
BRIDGE_Z0, BRIDGE_Z1 = 11.95, 14.8
RAIL_Z = 11.95
PIER_Z = 14.0
BAY_X = 6.0
BAY_BACK = 18.2
BAY_CEIL = 6.2
LIFT_POS = (0.0, 0.0, 16.4)
ISLAND_Y = 2.5
ISLAND_R = 3.0
BEAM_Y = 1.8
CORE_C = (0.0, 4.1, 0.0)
APSE_R = 3.6
APSE_H = 4.6
APSE_CX = -math.sqrt(R_HALL ** 2 - APSE_R ** 2)       # -13.53: where the niche meets the hall circle
BAY_PHI = (180.0 - math.degrees(math.asin(BAY_X / R_HALL)), 180.0 + math.degrees(math.asin(BAY_X / R_HALL)))
APSE_PHI = (270.0 - math.degrees(math.asin(APSE_R / R_HALL)), 270.0 + math.degrees(math.asin(APSE_R / R_HALL)))
MARK_PHI = [180.0 + 45.0 * p for p in range(8)]       # mark p + 1


def ensure_materials() -> None:
    K.ensure_materials()
    D.ensure_materials()
    M.material(CHALK, color="ECE6D6", rough=1.0)
    for n in (CONC, GREEN, STEEL, BRASS, PAINT, CHEQ, CHROME, GLASS, GDARK, FROST, BAKE, CREAM, VELVET, CRYSTAL, LUMEN,
              CHALK, BRASS_P, SHQ, WALNUT, PAPER):
        M.material(n)


# ---------------------------------------------------------------------- geometry helpers (G-frame)
polar = K.polar


def dome_centre_y() -> float:
    """Centre height of the sphere the vault is cut from (through (14, 7) and (1.5, 12))."""
    return (R_HALL ** 2 + WALL_TOP ** 2 - OCULUS_R ** 2 - VAULT_APEX ** 2) / (2.0 * (WALL_TOP - VAULT_APEX))


def dome_y(r: float) -> float:
    """Underside height of the vault at radius r (a spherical cap through (14, 7) and (1.5, 12))."""
    yc = dome_centre_y()
    rr = math.sqrt(R_HALL ** 2 + (WALL_TOP - yc) ** 2)
    return yc + math.sqrt(max(rr * rr - r * r, 0.0))


def yaw_mesh(obj, deg: float, pivot=(0.0, 0.0, 0.0)) -> None:
    """Rotate mesh DATA about +Y through `pivot` by deg (counter-clockwise seen from above, the Godot sign)."""
    m = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(deg), 4, "Y") @ Matrix.Translation(-Vector(pivot))
    obj.data.transform(m)


def at_azimuth(obj, phi: float, r: float, y: float = 0.0) -> None:
    """Move a mesh built at the origin, its front (+Z) toward the SOUTH, onto azimuth phi (degrees from north,
    clockwise seen from above) at radius r, its front pointing OUTWARD (a south mesh already points outward)."""
    yaw_mesh(obj, -(phi - 180.0))
    obj.data.transform(Matrix.Translation(polar(r, phi, y)))


def orient(obj, pt, toward: bool = True) -> None:
    """Flip the faces of an open surface so every normal looks toward (or away from) the point pt."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    p = Vector(pt)
    for f in bm.faces:
        d = p - f.calc_center_median()
        if (f.normal.dot(d) > 0.0) != toward:
            f.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()


def arc_strip(name, pts_xz, y0, y1, mat, inside_pt=None, toward=True):
    """A vertical strip along a polyline of (x, z) points between heights y0 and y1."""
    bm = bmesh.new()
    lo = [bm.verts.new((x, y0, z)) for (x, z) in pts_xz]
    hi = [bm.verts.new((x, y1, z)) for (x, z) in pts_xz]
    for i in range(len(pts_xz) - 1):
        bm.faces.new((lo[i], lo[i + 1], hi[i + 1], hi[i]))
    o = K.obj_from_bm(name, bm, mat)
    if inside_pt is not None:
        orient(o, inside_pt, toward)
    return o


def smooth(objs, angle: float = 40.0) -> None:
    for o in objs:
        if o is not None and o.type == "MESH":
            M.smooth(o, angle)


def merge(name, objs, smooth_angle: float = 40.0):
    objs = [o for o in objs if o is not None]
    o = K.merge(name, objs)
    M.smooth(o, smooth_angle)
    return o


def finalize(objs=None) -> None:
    D.finalize(objs)


def export(name: str) -> str:
    return K.export(name)


def verify(path, required=(), identity=(), expect=None, parents=None, rot_expect=None, tri_budget=0, surf_budget=0,
           mat_budget=4):
    return D.verify(path, required=required, identity=identity, expect=expect, parents=parents, rot_expect=rot_expect,
                    tri_budget=tri_budget, surf_budget=surf_budget, mat_budget=mat_budget)


def bounds(names):
    return D.bounds(names)


def report(label):
    return K.report(label)


# ---------------------------------------------------------------------- views (ch4.md section 2)
VIEWS = {
    "lift": ((1.55, 1.6, 16.5), (5.0, 2.2, 12.5), 64),
    "bay_hero": ((0.0, 1.7, 7.5), (0.0, 2.6, 15.5), 60),
    "lift_chalk": ((-2.9, 1.55, 15.4), (-3.0, 1.5, 18.18), 46),
    "bridge": ((0.0, 4.4, 14.6), (0.0, 3.4, 0.0), 66),
    "desk": ((0.0, 4.35, 14.5), (0.0, 3.5, 13.1), 58),
    "chronometer": ((0.0, 4.5, 14.3), (0.0, 3.75, 13.2), 40),
    "handwheels": ((0.0, 4.9, 15.2), (0.0, 3.3, 9.0), 84),
    "panel0": ((0.0, 1.15, 12.3), (0.0, 1.15, 14.0), 66),
    "catwalk": ((0.0, 3.9, 11.6), (0.0, 3.0, 3.0), 64),
    "island": ((0.0, 3.8, 5.6), (0.0, 3.2, 0.0), 64),
    "apse": ((-5.5, 1.7, 0.3), (-12.5, 1.8, 0.0), 62),
    "booth": ((0.0, 1.7, -6.5), (0.0, 3.2, -13.0), 62),
    "watch": ((6.5, 1.7, 0.0), (12.7, 1.5, 0.0), 64),
}


def view(name):
    return VIEWS[name]


def hatch_view(n: int):
    z = RING_R[n - 1]
    return ((0.0, 3.35, z + 0.55), (0.0, 0.65, z - 0.05), 50)


# ---------------------------------------------------------------------- QA scene
def qa_begin() -> None:
    D.qa_begin()


def qa_import(name, pos=(0, 0, 0), yaw=0.0, prefix=None):
    prefix = prefix or f"qa_{name}_"
    if not os.path.exists(K.V.model_glb(name)):
        return None
    return K.qa_import(name, pos, yaw, prefix=prefix)


def qa_floor_nonormal(prefix: str) -> None:
    """QA only: a huge tiled floor seen at a grazing angle goes black under the preview stone normal map in Cycles; give
    the floor a copy of its material without the normal map (the game uses its own .tres)."""
    for o in bpy.data.objects:
        if o.name.startswith(prefix) and o.type == "MESH":
            for slot in o.material_slots:
                m = slot.material.copy()
                for lk in list(m.node_tree.links):
                    if lk.to_socket.name == "Normal":
                        m.node_tree.links.remove(lk)
                slot.material = m


def glow_lamps(prefix: str, colour="FFD9A0", strength=6.0) -> None:
    for o in bpy.data.objects:
        if o.name.startswith(prefix) and "lamp" in o.name:
            K.override(o, K.glow("qa_lampglow", colour, strength))


def qa_hall(extra=(), shell=True):
    """Import the hall shell and the neighbouring GLBs: extra = [(name, pos, yaw)]."""
    if shell:
        qa_import("shell_hall", prefix="qa_sh_")
    for item in extra:
        name, pos, yaw = item[0], item[1], item[2]
        qa_import(name, pos, yaw, prefix=f"qa_{name}_")


def lights(cam=None, fill=40.0, shaft=True, core=True, work=True, bridge_lamp=False, ambient=1.0):
    """The hall's section 1.5 lights as QA lights (and a camera-following fill)."""
    K.clear_lights()
    if shaft:
        K.light("key_shaft", "SPOT", (0.0, 12.4, 0.0), 90000.0 * ambient, "BFD8FF", radius=0.6, target=(0.0, 0.0, 0.0),
                spot_deg=20, blend=0.5)
    if core:
        K.light("core_glow", "POINT", CORE_C, 60000.0 * ambient, "CFF6FF", radius=0.5)
    if work:
        for k, r in enumerate(RING_R):
            K.light(f"work_{k + 1}", "POINT", (0.0, 5.5, -r), 9000.0 * ambient, "FFB46B", radius=0.15)
    if bridge_lamp:
        K.light("bridge_lamp", "SPOT", (0.0, 5.9, 13.5), 900.0 * ambient, "FFC98A", radius=0.1, target=(0.0, 3.5, 13.1),
                spot_deg=60)
    if cam is not None and fill > 0:
        K.light("fill", "POINT", (cam[0] + 0.12, cam[1] + 0.18, cam[2] + 0.05), fill, "FFE2C2", radius=0.2)


def rot_about(obj, axis_godot, deg: float) -> None:
    """QA pose: turn a placed part about an arbitrary Godot axis through its own origin (its parent has no rotation)."""
    a = K.V.C @ Vector(axis_godot).normalized()
    p = obj.matrix_basis.translation.copy()
    obj.matrix_basis = Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, a) @ Matrix.Translation(-p) @ obj.matrix_basis
    M.refresh()


def shoot(name, cam, target, vfov, samples=32, res=(960, 640), world=0.03):
    return K.shoot(name, cam, target, vfov, res=res, samples=samples, world=world)


def want(args, tag):
    return K.want(args, tag)
