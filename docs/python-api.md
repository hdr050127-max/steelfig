# Python API (for figures the scene format cannot express)

A figure script runs inside Blender: `steelfig render fig.py out/ [quick] [cam=x,y,z,tx,ty,tz,lens]`. It imports
`bfig` (modelling, camera, render) and `assembly` (lines, patterns, connections, model import). Annotation is a
second, ordinary-Python script that imports `steelfig.overlay`. See `examples/kjoint/` for both halves.

## bfig (inside Blender; metres)

Scene: `args()` → (out_dir, quick, opts); `reset()`; `mats()` → palette of the style sheet; `mat(name, rgba)`;
`hatch_mat(name, base_rgb, ink_rgb, pitch, angle, plane)`.

Members: `member(name, p0, p1, designation, material, up, cut0, cut1, align, flip)` for any catalogue section;
the older shortcuts `shs / rhs / chs / isec / zsec / angle / prism / plate / box / cyl / bolt / anchor_bolt /
sheeting / sheet_slope` still exist. `section(designation)` → catalogue row (mm).

Joints: `boolean_cut(target, cutters)`, `solid_prism`, `edge_hits`, `weld_ring`, `weld_line`, `section_cut(objs,
point, normal, hatch)`, `explode(objs, vector)`, `delete`, `all_meshes()`.

Camera / render: `setup(cam_loc, target, lens, res, ortho, line, quick, cam)`; `ortho_view(cam, look, scale, at)`;
`render(out_dir, name, anchors, margin, bounds_extra, crop_pts, ids=True)` → png + json (image coordinates and 3D
points of every anchor, the object-ID colours) + `<name>_id.png` (flat colour per object, for highlights).
`member_anchors()` → automatic `m.<name>` anchors for every member drawn. Anchors: `dim3(anch, name, p, q, off)`, `wave(p, q, amp, side)`.

## assembly (inside Blender)

`Line(points, lift)` with `.at(x)`, `.along(s)`, `.normal(x)`, `.tangent(x)`, `.length()`.
`array`, `every_nth`, `mirror_y`, `frames`.
`end_plate`, `bolt_rows`, `stiffeners`, `cap_plate`, `base_plate`, `fly_brace`, `purlins_on`, `girts_on`, `cleat`.
`build_model(model, mapping, materials, default, web, accent, skip, xmax, y, top_lift)`.

## steelfig.sections (anywhere)

`find(designation)` → row (mm); `profile(designation)` → polygon(s) in metres; `search(text)`; `bolt("M20")`.

## steelfig.overlay (system Python)

`Pic` (`.highlight(names, colour, alpha, outline, dim)` tints members from the ID render), `pic_by_height`, `balloon`, `rail`, `keylist`, `keycols`, `row`, `captioned`, `swatch`, `dash`, `flatten`,
`emit`, `preview`, `standalone`, `warnings()`, `STRICT`. Draw items are listed in the module docstring.

## steelfig.readers

`read(path)` → `Model` (nodes z-up in metres, members, props); Microstran `.arc` or `nodes.csv` + `members.csv`.
