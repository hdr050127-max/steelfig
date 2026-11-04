---
name: blender-figures
description: True-size 3D figures of steel structures for reports and teaching, made with steelfig (Blender + TikZ): members from the Australian catalogues (UB, UC, PFC, angles, SHS/RHS/CHS, Stramit purlins), generated connections (knee, splice, cap, base, purlin cleats, fly braces), frames drawn straight from a Microstran .arc model, numbered balloons and dimension lines checked against the model, clash and realism checks, and a written rationale for every part. Use it whenever someone asks for a 3D figure, an isometric, a connection or joint drawing, "show where the purlins / fly braces go", "draw the model", or a figure of any steel member, frame, truss or detail for a report, assignment, slide or handout, even if they do not say Blender or 3D.
---

# blender-figures: report figures of steel structures with steelfig

The tool is the `steelfig` repository (https://github.com/hdr050127-max/steelfig). Find it in this order:
`$STEELFIG_HOME`, `~/steelfig`, `~/Developer/steelfig`; if none exists, clone it (`git clone
https://github.com/hdr050127-max/steelfig ~/steelfig`) and run `bin/steelfig doctor` (needs Blender 4.2+, Python
3.11+ with Pillow, optionally pdflatex and pdftoppm). Below, `steelfig` means `<repo>/bin/steelfig`.

Read `README.md` first, `docs/scene-format.md` before writing a scene, `docs/figure-style.md` for the look the
figures must have (grey line-art like a fabricator's manual, one accent colour, no text on the picture, parts
named only by numbered balloons and a key, dimensions in orthographic views or true 3D dimension lines), and
`docs/pitfalls.md` when something goes wrong. Teachers dislike AI-looking structural drawings: geometry must be
true to the catalogue and to the standard details, and every part must have a reason.

## Step 1, always: expand the request into a brief and get it confirmed

A request is usually one sentence. Do not build yet. Expand it with `docs/figure-brief.md` into a brief: purpose
and source (why this figure, which brief page / lecture / clause it illustrates), the one subject (accent colour),
the structure with catalogue designations and spacings, which parts are assumptions, the explanation content to
draw in full (dimensions with values, centrelines, buckled shapes, tributary areas, load arrows), each view
(perspective or orthographic, what it crops to, size on the page), the balloon list with key texts, checks,
outputs, and open questions numbered. Show it, wait for the person to confirm or correct, then build. This step is
what makes the figure right; skip it only if the person asks you to.

## Step 2: build the scene

Three routes, in order of preference:

1. **TOML scene** (`examples/knee/knee.toml` as the template, format in `docs/scene-format.md`). Sections are
   catalogue names (`310UB46.2`, `200x200x9SHS`, `100x100x8 EA`, `Z25019`); points may be expressions
   (`roof.at(3.2)`, `sec('410UB59.7')['d']`). Connections are generated, never hand-placed:
   `[[connection]] type = "knee" | "splice" | "cap" | "base"` with the line, position and member names; purlins
   `cleats = true`; fly braces `[[fly_brace]] purlins = … at = […] member_depth = … member_bf = …`. Members
   named in a connection are trimmed to its faces automatically.
2. **From an analysis model**: `[[model]] path = "x.arc"` (Microstran) with `sections = {…}` for PROP names that
   are not catalogue names, `accent = [member ids]`, `frames = [y…]`, `top_lift`. `steelfig model x.arc` lists
   nodes, members and PROP names first. Example `examples/frame_from_model/`.
3. **Python API** (`examples/kjoint/`, `docs/python-api.md`) for what the scene format cannot express: boolean
   cuts, weld rings, overlapping SHS joints.

Build with `steelfig build scene.toml <out_dir> --report <report_dir> --quick --check`. The build chooses a
camera if none is given (`camera = "auto"`), places balloons that have no `dx`/`dy`, draws the outlines in a
hierarchy, and writes `<out>/<figure>_rationale.md` with every generated part's position, rule and source.

## Step 3: make the output silent, then show it

Treat every line of the build output as a task:
- `overlay WARNING` (dimension text vs model, balloon on a member, leaders crossing, anchor outside the picture,
  balloon without key line): fix the scene and rerun `steelfig annotate scene.toml <out_dir> --report <rep>`
  (no Blender, under a second) or rebuild if geometry changed.
- `CLASH a x b: … cm3 near (x, y, z)`: members pass through each other; fix the geometry.
- `REALISM …`: a rule of real construction is broken (AS 4100 edge distance / pitch, brace angle, spanner
  room); fix it.
- `ERROR in [[table]] name = …`: a scene mistake, one line says what.
Look at the preview PDF (`<rep>/preview/prev_<figure>.pdf`, rasterise with pdftoppm to inspect) and compare it
line by line with the brief. Only then render without `--quick` and show the figure. Give the person the
rationale file's ASSUMPTION lines: they must appear in the brief, caption or key.

## Camera

If the person wants to choose the view: `steelfig view <out_dir>` serves `viewer.html` (orbit / pan / zoom at the
recommended camera, same lens and frame as the render). In Claude's browser pane read `window.cam` when they
are done, then `steelfig set-camera scene.toml <view> "x,y,z,tx,ty,tz,lens"` and rebuild.

## Into the document

LaTeX: `\input{figures/fig_<name>}` inside the report's own `figure` environment (`[!htbp]`); the preamble
needs `tikz`, `arrows.meta`, `\definecolor{acc}{rgb}{0.62,0.16,0.10}` and the `\ball` macro (`PRE` in
`steelfig/overlay.py`). Word or slides: `--png` writes `preview/prev_<name>.png`. Several figures of one report:
a set file and `steelfig build-all set.toml <out_root> --report <rep>` so they share one style.

## Extending

New section: a row in `steelfig/data/*.csv` with its source in `data/README.md` (`verified=no` until checked).
New connection: a generator in `blender/connections.py` that records every decision with `rationale.note()` and
checks real-construction rules with `rationale.check()`, plus a table in `blender/build_scene.py`; a part without a
rationale entry is not finished. Another course's look: a style file in `steelfig/styles/`.
