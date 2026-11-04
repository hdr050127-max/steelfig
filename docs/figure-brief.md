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
Views        each view: perspective (from where, looking at what) or orthographic (direction, what it crops to);
             size on the page; which views sit side by side
Labels       the numbered parts, in order, with the text of each key line
Style        style sheet; anything that departs from the defaults (colour, line weight)
Checks       what must be true (dimension texts match the model; no members passing through each other;
             purlins on the top flange; bolts either side of the web; …)
Output       fragment name, image folder, preview, PNG for Word?
Open points  what the person must decide before building (numbered questions)
```

Keep it short: a brief for a simple figure is ten lines. Write values, not adjectives ("purlins Z25019 at 1200
from the eave", not "purlins at reasonable spacing"). Where the request leaves a choice that changes the
drawing (which bay, which side, real sections or sketch), ask under Open points rather than guessing.

After confirmation: write the scene file straight from the brief (one line of the brief → one table of the
scene), build with `--quick --check`, compare the preview with the brief line by line, then render full size.
