"""Why every part is where it is. Generators call note() for each part they place; the build prints the list and
writes <out>/<figure>_rationale.md so the reasoning can go into the brief, the key or an answer to a tutor.
Each entry: part, what was decided (with the numbers), the rule, and the source — a standard clause, a catalogue, a
standard detail, or ASSUMPTION when it is only common practice we could not point to a document for.
Realism checks call check() with a condition; failures are printed as REALISM lines and listed in the file."""
_notes = []
_fails = []

SRC = {
    "edge": "AS 4100 Cl 9.6.2: minimum edge distance 1.5 d_f (sheared / hand-flame-cut edge), 1.25 d_f (rolled / machine-cut)",
    "pitch": "AS 4100 Cl 9.6.1: minimum bolt pitch 2.5 d_f",
    "hole": "AS 4100 Cl 14.3.5.2: hole 2 mm larger than the bolt up to M24, 3 mm above",
    "purlin": "Stramit purlin & girt manual / Lysaght purlin manual: Z purlin lies with bottom flange downslope, top flange upslope; fly brace to the purlin web (ASSUMPTION for the exact bolt height: mid-web)",
    "flybrace": "common Australian portal-frame practice (e.g. ASI 'Economical structural steelwork', purlin manuals): fly brace = angle from the rafter bottom flange to the purlin web, both sides, at 30-60 degrees",
    "ttw": "TTW standard details ST-30xxx (course drawings): extended end plate knee, bolted end-plate splice, cap plate on SHS, pinned base plate",
    "asi_ep": "ASI standardized structural connections (bolted moment end plate): bolt gauge about the web, rows above and below each flange, plate 20-32 mm",
    "assume": "ASSUMPTION (common practice, no document checked)",
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
    if path: open(path, "w").write(text)
    for part, msg, src in _fails: print("REALISM %s: %s" % (part, msg))
    print("rationale: %d decisions, %d realism check(s) failed%s" % (len(_notes), len(_fails), ", written to " + path if path else ""))
    return text


def reset():
    _notes.clear(); _fails.clear()
