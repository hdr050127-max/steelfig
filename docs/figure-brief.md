# Figure brief (fill this in before building anything)

A figure request usually arrives as one sentence ("draw the knee with the fly braces", "show where the purlins
sit", "a 3D view of the K joint"). Before touching a scene file, expand it into this brief, show it to the person
who asked, and build only after they confirm. Most wrong figures come from a wrong brief, not from the tool.

```
Figure brief: <working title>

Purpose      what the figure must explain, in one sentence, and where it goes (report section / slide / handout)
Source       what says this figure is needed or what it illustrates (brief page, lecture week, tutor note, Ed thread,
             AS 4100 clause, standard detail) — this ends up in the caption
Subject      the ONE thing in the accent colour
Structure    what is drawn and at what sizes: members with catalogue designations, lengths shown, spacing of
             purlins / girts / bolts, which connections (type and standard detail), what is cut away or omitted
             — and which of these are assumptions (write "assumed: …")
Explanation  the engineering content drawn in full: dimensions (name + value + between what), centrelines,
             buckled shapes, tributary areas, load arrows, grid names, section cuts
Views        ONE view unless the request asks for more or the explanation cannot be read from one; each extra
             view gets a one-line reason ("plan: the bolt pattern is hidden in the perspective") and is a
             question to the person, not a decision. Each view: perspective (from where, looking at what) or
             orthographic (direction, what it crops to); size on the page; which views sit side by side
Labels       the numbered parts, in order, with the text of each key line
Style        style sheet; anything that departs from the defaults (colour, line weight)
Checks       what must be true (dimension texts match the model; no members passing through each other;
             purlins on the top flange; bolts either side of the web; …)
Output       fragment name, image folder, preview, PNG for Word?
Open points  what the person must decide before building (numbered questions)
```

## Three sizes of brief

Pick the size from the request, and say which you picked:
- **Small** (one member or one connection, one view, no model import: "a pinned base for a 610UB113"): three
  lines in the reply, confirmed with a word: the subject and sections, what is dimensioned / labelled, the view.
  Assumptions still listed.
- **Medium** (a bay, a frame, two or three views, a model import): the full template below, about ten lines.
- **Large** (a building, several connections, more than three views, or anything the tool has no generator for):
  the full template plus numbered open questions, and a note of which parts will be schematic. Do not start until
  the open questions are answered.

Keep it short: a brief for a simple figure is ten lines. Write values, not adjectives ("purlins Z25019 at 1200
from the eave", not "purlins at reasonable spacing"). Where the request leaves a choice that changes the
drawing (which bay, which side, real sections or sketch), ask under Open points rather than guessing.

## Machine-readable copy

Next to the Markdown brief write `brief.toml` with the lists a machine can check against the scene and the
build (`steelfig brief-check brief.toml scene.toml [build log]`):

```toml
figure = "colbase"
parts = ["610UB113 column", "base plate", "holding-down bolts", "grout", "footing"]   # each must be a key line
dims = ["487", "120"]                                   # each must be a dimension text in the scene
views = ["base3d", "baseplan"]                          # each must be a [[view]]
assumptions = ["bolt size", "footing size"]             # reported to the person, kept in the caption / key
```

After confirmation: write the scene file straight from the brief (one line of the brief → one table of the
scene) and build it **plain** first (`--quick --check --plain`): no labels, no dimensions. Show that render to the
person and ask whether the geometry is right (sections, positions, connections, what is cut away). Only after
they agree, add the annotation (`steelfig annotate`), run the checks, compare with the brief, then render full
size. Geometry mistakes are cheap to fix before labels are placed and expensive after.
