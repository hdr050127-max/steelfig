# Feedback log

Every correction a person makes to a figure or to the way of working goes here first (date, who, their words,
what changed), and then into the rule it belongs to (`figure-style.md`, `pitfalls.md`, `docs/details/*.md`,
the style sheet, or a generator). A correction that is not written down will be made again.

| date | who | what they said | where it went |
|---|---|---|---|
| 2026-10-09 | user (CIVL3206) | text on top of the picture looks messy; earlier TikZ figures were "too AI" (many colours, small grey text) | figure-style.md: balloons + key only, one accent colour |
| 2026-10-09 | user | draw the explanation in full (dimension lines, centrelines, buckled shapes, tributary areas); only figures the brief / lecturer / tutor want | figure-style.md |
| 2026-11-04 | user | light overlaps at connections are acceptable; parts must connect | clash check threshold 5 cm³ |
| 2026-11-04 | user | every part's position and connection must be explainable and realistic | rationale.py, docs/details/ |
| 2026-11-04 | user | a one-line request must first be expanded into a brief and confirmed | figure-brief.md, SKILL.md step 1 |
| 2026-11-04 | user | steel should look like steel, not a white model; grades may differ | style finishes by product type |
| 2026-11-04 | user | figures came with many sub-views nobody asked for; our own judgement must be stated before it is drawn | figure-brief.md: one view by default, extra views justified and asked |
| 2026-11-04 | user | after the model is built, show the plain render for a geometry check before any annotation | build --plain, SKILL.md step 2 checkpoint |
| 2026-11-04 | user | fly brace: the lower end and cleat hung below the rafter bottom flange, marked on the render as wrong | fly_braces_on rebuilt from TTW ST-30202: cleat in the web-flange corner, 45 deg, bolts on the leg centre line; docs/details/fly_brace.md |
| 2026-11-04 | user | materials a little more real, basic light and shadow, but no long render times | default style: three-point light, soft shadows, coated steel; EEVEE kept, ~3 s per view |
