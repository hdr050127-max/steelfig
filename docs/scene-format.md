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
| `math` | Python's math module |

A point may also be `[x, y, z]` or `[x, z]` (y = 0).

## Tables

```toml
title = "…"                       # free text
style = "default"                 # style sheet (steelfig/styles/<name>.toml or a path); optional
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
[[model]]  path = "model.arc"  sections = { "PROP name or member id" = "designation" }  default  accent = [ids]
           skip = [ids]  xmax  frames = [ys]  top_lift
[[section_cut]]  point  normal  plane = "xz"  pitch = 0.012      # cuts everything on the +normal side, hatches the faces
[[explode]]  objects = ["ep", "kb"]  vector = [0, -0.3, 0]      # pull parts away (names or name prefixes)

[anchors]            # name = point | list of points; what the labels and lines attach to
[[dim]]  name  a  b  off                 # 3D dimension line: off = offset vector in the plane of the measured face
[[wave]]  name  a  b  amp  side          # buckled shape polyline from a to b bowing by amp along side

[[view]]
name = "knee"
camera = [x, y, z, tx, ty, tz, lens]     # perspective, or:
ortho = { look = "+y", scale = 2.6, at = [x, y, z] }    # look: +x -x +y -y -z(plan)
crop = [p0, p1]                           # fixed crop (ortho views); otherwise the render crops to the meshes
bounds = ["wave", …]                      # anchors that must stay inside the crop
width_cm = 14  |  height_cm = 5.5  max_width_cm = 7     # size on the page
caption = "…"                             # small caption under this view
draw = [["dim3", "le", "$L_e = 2400$", "below"], ["line", ["wave"], "line width=0.8pt, densely dashed, acc"], …]
  [[view.label]]  anchor = "col"  text = "…"  dx = 1.3  dy = -0.5  num = 3    # balloon (dx, dy in cm); num repeats a number

[figure]
name = "knee"          # fig_<name>.tex, preview/prev_<name>.pdf
width_cm = 15          # key width
layout = "stack"       # stack | row
key_cols = 2
key_beside = true      # key beside the last view instead of under everything
key_extra = ["…"]      # extra key lines (fills, line styles) in TikZ/LaTeX
image_dir = "images/steelfig"
```

`draw` items: `line`, `fill`, `arrow`, `dim`, `dim3`, `angle`, `text`, `grid`, `letter`, `detail`, `cutline`,
`support`, `raw`, as documented in `steelfig/overlay.py`. Every `dim`/`dim3` text is checked against the model
distance and a mismatch is printed as a WARNING. A 2D `dim` on a perspective view is also warned.

## Output

`out/<view>.png` + `.json` (anchors), `rep/images/steelfig/<view>.jpg`, `rep/figures/fig_<name>.tex` (the fragment to
`\input` inside your own `figure` environment), `rep/preview/prev_<name>.pdf` (+ `.png` with `--png`).
The report preamble needs `\usepackage{tikz,graphicx,amsmath}`, `\usetikzlibrary{arrows.meta}`,
`\definecolor{acc}{rgb}{0.62,0.16,0.10}` and the `\ball` macro (`overlay.PRE`).
