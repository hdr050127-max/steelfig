# Scene file format (TOML)

A scene file describes one figure: the steel, the camera views, the labels. `steelfig build scene.toml out/
--report rep/` builds it. Units are metres; x east (along the frame), y north (along the building), z up.

## Expressions

Any point, vector or number may be a string expression. Available names:

| name | meaning |
|---|---|
| `V(x, y, z)` | a vector |
| `roof.at(x)`, `roof.along(s)`, `roof.normal(x)`, `roof.tangent(x)` | the `[[line]]` called `roof` (any name): point at horizontal x, point at slope distance s, unit normal, unit tangent |
| `sec("310UB46.2")` | profile dict: `["d"]`, `["b"]`, `["tf"]`, `["tw"]`, `["t"]` in metres |
| `m.col.a`, `m.col.b` | end points of the member named `col` (declared earlier) |
| `pur[3]` | the fourth purlin's point on the line (from `[[purlins]] name = "pur"`) |

Automatic anchors: every member gets `m.<name>` (midpoint), `m.<name>.a`, `m.<name>.b` (ends) without declaring
anything, so a label can say `anchor = "m.raf"`. Model members are called `m<id>` for the first frame and
`m<id>_<y>` for copies (`m.m101_11.315`).
| `math` | Python's math module |

A point may also be `[x, y, z]` or `[x, z]` (y = 0).

## Tables

```toml
title = "…"                       # free text
style = "default"                 # style sheet (steelfig/styles/<name>.toml, resources/styles/, or a path); optional
                                  # default = three-point light with soft shadows, light cool-grey coated steel, one warm
                                  # accent (chosen 2026-11-04); "light" = pale textbook look; finishes have coat / edge keys
                                  # members get a steel finish from their catalogue type ([finishes] / [finish_of] in the
                                  # style: hot_rolled, hollow, galvanised, bolt, accent) unless `material` is given
frames = [0.0, 11.315, 22.63]     # y positions; members with per_frame = true are repeated at each

[[line]]  name = "roof"  points = [[x, z], …]  lift = 0.2665     # polyline in the xz plane; lift along its normal

[[member]]
name = "col"  section = "460UB82.1"  from = …  to = …
up = [1, 0, 0]            # web / long-leg / depth direction (default [0,0,1])
align = "centroid"        # "top" | "bottom" | "heel": where the line sits on the profile
cut0 = [point, normal]    # trim the start by a plane; cut1 for the end
material = "steel"        # steel | light | dark | accent | sheet | weld | conc | grout
flip = false              # mirror the profile (Z purlins, channel toes)
per_frame = false

[[plate]]  name  centre  ex  ey  size = [along ex, along ey, thickness]  material
[[bolts]]  name  centre  axis  up  side  rows = [offsets along up]  cols = [offsets along side]  bolt = "M20"  grip  material
[[stiffeners]]  name  column_pt  section  levels = [z, …]  t  up  material
[[purlins]]  name  line  spacing  start  until  y0  y1  section  material  from_end  flip_alternate
[[girts]]  name  x  levels  y0  y1  section  outward  material
[[fly_brace]]  name  flange_pt  purlin_pt  section = "75x75x6 EA"  both_sides = true  material
[[sheeting]]  name  line  x0  x1  y0  y1  lift  rib  pitch  material
[[connection]]  type = "knee"   name = "k"  line = "roof"  x = 0.0  column = "col"  rafter = "raf"  [diagonal = true]
[[connection]]  type = "splice" name = "s"  line = "roof"  x = 6.278  a = "haunch"  b = "rafter"
[[connection]]  type = "cap"    name = "c"  line = "roof"  x = 21.993  column = "colB"  rafter = "haunchB"  [y = 0.0]
[[connection]]  type = "base"   name = "b"  x = 0.0  column = "col"  [y = 0.0  z0 = 0.0  plate_t  grout  bolt = "M24"]
[[connection]]  type = "knee"  … [y = 6.0  side = -1]                  # y: frame position; side = -1 when the rafter runs towards -x
[[connection]]  type = "splice" … [y = 6.0  b_end = "cut1"]             # b_end: b is declared running towards x (rafter from its knee to the ridge)
[[connection]]  type = "xbrace" name = "x"  a0  a1  b0  b1  normal  host = "col"  section = "75x75x6 EA"
      # X of angles between work points a0, a1 on one frame and b0, b1 on the next (on the host web at mid-depth): gussets, cleat
      # plates, bolts from the TTW table, web stiffeners, pack and bolt at the crossing. Anchors: x.a0_gusset x.a0_cleat x.a0_bolt … x.cross
[[connection]]  type = "strut"  name = "st" a  b  normal  along  section = "114.3x3.2CHS"
      # CHS strut type A between the gussets at two work points of an xbrace; along = the host member's direction. Anchors: st.a_end st.a_bolt …
[[connection]]  type = "wsp"    name = "w"  y = 0.0  primary = "pri"  secondary = "sec"
      # web side plate: a PFC running along y (align = "top", member line on the web back face, flip for the toes) into
      # the web of a primary along x at y; top flush, flanges and top of web coped. Anchors: w.fin w.bolt w.cope w.web.
      # extra keys: bolt rows pitch fin_t fin_h fin_w bolt_off gap cope_len cope_d weld
      # generated from the member sections: plates, bolt rows, stiffeners, grips; the named members are trimmed
      # to the connection faces automatically (declare them to the column axis / splice point). Anchors:
      # k.ep k.bolt k.bolt2 k.stiff k.face | s.ep s.bolt s.bolt2 s.face | c.capp c.bolt c.ws c.col | b.bp b.ab b.ab2 b.grout b.foot b.col
      # extra keys: ep_t ep_ext bolt bolt_in row_off stiff_t cap_t plate_t grout footing bolts_in — when left out they
      # scale with the member depth (connections.defaults: M16/16 plate under 320, M20/20 to 470, M24/25 to 620, M24/32 above)
[[purlins]] … cleats = true  [cleat_frames = [0, 6, 12]  flip = true]  # plate cleat + two bolts under every purlin at each frame; flip on the slope where the line runs downhill
[[girts]] … [cleat_frames = [0, 6, 12]]    # plate cleat + two bolts at the column flange
[[fly_brace]] … [y = 6.0  sides = [1]]     # the frame it belongs to; which sides of the rafter (an end frame has purlins beyond it on one side only)
[[fly_brace]]  purlins = "pur"  at = [1, 3]  member_depth = "sec('410UB59.7')['d']"  member_bf = "sec('410UB59.7')['b']"
               section = "75x75x6 EA"  both_sides = true  cleat = true     # against the purlin web, cut under the top flange
check = true           # top level: report solids passing through each other (> check_min_cm3, default 5 cm3)
[[model]]  path = "model.arc"  sections = { "PROP name or member id" = "designation" }  default  accent = [ids]
           skip = [ids]  xmax  frames = [ys]  top_lift  connections = true
      # connections = true (default): at every node a column top meeting one inclined member gets a knee, a
      # column top under a continuous rafter a cap plate, two inclined members of different sections a splice;
      # the members are trimmed to those faces (the analysis lines would otherwise pass through each other).
      # Anchors: knee<node>.ep / .bolt / .stiff, cap<node>.capp / .bolt / .ws, splice<node>.ep / .bolt
[[section_cut]]  point  normal  plane = "xz"  pitch = 0.012      # cuts everything on the +normal side, hatches the faces
[[explode]]  objects = ["ep", "kb"]  vector = [0, -0.3, 0]      # pull parts away (names or name prefixes)

[anchors]            # name = point | list of points; what the labels and lines attach to
[[dim]]  name  a  b  [off]               # 3D dimension line; without `off` (or off = "auto") the overlay picks a clear
                                         # place among 32 candidates (perpendicular directions × distances), off the steel
[[wave]]  name  a  b  amp  side          # buckled shape polyline from a to b bowing by amp along side

[[view]]
name = "knee"
camera = [x, y, z, tx, ty, tz, lens]     # perspective; or camera = "auto" (or leave it out): the camera is chosen to look at
auto = { focus = ["col", "raf"], fit = [...], dir = [0.6, -1, 0.45], lens = 40, fill = 0.8 }
                                          # the focus objects (default: the accent ones) from direction `dir`, at the distance
                                          # that fits the `fit` objects (default: everything) in 80 % of the frame; the result is
                                          # printed as `camera <view> = [...]` and used by the viewer, so you can adjust it from there
                                          # or:
ortho = { look = "+y", scale = 2.6, at = [x, y, z] }    # look: +x -x +y -y -z(plan)
ortho = { look = "-z", auto = true, fit = ["b_bp", "b_foot"], fill = 0.85 }   # or fitted automatically to objects
cut = { point = [0, 0, 0.35], normal = [0, 0, 1], objects = ["col"], plane = "xy", hatch = true }
                                          # section for THIS view only: removes everything on the +normal side of the
                                          # plane (of the listed objects, default all), hatches the cut faces
main = true                               # in a row of two, this view takes main_share (0.62) of the width
crop = [p0, p1]                           # fixed crop (ortho views); otherwise the render crops to the meshes
bounds = ["wave", …]                      # anchors that must stay inside the crop
width_cm = 14  |  height_cm = 5.5  max_width_cm = 7     # size on the page
caption = "…"                             # small caption under this view
draw = [["dim3", "le", "$L_e = 2400$", "below"], ["line", ["wave"], "line width=0.8pt, densely dashed, acc"], …]
highlight = [{ objects = ["raf"], colour = "#c9553f", alpha = 0.55, outline = 2, dim = 0.35 }]
                                          # tint members on the picture after rendering (from the ID render), outline
                                          # them (px), fade everything else towards white; names or prefixes
  [[view.label]]  anchor = "col"  text = "…"  [dx = 1.3  dy = -0.5]  [num = 3]
      # balloon; without dx / dy the position is chosen automatically (off the steel, apart from other balloons, no
      # crossing leaders, inside the picture); num repeats an earlier number for the same part seen again

[figure]
name = "knee"          # fig_<name>.tex, preview/prev_<name>.pdf
width_cm = 15.6        # figure width on the page (A4 text width with 25 mm margins)
layout = "auto"        # auto (1 view: stack, 2-3: row, 4+: grid2) | stack | row | grid2
key_cols = 2           # default: 2 columns when the key has 4+ lines and the figure is wide
key_extra = ["…"]      # extra key lines (fills, line styles) in TikZ/LaTeX
image_dir = "images/steelfig"
# Composition (steelfig/compose.py): views in a row share one height and fill the width with 4 mm gaps;
# captions become "(a) …" automatically when there are several views; the key goes under the views; the
# plain (geometry) preview uses exactly the same arrangement. A view's own width_cm / height_cm overrides it.
```

`draw` items: `line`, `fill`, `arrow`, `dim`, `dim3`, `angle`, `text`, `grid`, `letter`, `detail`, `cutline`,
`support`, `raw`, as documented in `steelfig/overlay.py`. Every `dim`/`dim3` text is checked against the model
distance and a mismatch is printed as a WARNING. A 2D `dim` on a perspective view is also warned.

## Why each part is where it is

Every connection and fly brace generator records its decisions with the rule and the source (an AS 4100 clause,
a catalogue, a standard detail, or ASSUMPTION when it is only common practice): `out/<figure>_rationale.md`,
one line per decision, plus the realism checks that failed (`REALISM …` lines in the build output: bolt edge
distances and pitch to AS 4100:2020 Cl 9.5, brace angle 35-55°, nut on the open face, cleat bolt edge distance). Put
the relevant lines in the figure's key or caption, and treat an ASSUMPTION entry as something to confirm before
the figure is quoted as a detail.

Fly brace rules (`[[fly_brace]] purlins = … at = […] member_depth = … member_bf = …`, optional `section`, `bolt`,
`reach`): angle and bolt by rafter depth; long leg flat on the flange-free face of the purlin web (upslope for a
Z, back for a C); one bolt at mid-web; angle end 15 mm under the top flange; ~45° by setting the reach; cleat
plate welded to the flange tip with one bolt. All of these are in the rationale file with their sources.

## Checks run on every build

After the annotation, every view is checked and findings are printed as `overlay WARNING: [view] …`: dimension
texts against the model, balloons sitting on a member, leaders crossing, balloons or anchors outside the picture,
balloon numbers without a key line, a dimension line lying on a member. `check = true` adds the clash check of the
solids. Fix the scene until the build is silent; `overlay.STRICT = True` turns warnings into errors.

## Lines

Outlines come in a hierarchy (`[lines]` in the style): outer contours thicker, internal creases thinner, parts in
the secondary collection (purlins, girts, sheeting, cleats, or `[[member]] secondary = true`) thinner again, and a
mild fade with distance from the camera. This is what separates a manual-style drawing from a CAD screenshot.

## Two-stage work

`steelfig build … --plain` renders the views and stops: `<rep>/preview/prev_<figure>_plain.pdf` and the view
JPEGs show the geometry with nothing on it, which is what to check first. `steelfig annotate` then adds the
annotation. A build renders every view once (`<view>.png` plus `<view>_id.png`, a flat-colour image that says which pixel
belongs to which object). Labels, highlights, fills and dimensions are drawn afterwards from those files, so you can
start with a view that has no annotation at all, then add `[[view.label]]`, `highlight`, `draw` items and rerun
only `steelfig annotate scene.toml out/ --report rep/` (no Blender, under a second). Re-render only when the
geometry or the camera changes. A region (tributary area, panel zone) is a `fill` over a polygon of 3D anchors;
a member is a `highlight`. See `examples/highlight/`.

## Picking the camera in the browser

Every build also writes `out/scene.glb`. `steelfig view out/` serves a page (`viewer.html`) that shows the model
with the recommended camera of each view, the same lens and frame as the render: drag to orbit, right-drag to
pan, wheel to zoom (the camera moves, the lens stays). The current camera is shown as `x, y, z, tx, ty, tz,
lens`; copy it into the scene (`camera = [...]`) or run `steelfig set-camera scene.toml <view> "x,y,…"`, then
rebuild. Needs internet once for three.js (unpkg).

## Figure sets

`steelfig build-all <folder | set.toml> <out_root> --report <dir>` builds every scene with one style and shared
`[figure]` defaults (width, key columns), so the figures of a report match; a set file lists `scenes = [...]`
(above any table header), `style`, and `[defaults]`. The summary lists each figure with its warning count.

## Errors

A mistake in a scene file stops the build with one line, e.g. `ERROR in [[member]] name = "raf": section
'410UB58' not in the catalogue; near: 410UB53.7, 410UB59.7` or `ERROR in [anchors] col: name 'roof2' is not
defined (names you can use: …)`.

## Output

`out/<view>.png` + `.json` (anchors), `rep/images/steelfig/<view>.jpg`, `rep/figures/fig_<name>.tex` (the fragment to
`\input` inside your own `figure` environment), `rep/preview/prev_<name>.pdf` (+ `.png` with `--png`).
The report preamble needs `\usepackage{tikz,graphicx,amsmath}`, `\usetikzlibrary{arrows.meta}`,
`\definecolor{acc}{rgb}{0.62,0.16,0.10}` and the `\ball` macro (`overlay.PRE`).
