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
        """point on the (lifted) line at horizontal position x, extended straight beyond the ends."""
        i = self.seg(x); a, b = self.P[i], self.P[i + 1]
        z = a.z + (b.z - a.z) * (x - a.x) / (b.x - a.x)
        n = self.normal(x)
        return Vector((x, y, z)) + n * (self.lift / n.z if n.z else self.lift)

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
    """angle(s) from a restrained flange (flange_pt on the member axis plane) up to a purlin (purlin_pt)."""
    out = []
    for s in ((-1, 1) if both_sides else (1,)):
        p0 = Vector(flange_pt) + Vector((0, s * y_in, 0)); p1 = Vector(purlin_pt)
        p1 = Vector((p1.x, s * abs(p1.y) if p1.y else p1.y, p1.z))
        out.append(B.member("%s%+d" % (name, s), p0, p1, section, material, up=(0, 0, 1), align="heel"))
    return out


def purlins_on(name, line, spacing, y0, y1, section, material, start=0.0, until=None, up=None, flip_alternate=False, from_end=False):
    """Z/C purlins along a roof Line at slope spacing, bottom flange on the line, web along the roof normal."""
    out = []; k = 0
    L = line.length() if until is None else until
    while start + spacing * k <= L + 1e-9:
        p = line.along(start + spacing * k, from_end=from_end)
        n = up or line.normal(p.x)
        out.append((p, B.member("%s%d" % (name, k), p + Vector((0, y0, 0)), p + Vector((0, y1, 0)), section, material, up=n, align="heel",
                                flip=flip_alternate and k % 2 == 1)))
        k += 1
    return out


def girts_on(name, x, zs, y0, y1, section, material, outward=(-1, 0, 0)):
    """Z/C girts on a wall at x, at the given levels; web pointing outward."""
    return [(Vector((x, 0, z)), B.member("%s%d" % (name, k), (x, y0, z), (x, y1, z), section, material, up=outward, align="heel")) for k, z in enumerate(zs)]


def cleat(name, pt, size=(0.008, 0.14, 0.14), material=None):
    return B.box(name, pt, size, material)


# ---------------------------------------------------------------- from an analysis model
def build_model(model, mapping, materials, default=None, web=(0, 0, 1), accent=(), skip=(), xmax=None, y=0.0, top_lift=None):
    """draw every member of a readers.Model. Section: mapping (member id / property name -> designation), else the
    property name itself when it is a catalogue designation, else `default`. Vertical members get their web along
    +x, others along `web`. accent: member ids or property names drawn in the accent material. top_lift: shift
    every non-vertical member along its normal so that its top face sits top_lift above the analysis axis (stepped
    rafters with flush tops, e.g. half the haunch depth); None keeps the analysis axis as the centroid.
    Returns {member id: object}; prints the members it could not place."""
    out = {}; missing = []
    for m in model.members:
        if m["id"] in skip or model.props.get(m["prop"]) in skip: continue
        sec = model.section_of(m, mapping)
        if sec is None:
            try: sec = SEC_DB.find(model.props.get(m["prop"], ""))["designation"]
            except KeyError: sec = default
        if sec is None: missing.append((m["id"], model.props.get(m["prop"]))); continue
        a, b = (Vector(p) for p in model.member_line(m))
        if xmax is not None and min(a.x, b.x) > xmax: continue
        if xmax is not None and max(a.x, b.x) > xmax:
            if b.x > a.x: b = a + (b - a) * ((xmax - a.x) / (b.x - a.x))
            else: a = b + (a - b) * ((xmax - b.x) / (a.x - b.x))
        a.y += y; b.y += y
        ex = (b - a).normalized()
        up = Vector((1, 0, 0)) if abs(ex.z) > 0.99 else Vector(web)
        if abs(up.dot(ex)) > 0.99: up = Vector((0, 1, 0))
        mat = materials["accent"] if (m["id"] in accent or model.props.get(m["prop"]) in accent) else materials["steel"]
        if top_lift is not None and abs(ex.z) < 0.99:
            n = up - up.dot(ex) * ex; n.normalize(); d = SEC_DB.profile(sec)["d"]
            a = a + n * (top_lift - d / 2); b = b + n * (top_lift - d / 2)
        out[m["id"]] = B.member("m%d_%g" % (m["id"], y), a, b, sec, mat, up=up)
    if missing: print("WARNING build_model: no section for members", missing, "- add them to `sections` or set `default`")
    return out
