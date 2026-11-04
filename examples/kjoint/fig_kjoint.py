"""K-gap and K-overlap joints of an SHS Warren truss at true size (the Python-API route).
Chord 150x150x6.0 SHS, diagonals 89x89x3.5 SHS at 45 deg, fillet welds all round; diagonals trimmed to the chord
face with boolean cuts, the overlapping diagonal cut by the through one. Gap joint g = 44 mm (node e = +10 mm below
the chord axis); overlap O_v = 50 % (q = 63 mm, e = -44 mm). Sizes are an illustration, not a design. Each joint gets a 3D view and an orthographic elevation.
Run: steelfig render examples/kjoint/fig_kjoint.py <out_dir> [quick]; then python3 make_kjoint.py <out_dir> <report_dir>"""
import sys, math, os

import bfig as B
from mathutils import Vector

out, quick, opt = B.args()
h0, t0, b1, t1 = 0.150, 0.006, 0.089, 0.0035
th = math.radians(45); W = 0.008                       # weld leg (drawn slightly large so it reads at print size)
Lc, Ld = 0.62, 0.62                                    # half chord length shown, diagonal length above the chord face
dL, dR = Vector((-math.cos(th), 0, math.sin(th))), Vector((math.cos(th), 0, math.sin(th)))


def build(kind):
    B.reset()
    steel, light, weld = B.mat("steel", B.GREY), B.mat("light", B.LIGHT), B.mat("weld", B.WELD)
    e = 0.010 if kind == "gap" else -0.04352              # g = 2(h0/2+e)cot(th) - b1/sin(th): 44 mm; overlap q = 63 mm = 50 % of p
    I = Vector((0, 0, -h0 / 2 - e))                     # intersection of the diagonal centrelines
    tC = (h0 / 2 + e) / math.sin(th)                    # distance from I to the chord face along each axis
    B.shs("chord", (-Lc, 0, -h0 / 2), (Lc, 0, -h0 / 2), h0, t0, light)
    pL0, pL1 = I + 0.0 * dL, I + (tC + Ld) * dL
    pR0, pR1 = I + 0.0 * dR, I + (tC + Ld) * dR
    left = B.shs("diag_L", pL0, pL1, b1, t1, steel)
    right = B.shs("diag_R", pR0, pR1, b1, t1, steel)
    below = B.box("below", (0, 0, -1.0), (4, 4, 2.0), None)   # everything under the chord face
    B.boolean_cut(left, [below]); B.boolean_cut(right, [below])
    cL, axL = B.edge_hits(pL0, pL1, b1, 0.0)
    cR, axR = B.edge_hits(pR0, pR1, b1, 0.0)
    if kind == "overlap":                                # right diagonal sits partly on the left (through) one
        thru = B.solid_prism("thru", I - 0.3 * dL, I + (tC + Ld + 0.3) * dL, b1)
        B.boolean_cut(right, [thru])
    wl = B.weld_ring("weld_L", cL, axL, W, weld)
    wr = B.weld_ring("weld_R", cR, axR, W, weld)
    if kind == "overlap":
        B.boolean_cut(wr, [thru]); B.delete([thru])
    B.delete([below])
    xs = sorted(p.x for p in cL + cR)
    # anchors (3D points) for the TikZ overlay
    A = dict(
        I=tuple(I), cl0=(-Lc, 0, -h0 / 2), cl1=(Lc, 0, -h0 / 2),
        axL=[tuple(I + s * dL) for s in (0, tC + Ld + 0.08)], axR=[tuple(I + s * dR) for s in (0, tC + Ld + 0.08)],
        topL=tuple(I + (tC + Ld) * dL), topR=tuple(I + (tC + Ld) * dR),
        fL=[tuple(I + (tC + Ld + s) * dL) for s in (0.30, 0.04)], fR=[tuple(I + (tC + Ld + s) * dR) for s in (0.04, 0.30)],
        chord=(0.42, -h0 / 2, -0.06), chord_end=(Lc, 0.02, -h0 / 2 + 0.05), diagL=tuple(I + (tC + 0.38) * dL - Vector((0, b1 / 2, 0))),
        diagR=tuple(I + (tC + 0.38) * dR - Vector((0, b1 / 2, 0))), weld=tuple((cR[0] + cR[1]) / 2 + Vector((0, -W, 0))),
        toeL=(xs[1] if kind == "gap" else xs[0], -b1 / 2, 0.0), toeR=(xs[2] if kind == "gap" else xs[3], -b1 / 2, 0.0),
        gap0=(max(p.x for p in cL), 0, 0), gap1=(min(p.x for p in cR), 0, 0),
        ov0=(min(p.x for p in cR), 0, 0), ov1=(max(p.x for p in cL), 0, 0),
        face=(-Lc, 0, 0), face1=(Lc, 0, 0), c0=(0, 0, -h0 / 2),
        eL=(-0.34, 0, -h0 / 2), eR=(0.34, 0, -h0 / 2), angL=tuple(I + (tC + 0.10) * dL),
        axLe=[tuple(I), tuple(I + (0.27 - I.z) / math.sin(th) * dL)], axRe=[tuple(I), tuple(I + (0.27 - I.z) / math.sin(th) * dR)],
    )
    return A, e


for kind in ("gap", "overlap"):
    A, e = build(kind)
    cam = B.setup(cam_loc=(1.25, -1.85, 1.20), target=(0.0, 0.0, 0.10), lens=50, res=(2000, 1500), line=1.4, quick=quick)
    B.render(out, f"k{kind}_3d", A, margin=0.03, bounds_extra=A["fL"] + A["fR"])
    B.ortho_view(cam, "+y", 1.6, (0, 0, 0))                 # elevation at the node, looking north, cropped to the joint
    B.render(out, f"k{kind}_elev", A, crop_pts=[(-0.40, 0, -0.27), (0.40, 0, 0.30)])
    print(kind, "e =", e)
