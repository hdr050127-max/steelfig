# Rigid knee: extended end plate bolted to the column flange

**Parts**: rafter (or haunch) end plate; bolts in two columns about the web, a row above and below each rafter
flange; column web stiffeners in line with the rafter flanges; optional diagonal panel-zone stiffener; the column
top cut flush under the roof line.

**Rules used** (`connections.knee`, defaults by rafter depth in `connections.defaults`):
- plate thickness 16 / 20 / 25 / 32 mm for rafter depth < 320 / < 470 / < 620 / larger; bolts M16 / M20 / M24 / M24
- bolt gauge 2 × 40–55 mm about the web; rows 45–65 mm from each rafter flange (both ≥ 1.5 d_f edge, 2.5 d_f pitch)
- plate extends 75 mm beyond each flange; plate width = flange width + 20 mm
- stiffeners 10–20 mm, between the column flanges, in line with each rafter flange
- rafter ends on the plate face (column flange face + plate thickness); column cut by the roof plane

**Sources**: ASI *Standardised Structural Connections* (bolted moment end plate: layout of rows and gauge);
TTW course standard details ST-30xxx (knee with extended end plate); AS 4100 Cl 9.6 (edge distance, pitch).
**To verify**: the thickness steps by depth (ASSUMPTION, common practice); diagonal stiffener thickness.
