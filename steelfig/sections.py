"""Section catalogue: Australian designations -> dimensions and drawing profiles. Pure Python (also runs inside
Blender). Dimensions from the CSV tables in data/ (mm); profiles are returned in metres as closed polygons in the
(u, v) plane of a member: u along the member's `up` direction (web of an I section, long leg of an angle, depth of
a channel or RHS), v across it. The member axis (ex) is perpendicular to the profile plane.

    >>> find("310UB46.2")["d"]           # 307.2
    >>> profile("200x200x9SHS")          # {"kind": "hollow", "outer": [...], "inner": [...], ...}
"""
import csv, os, re, math

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_db = None


def _norm(s):
    s = str(s).strip().upper().replace(" ", "")
    s = re.sub(r"(\d)\.0(?=\D|$)", r"\1", s)            # 9.0 -> 9
    return s


def _load():
    global _db
    if _db is not None: return _db
    _db = {}
    import glob
    files = [os.path.join(DATA, f) for f in ("i_sections.csv", "channels.csv", "angles.csv", "hollow_sections.csv", "purlins.csv")]
    extra = os.environ.get("STEELFIG_DATA")                       # a folder of your own CSVs with the same columns (own catalogue, other grades)
    if extra: files += sorted(glob.glob(os.path.join(extra, "*.csv")))
    res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "catalogues")
    files += sorted(glob.glob(os.path.join(res, "*.csv")))        # shared resources folder of the repository
    for p in files:
        if not os.path.exists(p): continue
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                rec = {}
                for k, v in r.items():
                    if v is None or v == "": continue
                    try: rec[k] = float(v)
                    except ValueError: rec[k] = v
                rec["designation"] = r["designation"]
                key = _norm(r["designation"])
                _db.setdefault(key, rec)                     # first row wins for the bare key (C450 precedes C350 in the file)
                if rec.get("grade"): _db[key + "/" + rec["grade"]] = rec
    return _db


def find(designation):
    """the catalogue row for a designation (dict, mm), or raise KeyError with suggestions.
    A grade may be appended: "200x200x9SHS/C350"."""
    db = _load(); key = _norm(designation)
    if key in db: return db[key]
    key2 = key.replace("SHS", "").replace("RHS", "").replace("CHS", "")
    near = [d for d in db if "/" not in d and (key2 and key2 in d or d in key)][:8]
    raise KeyError("section %r not in the catalogue%s" % (designation, "; near: " + ", ".join(near) if near else ""))


def search(text):
    db = _load(); t = _norm(text)
    return sorted({r["designation"] for k, r in db.items() if "/" not in k and t in k}, key=_norm)


def kinds():
    return sorted({r["type"] for k, r in _load().items() if "/" not in k})


# ---------------------------------------------------------------- profiles (metres)
def _i(d, bf, tf, tw):
    h, w = d / 2, bf / 2
    return [(-h, -w), (-h, w), (-h + tf, w), (-h + tf, tw / 2), (h - tf, tw / 2), (h - tf, w), (h, w), (h, -w),
            (h - tf, -w), (h - tf, -tw / 2), (-h + tf, -tw / 2), (-h + tf, -w)]


def _channel(d, bf, tf, tw):
    """PFC: web at v = 0 .. tw on the -v side, flanges towards +v; centroid of the drawing at mid-depth, web face at v=0."""
    h = d / 2
    return [(-h, 0), (-h, bf), (-h + tf, bf), (-h + tf, tw), (h - tf, tw), (h - tf, bf), (h, bf), (h, 0)]


def _angle(b1, b2, t):
    """angle with the heel at the origin: long leg b1 along +u, short leg b2 along +v."""
    return [(0, 0), (0, b2), (t, b2), (t, t), (b1, t), (b1, 0)]


def _rect(b, d):
    return [(-d / 2, -b / 2), (-d / 2, b / 2), (d / 2, b / 2), (d / 2, -b / 2)]


def _circle(r, n):
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def _z(d, ft, fb, lip, t):
    """cold-formed Z with lips: bottom flange on u = 0 towards -v, top flange towards +v; web on v in [0, t]."""
    return [(0, -fb), (0, t / 2), (d - t, t / 2), (d - t, ft), (d, ft), (d, -t / 2), (t, -t / 2), (t, -fb)]


def _c(d, ft, fb, lip, t):
    """cold-formed C (lips omitted): u along the depth from the bottom flange, web on v in [0, t], flanges to +v."""
    return [(0, 0), (0, fb), (t, fb), (t, t), (d - t, t), (d - t, ft), (d, ft), (d, 0)]


def profile(designation, segments=32, min_t=0.0):
    """drawing profile for a designation, in metres. Returns dict(kind, pts | outer+inner, d, b, t..., row).
    kind "solid": one closed polygon `pts`; kind "hollow": `outer` and `inner` polygons with equal point counts.
    min_t thickens very thin walls (cold-formed purlins) so they still read at report scale."""
    r = find(designation); typ = r["type"]; S = 1 / 1000
    if typ in ("UB", "UC", "WB", "WC", "TFB"):
        d, bf, tf, tw = r["d"], r["bf"], r["tf"], r["tw"]
        return dict(kind="solid", pts=[(u * S, v * S) for u, v in _i(d, bf, tf, tw)], d=d * S, b=bf * S, tf=tf * S, tw=tw * S, row=r)
    if typ == "PFC":
        d, bf, tf, tw = r["d"], r["bf"], r["tf"], r["tw"]
        return dict(kind="solid", pts=[(u * S, v * S) for u, v in _channel(d, bf, tf, tw)], d=d * S, b=bf * S, tf=tf * S, tw=tw * S, row=r)
    if typ in ("EA", "UA"):
        b1, b2, t = r["b1"], r["b2"], r["t"]
        return dict(kind="solid", pts=[(u * S, v * S) for u, v in _angle(b1, b2, t)], d=b1 * S, b=b2 * S, t=t * S, row=r)
    if typ in ("SHS", "RHS"):
        d, b, t = r["d"], r["b"], r["t"]
        return dict(kind="hollow", outer=[(u * S, v * S) for u, v in _rect(b, d)], inner=[(u * S, v * S) for u, v in _rect(b - 2 * t, d - 2 * t)],
                    d=d * S, b=b * S, t=t * S, row=r)
    if typ == "CHS":
        d, t = r["d"], r["t"]
        return dict(kind="hollow", outer=_circle(d / 2 * S, segments), inner=_circle((d / 2 - t) * S, segments), d=d * S, b=d * S, t=t * S, round=True, row=r)
    if typ in ("Z", "C"):
        d, ft, fb, lip, t = r["d"], r["bf_top"], r["bf_bottom"], r["lip"], max(r["t"], min_t * 1000)
        f = _z if typ == "Z" else _c
        return dict(kind="solid", pts=[(u * S, v * S) for u, v in f(d, ft, fb, lip, t)], d=d * S, b=max(ft, fb) * S, t=t * S, row=r)
    raise KeyError("no profile rule for type %s" % typ)


def bolt(designation):
    """bolt dimensions (metres) from data/bolts.csv: d, pitch, head_af, head_h, nut_h, washer_od, washer_t, hole."""
    with open(os.path.join(DATA, "bolts.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if _norm(r["designation"]) == _norm(designation):
                return {k: (float(v) / 1000 if k not in ("designation", "verified") else v) for k, v in r.items()}
    raise KeyError("bolt %r not in data/bolts.csv" % designation)


if __name__ == "__main__":
    import sys
    for q in sys.argv[1:] or ["UB"]:
        for d in search(q): print(d, {k: v for k, v in find(d).items() if k in ("type", "d", "b", "bf", "tf", "tw", "t", "b1", "b2", "mass_kg_m", "grade")})
