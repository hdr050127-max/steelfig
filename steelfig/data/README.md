# Section data

All dimensions in mm, mass in kg/m. Designations are written as the Australian mills print them, so a user types
what the catalogue shows (`310UB46.2`, `200UC59.5`, `250PFC`, `100x100x8 EA`, `150x90x10 UA`, `200x200x9SHS`,
`250x150x6RHS`, `219.1x6.4CHS`, `Z20019`). Lookup is forgiving about spaces, case and a trailing `.0`.

| file | contents | source | status |
|---|---|---|---|
| `i_sections.csv` | UB, UC, WB, WC, TFB: d, bf, tf, tw, r1, d1, Ag | Liberty Steel hot-rolled and structural steel products: the mill's section property workbook (AS/NZS 3679.1 sizes) | verified against the workbook |
| `channels.csv` | PFC | same workbook | verified against the workbook |
| `angles.csv` | EA, UA: b1, b2, t, r1, r2, Ag | same workbook | verified against the workbook |
| `hollow_sections.csv` | SHS, RHS (C350L0, C450L0), CHS (C250, C350): d, b, t, mass, Ag | Austube Mills design capacity tables (the mill's section property workbook); AS/NZS 1163 | verified against the workbook |
| `purlins.csv` | Stramit Z and C purlins: web D, flanges (C: B both sides; Z: E narrow = `bf_top`, F wide = `bf_bottom`), lip L, thickness t, mass | Stramit *Purlins, Girts & Bridging Detailing & Installation Guide*, table "C & Z Section Size & Mass Range" (stramit.com.au, fetched 2026-11-04) | verified against that table; which Z flange is up depends on the installation (laps alternate), the drawing puts the narrow flange up |
| `bolts.csv` | metric bolts: head/nut across flats and heights, washer, hole | AS/NZS 1252 structural assemblies: across flats 27 / 32 / 41 / 50 / 60 for M16 / M20 / M24 / M30 / M36 confirmed from supplier listings of the standard (2026-11-04; the M20 value is the 1983 figure reinstated in the 2016 edition); holes AS 4100 Cl 14.3.5.2 | `partial`: across flats and holes checked, head/nut heights and washers still from memory |

Regenerate the first four files with `python3 tools/extract_sections.py <open.xlsx> <hollow.xlsx>`.
Numbers in these tables are for drawing at true size; they are not a substitute for the catalogue when
you are quoting a capacity or a mass in a report.
