# Rigid knee: extended end plate bolted to the column flange

**Parts**: rafter (or haunch) end plate extended beyond both flanges; bolts in two lines about the web, a row
above and below each rafter flange; column web stiffeners in line with the rafter flanges; optional diagonal
panel-zone stiffener; the column top cut under the roof line, flush with the top flange.

**Rules used** (`connections.knee`, `connections.defaults`):
- bolts M20 or M24 class 8.8, gauge 90 (M20) or 100 (M24) about the web → `bolt_in` 45 / 50 mm [SCI P398 §1.2]
- rows above and below each flange at 45–65 mm from the flange, i.e. ≥ 1.75 d_f edge to the plate end
  [AS 4100 Table 9.5.2]; vertical pitch between rows ≥ 2.5 d_f [AS 4100 Cl 9.5.1], SCI standard 90
- end plate thickness by rafter depth: 16 / 20 / 25 / 32 mm (ASSUMPTION of common practice; SCI only says
  "relatively thick" for a rigid joint, P398 §1.3); plate width = flange width + 20, extension 75 beyond flanges
- column stiffeners in line with both rafter flanges, thickness 10–20 by depth [AS 4100 Cl 5.14; SCI P398 §2.4]
- rafter ends on the plate face; column kept up to the plate top so the top bolt row has column flange behind it
- holes 2 mm over the bolt up to M24 [AS 4100 Cl 14.3.5.2]

**Sources**: SCI P398 §1.2, §2, Fig 2.5; AS 4100 Cl 9.5, 5.14, 14.3.5.2. See `SOURCES.md`.
**To verify**: plate thickness steps; diagonal stiffener thickness; Australian standard end-plate sizes (ASI
*Standardised Structural Connections*, not consulted).
