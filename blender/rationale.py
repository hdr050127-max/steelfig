"""Why every part is where it is. Generators call note() for each part they place; the build prints the list and
writes <out>/<figure>_rationale.md so the reasoning can go into the brief, the key or an answer to a tutor.
Each entry: part, what was decided (with the numbers), the rule, and the source — a standard clause, a catalogue, a
standard detail, or ASSUMPTION when it is only common practice we could not point to a document for.
Realism checks call check() with a condition; failures are printed as REALISM lines and listed in the file."""
_notes = []
_fails = []

# every key also names the knowledge file that states the rule in full (docs/details/)
SRC = {
    "edge": "AS 4100:2020 Table 9.5.2: minimum edge distance 1.75 d_f sheared or hand flame-cut, 1.50 d_f rolled plate, flat bar or section with a machine-cut, sawn or planed edge, 1.25 d_f rolled edge",
    "pitch": "AS 4100:2020 Cl 9.5.1: minimum bolt pitch 2.5 d_f",
    "hole": "AS 4100:2020 Cl 14.3.5.2: standard hole 2 mm larger than the bolt up to M24, 3 mm above",
    "weld": "AS 4100:2020 Table 9.6.3.2: minimum fillet weld size by the thicker part joined; SCI P358 7.2: 6 or 8 mm fillets on base plates",
    "stiff": "AS 4100:2020 Cl 5.14 load-bearing stiffeners at concentrated loads; SCI P398 2.4 column stiffening in line with the beam flanges",
    "sci_p398": "SCI P398 Moment-Resisting Joints (2013) 1.2: M20 / M24 class 8.8, gauge 90 or 100, pitch 90, S275 / S355 fittings; Fig 2.5 end-plate geometry; 4.4 bolted end-plate splices (docs/details/knee.md, splice.md)",
    "sci_p358": "SCI P358 Simple Joints (2014) 2: standard layouts gauge 90 / 140, pitch 70, end distance 40, edge distance 30, M20 in 22 holes (docs/details/cap.md)",
    "sci_p358_base": "SCI P358 7 column bases: plate 100 mm larger all round than the column, thickness >= flange, HD bolts 8.8 M20-M24 (M36 over 50 mm plates), holes d + 6, bedding 25-50 (P398 5.4: 20-40), fillets 6 or 8 (docs/details/base.md)",
    "sci_p358_brace": "SCI P358 8 bracing connections: bolted lap on a gusset welded to the main member, gusset supported on two edges, generous thickness; CHS ends in a slotted T plate (docs/details/xbrace.md)",
    "purlin": "Stramit purlin manuals: Z purlin lies with the narrow flange up, wide flange down; fly brace to the purlin web through the lower web hole (docs/details/fly_brace.md)",
    "flybrace": "common Australian portal-frame practice (purlin manuals, published typical fly brace details): angle from the rafter bottom flange to the purlin web, both sides, at about 45 degrees (docs/details/fly_brace.md)",
    "asi_ep": "ASI Standardised Structural Connections (bolted moment end plate): bolt gauge about the web, rows above and below each flange (not consulted directly; docs/details/knee.md)",
    "stramit": "Stramit Purlins, Girts & Bridging Detailing & Installation Guide (resources/catalogues/stramit-purlins-girts-guide-excerpt.md): cleat nominal dimensions; fly bracing through the lower web hole; no welding to purlins",
    "assume": "ASSUMPTION (typical practice, no document checked; see the To verify list in docs/details/)",
}


def note(part, decision, rule, source):
    _notes.append((part, decision, rule, SRC.get(source, source)))


def check(ok, part, message, source="assume"):
    if not ok: _fails.append((part, message, SRC.get(source, source)))
    return ok


def dump(path=None, title="figure"):
    lines = ["# Why the parts are where they are: %s" % title, ""]
    for part, dec, rule, src in _notes:
        lines.append("- **%s** - %s. Rule: %s. Source: %s" % (part, dec, rule, src))
    if _fails:
        lines += ["", "## Realism checks that failed", ""]
        for part, msg, src in _fails: lines.append("- **%s** - %s (%s)" % (part, msg, src))
    else:
        lines += ["", "All realism checks passed."]
    text = "\n".join(lines) + "\n"
    if path: open(path, "w", encoding="utf-8").write(text)
    for part, msg, src in _fails: print("REALISM %s: %s" % (part, msg))
    print("rationale: %d decisions, %d realism check(s) failed%s" % (len(_notes), len(_fails), ", written to " + path if path else ""))
    return text


def reset():
    _notes.clear(); _fails.clear()
