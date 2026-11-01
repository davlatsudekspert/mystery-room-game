class_name ArchiveUpperArt
extends RefCounted
## Pictures the upper floor draws in code (docs/CHAPTER2_EXPANSION.md N7-N10): this game's variant decides what they show,
## and none of them contains a word (the solutions are language-neutral): the load plate numerals, the roll-call slips,
## the negative strips with their edge symbols, Strand's cabinet label, the enlarger's projected image and the staff print.
## The six portraits are the cells of the roll-call atlas (the model's M_Decal_RollTags), the six symbols follow the Chapter 3
## drum order (0 sun, 1 moon, 2 star, 3 triangle, 4 circle, 5 square). Static helpers, no scene access.

const TAG_ATLAS := "res://assets/textures/decals/ch2x/roll_tags.png"
const NEG_BASE := "res://assets/textures/decals/ch2x/negatives.png"
const PAPER := Color("e6dcc0")
const INK := Color("2a2118")
const BRASS := Color("a8843c")

static var _atlas: Image
static var _cache: Dictionary = {}


static func atlas() -> Image:
	if _atlas == null:
		var tex := load(TAG_ATLAS) as Texture2D
		_atlas = tex.get_image()
		if _atlas.is_compressed():
			_atlas.decompress()
		_atlas.convert(Image.FORMAT_RGBA8)
	return _atlas


## The head and shoulders of staff member k (0..5) alone, 208 x 142.
static func portrait(k: int) -> Image:
	var a := atlas()
	var cw := a.get_width() / 3
	var ch := a.get_height() / 2
	var kk := posmod(k, 6)
	var img := Image.create(208, 142, false, Image.FORMAT_RGBA8)
	img.blit_rect(a, Rect2i((kk % 3) * cw + 24, (kk / 3) * ch + 40, 208, 142), Vector2i.ZERO)
	return img


# ---------------------------------------------------------------------- primitives
static func _poly(img: Image, pts: PackedVector2Array, col: Color) -> void:
	var lo := Vector2(1e9, 1e9)
	var hi := Vector2(-1e9, -1e9)
	for p in pts:
		lo = lo.min(p)
		hi = hi.max(p)
	for y in range(maxi(0, int(lo.y)), mini(img.get_height(), int(hi.y) + 1)):
		for x in range(maxi(0, int(lo.x)), mini(img.get_width(), int(hi.x) + 1)):
			if Geometry2D.is_point_in_polygon(Vector2(x + 0.5, y + 0.5), pts):
				img.set_pixel(x, y, col)


static func _arrow(img: Image, a: Vector2, b: Vector2, w: float, col: Color, both: bool = false) -> void:
	ArchivePump._line(img, a, b, w, col)
	var d := (b - a).normalized()
	var n := Vector2(-d.y, d.x)
	_poly(img, PackedVector2Array([b + d * w * 1.2, b - d * w * 2.2 + n * w * 2.0, b - d * w * 2.2 - n * w * 2.0]), col)
	if both:
		_poly(img, PackedVector2Array([a - d * w * 1.2, a + d * w * 2.2 + n * w * 2.0, a + d * w * 2.2 - n * w * 2.0]), col)


## One of the six symbols drawn centred on `c`, radius r, in `col`.
static func symbol(img: Image, k: int, c: Vector2, r: float, col: Color) -> void:
	match posmod(k, 6):
		0: # sun
			ArchivePump._disc(img, c, r * 0.5, col)
			for i in 8:
				var d := Vector2.from_angle(i * TAU / 8.0)
				ArchivePump._line(img, c + d * r * 0.7, c + d * r * 1.0, maxf(2.0, r * 0.16), col)
		1: # moon
			var lo := (c - Vector2(r, r)).floor().max(Vector2.ZERO)
			var hi := (c + Vector2(r, r)).ceil().min(Vector2(img.get_width() - 1, img.get_height() - 1))
			for y in range(int(lo.y), int(hi.y) + 1):
				for x in range(int(lo.x), int(hi.x) + 1):
					var p := Vector2(x, y)
					if p.distance_to(c) <= r * 0.9 and p.distance_to(c + Vector2(r * 0.42, -r * 0.12)) > r * 0.72:
						img.set_pixel(x, y, col)
		2: # star
			var pts := PackedVector2Array()
			for i in 10:
				pts.append(c + Vector2.from_angle(-PI / 2.0 + i * TAU / 10.0) * (r if i % 2 == 0 else r * 0.42))
			_poly(img, pts, col)
		3: # triangle
			_poly(img, PackedVector2Array([c + Vector2(0, -r), c + Vector2(r * 0.95, r * 0.8), c + Vector2(-r * 0.95, r * 0.8)]), col)
		4: # circle (a ring)
			ArchivePump._ring(img, c, r * 0.9, maxf(3.0, r * 0.28), col)
		5: # square
			_poly(img, PackedVector2Array([c + Vector2(-r * 0.8, -r * 0.8), c + Vector2(r * 0.8, -r * 0.8), c + Vector2(r * 0.8, r * 0.8), c + Vector2(-r * 0.8, r * 0.8)]), col)


static func _put(img: Image, src: Image, at: Vector2i, size: Vector2i) -> void:
	var s := src.duplicate() as Image
	s.resize(size.x, size.y, Image.INTERPOLATE_BILINEAR)
	img.blend_rect(s, Rect2i(Vector2i.ZERO, size), at)


# ---------------------------------------------------------------------- N7: the cage's load plate
## "LOAD n": the numeral in black on a cream plate with a small iron-weight mark (the model's plate is 0.20 x 0.10).
static func lift_plate(load: int) -> ImageTexture:
	var img := Image.create(400, 200, false, Image.FORMAT_RGBA8)
	img.fill(PAPER)
	for x in 400:
		for y in [0, 1, 2, 3, 4, 5, 196, 197, 198, 199, 192, 193, 194, 195]:
			img.set_pixel(x, y, INK)
	for y in 200:
		for x in [0, 1, 2, 3, 4, 5, 394, 395, 396, 397, 398, 399]:
			img.set_pixel(x, y, INK)
	# an iron weight (a disc with a ring) on the left, the number on the right
	ArchivePump._disc(img, Vector2(78, 108), 40.0, INK)
	ArchivePump._disc(img, Vector2(78, 108), 14.0, PAPER)
	ArchivePump._ring(img, Vector2(78, 58), 14.0, 5.0, INK)
	var text := str(load)
	var sc := 15
	var w := text.length() * 4 * sc
	var x0 := 150.0 + (230.0 - w) * 0.5 + sc * 1.5
	for i in text.length():
		ArchivePump._digit(img, Vector2(x0 + i * 4 * sc, 100.0), int(text[i]), sc, INK)
	return ImageTexture.create_from_image(img)


## The three floor pictograms of the book lift's buttons: 0 flask (floor -1), 1 book (floor 0), 2 lamp (floor +1).
static func lift_icon(k: int) -> ImageTexture:
	var key := "lift_icon_%d" % k
	if _cache.has(key):
		return _cache[key]
	var img := Image.create(96, 96, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var col := Color("f0e6c8")
	match k:
		0: # flask
			_poly(img, PackedVector2Array([Vector2(38, 12), Vector2(58, 12), Vector2(58, 36), Vector2(80, 80), Vector2(16, 80), Vector2(38, 36)]), col)
			_poly(img, PackedVector2Array([Vector2(34, 8), Vector2(62, 8), Vector2(62, 14), Vector2(34, 14)]), col)
		1: # book
			_poly(img, PackedVector2Array([Vector2(18, 16), Vector2(78, 16), Vector2(78, 80), Vector2(18, 80)]), col)
			ArchivePump._line(img, Vector2(28, 16), Vector2(28, 80), 5.0, Color("201a14"))
			ArchivePump._line(img, Vector2(40, 34), Vector2(68, 34), 4.0, Color("201a14"))
			ArchivePump._line(img, Vector2(40, 48), Vector2(68, 48), 4.0, Color("201a14"))
		_: # lamp
			ArchivePump._disc(img, Vector2(48, 38), 26.0, col)
			_poly(img, PackedVector2Array([Vector2(36, 62), Vector2(60, 62), Vector2(56, 84), Vector2(40, 84)]), col)
	var tex := ImageTexture.create_from_image(img)
	_cache[key] = tex
	return tex


# ---------------------------------------------------------------------- N8: the roll-call slips
## One slip as [type, a, b] drawn on paper: language-neutral pictograms. status: 1 true (green lamp), 0 false (red), -1 open.
static func slip_image(slip: Array, status: int = -1, w: int = 240, h: int = 170) -> Image:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(PAPER)
	for x in w:
		for y in [0, 1, h - 2, h - 1]:
			img.set_pixel(x, y, Color("b9a982"))
	for y in h:
		for x in [0, 1, w - 2, w - 1]:
			img.set_pixel(x, y, Color("b9a982"))
	var t := int(slip[0])
	var a := int(slip[1])
	var b := int(slip[2])
	var pw := Vector2i(72, 50)
	var hook_y := h - 30.0
	var hooks: Array[Vector2] = []
	for i in 6:
		hooks.append(Vector2(34.0 + i * (w - 68.0) / 5.0, hook_y))
	match t:
		ArchiveExpData.SLIP_END_L, ArchiveExpData.SLIP_END_R, ArchiveExpData.SLIP_NOT_END:
			var pc := Vector2(w / 2.0, 52.0)
			_put(img, portrait(a), Vector2i(int(pc.x) - pw.x / 2, int(pc.y) - pw.y / 2), pw)
			for i in 6:
				ArchivePump._disc(img, hooks[i], 7.0, Color("8a7a58"))
			if t == ArchiveExpData.SLIP_END_L:
				ArchivePump._disc(img, hooks[0], 13.0, BRASS)
				_arrow(img, pc + Vector2(-22, 30), hooks[0] + Vector2(2, -18), 4.0, INK)
			elif t == ArchiveExpData.SLIP_END_R:
				ArchivePump._disc(img, hooks[5], 13.0, BRASS)
				_arrow(img, pc + Vector2(22, 30), hooks[5] + Vector2(-2, -18), 4.0, INK)
			else:
				for e in [0, 5]: # not at either end: both end hooks are crossed out
					ArchivePump._line(img, hooks[e] + Vector2(-13, -13), hooks[e] + Vector2(13, 13), 5.0, Color("9a2c22"))
					ArchivePump._line(img, hooks[e] + Vector2(-13, 13), hooks[e] + Vector2(13, -13), 5.0, Color("9a2c22"))
		_:
			var ya := 62.0
			_put(img, portrait(a), Vector2i(18, int(ya) - pw.y / 2), pw)
			_put(img, portrait(b), Vector2i(w - 18 - pw.x, int(ya) - pw.y / 2), pw)
			if t == ArchiveExpData.SLIP_LEFT: # a hangs somewhere left of b
				_arrow(img, Vector2(18 + pw.x + 10, ya), Vector2(w - 18 - pw.x - 10, ya), 5.0, INK)
			else: # a hangs next to b: two hooks side by side, an arrow both ways
				_arrow(img, Vector2(18 + pw.x + 10, ya), Vector2(w - 18 - pw.x - 10, ya), 4.0, INK, true)
			for i in 6:
				ArchivePump._disc(img, hooks[i], 7.0, Color("8a7a58"))
	if status >= 0:
		ArchivePump._disc(img, Vector2(w - 18, 18), 9.0, Color("2f9a4a") if status == 1 else Color("b02a20"))
	return img


## All the slips side by side on one sheet (the item's reading view): `status` per slip as the board shows it.
static func slips_sheet(slips: Array, status: Array) -> ImageTexture:
	var cols := 2
	var rows := int(ceil(slips.size() / float(cols)))
	var sw := 240
	var sh := 170
	var gap := 18
	var img := Image.create(cols * sw + (cols + 1) * gap, rows * sh + (rows + 1) * gap, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for i in slips.size():
		var s := slip_image(slips[i], int(status[i]) if i < status.size() else -1, sw, sh)
		img.blit_rect(s, Rect2i(0, 0, sw, sh), Vector2i(gap + (i % cols) * (sw + gap), gap + (i / cols) * (sh + gap)))
	return ImageTexture.create_from_image(img)


# ---------------------------------------------------------------------- N9: strips, label, projected image, print
## A negative strip: the base art with the edge-symbol window painted with this strip's symbol and four portraits in
## the order given by `order` (staff member per frame).
static func strip_texture(symbol_k: int, order: Array) -> ImageTexture:
	var key := "strip_%d_%s" % [symbol_k, str(order)]
	if _cache.has(key):
		return _cache[key]
	var base := (load(NEG_BASE) as Texture2D).get_image()
	if base.is_compressed():
		base.decompress()
	base.convert(Image.FORMAT_RGBA8)
	var img := base.duplicate() as Image
	var frame_w := 200
	for f in 4:
		var x0 := 20 + f * 232
		img.fill_rect(Rect2i(x0, 28, frame_w, 104), Color("453c34"))
		var p := portrait(int(order[f]))
		var inv := Image.create(208, 142, false, Image.FORMAT_RGBA8)
		inv.fill(Color(0, 0, 0, 0))
		for yy in 142:
			for xx in 208:
				var c := p.get_pixel(xx, yy)
				if c.get_luminance() < 0.35: # the figure: pale on the negative
					inv.set_pixel(xx, yy, Color("c3baa6"))
		var scaled := inv.duplicate() as Image
		scaled.resize(frame_w, 104, Image.INTERPOLATE_BILINEAR)
		img.blend_rect(scaled, Rect2i(0, 0, frame_w, 104), Vector2i(x0, 28))
	img.fill_rect(Rect2i(954, 24, 50, 112), Color("8a8272"))
	symbol(img, symbol_k, Vector2(979, 80), 20.0, Color("1d1914"))
	var tex := ImageTexture.create_from_image(img)
	_cache[key] = tex
	return tex


## Strand's cabinet label: the symbol on a brass-framed card.
static func cabinet_label(symbol_k: int) -> ImageTexture:
	var img := Image.create(256, 192, false, Image.FORMAT_RGBA8)
	img.fill(Color("a8843c"))
	img.fill_rect(Rect2i(14, 14, 228, 164), PAPER)
	symbol(img, symbol_k, Vector2(128, 96), 56.0, INK)
	return ImageTexture.create_from_image(img)


## The picture on the enlarger's paper: the staff member of the loaded strip (-1 = blank paper), blurred by the focus
## error and scaled by the zoom error; the fit frame marks the size that fits. digits (4 ints) only when the print is right.
static func enlarger_image(who: int, blur: int, scale: float, digits: Array) -> ImageTexture:
	var key := "enl_%d_%d_%d_%s" % [who, blur, int(scale * 100.0), str(digits)]
	if _cache.has(key):
		return _cache[key]
	var w := 160
	var h := 120
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color("d8d2c0"))
	# the fit frame printed on the easel (the portrait fills it at the right zoom)
	var fr := Rect2i(20, 14, 120, 92)
	for x in range(fr.position.x, fr.end.x):
		for t in [0, 1]:
			img.set_pixel(x, fr.position.y + t, Color("a89c84"))
			img.set_pixel(x, fr.end.y - 1 - t, Color("a89c84"))
	for y in range(fr.position.y, fr.end.y):
		for t in [0, 1]:
			img.set_pixel(fr.position.x + t, y, Color("a89c84"))
			img.set_pixel(fr.end.x - 1 - t, y, Color("a89c84"))
	if who >= 0:
		var p := portrait(who)
		var sz := Vector2i(maxi(8, int(120.0 * scale)), maxi(6, int(92.0 * scale)))
		p.resize(sz.x, sz.y, Image.INTERPOLATE_BILINEAR)
		var at := Vector2i(80 - sz.x / 2, 60 - sz.y / 2)
		var cut := Rect2i(Vector2i.ZERO, sz).intersection(Rect2i(-at, Vector2i(w, h)))
		if cut.size.x > 0 and cut.size.y > 0:
			img.blit_rect(p, cut, at + cut.position)
		if blur > 0:
			_box_blur(img, blur)
		if not digits.is_empty():
			var s := ""
			for d in digits:
				s += str(int(d))
			var sc := 3
			for i in s.length():
				ArchivePump._digit(img, Vector2(26 + i * 4 * sc + 6, 99), int(s[i]), sc, Color("4a4a50"))
	var tex := ImageTexture.create_from_image(img)
	_cache[key] = tex
	return tex


static func _box_blur(img: Image, r: int) -> void:
	var w := img.get_width()
	var h := img.get_height()
	var rr := clampi(r, 1, 12)
	for pass_i in 2:
		var src := img.duplicate() as Image
		for y in h:
			for x in w:
				var acc := Color(0, 0, 0, 0)
				var n := 0
				for k in range(-rr, rr + 1):
					var xx := clampi(x + k, 0, w - 1) if pass_i == 0 else x
					var yy := y if pass_i == 0 else clampi(y + k, 0, h - 1)
					acc += src.get_pixel(xx, yy)
					n += 1
				img.set_pixel(x, y, acc / float(n))


## The staff print as a reader picture: the photo with the four digits pencilled across the foot, large.
static func staff_print(who: int, digits: Array) -> ImageTexture:
	var w := 480
	var h := 380
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color("d8d2c0"))
	var p := portrait(who)
	p.resize(420, 287, Image.INTERPOLATE_BILINEAR)
	img.blit_rect(p, Rect2i(0, 0, 420, 287), Vector2i(30, 16))
	var s := ""
	for d in digits:
		s += str(int(d))
	var sc := 11
	for i in s.length():
		ArchivePump._digit(img, Vector2(110 + i * 4 * sc + 20, 332), int(s[i]), sc, Color("48484e"))
	return ImageTexture.create_from_image(img)
