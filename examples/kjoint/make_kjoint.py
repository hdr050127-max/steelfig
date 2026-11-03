"""Annotation for the K-joint renders: 3D view with balloons + force arrows, elevation with centrelines, e, g / q
and the 60 deg angle; both joints stacked, one key. python3 make_kjoint.py <render_dir> <report_dir>"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from steelfig import overlay as O

rd, rep = sys.argv[1], sys.argv[2]; x = r"$\times$"
IMG = "images/steelfig"


def pic(name, w):
    O.flatten(os.path.join(rd, name + ".png"), os.path.join(rep, IMG, name + ".jpg"))
    return O.Pic(os.path.join(IMG, name + ".jpg"), os.path.join(rd, name + ".json"), w)


def k3d(kind):
    lab = [("chord_end", "", -0.3, -0.8, 1), ("weld", "", 0.6, -0.7, 3)]
    lab += ([("diagL", "", -0.8, 0.0, 2), ("mid:gap0,gap1", "", 0.0, 0.95, 4)] if kind == "gap" else [("diagL", "", -0.8, 0.0, 5), ("diagR", "", 0.9, 0.1, 6)])
    f, _ = O.balloon(pic(f"k{kind}_3d", 6.2), lab, [("arrow", "fL#0", "fL#1", O.FARROW, r"$N^*_c$", "south east"), ("arrow", "fR#0", "fR#1", O.FARROW, r"$N^*_t$", "south west", "b")])
    return f


def kel(kind):
    p = pic(f"k{kind}_elev", 6.25)
    d = [("line", ["eL", "eR"], O.CL), ("line", ["axLe"], O.CL), ("line", ["axRe"], O.CL), ("raw", r"\fill (%.3f,%.3f) circle (1.1pt);" % p.pts("I")[0]),
         ("dim", "c0", "I", r"$e$", 1.0 if kind == "gap" else 1.3, "right" if kind == "gap" else "left")]
    d += ([("dim", "gap0", "gap1", r"$g$", 0.5, "above"), ("angle", "I", "eR", "axRe#1", 0.75, r"60$^\circ$")] if kind == "gap" else [("dim", "ov1", "ov0", r"$q$", 0.75, "above")])
    f, _ = O.balloon(p, [], d)
    note = r"$g = 40$ mm; node $e = 35$ mm below the chord axis" if kind == "gap" else r"overlap $q = 58$ mm ($O_v = 50\%$); node $e = 50$ mm above the chord axis"
    return f + r"\\[0.5mm]{\footnotesize " + note + "}"


key = [r"\ball{1}\ chord 200" + x + "200" + x + r"9.0 SHS; the cut end shows the true 9.0 mm wall", r"\ball{2}\ diagonals 100" + x + "100" + x + r"4.0 SHS at 60$^\circ$",
       r"\ball{3}\ fillet weld all round", r"\ball{4}\ gap $g$ between the diagonal toes", r"\ball{5}\ through member (welded to the chord only)",
       r"\ball{6}\ overlapping member: cut to sit partly on \ball{5}", O.dash(O.CL) + r"\ member centrelines; $e$ = distance of the node below (+) or above ($-$) the chord axis"]
body = (O.row([k3d("gap"), kel("gap")]) + r"\\[1mm]{\small (a) K-gap joint}\\[4mm]" + O.row([k3d("overlap"), kel("overlap")]) + r"\\[1mm]{\small (b) K-overlap joint}\\[3mm]"
        + O.keycols(key, 15.4, 2))
O.emit(os.path.join(rep, "figures", "fig_kjoints.tex"), body, "examples/kjoint/make_kjoint.py")
print("preview", O.preview(body, os.path.join(rep, "preview"), "kjoints", cwd=rep))
