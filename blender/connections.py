"""connections: standard steel connections generated from the member sections, so that plates, bolts and
stiffeners land where the real detail puts them and nothing has to be placed by hand. Each generator returns
    dict(cuts={member_name: {"cut0": plane} | {"cut1": plane}}, build=callable, anchors={})
The scene builder applies the cuts when it creates the members (the rafter stops at the end-plate face, the
column stops under the roof, the column base starts above the base plate) and calls build() afterwards; build()
adds the parts and fills `anchors` (points for the overlay: plate, bolt, stiffener, …).
Proportions follow common Australian practice (TTW / ASI standard connections): end plates 20 mm, bolts 45 mm
either side of the web, rows 55–60 mm from each flange, stiffeners 12–16 mm, base plate 20 mm on 40 mm grout.
Units metres. `line` is an assembly.Line (the rafter TOP line); members are referenced by scene name."""
import math
from mathutils import Vector
import bfig as B
from steelfig import sections as SEC_DB

X = Vector((1, 0, 0)); Y = Vector((0, 1, 0)); Z = Vector((0, 0, 1))


def _sec(d):
    return SEC_DB.profile(d)


def _bolt_group(name, centre, axis, up, side, rows, cols, bolt, grip, mat):
    bd = SEC_DB.bolt(bolt); out = []
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            p = Vector(centre) + up * r + side * c
            B.bolt("%s_%d_%d" % (name, i, j), p, axis, bd["d"], grip, mat)
    return out


# ---------------------------------------------------------------- knee: rafter end plate bolted to the column flange
def knee(name, line, x_col, col, col_sec, raf, raf_sec, M, side=1, ep_t=0.020, ep_ext=0.075, bolt="M20", stiff_t=0.012,
         diagonal=False, bolt_in=0.045, row_off=0.055):
    """rigid knee: the rafter (top on `line`) ends on an extended end plate bolted to the inside flange of the
    column at x_col (web along x); bolts in two columns 45 mm off the web, a row above and below each rafter flange;
    column stiffeners in line with the rafter flanges; optional diagonal panel-zone stiffener. side = +1 when the
    rafter runs towards +x from the column."""
    C, R = _sec(col_sec), _sec(raf_sec)
    dC, tfC, twC, bfC = C["d"], C["tf"], C["tw"], C["b"]; dR, tfR, bfR = R["d"], R["tf"], R["b"]
    xf = x_col + side * dC / 2                           # inside flange face of the column
    xp = xf + side * ep_t                                # rafter end face (plate face)
    n = line.normal(x_col + side * 0.1); t = line.tangent(x_col + side * 0.1)
    ptop = line.at(x_col)                                # roof line over the column axis
    cuts = {col: {"cut1": (ptop, n)}, raf: {"cut0": (line.at(xp), side * X)}}
    anchors = {}

    def build():
        pk = line.at(xp); zt = pk.z; zb = zt - dR / n.z          # plate top / bottom at the rafter faces (vertical)
        B.plate(name + "_ep", Vector((xf + side * ep_t / 2, 0, (zt + zb) / 2)), X, Y, (ep_t, bfR + 0.02, zt - zb + 2 * ep_ext), M["steel"])
        rows = (zt + row_off, zt - tfR - row_off, zb + tfR + row_off, zb - row_off)
        _bolt_group(name + "_b", Vector((xf + side * (ep_t - tfC) / 2, 0, 0)), X, Z, Y, rows, (-bolt_in, bolt_in), bolt, ep_t + tfC, M["dark"])
        for z in (zt - tfR / 2, zb + tfR / 2):             # column stiffeners in line with the rafter flanges
            for sy in (-1, 1):
                B.plate("%s_st%+d_%.3f" % (name, sy, z), Vector((x_col, sy * (twC / 2 + (bfC / 2 - twC / 2) / 2), z)), X, Y,
                        (dC - 2 * tfC, bfC / 2 - twC / 2 - 0.004, stiff_t), M["light"])
        if diagonal:
            for sy in (-1, 1):
                a = Vector((x_col - side * (dC / 2 - tfC), sy * 0.06, zb + tfR)); b = Vector((x_col + side * (dC / 2 - tfC), sy * 0.06, zt - tfR))
                u = (b - a).normalized(); a, b = a + u * 0.07, b - u * 0.07
                B.plate("%s_dg%+d" % (name, sy), (a + b) / 2, b - a, Y, ((b - a).length, 0.10, stiff_t), M["light"])
        anchors.update(ep=(xp, -bfR / 2 - 0.01, zb - ep_ext / 2), bolt=(xp + side * 0.02, -bolt_in, rows[0]), bolt2=(xp + side * 0.02, -bolt_in, rows[3]),
                       stiff=(x_col, -bfC / 2, zb + tfR / 2), face=(xp, 0, (zt + zb) / 2))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- splice: two end plates back to back on the roof line
def splice(name, line, x, a, a_sec, b, b_sec, M, ep_t=0.020, ep_ext=0.05, bolt="M20", bolt_in=0.045, row_off=0.050):
    """bolted end-plate splice at horizontal position x between member a (ends there) and member b (starts
    there); plates span the deeper section; bolt rows above and below each flange of the shallower one."""
    A_, B_ = _sec(a_sec), _sec(b_sec)
    n = line.normal(x); dmax = max(A_["d"], B_["d"]); dmin = min(A_["d"], B_["d"]); tf = min(A_["tf"], B_["tf"]); bf = max(A_["b"], B_["b"])
    cuts = {a: {"cut1": (line.at(x - ep_t), X)}, b: {"cut0": (line.at(x + ep_t), X)}}
    anchors = {}

    def build():
        ps = line.at(x); zt = ps.z; zb = zt - dmax / n.z
        for s_, dx in (("a", -ep_t / 2), ("b", ep_t / 2)):
            B.plate("%s_p%s" % (name, s_), Vector((x + dx, 0, (zt + zb) / 2)), X, Y, (ep_t, bf + 0.02, zt - zb + 2 * ep_ext), M["steel"])
        zbs = zt - dmin / n.z
        rows = (zt + row_off, zt - tf - row_off, zbs + tf + row_off, zbs - row_off)
        _bolt_group(name + "_b", Vector((x, 0, 0)), X, Z, Y, rows, (-bolt_in, bolt_in), bolt, 2 * ep_t, M["dark"])
        anchors.update(ep=(x, -bf / 2 - 0.01, zb - ep_ext / 2), bolt=(x + 0.02, -bolt_in, rows[0]), bolt2=(x + 0.02, -bolt_in, rows[3]), face=(x, 0, (zt + zb) / 2))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- cap: rafter continuous over a column, cap plate
def cap(name, line, x, col, col_sec, raf_sec, M, cap_t=0.020, bolt="M20", stiff_t=0.010):
    """pinned cap: the rafter (continuous) sits on a cap plate on top of the column at x; bolts just outside
    the column walls (SHS) or flanges (UC); rafter web stiffeners over the column walls."""
    C, R = _sec(col_sec), _sec(raf_sec); n = line.normal(x)
    dR, tfR, twR, bfR = R["d"], R["tf"], R["tw"], R["b"]
    cw = C["b"] if C["row"]["type"] in ("SHS", "RHS", "CHS") else C["d"]        # column size along x
    tt = line.tangent(x)
    under = line.at(x) - n * dR                                                  # underside of the rafter over the column axis
    cuts = {col: {"cut1": (under - n * cap_t, n)}}                              # column top cut parallel to the roof
    anchors = {}

    def build():
        B.plate(name + "_cap", under - n * cap_t / 2, tt, Y, (cw + 0.16, max(bfR, C["b"]) + 0.04, cap_t), M["steel"])
        for sx in (-1, 1):
            for sy in (-1, 1):
                B.bolt("%s_b%+d%+d" % (name, sx, sy), under + tt * sx * (cw / 2 + 0.045) + Vector((0, sy * 0.06, 0)) + n * (tfR - cap_t) / 2, n,
                       SEC_DB.bolt(bolt)["d"], cap_t + tfR, M["dark"])
            for sy in (-1, 1):
                B.plate("%s_ws%+d%+d" % (name, sx, sy), under + tt * sx * (cw / 2 - 0.005) + Vector((0, sy * (twR / 2 + (bfR / 2 - twR / 2) / 2), 0)) + n * dR / 2, n, Y,
                        (dR - 2 * tfR, bfR / 2 - twR / 2 - 0.004, stiff_t), M["light"])
        anchors.update(capp=tuple(under - tt * (cw / 2 + 0.08) + Vector((0, -bfR / 2 - 0.02, 0)) - n * cap_t / 2), bolt=tuple(under + tt * (cw / 2 + 0.045) + Vector((0, -0.06, 0)) - n * (cap_t + 0.02)),
                       ws=tuple(under - tt * (cw / 2 - 0.005) + Vector((0, -bfR / 2 + 0.02, 0)) + n * (dR / 2 - 0.1)), col=(x, -C["b"] / 2, under.z - 0.6))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- base: pinned base plate with four holding-down bolts
def base(name, x, col, col_sec, M, z0=0.0, plate_t=0.020, grout=0.040, bolt="M24", footing=(1.3, 0.9, 0.6), bolts_in=0.060):
    """base plate on grout on a concrete footing; four anchor bolts 60 mm inside the flange faces (pinned)."""
    C = _sec(col_sec); dC, bfC = C["d"], C["b"]
    cuts = {col: {"cut0": (Vector((x, 0, z0 + grout + plate_t)), Z)}}
    anchors = {}

    def build():
        B.plate(name + "_foot", Vector((x + 0.05, 0, z0 - footing[2] / 2 - 0.0)), X, Y, footing, M["conc"])
        objs, top = B_base(name, Vector((x, 0, z0)), (dC + 0.14, bfC + 0.10), plate_t, M, grout, bolts=[(sx * (dC / 2 - bolts_in), sy * 0.06) for sx in (-1, 1) for sy in (-1, 1)],
                           bolt_dia=SEC_DB.bolt(bolt)["d"])
        anchors.update(bp=(x + dC / 2 + 0.05, -bfC / 2 - 0.05, z0 + grout + plate_t / 2), ab=(x + dC / 2 - bolts_in, -0.06, top.z + 0.03), ab2=(x - dC / 2 + bolts_in, -0.06, top.z + 0.03),
                       grout=(x + dC / 2 + 0.07, -bfC / 2 - 0.05, z0 + grout / 2), foot=(x + 0.55, -0.45, z0 - 0.3), col=(x + dC / 2, -bfC / 2 + 0.02, z0 + 1.1))
    return dict(cuts=cuts, build=build, anchors=anchors)


def B_base(name, base_pt, size, t, M, grout, bolts, bolt_dia):
    import assembly as A
    return A.base_plate(name + "_bp", base_pt, size, t, M["steel"], grout, M["grout"], bolts, bolt_dia, M["dark"])


# ---------------------------------------------------------------- purlin cleats on a rafter top flange
def purlin_cleats(name, purlin_pts, purlin_section, line, M, t=0.008, h=None, bolt="M12"):
    """angle cleat welded to the top flange under each purlin, the purlin web bolted to it (two bolts)."""
    P = _sec(purlin_section); d = P["d"]; h = h or 0.6 * d; out = []
    for k, p in enumerate(purlin_pts):
        n = line.normal(p.x); tt = line.tangent(p.x)
        c = Vector(p) - tt * (P["t"] / 2 + t / 2 + 0.001) + n * h / 2          # downslope face of the web (bottom flange side has the lip; schematic)
        out.append(B.plate("%s%d" % (name, k), c, Y, n, (0.10, h, t), M["steel"]))
        for dz in (0.3 * h, 0.7 * h):
            B.cyl("%s%d_b%.2f" % (name, k, dz), Vector(p) + n * dz, tt, SEC_DB.bolt(bolt)["d"] / 2, t + P["t"] + 0.02, M["dark"], segments=12)["clash_ok"] = 1
    return out


TYPES = dict(knee=knee, splice=splice, cap=cap, base=base)
