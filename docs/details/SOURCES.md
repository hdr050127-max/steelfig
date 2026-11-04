# Sources used by the detail files

Only standards, industry publications and manufacturers' documents. No course material, no assignments.

| key | document | where |
|---|---|---|
| AS 4100 | AS 4100:2020 Steel structures (Standards Australia). Cl 9.5.1 minimum pitch 2.5 d_f; Cl 9.5.2 / Table 9.5.2 minimum edge distance 1.75 d_f (sheared or hand flame-cut edge), 1.50 d_f (rolled plate, flat bar or section with machine-cut, sawn or planed edge), 1.25 d_f (rolled edge of a rolled section); Cl 9.5.5 holes; Cl 9.6.3.2 / Table 9.6.3.2 minimum fillet weld size; Cl 5.14 load-bearing stiffeners; Cl 14.3.5.2 hole sizes | via a library subscription; keep your copy in `resources/local/` |
| AS/NZS 1252 | High-strength steel fastener assemblies: across flats 27 / 32 / 41 / 50 / 60 for M16 / M20 / M24 / M30 / M36 (nut and head values differ for M20 between editions) | library |
| SCI P398 | *Joints in Steel Construction: Moment-Resisting Joints to Eurocode 3* (SCI/BCSA, 2013, free PDF). §1.2 standardisation: M20 or M24 class 8.8 fully threaded, gauge 90 or 100, pitch 90, S275/S355 fittings; Fig 2.5 end-plate geometry; §2.4 stiffening; §4.4 bolted end-plate splices; §5.3 column base typical details (M20 minimum, M24 appropriate, M30 substantial; anchor plates Table 5.1); §5.4 bedding 20-40 mm | `resources/local/sources/SCI_P398.pdf` |
| SCI P358 | *Joints in Steel Construction: Simple Joints to Eurocode 3* (SCI/BCSA, 2014, free PDF). §2 standard layouts: gauge 90 or 140, pitch 70, end distance 40, edge distance 30, M20 in 22 holes, end plates 150x10 (≤533 deep) / 200x12; §7 column bases: fillet welds 6 or 8 mm, HD bolt holes d + 6, bolts 8.8 M20 (M24 for plates to 50 mm, M36 above), embedment 16-18 d, thread 100 + d, bedding 25-50 mm, plate ≥ 100 mm larger all round than the column, thickness ≥ flange thickness, dimensions rounded up to 50 mm; §8 bracing connections: bolted lap on a gusset welded to the main member, gusset supported on two edges, generous thickness | `resources/local/sources/SCI_P358.pdf` |
| Stramit | *Purlins, Girts & Bridging Detailing & Installation Guide*: C/Z section sizes, cleat nominal dimensions, laps, fly bracing through the lower web hole, no welding to purlins | `resources/catalogues/stramit-purlins-girts-guide-excerpt.md` |
| Liberty / Austube | section property workbooks (AS/NZS 3679.1 open sections, AS/NZS 1163 hollow sections) | `steelfig/data/` |

Eurocode geometry (SCI) is used for the *arrangement* of parts; Australian clauses (AS 4100, AS/NZS 1252) for
distances, holes and welds. Where a number has no line in this table it is an ASSUMPTION and says so.
