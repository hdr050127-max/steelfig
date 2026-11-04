# Figure brief: column base (pinned)

Purpose      show how a pinned portal-frame column base is built: base plate on grout, four holding-down bolts
             close to the column axis, so the reader sees why it is modelled as a pin
Source       AS 4100 (bolted base plates), SCI P358 section on column bases, docs/details/base.md
Subject      base plate (accent)
Structure    410UB53.7 column, base plate by the depth rule (connections.defaults), 40 mm grout, four holding-down
             bolts 60 mm inside the flange faces, footing 1.3 x 0.9 x 0.6 m (schematic)
             assumed: bolt size from the depth rule; footing size schematic
Explanation  bolt spacing along the column (403 - 120 = 283) and across (120), 3D in (a), plan in (b)
Views        (a) perspective from the south-east; (b) plan with the column cut 350 mm above the plate
Labels       1 column 2 base plate 3 holding-down bolts 4 grout 5 footing (automatic placement)
Style        default
Checks       dimensions vs model; no clashes; REALISM clear
Output       fig_colbase.tex
Open points  bolt size (generator default or specified?); real footing size?
