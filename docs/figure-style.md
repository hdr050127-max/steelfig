# Figure style (what the figures must look like)

Agreed with the user on 2026-10-09 and kept since. Reviewers of student reports have mocked AI-looking
connection drawings, so the figures have to look like a fabricator's manual or a steel textbook, and every part
has to be geometrically right.

## What to draw
- Only figures the brief or the reviewer asks for, or that explain a step of the design. A figure that
  repeats a table is dropped. No software screenshots as evidence.
- True size, in metres: real section depths and flange widths, real wall thickness visible at every cut end,
  purlins only where they really sit (on the top flange, over the nodes for a truss), fly braces as angles from the
  restrained flange up to the purlin, welds and bolts where the connection needs them.
- Where a figure explains something, draw the explanation in full: dimension lines (`dim3`), centrelines, buckled
  shapes (`wave`, dashed accent), tributary areas (`fill`, accent at 10 % and 30 %), load arrows, grid names.
- The subject of the figure is the ONE accent colour (muted brick red `acc`); everything else grey. Secondary
  members (purlins, girts, diagonals) in `light`, bolts in `dark`.
- Cut-away: show one bay, one end, part of the sheeting; cut members at a clean plane so the section shows.

## The render (style sheet `default.toml`, 2026-11-04)
- Lighting: a key sun (50° up, 35° east of south, 6° soft) that casts the only shadows, a fill without shadow, a
  rim from behind; a white-to-grey gradient sky so metal has something to reflect. Shadows exist but are soft:
  depth without drama. Render time stays a few seconds per view (EEVEE).
- Steel: light cool grey with roughness noise (mill scale), a light clearcoat and an edge lift; galvanised parts
  lighter with a faint spangle; bolts dark. One warm accent (#c4603f) on the subject only.
- Lines: dark grey (not black) outlines, contour heavier than creases, secondary parts thinner, mild depth fade.

## How to label
- Parts are named only with numbered balloons beside the part, an arrow leader back to the part, and the text in a
  key below or beside the figure. Never write words on top of the picture (rejected 2026-10-09 as messy).
- Dimensions go in orthographic views, or as true 3D dimension lines (`dim3`: the offset vector lies in the plane
  of the face being measured). Never a 2D dimension drawn over a perspective view.
- Sub-figures referenced from an overview get boxed letters (`letter`), the sub-figures carry "(a) …" captions.
- Key lines: short, one fact each; a swatch (`swatch`) or line sample (`dash`) explains fills and line styles.
- One accent colour, grey/black linework, `\footnotesize` text. Not many colours, not lots of small grey text
  (the earlier TikZ figures were rejected as "too AI" for that).

## Layout in the report
- Floats `[!htbp]` with `placeins` per section, never `[H]`; caption on top for tables; after each build check every
  page for text outside the margins, overlapping words and empty half pages.
- The figure body is a fragment `figures/fig_<name>.tex` the report `\input`s inside its own `figure` environment,
  so captions and labels stay in the report source.
- Say in the caption when something is schematic ("sheeting schematic", "bolt layout illustrative, not designed").
- Cite the source of every drawn assumption in the caption or key (brief page, lecture week, Ed thread, AS clause,
  fabricator's standard detail), as for any other claim in the report.
