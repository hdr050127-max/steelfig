# Section data

All dimensions in mm, mass in kg/m. Designations are written as the Australian mills print them, so a user types
what the catalogue shows (`310UB46.2`, `200UC59.5`, `250PFC`, `100x100x8 EA`, `150x90x10 UA`, `200x200x9SHS`,
`250x150x6RHS`, `219.1x6.4CHS`, `Z20019`). Lookup is forgiving about spaces, case and a trailing `.0`.

| file | contents | source | status |
|---|---|---|---|
| `i_sections.csv` | UB, UC, WB, WC, TFB: d, bf, tf, tw, r1, d1, Ag | Liberty Steel hot-rolled and structural steel products (open sections property workbook on CIVL3206 Canvas, 2026) | verified against the workbook |
| `channels.csv` | PFC | same workbook | verified against the workbook |
| `angles.csv` | EA, UA: b1, b2, t, r1, r2, Ag | same workbook | verified against the workbook |
| `hollow_sections.csv` | SHS, RHS (C350L0, C450L0), CHS (C250, C350): d, b, t, mass, Ag | Austube Mills design capacity tables (hollow-section property workbook on CIVL3206 Canvas, 2026); AS/NZS 1163 | verified against the workbook |
| `purlins.csv` | Stramit Z and C purlins: depth, flanges, lip, thickness | typed from memory of the Stramit Purlins & Girts catalogue | **unverified** (`verified=no`): check against the current catalogue before quoting a number |
| `bolts.csv` | metric bolts: head/nut across flats and heights, washer, hole | AS/NZS 1252 (8.8/S) and AS 4100 Cl 14.3.5.2 holes; M20/M24 checked, others from memory | mixed, see `verified` column |

Regenerate the first four files with `python3 tools/extract_sections.py <open.xlsx> <hollow.xlsx>`.
Numbers in these tables are for drawing at true size; they are not a substitute for the catalogue when
you are quoting a capacity or a mass in a report.
