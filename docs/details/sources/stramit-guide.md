# Stramit Purlins, Girts & Bridging: Detailing & Installation Guide (excerpts, fetched 2026-11-04)

Source: https://www.stramit.com.au/assets/Technical-Resource-Documents/5b51ae3e0e/Purlins-Girts-Bridgin-Detailing-Installation-Guide.pdf
(text extracted with pdftotext; values copied as printed, mm and kg/m).

## C & Z section size & mass range (now in `steelfig/data/purlins.csv`)

| Section | Web D | C flange B | Z flange E | Z flange F | Lip L | t | Mass |
|---|---|---|---|---|---|---|---|
| C/Z100-10/12/15/19 | 102 | 51 | 49 | 53 | 12.5 / 13 / 14 / 15 | 1.0 / 1.2 / 1.5 / 1.9 | 1.77 / 2.11 / 2.61 / 3.29 |
| C/Z150-10/12/15/19/24 | 152 | 64 | 61 | 65 (66 at 2.4) | 14.5 / 15 / 16 / 17 / 18.5 | 1.0 … 2.4 | 2.43 … 5.67 |
| C/Z200-15/19/24 | 203 | 76 | 74 | 79 | 16 / 19.5 / 21 | 1.5 / 1.9 / 2.4 | 4.50 / 5.74 / 7.21 |
| C/Z250-19/24 | 254 | 76 | 74 | 79 | 19 / 20.5 | 1.9 / 2.4 | 6.50 / 8.17 |
| C/Z300-24/30 | 300 | 96 | 93 | 100 | 28 / 31.5 | 2.4 / 3.0 | 10.18 / 12.69 |
| C/Z350-30 | 350 | 125 | 121 | 129 | 30 | 3.0 | 15.19 |

## Cleat nominal dimensions (single cleat; X = hole spacing, B = bottom hole above the base, Y = height, W = width)

| Section | X | B | Y | t | gap | hole D | W | V |
|---|---|---|---|---|---|---|---|---|
| 100 | 40 | 40 | 105 | 8 | 10 | 18 | 50 | 130 |
| 150 | 60 (70 Vic) | 55 (50 Vic) | 145 | 8 | 10 | 18 | 60 | 140 |
| 200 | 110 | 55 | 195 | 8 | 10 | 18 | 60 | 140 |
| 250 | 160 | 55 | 245 | 8 | 10 | 18 | 60 | 140 |
| 300 | 210 | 65 | 305 | 12 | 20 | 22 | 60 | 140 |
| 350 | 260 | 65 | 355 | 12 | 20 | 22 | 60 | 140 |

18 mm holes = M16 bolts (22 mm = M20 for 300 / 350). Downturn-lip sections: add the lip length to B and Y.

## Fly bracing

"If the lower web hole in a lap is used for attaching fly bracing ensure that an additional bolt is used." So
the fly brace bolts to the purlin **web through the lower (lap / cleat) hole**, i.e. B above the purlin bottom
(55 mm for the 150-250 series), not at mid-web. Stramit does not recommend welding to purlins.

## What this changes in the generators (to do in the connections worktree)

- purlin cleat: W × Y × t from the table, two bolts at B and B + X, M16 (M20 for 300/350)
- fly brace web bolt height: B (lower web hole) instead of mid-web; angle end ≥ 1.5 d_f above it; the
  remaining assumptions are the angle size and the rafter-end cleat
