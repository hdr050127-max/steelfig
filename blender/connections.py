"""connections: standard steel connections generated from the member sections, so that plates, bolts and
stiffeners land where the real detail puts them and nothing has to be placed by hand. Each generator returns
    dict(cuts={member_name: {"cut0": plane} | {"cut1": plane}}, build=callable, anchors={})
The scene builder applies the cuts when it creates the members (the rafter stops at the end-plate face, the
column stops under the roof, the column base starts above the base plate) and calls build() afterwards; build()
adds the parts and fills `anchors` (points for the overlay: plate, bolt, stiffener, …).
Proportions follow SCI P398 / P358 and common Australian practice: end plates 20 mm, bolts 45 mm
either side of the web, rows 55–60 mm from each flange, stiffeners 12–16 mm, base plate 20 mm on 40 mm grout.
Units metres. `line` is an assembly.Line (the rafter TOP line); members are referenced by scene name."""
import math
from mathutils import Vector
import bfig as B
import rationale as RA
from steelfig import sections as SEC_DB

X = Vector((1, 0, 0)); Y = Vector((0, 1, 0)); Z = Vector((0, 0, 1))


def defaults(depth):
    """connection proportions by the depth (m) of the connected beam / column, following common Australian
    practice (SCI P398 standardisation, ASI): bolt size, end-plate thickness, bolt gauge from the web,
    row distance from the flange, stiffener and base-plate thickness, holding-down bolt."""
    if depth < 0.32:   return dict(bolt="M16", ep_t=0.016, bolt_in=0.040, row_off=0.045, stiff_t=0.010, cap_t=0.016, plate_t=0.020, hd_bolt="M20")
    if depth < 0.47:   return dict(bolt="M20", ep_t=0.020, bolt_in=0.045, row_off=0.055, stiff_t=0.012, cap_t=0.020, plate_t=0.025, hd_bolt="M24")
    if depth < 0.62:   return dict(bolt="M24", ep_t=0.025, bolt_in=0.050, row_off=0.060, stiff_t=0.016, cap_t=0.020, plate_t=0.032, hd_bolt="M24")
    return dict(bolt="M24", ep_t=0.032, bolt_in=0.055, row_off=0.065, stiff_t=0.020, cap_t=0.025, plate_t=0.040, hd_bolt="M30")


def _fill(kw, depth):
    """resolve None values in kw from defaults(depth)."""
    d = defaults(depth)
    return {k: (d[k] if v is None and k in d else v) for k, v in kw.items()}


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
def knee(name, line, x_col, col, col_sec, raf, raf_sec, M, side=1, ep_t=None, ep_ext=None, bolt=None, stiff_t=None,
         diagonal=False, bolt_in=None, row_off=None, y=0.0):
    """rigid knee: the rafter (top on `line`) ends on an extended end plate bolted to the inside flange of the
    column at x_col (web along x); bolts in two columns 45 mm off the web, a row above and below each rafter flange;
    column stiffeners in line with the rafter flanges; optional diagonal panel-zone stiffener. side = +1 when the
    rafter runs towards +x from the column. The plate runs past the top bolt row by the edge distance and the column
    is kept up to the plate top, so the top row has a column flange to bolt to. y: position along the building."""
    C, R = _sec(col_sec), _sec(raf_sec)
    dC, tfC, twC, bfC = C["d"], C["tf"], C["tw"], C["b"]; dR, tfR, bfR = R["d"], R["tf"], R["b"]
    g = _fill(dict(ep_t=ep_t, bolt=bolt, stiff_t=stiff_t, bolt_in=bolt_in, row_off=row_off), dR)
    ep_t, bolt, stiff_t, bolt_in, row_off = g["ep_t"], g["bolt"], g["stiff_t"], g["bolt_in"], g["row_off"]
    df = SEC_DB.bolt(bolt)["d"]; ep_ext = row_off + 1.5 * df if ep_ext is None else ep_ext
    xf = x_col + side * dC / 2                           # inside flange face of the column
    xp = xf + side * ep_t                                # rafter end face (plate face)
    RA.note(name, "end plate %.0f mm thick, %s bolts, gauge %.0f mm about the web, rows %.0f mm from each rafter flange, stiffeners %.0f mm" % (
        ep_t * 1000, bolt, 2 * bolt_in * 1000, row_off * 1000, stiff_t * 1000), "sized by the rafter depth %.0f mm (connections.defaults)" % (dR * 1000), "asi_ep")
    RA.note(name, "rafter ends on the plate face %.0f mm off the column flange; plate and column top %.0f mm past the rafter top" % (ep_t * 1000, ep_ext * 1000),
           "the plate bears on the column flange; the bolt row above the rafter needs column flange behind it and an edge distance to the plate end", "sci_p398")
    RA.note(name, "column stiffeners in line with both rafter flanges", "flange forces of a moment connection go into the column web as concentrated loads", "asi_ep")
    RA.check(ep_ext - row_off >= 1.5 * df - 1e-9, name, "bolt row %.0f mm from the plate end" % ((ep_ext - row_off) * 1000), "edge")
    RA.check(2 * bolt_in >= 2.5 * df, name, "bolt gauge %.0f mm: minimum pitch 2.5 d_f" % (2 * bolt_in * 1000), "pitch")
    n = line.normal(x_col + side * 0.1); t = line.tangent(x_col + side * 0.1)
    ptop = line.at(x_col)                                # roof line over the column axis
    cuts = {col: {"cut1": (ptop + n * ep_ext, n)}, raf: {"cut0": (line.at(xp), side * X)}}
    anchors = {}

    def build():
        pk = line.at(xp); zt = pk.z; zb = zt - dR / n.z          # plate top / bottom at the rafter faces (vertical)
        B.plate(name + "_ep", Vector((xf + side * ep_t / 2, y, (zt + zb) / 2)), X, Y, (ep_t, bfR + 0.02, zt - zb + 2 * ep_ext), M["steel"])
        rows = (zt + row_off, zt - tfR - row_off, zb + tfR + row_off, zb - row_off)
        _bolt_group(name + "_b", Vector((xf + side * (ep_t - tfC) / 2, y, 0)), X, Z, Y, rows, (-bolt_in, bolt_in), bolt, ep_t + tfC, M["dark"])
        for z in (zt - tfR / 2, zb + tfR / 2):             # column stiffeners in line with the rafter flanges
            for sy in (-1, 1):
                B.plate("%s_st%+d_%.3f" % (name, sy, z), Vector((x_col, y + sy * (twC / 2 + (bfC / 2 - twC / 2) / 2), z)), X, Y,
                        (dC - 2 * tfC, bfC / 2 - twC / 2 - 0.004, stiff_t), M["light"])
        if diagonal:
            for sy in (-1, 1):
                a = Vector((x_col - side * (dC / 2 - tfC), y + sy * 0.06, zb + tfR)); b = Vector((x_col + side * (dC / 2 - tfC), y + sy * 0.06, zt - tfR))
                u = (b - a).normalized(); a, b = a + u * 0.07, b - u * 0.07
                B.plate("%s_dg%+d" % (name, sy), (a + b) / 2, b - a, Y, ((b - a).length, 0.10, stiff_t), M["light"])
        anchors.update(ep=(xp, y - bfR / 2 - 0.01, zb - ep_ext / 2), bolt=(xp + side * 0.02, y - bolt_in, rows[0]), bolt2=(xp + side * 0.02, y - bolt_in, rows[3]),
                       stiff=(x_col, y - bfC / 2, zb + tfR / 2), face=(xp, y, (zt + zb) / 2))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- splice: two end plates back to back on the roof line
def splice(name, line, x, a, a_sec, b, b_sec, M, ep_t=None, ep_ext=None, bolt=None, bolt_in=None, row_off=None, y=0.0, b_end="cut0"):
    """bolted end-plate splice at horizontal position x between member a (ends there) and member b (starts
    there); plates span the deeper section and run past the outer bolt rows by the edge distance; bolt rows above and
    below each flange of the shallower one. y: position along the building. b_end: "cut1" when b is declared
    running towards x (a rafter from its knee up to the ridge)."""
    A_, B_ = _sec(a_sec), _sec(b_sec)
    n = line.normal(x); dmax = max(A_["d"], B_["d"]); dmin = min(A_["d"], B_["d"]); tf = min(A_["tf"], B_["tf"]); bf = max(A_["b"], B_["b"])
    g = _fill(dict(ep_t=ep_t, bolt=bolt, bolt_in=bolt_in, row_off=row_off), dmin)
    ep_t, bolt, bolt_in, row_off = g["ep_t"], g["bolt"], g["bolt_in"], g["row_off"]
    df = SEC_DB.bolt(bolt)["d"]; ep_ext = row_off + 1.5 * df if ep_ext is None else ep_ext
    cuts = {a: {"cut1": (line.at(x - ep_t), X)}, b: {b_end: (line.at(x + ep_t), X)}}
    anchors = {}
    RA.note(name, "two end plates %.0f mm back to back at x = %.3f m, %s bolts above and below each flange of the shallower section" % (ep_t * 1000, x, bolt),
           "plates span the deeper section; the bolts work on the shallower flanges", "sci_p398")
    RA.check(ep_ext - row_off >= 1.5 * df - 1e-9, name, "bolt row %.0f mm from the plate end" % ((ep_ext - row_off) * 1000), "edge")

    def build():
        ps = line.at(x); zt = ps.z; zb = zt - dmax / n.z
        for s_, dx in (("a", -ep_t / 2), ("b", ep_t / 2)):
            B.plate("%s_p%s" % (name, s_), Vector((x + dx, y, (zt + zb) / 2)), X, Y, (ep_t, bf + 0.02, zt - zb + 2 * ep_ext), M["steel"])
        zbs = zt - dmin / n.z
        rows = (zt + row_off, zt - tf - row_off, zbs + tf + row_off, zbs - row_off)
        _bolt_group(name + "_b", Vector((x, y, 0)), X, Z, Y, rows, (-bolt_in, bolt_in), bolt, 2 * ep_t, M["dark"])
        anchors.update(ep=(x, y - bf / 2 - 0.01, zb - ep_ext / 2), bolt=(x + 0.02, y - bolt_in, rows[0]), bolt2=(x + 0.02, y - bolt_in, rows[3]), face=(x, y, (zt + zb) / 2))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- cap: rafter continuous over a column, cap plate
def cap(name, line, x, col, col_sec, raf_sec, M, cap_t=None, bolt=None, stiff_t=None, y=0.0):
    """pinned cap: the rafter (continuous) sits on a cap plate on top of the column at x; bolts just outside
    the column walls (SHS) or flanges (UC); rafter web stiffeners over the column walls. y: position of the
    rafter and column along the building (the line itself is in y = 0)."""
    C, R = _sec(col_sec), _sec(raf_sec); n = line.normal(x)
    dR, tfR, twR, bfR = R["d"], R["tf"], R["tw"], R["b"]
    g = _fill(dict(cap_t=cap_t, bolt=bolt, stiff_t=stiff_t), dR); cap_t, bolt, stiff_t = g["cap_t"], g["bolt"], g["stiff_t"]
    cw = C["b"] if C["row"]["type"] in ("SHS", "RHS", "CHS") else C["d"]        # column size along x
    tt = line.tangent(x)
    off = Y * y
    under = line.at(x) + off - n * dR                                            # underside of the rafter over the column axis
    cuts = {col: {"cut1": (under - n * cap_t, n)}}                              # column top cut parallel to the roof
    anchors = {}
    RA.note(name, "cap plate %.0f mm on the roof slope, column cut parallel to the roof, %s bolts 45 mm outside the column walls, web stiffeners over the walls" % (cap_t * 1000, bolt),
           "a flat plate under a sloping rafter would leave a wedge; bolts cannot be inside a tube; the rafter web must carry the wall reactions", "sci_p398")

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
                       ws=tuple(under - tt * (cw / 2 - 0.005) + Vector((0, -bfR / 2 + 0.02, 0)) + n * (dR / 2 - 0.1)), col=(x, y - C["b"] / 2, under.z - 0.6))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- base: pinned base plate with four holding-down bolts
def base(name, x, col, col_sec, M, z0=0.0, plate_t=None, grout=0.040, bolt=None, footing=(1.3, 0.9, 0.6), bolts_in=0.060, y=0.0):
    """base plate on grout on a concrete footing; four anchor bolts 60 mm inside the flange faces of an I section,
    45 mm outside the walls of a tube (a bolt cannot be inside a tube); pinned. y: position along the building."""
    C = _sec(col_sec); dC, bfC = C["d"], C["b"]
    g = defaults(dC); plate_t = plate_t or g["plate_t"]; bolt = bolt or g["hd_bolt"]
    tube = C["row"]["type"] in ("SHS", "RHS", "CHS")
    bx = dC / 2 + 0.045 if tube else dC / 2 - bolts_in                           # bolts from the column axis along x
    px = 2 * bx + 0.08 if tube else dC + 0.14                                    # base plate along x
    df = SEC_DB.bolt(bolt)["d"]
    cuts = {col: {"cut0": (Vector((x, y, z0 + grout + plate_t)), Z)}}
    anchors = {}
    RA.note(name, "base plate %.0f mm on %.0f mm grout, four %s holding-down bolts %s" % (plate_t * 1000, grout * 1000, bolt, "45 mm outside the tube walls" if tube else "%.0f mm inside the flange faces" % (bolts_in * 1000)),
           "pinned base: bolts close to the column axis give little moment capacity; a bolt cannot be inside a tube; grout takes the levelling tolerance", "sci_p358_base")
    RA.check(px / 2 - bx >= 1.5 * df, name, "holding-down bolt %.0f mm from the base plate end" % ((px / 2 - bx) * 1000), "edge")

    def build():
        B.plate(name + "_foot", Vector((x, y, z0 - footing[2] / 2 - 0.0)), X, Y, footing, M["conc"])
        objs, top = B_base(name, Vector((x, y, z0)), (px, bfC + 0.10), plate_t, M, grout, bolts=[(sx * bx, sy * 0.06) for sx in (-1, 1) for sy in (-1, 1)],
                           bolt_dia=df)
        anchors.update(bp=(x + px / 2 - 0.02, y - bfC / 2 - 0.05, z0 + grout + plate_t / 2), ab=(x + bx, y - 0.06, top.z + 0.03), ab2=(x - bx, y - 0.06, top.z + 0.03),
                       grout=(x + px / 2, y - bfC / 2 - 0.05, z0 + grout / 2), foot=(x + 0.25, y - footing[1] / 2, z0 - 0.25), col=(x + dC / 2, y - bfC / 2 + 0.02, z0 + 1.1))
    return dict(cuts=cuts, build=build, anchors=anchors)


def B_base(name, base_pt, size, t, M, grout, bolts, bolt_dia):
    import assembly as A
    return A.base_plate(name + "_bp", base_pt, size, t, M["steel"], grout, M["grout"], bolts, bolt_dia, M["dark"])


# ---------------------------------------------------------------- wsp: secondary beam into a primary web, web side plate
def wsp(name, x, y, side, end, toes, sec, sec_sec, pri_sec, top, members, M, bolt="M20", rows=3, pitch=0.060, fin_t=0.010, fin_h=0.180, fin_w=0.130,
        bolt_off=0.090, gap=0.010, cope_len=0.110, cope_d=0.035, weld=0.006):
    """simple shear connection, secondary top flush with the primary top: a fin plate welded to the primary web
    (the primary runs along x with its web at y), a column of bolts through the fin and the secondary web, the
    secondary flanges and the top of its web coped clear of the primary flange. The secondary runs along y from
    the primary towards `side` (+1 / -1), with its web back face on the member line at x and its toes towards
    `toes` in x; the fin is on the back of the web, away from the toes."""
    P, S = _sec(pri_sec), _sec(sec_sec); twP, tfP = P["tw"], P["tf"]; r1 = float(P["row"]["r1"]) / 1000
    d, bf, tf, tw = S["d"], S["b"], S["tf"], S["tw"]; df = SEC_DB.bolt(bolt)["d"]
    face = y + side * twP / 2                                                    # primary web face
    zc = top - d / 2; zr = [zc + pitch * (k - (rows - 1) / 2) for k in range(rows)]; yb = face + side * bolt_off
    cuts = {sec: {end: (Vector((x, face + side * gap, top)), Y)}}
    anchors = {}
    RA.note(name, "web side plate %.0f x %.0f x %.0f mm welded to the primary web, %d %s 8.8/S at %.0f mm pitch, secondary stops %.0f mm off the primary web" % (
        fin_h * 1000, fin_w * 1000, fin_t * 1000, rows, bolt, pitch * 1000, gap * 1000), "a simple shear connection: bolts in one line near mid-depth of the secondary web, the fin carries the reaction to the primary web", "assume")
    RA.note(name, "secondary top flush with the primary top; flanges coped back %.0f mm from the primary web centre, top of its web coped %.0f mm" % (cope_len * 1000, cope_d * 1000),
           "the secondary must clear the primary flange (half width %.0f mm) and root radius, and any web stiffeners" % (P["b"] / 2 * 1000), "assume")
    RA.check(pitch >= 2.5 * df, name, "bolt pitch %.0f mm" % (pitch * 1000), "pitch")
    RA.check(fin_h / 2 - pitch * (rows - 1) / 2 >= 1.5 * df, name, "top bolt %.0f mm from the fin plate edge" % ((fin_h / 2 - pitch * (rows - 1) / 2) * 1000), "edge")
    RA.check(fin_w - bolt_off >= 1.5 * df, name, "bolt line %.0f mm from the fin plate end" % ((fin_w - bolt_off) * 1000), "edge")
    RA.check(zr[-1] <= top - cope_d - 1.5 * df, name, "top bolt %.0f mm below the web cope" % ((top - cope_d - zr[-1]) * 1000), "edge")
    RA.check(zc + fin_h / 2 <= top - tfP - r1, name, "fin plate top %.0f mm below the primary top: must clear the primary flange root" % ((top - zc - fin_h / 2) * 1000), "assume")
    RA.check(cope_d >= tfP + r1, name, "web cope %.0f mm deep: must clear the primary flange root" % (cope_d * 1000), "assume")
    RA.check(cope_len >= P["b"] / 2, name, "flange cope %.0f mm: must clear the primary flange tip" % (cope_len * 1000), "assume")

    def build():
        ob = members[sec]; xm = x + toes * bf / 2; ym = y + side * cope_len / 2
        for k, (zt, zb) in enumerate(((top + 0.02, top - cope_d), (top - d + tf, top - d - 0.02))):
            cut = B.plate("%s_cope%d" % (name, k), Vector((xm, ym, (zt + zb) / 2)), X, Y, (bf + 0.04, cope_len, zt - zb), M["steel"])
            B.boolean_cut(ob, [cut]); B.delete([cut])
        B.plate(name + "_fin", Vector((x - toes * fin_t / 2, face + side * fin_w / 2, zc)), X, Y, (fin_t, fin_w, fin_h), M["steel"])
        for k, z in enumerate(zr):
            B.bolt("%s_b%d" % (name, k), Vector((x + toes * (tw - fin_t) / 2, yb, z)), X, df, fin_t + tw, M["dark"])
        for s_ in (0, 1):
            xw = x - toes * fin_t * s_
            B.weld_line("%s_w%d" % (name, s_), Vector((xw, face, zc - fin_h / 2)), Vector((xw, face, zc + fin_h / 2)), weld, (toes if s_ == 0 else -toes) * X, side * Y, M.get("weld", M["steel"]))
        anchors.update(fin=(x - toes * fin_t, face + side * fin_w * 0.35, zc - fin_h * 0.25), bolt=(x - toes * (fin_t + 0.012), yb, zr[0]), cope=(x + toes * bf * 0.6, y + side * cope_len, top),
                       web=(x, y + side * (cope_len + 0.15), zc))
    return dict(cuts=cuts, build=build, anchors=anchors)


# ---------------------------------------------------------------- purlin cleats on a rafter top flange
def purlin_cleats(name, purlin_pts, purlin_section, line, M, t=0.008, h=None, bolt="M12", frames=(0.0,), flip=False):
    """plate cleat welded to the top flange under each purlin at each frame y, the purlin web bolted to it (two bolts),
    on the face of the web that has no flange in the way (upslope for a Z, the back for a C). flip: the purlins are
    flipped, as on the slope where the line's tangent runs downhill."""
    P = _sec(purlin_section); d = P["d"]; dn = round(d, 2); h = h or dn - 0.005; out = []
    w = 0.050 if dn <= 0.102 else 0.060; t = 0.012 if dn >= 0.30 else t; bolt = ("M20" if dn >= 0.30 else "M16") if bolt == "M12" else bolt   # Stramit cleat table: W, t, hole
    df = SEC_DB.bolt(bolt)["d"]
    fs = 1 if P["row"]["type"] == "Z" else -1; lo = 0.040 if dn <= 0.102 else (0.055 if dn <= 0.25 else 0.065); hi = lo + dn - 0.09   # holes at B and B + X
    RA.note(name, "cleat %.0f x %.0f mm plate, %.0f high, 2 %s through the purlin web, on the flange-free face" % (w * 1000, t * 1000, h * 1000, bolt),
           "the purlin web is the part that bolts; the cleat keeps it upright and carries the load into the rafter top flange; width, thickness, bolt and hole positions from the manufacturer's cleat table", "stramit")
    RA.note(name, "height %.0f, holes %.0f and %.0f above the base" % (h * 1000, lo * 1000, hi * 1000), "Stramit gives width, thickness and bolt; the height and hole positions are the Stramit cleat table (which itself gives 60 wide and M16)", "stramit")
    RA.check(h - hi >= 1.5 * df - 1e-9, name, "cleat bolt %.0f mm from the cleat end" % ((h - hi) * 1000), "edge")
    RA.check(hi - lo >= 2.5 * df, name, "cleat bolt pitch %.0f mm" % ((hi - lo) * 1000), "pitch")
    for fy in frames:
        for k, p in enumerate(purlin_pts):
            q = Vector(p) + Y * fy; n = line.normal(p.x); tt = line.tangent(p.x) * (-1 if flip else 1)
            c = q + tt * fs * (P["t"] / 2 + t / 2 + 0.001) + n * h / 2
            out.append(B.plate("%s%d_%g" % (name, k, fy), c, Y, n, (w, h, t), M["steel"]))
            for dz in (lo, hi):
                B.cyl("%s%d_%g_b%.2f" % (name, k, fy, dz), q + n * dz, tt, df / 2, t + P["t"] + 0.02, M["dark"], segments=12)["clash_ok"] = 1
    return out


def girt_cleats(name, x, levels, frames, girt_section, outward, M, t=0.008, h=None, bolt="M12"):
    """plate cleat welded to the column outer flange under the web of each Z or C girt at each frame y, two bolts
    through the web. A girt web is horizontal, so the cleat is too; it sits on the face without the inner flange."""
    P = _sec(girt_section); d = P["d"]; dn = round(d, 2); h = h or dn - 0.005; out = []
    w = 0.050 if dn <= 0.102 else 0.060; t = 0.012 if dn >= 0.30 else t; bolt = ("M20" if dn >= 0.30 else "M16") if bolt == "M12" else bolt
    df = SEC_DB.bolt(bolt)["d"]
    o = Vector(outward).normalized(); v = Y.cross(o); fs = 1 if P["row"]["type"] == "Z" else -1
    RA.note(name, "cleat %.0f x %.0f mm plate welded to the column flange, %.0f long, 2 %s through the girt web" % (w * 1000, t * 1000, h * 1000, bolt),
           "same arrangement as a purlin cleat turned onto the wall; the girt web is horizontal, the bolts vertical", "stramit")
    RA.check(0.3 * h >= 1.5 * df, name, "cleat bolt %.0f mm from the cleat end" % (0.3 * h * 1000), "edge")
    RA.check(0.4 * h >= 2.5 * df, name, "cleat bolt pitch %.0f mm" % (0.4 * h * 1000), "pitch")
    for fy in frames:
        for k, z in enumerate(levels):
            q = Vector((x, fy, z))
            out.append(B.plate("%s%d_%g" % (name, k, fy), q + o * h / 2 + v * fs * (P["t"] / 2 + t / 2 + 0.001), o, Y, (h, w, t), M["steel"]))
            for dz in (0.3 * h, 0.7 * h):
                B.cyl("%s%d_%g_b%.2f" % (name, k, fy, dz), q + o * dz, v, df / 2, t + P["t"] + 0.02, M["dark"], segments=12)["clash_ok"] = 1
    return out


# ---------------------------------------------------------------- xbrace: an X of angles between two frames
XBRACE = {50: (3, "M16", 0.080, 0.010), 75: (3, "M24", 0.090, 0.012), 90: (3, "M24", 0.140, 0.016), 100: (3, "M30", 0.160, 0.020)}   # typical X bracing table: bolts, cleat plate
GUSSET_A, GUSSET_W = 0.20, 0.26                                                  # half length along the host, reach out from the web centre


def xbrace(name, a0, a1, b0, b1, normal, host_sec, section, M, stiff_t=0.010):
    """two angles crossing between work points on two frames: a0 -> b1 on the +normal face of the plates, a1 -> b0 on
    the -normal face, so they pass without cutting; a pack and one bolt where they cross. At each work point (on the host
    web, at mid-depth): a gusset welded to the web, a cleat plate in the gusset's plane along the brace, the angle's
    leg lapped on the cleat with the bolts of the X bracing table, web stiffeners each side, the gusset slotted over them."""
    H, E = _sec(host_sec), _sec(section); leg, tl = E["d"], E["t"]; N = Vector(normal).normalized()
    if round(leg * 1000) not in XBRACE: raise ValueError("no X bracing table row for a %.0f leg" % (leg * 1000))
    nb, bolt, wp, tp = XBRACE[round(leg * 1000)]; df = SEC_DB.bolt(bolt)["d"]; tw = H["tw"]; end, pitch = 0.050, 0.070; Lp = 2 * end + (nb - 1) * pitch
    an = {"a0": Vector(a0), "a1": Vector(a1), "b0": Vector(b0), "b1": Vector(b1)}; anchors = {}
    RA.note(name, "%s X: cleat %.0f x %.0f x %.0f mm, %d %s 8.8/S at %.0f pitch, %.0f end distances; gusset the same thickness" % (section, Lp * 1000, wp * 1000, tp * 1000, nb, bolt, pitch * 1000, end * 1000),
           "bolt group and plate from the X bracing table for this angle size; the gusset matches the largest cleat", "assume")
    RA.note(name, "gusset %.0f x %.0f x %.0f mm welded to the web at mid-depth; %.0f mm web stiffeners each side, gusset slotted over them" % (2 * GUSSET_A * 1000, (GUSSET_W - tw / 2) * 1000, tp * 1000, stiff_t * 1000),
           "the bracing plane runs through the member at mid-depth, clear of both flanges and of the purlins above; stiffeners keep the thin web from bending under the brace force", "assume")
    RA.note(name, "the angles lie on opposite faces of the plates and cross with a %.0f mm pack and 1 M20 8.8/S" % (tp * 1000),
           "they pass without cutting; the bolt ties them together so each restrains the other out of plane; the pack fills the gap the plate thickness leaves", "assume")
    RA.check(pitch >= 2.5 * df, name, "brace bolt pitch %.0f mm" % (pitch * 1000), "pitch")
    RA.check(end >= 1.5 * df, name, "brace bolt %.0f mm from the plate or angle end" % (end * 1000), "edge")
    RA.check(leg / 2 >= 1.25 * df, name, "brace bolt %.0f mm from the rolled edge of the leg" % (leg / 2 * 1000), "edge")
    RA.check(wp / 2 >= 1.5 * df, name, "brace bolt %.0f mm from the cleat plate edge" % (wp / 2 * 1000), "edge")
    d0 = (an["b1"] - an["a0"]).normalized(); dang = math.degrees(math.acos(abs(d0.dot((an["a1"] - an["a0"]).normalized()))))
    RA.check(30 <= dang <= 60, name, "brace at %.0f deg to the frame member; aim for 30-60 deg" % dang, "assume")

    def end_at(tag, p, q, s, k):
        """cleat, gusset, stiffeners and bolts at work point p for the brace running to q, on face s of the plates."""
        d = (q - p).normalized(); em = (an["a1"] - an["a0"]).normalized(); eo = (d - d.dot(em) * em).normalized()
        r_exit = min(GUSSET_A / abs(d.dot(em)), (GUSSET_W) / d.dot(eo)); r0 = r_exit - 0.06
        gn = "%s_%s" % (name, tag)
        B.plate(gn + "_gusset", p + eo * (tw / 2 + (GUSSET_W - tw / 2) / 2), em, eo, (2 * GUSSET_A, GUSSET_W - tw / 2, tp), M["steel"])
        c = B.plate(gn + "_cleat", p + d * (r0 + Lp / 2), d, N.cross(d), (Lp, wp, tp), M["steel"]); c["clash_ok"] = 1      # welded into the gusset, same plane
        for i in range(nb):
            B.bolt("%s_b%d" % (gn, i), p + d * (r0 + end + i * pitch) + N * s * tl / 2, N, df, tp + tl, M["dark"])
        wst = H["b"] / 2 - tw / 2 - 0.004
        for sg in (-1, 1):
            st = B.plate("%s_st%+d" % (gn, sg), p + eo * sg * (tw / 2 + wst / 2), N, eo, (H["d"] - 2 * H["tf"], wst, stiff_t), M["light"]); st["clash_ok"] = 1   # gusset slotted over it
        for sg in (-1, 1):
            B.weld_line("%s_w%+d" % (gn, sg), p + eo * tw / 2 - em * GUSSET_A + N * sg * tp / 2, p + eo * tw / 2 + em * GUSSET_A + N * sg * tp / 2, 0.006, N * sg, eo, M.get("weld", M["steel"]))
        anchors.update({tag + "_gusset": tuple(p + eo * (tw / 2 + 0.12) + em * 0.14), tag + "_cleat": tuple(p + d * (r0 + Lp * 0.75) + N.cross(d) * wp * 0.3 + N * s * 0.0), tag + "_bolt": tuple(p + d * (r0 + end + pitch) + N * s * (tl + 0.01))})
        return r0

    def angle(tag, p, q, s, r_p, r_q):
        d = (q - p).normalized(); ey = N.cross(d); hl = -ey * leg / 2 + N * s * tp / 2
        B.member("%s_%s" % (name, tag), p + d * r_p + hl, q - d * r_q + hl, section, None, up=ey, align="heel", flip=s < 0)
        anchors[tag] = tuple((p + q) / 2)

    def build():
        ra0 = end_at("a0", an["a0"], an["b1"], 1, 0); rb1 = end_at("b1", an["b1"], an["a0"], 1, 1)
        ra1 = end_at("a1", an["a1"], an["b0"], -1, 2); rb0 = end_at("b0", an["b0"], an["a1"], -1, 3)
        angle("d1", an["a0"], an["b1"], 1, ra0, rb1); angle("d2", an["a1"], an["b0"], -1, ra1, rb0)
        # the two lines cross at the centre of the four work points (a parallelogram)
        pa, u = an["a0"], an["b1"] - an["a0"]; pb, w = an["a1"], an["b0"] - an["a1"]
        cr = u.cross(w); t_ = (pb - pa).cross(w).dot(cr) / cr.dot(cr); xc = pa + u * t_
        e1 = u.normalized(); e2 = N.cross(e1)
        B.plate(name + "_pack", xc, e1, e2, (0.06, 0.06, tp), M["steel"])
        B.bolt(name + "_xb", xc, N, SEC_DB.bolt("M20")["d"], tp + 2 * tl, M["dark"])
        anchors["cross"] = tuple(xc)
    return dict(cuts={}, build=build, anchors=anchors)


# ---------------------------------------------------------------- strut: CHS between two gussets
STRUT = {"114.3": (0.100, 0.160, 0.010, 2, "M20", 0.060), "88.9": (0.080, 0.110, 0.010, 2, "M16", 0.050)}   # typical CHS strut table (ASSUMPTION), type A: attached plate E, F, G, bolts H, I, gauge J


def strut(name, a, b, normal, along, section, M, gusset_t=0.012, reach=GUSSET_W):
    """CHS strut of type A between the gussets at work points a and b: end plate welded to the tube, attached plate welded
    to the end plate and lapped on the gusset face (+normal), two bolts, 20 mm gap between the gusset edge and the end plate."""
    S = _sec(section); key = section.split("x")[0]; N = Vector(normal).normalized(); em = Vector(along).normalized()
    if key not in STRUT: raise ValueError("no CHS strut table row for %s" % section)
    E_, F_, G_, nb, bolt, J = STRUT[key]; df = SEC_DB.bolt(bolt)["d"]; gap = 0.020; pa, pb = Vector(a), Vector(b); axis = (pb - pa).normalized(); anchors = {}
    lap = E_ - gap; ae = lap / 2                                                 # bolts mid-way along the lap
    RA.note(name, "%s strut type A: attached plate %.0f x %.0f x %.0f mm, end plate %.0f square, %d %s 8.8/S at %.0f gauge, %.0f mm gap" % (section, E_ * 1000, F_ * 1000, G_ * 1000, F_ * 1000, nb, bolt, J * 1000, gap * 1000),
           "plate and bolts from the CHS strut table; the strut carries the brace force along the building between the frames", "assume")
    RA.note(name, "end plate taken %.0f mm square" % (F_ * 1000), "the table gives its width only", "assume")
    RA.check(ae >= 1.5 * df, name, "strut bolt %.0f mm from the gusset edge and the plate end" % (ae * 1000), "edge")
    RA.check((F_ - J) / 2 >= 1.5 * df, name, "strut bolt %.0f mm from the attached plate side" % ((F_ - J) / 2 * 1000), "edge")
    RA.check(J >= 2.5 * df, name, "strut bolt gauge %.0f mm" % (J * 1000), "pitch")
    off = N * (gusset_t / 2 + G_ / 2)

    def build():
        for tag, p, sg in (("a", pa, 1), ("b", pb, -1)):
            e = axis * sg; pe = p + e * (reach + gap)
            B.plate("%s_%s_end" % (name, tag), pe + off + e * G_ / 2, em, N, (F_, F_, G_), M["steel"])
            B.plate("%s_%s_att" % (name, tag), pe + off - e * E_ / 2, e, em, (E_, F_, G_), M["steel"])
            for k in (-1, 1):
                B.bolt("%s_%s_b%+d" % (name, tag, k), p + e * (reach - ae) + em * k * J / 2 + N * G_ / 2, N, df, gusset_t + G_, M["dark"])
            anchors.update({tag + "_end": tuple(pe + off + e * G_ / 2 + N * F_ * 0.3), tag + "_bolt": tuple(p + e * (reach - ae) - em * J / 2 + N * (gusset_t / 2 + G_ + 0.01))})
        B.member(name, pa + axis * (reach + gap + G_) + off, pb - axis * (reach + gap + G_) + off, section, None)
    return dict(cuts={}, build=build, anchors=anchors)




TYPES = dict(knee=knee, splice=splice, cap=cap, base=base, wsp=wsp, xbrace=xbrace, strut=strut)
