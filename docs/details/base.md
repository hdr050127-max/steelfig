# Pinned base plate

**Parts**: base plate fillet-welded to the column; bedding grout; four holding-down bolts close to the column
axis (inside the flange faces, 60 mm in); location tubes and anchor plates not drawn; footing schematic.
**Rules** (`connections.base`, `connections.defaults`):
- plate at least 100 mm larger all round than the column, thickness ≥ column flange thickness, dimensions rounded
  up to 50 mm [SCI P358 §7.3]; the depth rule gives 20 / 25 / 32 / 40 mm
- bedding (grout) 20–40 mm [SCI P398 §5.4] (25–50 in P358 §7.3); 40 modelled
- holding-down bolts class 8.8: M20 minimum, M24 appropriate for most bases, M30 for substantial ones [SCI P398 §5.3;
  P358 §7.2 recommends M24 for plates up to 50 mm]; holes d + 6 [P358 §7.2]
- fillet welds 6 or 8 mm leg along the outside of the flanges [P358 §7.2; AS 4100 Table 9.6.3.2 minimum size]
- a pinned base keeps the bolts close to the column axis so the base has little moment capacity
**Sources**: SCI P358 §7, SCI P398 §5; AS 4100 Cl 9.6.3.2. See `SOURCES.md`.
**To verify**: the 60 mm inside-the-flange bolt position is ASSUMPTION (common Australian pinned-base practice);
SCI's simple bases put the four bolts outside the section (P358 §7.3) — both are used; choose by `bolts_in`.
