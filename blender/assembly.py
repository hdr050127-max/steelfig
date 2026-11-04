"""assembly: put catalogue members together into structures. Runs inside Blender on top of bfig.
  Polyline / roof line : Line(points) with top(x), normal(x), along(s) for rafters that change slope
  Patterns             : array(), every_nth(), mirror_y(), frames()
  Connections          : end_plate(), splice(), cap_plate(), base_plate(), bolt_rows(), stiffeners(), fly_brace(),
                         purlins_on(), girts_on(), cleat()
  From a model         : build_model(model, mapping) draws every member of a readers.Model
Every connection function returns the objects it made and the anchor points worth labelling, so figure scripts
can hand them straight to the overlay. Dimensions are in metres; x east, y north (along the building), z up."""
import math
import bpy
from mathutils import Vector
import bfig as B
from steelfig import sections as SEC_DB


# ---------------------------------------------------------------- lines
class Line:
    """a polyline in the xz plane (a rafter line through its nodes, a chord), queried by horizontal x or by slope
    distance. lift shifts the whole line along the local normal (e.g. +d/2 so the line becomes the top face)."""
    def __init__(self, pts, lift=0.0):
        self.P = [Vector((p[0], 0.0, p[-1])) for p in pts]; self.lift = lift

    def seg(self, x):
        for i, (a, b) in enumerate(zip(self.P, self.P[1:])):
            if a.x - 1e-9 <= x <= b.x + 1e-9: return i
        return 0 if x < self.P[0].x else len(self.P) - 2

    def tangent(self, x):
        a, b = self.P[self.seg(x)], self.P[self.seg(x) + 1]
        return (b - a).normalized()

    def normal(self, x):
        t = self.tangent(x); return Vector((-t.z, 0, t.x))

    def at(self, x, y=0.0):
        """point on the (lifted) line at horizontal position x, extended straight beyond the ends. The lift is a
        perpendicular offset, so at horizontal x the lifted line is lift / cos(slope) higher: x itself is kept."""
        i = self.seg(x); a, b = self.P[i], self.P[i + 1]
        z = a.z + (b.z - a.z) * (x - a.x) / (b.x - a.x)
        n = self.normal(x)
        return Vector((x, y, z + (self.lift / n.z if n.z else self.lift)))

    top = at

    def along(self, s, y=0.0, from_end=False):
        """point at slope distance s from the start (or from the end)."""
        if from_end:
            t = self.tangent(self.P[-1].x - 1e-6); return self.at(self.P[-1].x, y) - t * s
        t = self.tangent(self.P[0].x + 1e-6); return self.at(self.P[0].x, y) + t * s

    def length(self):
        return sum((b - a).length for a, b in zip(self.P, self.P[1:]))


# ---------------------------------------------------------------- patterns
def array(fn, start, step, n, name="a"):
    """call fn(i, offset_vector) for i in 0..n-1 with offset = start + i*step (vectors)."""
    out = []
    for i in range(n):
        out.append(fn(i, Vector(start) + Vector(step) * i))
    return out


def every_nth(items, n, start=0):
    return [it for i, it in enumerate(items) if (i - start) % n == 0]


def mirror_y(objs):
    """mirror objects about the xz plane (y -> -y), returns the copies."""
    out = []
    for o in objs:
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
        for v in c.data.vertices: v.co.y = -v.co.y
        for f in c.data.polygons: f.flip()
        c.name = o.name + "_m"; out.append(c)
    return out


def frames(ys, build, **kw):
    """call build(y, **kw) for each longitudinal position: three frames = frames([0, S, 2*S], build_frame)."""
    return [build(y, **kw) for y in ys]


# ---------------------------------------------------------------- connections
def end_plate(name, line_pt, axis, up, depth, width, t, material, extend=(0.05, 0.05), offset=0.0):
    """end plate normal to `axis` at line_pt, spanning the member depth (+ extend above/below) along `up`,
    `width` across. offset shifts the plate centre along `up` (e.g. -d/2 when line_pt is the top face)."""
    ax = Vector(axis).normalized(); up = Vector(up).normalized(); side = ax.cross(up)
    c = Vector(line_pt) + up * (offset + (extend[0] - extend[1]) / 2)
    return B.plate(name, c, up, side, (depth + extend[0] + extend[1], width, t), material)


def bolt_rows(name, centre, axis, up, side, rows, cols, bolt="M20", grip=0.04, material=None):
    """bolt group: rows = list of offsets along `up`, cols = list of offsets along `side`, all through `centre`."""
    bd = SEC_DB.bolt(bolt); out = []
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            p = Vector(centre) + Vector(up).normalized() * r + Vector(side).normalized() * c
            out.append(B.bolt("%s_%d_%d" % (name, i, j), p, axis, bd["d"], grip, material))
    return out


def stiffeners(name, column_pt, col_sec, levels, material, t=0.012, up=(1, 0, 0)):
    """pairs of web stiffeners inside an I column at the given z levels (in line with the beam flanges).
    column_pt: a point on the column axis; col_sec: designation; up: the column's web direction."""
    P = SEC_DB.profile(col_sec); d, bf, tf, tw = P["d"], P["b"], P["tf"], P["tw"]
    up = Vector(up).normalized(); side = Vector((0, 0, 1)).cross(up)
    out = []
    for z in levels:
        for s in (-1, 1):
            c = Vector((column_pt[0], column_pt[1], z)) + side * s * (tw / 2 + (bf / 2 - tw / 2) / 2)
            out.append(B.plate("%s_%g_%d" % (name, z, s), c, up, side, (d - 2 * tf, bf / 2 - tw / 2 - 0.004, t), material))
    return out


def cap_plate(name, top_pt, size, t, material):
    """plate under a beam / over a column, top face at top_pt."""
    return B.plate(name, Vector(top_pt) - Vector((0, 0, t / 2)), (1, 0, 0), (0, 1, 0), (size[0], size[1], t), material)


def base_plate(name, base_pt, size, t, material, grout=0.0, grout_mat=None, bolts=None, bolt_dia=0.024, bolt_mat=None):
    """base plate with its top face at base_pt + t (+ grout below); bolts = list of (dx, dy) positions."""
    objs = []
    if grout: objs.append(B.plate(name + "_grout", Vector(base_pt) + Vector((0, 0, grout / 2)), (1, 0, 0), (0, 1, 0), (size[0] + 0.06, size[1] + 0.06, grout), grout_mat or material))
    objs.append(B.plate(name, Vector(base_pt) + Vector((0, 0, grout + t / 2)), (1, 0, 0), (0, 1, 0), (size[0], size[1], t), material))
    top = Vector(base_pt) + Vector((0, 0, grout + t))
    for i, (dx, dy) in enumerate(bolts or []):
        B.anchor_bolt("%s_ab%d" % (name, i), top + Vector((dx, dy, 0)), bolt_dia, material=bolt_mat or material)
    return objs, top


def fly_brace(name, flange_pt, purlin_pt, material, section="75x75x6 EA", both_sides=True, y_in=0.06):
    """(legacy, schematic) angle(s) from a flange point straight to a purlin point; no connection geometry.
    Prefer fly_braces_on(), which puts the angle against the purlin web and stops it under the top flange."""
    out = []
    for s in ((-1, 1) if both_sides else (1,)):
        p0 = Vector(flange_pt) + Vector((0, s * y_in, 0)); p1 = Vector(purlin_pt)
        p1 = Vector((p1.x, s * abs(p1.y) if p1.y else p1.y, p1.z))
        out.append(B.member("%s%+d" % (name, s), p0, p1, section, material, up=(0, 0, 1), align="heel"))
    return out


def fly_braces_on(name, purlin_pts, purlin_section, member_depth, member_bf, material, bolt_mat=None, section=None,
                  normal=None, which=None, both_sides=True, reach=None, bolt=None, cleat=True, line_tangent=None, member_tf=None, sides=None, member_tw=None):
    """fly braces from the restrained (bottom) flange of a rafter up to the purlins, as TTW-00-DR-ST-30202 Typical Fly
    Brace Detail, placed by the rules below and explained in the rationale file:
      - angle size by rafter depth from the TTW fly brace table, one M12 8.8/S at each end;
      - an 8 mm cleat plate in the corner of the web and the top of the bottom flange, reaching just past the flange tip,
        so the whole lower end sits above the flange; its face is in line with the purlin web face;
      - the angle's long leg lies flat on the cleat and on the purlin web, on the face that has no flange in the way: the
        upslope face of a Z purlin (bottom flange is downslope), the back of a C purlin;
      - the two bolts are on the leg's centre line and the brace is at 45 degrees, which sets how far out along the purlin
        it lands (`reach` overrides it).
    purlin_pts: points from purlins_on (purlin bottom flange on the roof line); normal / line_tangent: roof unit vectors
    (the tangent pointing upslope); member_depth / member_bf / member_tf / member_tw: the rafter section (m); which: purlin
    indices (default every second from the second); sides: which sides of the rafter, e.g. [1] at an end frame (default
    both). Returns (objects, anchors)."""
    import rationale as RA
    pts = [p for p, _ in purlin_pts] if purlin_pts and isinstance(purlin_pts[0], tuple) else list(purlin_pts)
    P = SEC_DB.profile(purlin_section); d_p, t_p = P["d"], P["t"]; ptype = P["row"]["type"]
    given_sec = section; tf = member_tf or 0.012; tw = member_tw or 0.008
    section = section or next(s for dmax, s in ((0.32, "40x40x3 EA"), (0.42, "50x50x3 EA"), (0.62, "65x65x5 EA"), (9.0, "75x75x6 EA")) if member_depth <= dmax)   # <= 310, 410, 610 UB, above
    bolt = bolt or "M12"
    A_ = SEC_DB.profile(section); leg, leg_t = A_["d"], A_["t"]
    df = SEC_DB.bolt(bolt)["d"]; edge = 1.5 * df; end = max(edge, 0.025); t_c = 0.008
    c_w = member_bf / 2 + 0.015 - tw / 2; c_h = max(0.10, 1.2 * leg + 0.04)      # cleat: web face to 15 past the flange tip
    y1 = tw / 2 + 0.6 * c_w; h1 = 0.45 * c_h                                     # lower bolt from the web centre, above the flange top
    h2 = 0.055 if d_p <= 0.26 else 0.065                                         # purlin bolt: the lower web hole (Stramit B)
    RA.note(name, "angle %s with %s 8.8/S at each end for a %.0f mm deep rafter" % (section, bolt, member_depth * 1000),
           "angle by rafter depth: 40x40x3 up to 310 UB, 50x50x3 to 410, 65x65x5 to 610, 75x75x5.5 above (drawn 75x75x6)", "ttw2" if not given_sec else "assume")
    RA.note(name, "8 mm cleat %.0f x %.0f mm in the corner of the web and the top of the bottom flange, %.0f mm past the flange tip" % (c_w * 1000, c_h * 1000, 15),
           "nothing hangs below the flange, the brace pulls on the flange it restrains through the web-flange corner; the size is scaled from the drawing, which gives no dimension", "ttw2")
    out = []; anchors = {}
    if which is None: which = list(range(1, len(pts), 2))
    fs = 1 if ptype == "Z" else -1                      # face of the web that is free of flanges: upslope for Z, back for C
    RA.note(name, "long leg on the %s face of the %s purlin web, in line with the cleat face" % ("upslope" if fs > 0 else "downslope (back)", ptype),
           "the bottom flange of a Z purlin points downslope, so the upslope face of the web is free from the rafter up to the top flange; a C has both flanges one side, so its back is free", "purlin")
    RA.note(name, "purlin bolt %.0f mm above the purlin bottom, the lower web hole" % (h2 * 1000), "Stramit: fly bracing uses the lower web hole; welding to purlins is not recommended; TTW shows the same height", "stramit")
    for k in which:
        p = Vector(pts[k]); n = Vector(normal).normalized() if normal else Vector((0, 0, 1))
        t = Vector(line_tangent).normalized() if line_tangent else Vector((0, 1, 0)).cross(n).normalized()
        face = p + t * fs * (t_p / 2 + 0.001)             # the leg's back lies on this plane
        n1 = -(member_depth - tf) + h1                    # lower bolt height from the purlin bottom (negative: below it)
        r = reach if reach else y1 + (h2 - n1)            # 45 degrees between the two bolts
        for s in (sides or ((-1, 1) if both_sides else (1,))):
            Ys = Vector((0, s, 0))
            b1 = face + n * n1 + Ys * y1; b2 = face + n * h2 + Ys * r
            ex = (b2 - b1).normalized(); ey = (n - n.dot(ex) * ex).normalized(); ez = ex.cross(ey)
            flip = ez.dot(t * fs) < 0
            ob = B.member("%s%d%+d" % (name, k, s), b1 - ex * end - ey * leg / 2, b2 + ex * end - ey * leg / 2, section, material, up=ey, align="heel", flip=flip)
            out.append(ob)
            tag = "%s%d%+d" % (name, k, s)
            ang = math.degrees(math.atan2(ex.dot(n), abs(ex.dot(Ys))))
            RA.check(44 <= ang <= 46 or reach, tag, "brace at %.0f deg; TTW: always 45 deg" % ang, "ttw2")
            RA.check(leg / 2 >= 1.25 * df - 1e-9, tag + " bolt", "bolt %.0f mm from the rolled edge of the leg" % (leg / 2 * 1000), "edge")
            RA.check(end >= edge - 1e-9, tag + " bolt", "bolt %.0f mm from the angle end" % (end * 1000), "edge")
            RA.check(d_p - t_p - h2 >= edge, tag + " bolt", "purlin bolt %.0f mm below the top flange" % ((d_p - t_p - h2) * 1000), "edge")
            for c_ in (b1 - ex * end - ey * leg / 2, b1 - ex * end + ey * leg / 2):   # the angle's lower corners stay above the flange and off the web
                RA.check((c_ - p).dot(n) >= -(member_depth - tf) + 0.002, tag, "angle corner below the bottom flange top", "assume")
                RA.check(abs((c_ - p).dot(Ys)) >= tw / 2 + 0.002, tag, "angle corner into the rafter web", "assume")
            out.append(B.bolt(tag + "_b2", b2 + t * fs * (leg_t - t_p - 0.001) / 2, t, df, t_p + leg_t + 0.001, bolt_mat or material))
            if cleat:
                RA.check(min(c_w - 0.6 * c_w, 0.6 * c_w, h1, c_h - h1) >= edge - 1e-9, tag + " cleat", "cleat bolt too close to a cleat edge", "edge")
                c = p + t * fs * (t_p / 2 + 0.001 - t_c / 2) + n * (-(member_depth - tf) + c_h / 2) + Ys * (tw / 2 + c_w / 2)
                out.append(B.plate(tag + "_cleat", c, n, Ys, (c_h, c_w, t_c), material))
                out.append(B.bolt(tag + "_b1", b1 + t * fs * (leg_t - t_c) / 2, t, df, t_c + leg_t, bolt_mat or material))
            anchors[tag] = tuple((b1 + b2) / 2)
            anchors[tag + "_cleat"] = tuple(b1 - ex * 0.0 - n * h1 * 0.4 + Ys * 0.02)
    return out, anchors


def purlins_on(name, line, spacing, y0, y1, section, material, start=0.0, until=None, up=None, flip_alternate=False, from_end=False, flip=False):
    """Z/C purlins along a roof Line at slope spacing, bottom flange on the line, web along the roof normal."""
    out = []; k = 0
    L = line.length() if until is None else until
    while start + spacing * k <= L + 1e-9:
        p = line.along(start + spacing * k, from_end=from_end)
        n = up or line.normal(p.x)
        out.append((p, B.member("%s%d" % (name, k), p + Vector((0, y0, 0)), p + Vector((0, y1, 0)), section, material, up=n, align="heel",
                                flip=flip != (flip_alternate and k % 2 == 1))))
        k += 1
    return out


def girts_on(name, x, zs, y0, y1, section, material, outward=(-1, 0, 0)):
    """Z/C girts on a wall at x, at the given levels; web pointing outward."""
    return [(Vector((x, 0, z)), B.member("%s%d" % (name, k), (x, y0, z), (x, y1, z), section, material, up=outward, align="heel")) for k, z in enumerate(zs)]


def cleat(name, pt, size=(0.008, 0.14, 0.14), material=None):
    return B.box(name, pt, size, material)


# ---------------------------------------------------------------- from an analysis model
def model_connections(model, secs, M, top_lift=None):
    """find the standard connections at the nodes of a frame model and return [(kind, node, generator)]:
    knee   = a vertical member ends at the node from below and one inclined member starts/ends there
    cap    = a vertical member ends at the node and the inclined member runs through (continuous rafter)
    splice = two inclined members of different sections meet at a node with no vertical member
    secs: {member id: designation}. The generators work in the y = 0 plane; copies are shifted by the caller."""
    import connections as CN
    by_node = {}
    for m in model.members:
        if m["id"] not in secs: continue
        for end, nid in (("a", m["a"]), ("b", m["b"])): by_node.setdefault(nid, []).append((m, end))
    out = []
    for nid, inc in by_node.items():
        P = Vector(model.nodes[nid])
        vert = [(m, e) for m, e in inc if abs(Vector(model.member_line(m)[1]).x - Vector(model.member_line(m)[0]).x) < 1e-6]
        incl = [(m, e) for m, e in inc if (m, e) not in vert]
        if len(vert) == 1 and incl:
            m, e = vert[0]; a, b = (Vector(q) for q in model.member_line(m))
            top = max(a.z, b.z)
            if abs(top - P.z) > 1e-6: continue                     # column passes through: not its top
            col_sec = secs[m["id"]]
            if len(incl) == 1:                                    # knee
                r, re_ = incl[0]; ra, rb = (Vector(q) for q in model.member_line(r)); other = rb if re_ == "a" else ra
                side = 1 if other.x > P.x else -1
                line = Line([(min(ra.x, rb.x), ra.z if ra.x < rb.x else rb.z), (max(ra.x, rb.x), rb.z if ra.x < rb.x else ra.z)],
                            top_lift if top_lift is not None else SEC_DB.profile(secs[r["id"]])["d"] / 2)
                out.append(("knee", nid, CN.knee("knee%d" % nid, line, P.x, "m%d" % m["id"], col_sec, "m%d" % r["id"], secs[r["id"]], M, side=side)))
            elif len(incl) == 2:                                  # cap: rafter continuous over the column top
                r1, r2 = incl[0][0], incl[1][0]
                ra, rb = (Vector(q) for q in model.member_line(r1)); rc, rd = (Vector(q) for q in model.member_line(r2))
                pts = sorted({(round(q.x, 6), q.z) for q in (ra, rb, rc, rd)})
                line = Line([(x, z) for x, z in pts], top_lift if top_lift is not None else SEC_DB.profile(secs[r1["id"]])["d"] / 2)
                raf_sec = secs[r1["id"]] if SEC_DB.profile(secs[r1["id"]])["d"] >= SEC_DB.profile(secs[r2["id"]])["d"] else secs[r2["id"]]
                out.append(("cap", nid, CN.cap("cap%d" % nid, line, P.x, "m%d" % m["id"], col_sec, raf_sec, M)))
        elif not vert and len(incl) == 2:
            r1, r2 = incl[0][0], incl[1][0]
            if secs[r1["id"]] == secs[r2["id"]]: continue           # same section: continuous, no splice drawn
            ra, rb = (Vector(q) for q in model.member_line(r1)); rc, rd = (Vector(q) for q in model.member_line(r2))
            pts = sorted({(round(q.x, 6), q.z) for q in (ra, rb, rc, rd)})
            line = Line([(x, z) for x, z in pts], top_lift if top_lift is not None else max(SEC_DB.profile(secs[r1["id"]])["d"], SEC_DB.profile(secs[r2["id"]])["d"]) / 2)
            left, right = (r1, r2) if min(ra.x, rb.x) < min(rc.x, rd.x) else (r2, r1)
            out.append(("splice", nid, CN.splice("splice%d" % nid, line, P.x, "m%d" % left["id"], secs[left["id"]], "m%d" % right["id"], secs[right["id"]], M)))
    return out


def build_model(model, mapping, materials, default=None, web=(0, 0, 1), accent=(), skip=(), xmax=None, y=0.0, top_lift=None, connections=False):
    """draw every member of a readers.Model. Section: mapping (member id / property name -> designation), else the
    property name itself when it is a catalogue designation, else `default`. Vertical members get their web along
    +x, others along `web`. accent: member ids or property names drawn in the accent material. top_lift: shift
    every non-vertical member along its normal so that its top face sits top_lift above the analysis axis (stepped
    rafters with flush tops, e.g. half the haunch depth); None keeps the analysis axis as the centroid.
    connections=True: generate knee / cap / splice connections at the nodes (model_connections) and trim the
    members to them, so the frame is built as detailed, not as analysed.
    Returns {member id: object}; prints the members it could not place."""
    import bpy
    out = {}; missing = []; secs = {}
    for m in model.members:
        if m["id"] in skip or model.props.get(m["prop"]) in skip: continue
        sec = model.section_of(m, mapping)
        if sec is None:
            try: sec = SEC_DB.find(model.props.get(m["prop"], ""))["designation"]
            except KeyError: sec = default
        if sec is None: missing.append((m["id"], model.props.get(m["prop"]))); continue
        secs[m["id"]] = sec
    conns = model_connections(model, secs, materials, top_lift) if connections else []
    cuts = {}
    for kind, nid, c in conns:
        for mname, cc in c["cuts"].items(): cuts.setdefault(mname, {}).update(cc)
    for m in model.members:
        if m["id"] not in secs: continue
        sec = secs[m["id"]]
        a, b = (Vector(p) for p in model.member_line(m))
        if xmax is not None and min(a.x, b.x) > xmax: continue
        if xmax is not None and max(a.x, b.x) > xmax:
            if b.x > a.x: b = a + (b - a) * ((xmax - a.x) / (b.x - a.x))
            else: a = b + (a - b) * ((xmax - b.x) / (a.x - b.x))
        ex = (b - a).normalized()
        up = Vector((1, 0, 0)) if abs(ex.z) > 0.99 else Vector(web)
        if abs(up.dot(ex)) > 0.99: up = Vector((0, 1, 0))
        mat = materials["accent"] if (m["id"] in accent or model.props.get(m["prop"]) in accent) else None
        align = "centroid"
        if top_lift is not None and abs(ex.z) < 0.99:
            n = up - up.dot(ex) * ex; n.normalize(); d = SEC_DB.profile(sec)["d"]
            a = a + n * (top_lift - d / 2); b = b + n * (top_lift - d / 2)
        cc = cuts.get("m%d" % m["id"], {})
        sh = lambda pl: (pl[0] + Vector((0, y, 0)), pl[1]) if pl else None
        c0, c1 = cc.get("cut0"), cc.get("cut1")
        if c0 is not None or c1 is not None:
            # the generator's cut planes assume the member runs a -> b in +x (rafters) or upwards (columns)
            if abs(ex.z) > 0.99 and ex.z < 0: c0, c1 = c1, c0
            if abs(ex.z) < 0.99 and ex.x < 0: c0, c1 = c1, c0
        a.y += y; b.y += y
        out[m["id"]] = B.member("m%d_%g" % (m["id"], y), a, b, sec, mat, up=up, cut0=sh(c0), cut1=sh(c1), align=align)
    if conns:
        before = set(o.name for o in bpy.context.scene.objects)
        for kind, nid, c in conns: c["build"]()
        if y:
            for o in bpy.context.scene.objects:
                if o.name not in before: o.location = o.location + Vector((0, y, 0))
        # connection anchors for the first frame only (they would repeat per frame)
        CONN_ANCHORS = {}
        for kind, nid, c in conns:
            for k, v in c["anchors"].items(): CONN_ANCHORS["%s%d.%s" % (kind, nid, k)] = tuple(Vector(v) + Vector((0, y, 0)))
        out["_anchors"] = CONN_ANCHORS
        print("model connections at y=%g: %s" % (y, ", ".join("%s@node%d" % (k, n) for k, n, _ in conns)))
    if missing: print("WARNING build_model: no section for members", missing, "- add them to `sections` or set `default`")
    return out


