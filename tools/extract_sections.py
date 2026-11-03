"""Extract section dimension tables from the OneSteel / Liberty / Austube property workbooks into steelfig/data/*.csv.
Usage: python3 tools/extract_sections.py <open_sections.xlsx> <hollow_sections.xlsx>
(the Canvas copies: 'liberty-steel-hot-rolled-open-sections-properties.xlsx', 'properties-onesteel-hollow-sections.xlsx')"""
import sys, csv, os, re, openpyxl

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "steelfig", "data")
os.makedirs(OUT, exist_ok=True)


def num(v):
    try: return float(str(v).replace("SHS", "").replace("RHS", "").replace("CHS", "").replace("x", "").strip())
    except Exception: return None


def fmt(v):
    if v is None: return ""
    return ("%.6g" % v) if isinstance(v, float) else str(v)


def write(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print("wrote", name, len(rows))


# ---------------------------------------------------------------- open sections (Liberty workbook)
wb = openpyxl.load_workbook(sys.argv[1], data_only=True, read_only=True)
I_rows = []
for sh, typ in (("UB", "UB"), ("UC", "UC"), ("WB", "WB"), ("WC", "WC"), ("TFBs", "TFB")):
    for r in wb[sh].iter_rows(min_row=11, values_only=True):
        if not r[0] or num(r[2]) is None: continue
        des = str(r[0]).strip()
        # Designation, mass, d, bf, tf, tw, r1, d1, Ag, As, Ix, Zx, Sx, rx, Iy, Zy, Sy, ry, J, Iw
        I_rows.append([des, typ, fmt(num(r[1])), fmt(num(r[2])), fmt(num(r[3])), fmt(num(r[4])), fmt(num(r[5])), fmt(num(r[6])), fmt(num(r[7])), fmt(num(r[8]))])
write("i_sections.csv", ["designation", "type", "mass_kg_m", "d", "bf", "tf", "tw", "r1", "d1", "Ag"], I_rows)

C_rows = []
for r in wb["PFCs"].iter_rows(min_row=11, values_only=True):
    if not r[0] or num(r[2]) is None: continue
    C_rows.append([str(r[0]).strip(), "PFC", fmt(num(r[1])), fmt(num(r[2])), fmt(num(r[3])), fmt(num(r[4])), fmt(num(r[5])), fmt(num(r[6])), fmt(num(r[7])), fmt(num(r[8]))])
write("channels.csv", ["designation", "type", "mass_kg_m", "d", "bf", "tf", "tw", "r1", "d1", "Ag"], C_rows)

A_rows = []
for sh, typ in (("EAs", "EA"), ("UAs", "UA")):
    for r in wb[sh].iter_rows(min_row=11, values_only=True):
        if not r[0] or num(r[2]) is None: continue
        des = re.sub(r"\s+", " ", str(r[0]).strip())
        if typ == "EA": b1, b2, t, r1, r2, ag = r[2], r[3], r[4], r[6], r[7], r[9]
        else: b1, b2, t, r1, r2, ag = r[2], r[3], r[4], r[5], r[6], r[8]
        A_rows.append([des, typ, fmt(num(r[1])), fmt(num(b1)), fmt(num(b2)), fmt(num(t)), fmt(num(r1)), fmt(num(r2)), fmt(num(ag))])
write("angles.csv", ["designation", "type", "mass_kg_m", "b1", "b2", "t", "r1", "r2", "Ag"], A_rows)

# ---------------------------------------------------------------- hollow sections (Austube workbook)
wb = openpyxl.load_workbook(sys.argv[2], data_only=True, read_only=True)
H_rows = []
for sh in ("SHSC450", "SHSC350", "RHSC450", "RHSC350"):
    typ, grade = sh[:3], sh[3:]
    d = b = None
    for r in wb[sh].iter_rows(min_row=19, values_only=True):
        if r[0] and str(r[0]).strip().endswith("x"): d = num(r[0])
        if r[1] and str(r[1]).strip().endswith("x"): b = num(r[1])
        t = num(r[2]) if r[2] and str(r[2]).strip().endswith(typ) else None
        if d is None or b is None or t is None or num(r[3]) is None: continue
        des = "%gx%gx%g%s" % (d, b, t, typ)
        H_rows.append([des, typ, grade, fmt(d), fmt(b), fmt(t), fmt(num(r[3])), fmt(num(r[8]))])
for sh in ("CHSC350", "CHS250"):
    grade = "C350" if sh == "CHSC350" else "C250"
    d = None
    for r in wb[sh].iter_rows(min_row=16, values_only=True):
        if r[0] and str(r[0]).strip().endswith("x"): d = num(r[0])
        tcol = 1
        t = num(r[tcol]) if r[tcol] and "CHS" in str(r[tcol]) else None
        if d is None or t is None: continue
        mass, ag = num(r[3]), num(r[7])                       # both CHS sheets: mass col 3, Ag col 7
        H_rows.append(["%gx%gCHS" % (d, t), "CHS", grade, fmt(d), fmt(d), fmt(t), fmt(mass), fmt(ag)])
write("hollow_sections.csv", ["designation", "type", "grade", "d", "b", "t", "mass_kg_m", "Ag"], H_rows)
