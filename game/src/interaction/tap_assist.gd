class_name TapAssist
extends RefCounted
## Tap assist: a finger is about 10 mm wide, so a tap that misses a small 3D control by a few millimetres still
## means that control. The room's exact ray (RoomBase.raycast) comes first; only when it found no interactive part
## (nothing at all, or a plain surface such as a wall or the furniture a control sits on) does this look for the
## nearest interactive part whose outline on the screen lies within RADIUS_MM of the touch.
##
## Rules (all of them deterministic, there is no randomness and no state):
##   - a part the ray hit directly is never replaced: the assist only fills a gap;
##   - the part's outline is the convex hull of its collider box, projected to the screen (physical mm, from UITheme);
##   - candidates are ranked by screen distance to the outline, then by distance to the part's centre on the screen,
##     then by depth (the part nearer to the camera wins), then by scene-tree order;
##   - a part hidden behind geometry is never picked: a ray from the camera to its centre must reach it with nothing
##     in front of the part by more than OCCLUSION_TOL_M;
##   - a part whose centre lies under a HUD control (HUD.blocked_rects()) is never picked, and a touch inside such a
##     rect is not assisted (the room does not see it anyway);
##   - hidden or disabled parts (set_present(false): collision layer 0 / invisible) are ignored;
##   - the room can veto a part (the `accept` callable): RoomBase only lets a finger that is on a surface of the same
##     object (hotspot) as the part, or on a surface of no object, or on nothing, pull in that part, and only parts
##     that can be worked from the current view.
## A part that is picked answers with a hit dictionary like PhysicsDirectSpaceState3D.intersect_ray's: "collider",
## "rid", "position" (the tap ray at the depth of the part's centre, so a dial that reads where it was touched reads
## the finger) and "assisted": true.

## The finger's half-width: the reach of the assist around a touch, in millimetres on the physical screen.
const RADIUS_MM := 5.0
## Never wider than this share of the screen height, whatever dpi the platform reports.
const MAX_RADIUS_SCREEN := 0.12
## A blocker this far (or less) in front of a part counts as the surface the part sits on, not as something hiding it.
const OCCLUSION_TOL_M := 0.05
## Screen distances closer than this are a tie (px).
const TIE_PX := 0.5
## Depths closer than this are a tie (m).
const TIE_DEPTH_M := 0.005

## QA can switch the assist off to compare (qa/tap_map.gd).
static var enabled := true


## The reach in canvas px for this screen.
static func radius_px() -> float:
	var m := UITheme.metrics()
	var canvas: Vector2 = m["canvas"]
	return clampf(RADIUS_MM / float(m["mm_per_px"]), 6.0, canvas.y * MAX_RADIUS_SCREEN)


## `hit` is what the exact ray found ({} for nothing). Returns `hit` itself unless the touch should be assisted,
## else the hit dictionary of the part picked. `root` is the room (its StaticBody3D descendants with a "part" meta
## are the interactive parts), `blocked` the HUD's input-blocking rects, `radius` the reach in px (<= 0: radius_px()),
## `accept` an optional filter (body: Node, touched: Dictionary) -> bool for parts the room does not want assisted
## (`touched` is `hit`: what the finger is on, {} for nothing).
static func pick(root: Node3D, cam: Camera3D, screen: Vector2, hit: Dictionary, blocked: Array[Rect2] = [],
		radius: float = -1.0, accept: Callable = Callable()) -> Dictionary:
	if not enabled or root == null or cam == null or not cam.is_inside_tree():
		return hit
	if not hit.is_empty():
		var col: Variant = hit.get("collider")
		if col is Node and str((col as Node).get_meta("part", "")) != "":
			return hit # a direct hit on an interactive part always wins
	for r in blocked:
		if r.has_point(screen):
			return hit
	var reach := radius if radius > 0.0 else radius_px()
	var space := root.get_world_3d().direct_space_state
	var from := cam.global_position
	var best: Dictionary = {}
	var order := 0
	for n in root.find_children("*", "StaticBody3D", true, false):
		var body := n as StaticBody3D
		if body.collision_layer == 0 or not body.is_visible_in_tree():
			continue
		if str(body.get_meta("part", "")) == "":
			continue
		var box := _box(body)
		if box.is_empty():
			continue
		var xf: Transform3D = box["xform"]
		var aabb: AABB = box["aabb"]
		var centre := xf * aabb.get_center()
		if cam.is_position_behind(centre):
			continue
		var centre_px := cam.unproject_position(centre)
		var outline := _outline(cam, xf, aabb, centre_px)
		var rect := Rect2(outline[0], Vector2.ZERO)
		for p in outline:
			rect = rect.expand(p)
		if not rect.grow(reach).has_point(screen):
			continue
		var d := _distance_to_hull(screen, outline)
		if d > reach:
			continue
		var blocked_here := false
		for r in blocked:
			if r.has_point(centre_px):
				blocked_here = true
				break
		if blocked_here:
			continue
		if accept.is_valid() and not bool(accept.call(body, hit)):
			continue
		var cand := {"body": body, "d": d, "cd": screen.distance_to(centre_px), "depth": from.distance_to(centre),
			"order": order, "centre": centre, "xform": xf, "aabb": aabb}
		order += 1
		if not best.is_empty() and not _better(cand, best):
			continue
		if not _visible(space, from, cand):
			continue
		best = cand
	if best.is_empty():
		return hit
	var body := best["body"] as StaticBody3D
	var o := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var along := maxf(0.0, ((best["centre"] as Vector3) - o).dot(dir))
	return {"collider": body, "collider_id": body.get_instance_id(), "rid": body.get_rid(), "shape": 0,
		"position": o + dir * along, "normal": -dir, "assisted": true, "assist_px": best["d"]}


static func _better(a: Dictionary, b: Dictionary) -> bool:
	if absf(float(a["d"]) - float(b["d"])) > TIE_PX:
		return float(a["d"]) < float(b["d"])
	if absf(float(a["cd"]) - float(b["cd"])) > TIE_PX:
		return float(a["cd"]) < float(b["cd"])
	if absf(float(a["depth"]) - float(b["depth"])) > TIE_DEPTH_M:
		return float(a["depth"]) < float(b["depth"])
	return int(a["order"]) < int(b["order"])


## The part's collider as a local box and its transform: the box itself for a box collider, else the mesh it sits
## on (large parts have trimesh colliders), else the shape's bounds.
static func _box(body: StaticBody3D) -> Dictionary:
	for c in body.get_children():
		if not (c is CollisionShape3D):
			continue
		var cs := c as CollisionShape3D
		if cs.disabled or cs.shape == null:
			continue
		if cs.shape is BoxShape3D:
			var sz := (cs.shape as BoxShape3D).size
			return {"xform": cs.global_transform, "aabb": AABB(-sz * 0.5, sz)}
		var mi := body.get_parent() as MeshInstance3D
		if mi != null and mi.mesh != null:
			return {"xform": mi.global_transform, "aabb": mi.mesh.get_aabb()}
		var dm := cs.shape.get_debug_mesh()
		if dm != null:
			return {"xform": cs.global_transform, "aabb": dm.get_aabb()}
	return {}


## The 8 corners of the box on the screen. A corner behind the camera has no position: then the centre stands in.
static func _outline(cam: Camera3D, xf: Transform3D, aabb: AABB, centre_px: Vector2) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for k in 8:
		var wp := xf * aabb.get_endpoint(k)
		if cam.is_position_behind(wp):
			return PackedVector2Array([centre_px])
		pts.append(cam.unproject_position(wp))
	return pts


## 0 inside the outline's convex hull, else the distance to its edge (px).
static func _distance_to_hull(p: Vector2, pts: PackedVector2Array) -> float:
	if pts.size() < 3:
		return p.distance_to(pts[0])
	var hull := Geometry2D.convex_hull(pts)
	if hull.size() < 4: # a closed hull has its first point repeated: fewer than 4 entries is a line or a point
		var best := INF
		for q in pts:
			best = minf(best, p.distance_to(q))
		return best
	if Geometry2D.is_point_in_polygon(p, hull):
		return 0.0
	var dmin := INF
	for i in hull.size() - 1:
		dmin = minf(dmin, p.distance_to(Geometry2D.get_closest_point_to_segment(p, hull[i], hull[i + 1])))
	return dmin


## Is the part's centre in view? A ray from the camera to it must reach the part's own collider without meeting
## anything more than OCCLUSION_TOL_M in front of the part's nearest corner.
static func _visible(space: PhysicsDirectSpaceState3D, from: Vector3, cand: Dictionary) -> bool:
	var centre: Vector3 = cand["centre"]
	var body := cand["body"] as StaticBody3D
	var dir := (centre - from).normalized()
	var near := INF
	var xf: Transform3D = cand["xform"]
	var aabb: AABB = cand["aabb"]
	for k in 8:
		near = minf(near, (xf * aabb.get_endpoint(k) - from).dot(dir))
	var exclude: Array[RID] = []
	for i in 8:
		var q := PhysicsRayQueryParameters3D.create(from, centre + dir * 0.02)
		q.exclude = exclude
		var h := space.intersect_ray(q)
		if h.is_empty():
			return true
		if h["collider"] == body:
			return true
		if (h["position"] as Vector3 - from).dot(dir) < near - OCCLUSION_TOL_M:
			return false
		exclude.append(h["rid"]) # the surface the part sits in: look on behind it
	return true
