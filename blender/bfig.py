"""bfig: Blender helpers for true-size engineering illustrations (units: metres; x east, y north, z up).
Members are built as real solids: hollow SHS/RHS/CHS with the true wall, hot-rolled I sections from a section
table, cold-formed Z sections, equal angles, plates, bolts, welds, roof sheeting. Style: white background, grey
materials, black Freestyle outlines, one muted accent colour. Dimensions and labels are NOT drawn here: the
script records 3D anchor points, render() projects them to image coordinates (JSON) and overlay.py draws the
annotation in TikZ, so text stays vector and never sits on top of the picture.

Typical figure script:
    import bfig as B; from mathutils import Vector
    out, quick, opt = B.args()                      # "-- <out_dir> [quick] [cam=x,y,z,tx,ty,tz,lens] [k=v ...]"
    B.reset(); M = B.mats()
    B.shs("chord", (0,0,0), (4,0,0), 0.200, 0.009, M["steel"])
    A = {"chord": (2, -0.1, 0.1)}; B.dim3(A, "L", (0,0,-0.1), (4,0,-0.1), (0,0,-0.5))
    B.setup(cam_loc=(5,-8,4), target=(2,0,0), lens=40, quick=quick, cam=opt.get("cam"))
    B.render(out, "chord", A)                       # -> out/chord.png + out/chord.json
First version 2026-11-04."""
import bpy, bmesh, math, json, os, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from steelfig import sections as SEC_DB
from steelfig import style as STYLE
ST = STYLE.load()                        # STEELFIG_STYLE=<name or path> selects the style sheet

# ---------------------------------------------------------------- colours (linear RGBA) and materials
GREY = (0.30, 0.31, 0.33, 1); LIGHT = (0.55, 0.56, 0.58, 1); DARK = (0.18, 0.18, 0.20, 1)
SHEET = (0.70, 0.68, 0.62, 1); ACCENT = (0.62, 0.16, 0.10, 1); WELD = (0.12, 0.12, 0.12, 1)
CONC = (0.80, 0.79, 0.76, 1); GROUT = (0.62, 0.61, 0.58, 1)
ACCENT_TIKZ = "0.62,0.16,0.10"          # the same accent for \definecolor{acc}{rgb}{...} in the report preamble
_mats = {}


def reset():
    """empty scene; call once per figure (or per shot when several figures share a script)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear(); MEMBERS.clear(); PARTS.clear()


def mat(name, rgba, rough=0.55, metal=0.0):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = rgba; b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    _mats[name] = m; return m


def steel_mat(name, colour, metallic=0.55, roughness=0.55, noise=0.1, spangle=0.0, scale=6.0, coat=0.0, edge=0.0):
    """a steel finish: Principled BSDF with roughness varied by a noise texture (mill scale), a faint bump from
    the same noise, and optional galvanising spangle (Voronoi cells shifting the colour slightly)."""
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; Lk = nt.links; b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = colour; b.inputs["Metallic"].default_value = metallic; b.inputs["Roughness"].default_value = roughness
    if coat:
        for k, v in (("Coat Weight", coat), ("Coat Roughness", 0.25)):
            if k in b.inputs: b.inputs[k].default_value = v
    if edge:                                                                  # lighter towards grazing angles: reads as a reflective surface
        fr = N.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.8
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs["A"].default_value = colour
        mx.inputs["B"].default_value = tuple(min(1.0, c * 1.6) for c in colour[:3]) + (1.0,)
        mr2 = N.new("ShaderNodeMath"); mr2.operation = "MULTIPLY"; mr2.inputs[1].default_value = edge
        Lk.new(fr.outputs["Fac"], mr2.inputs[0]); Lk.new(mr2.outputs[0], mx.inputs["Factor"]); Lk.new(mx.outputs["Result"], b.inputs["Base Color"])
    if noise:
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 3.0
        Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.3; mr.inputs["From Max"].default_value = 0.7
        mr.inputs["To Min"].default_value = max(0.05, roughness - noise); mr.inputs["To Max"].default_value = min(1.0, roughness + noise)
        Lk.new(nz.outputs["Fac"], mr.inputs["Value"]); Lk.new(mr.outputs["Result"], b.inputs["Roughness"])
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.04 * (noise / 0.1); bp.inputs["Distance"].default_value = 0.002
        Lk.new(nz.outputs["Fac"], bp.inputs["Height"]); Lk.new(bp.outputs["Normal"], b.inputs["Normal"])
    if spangle:
        tc2 = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 40.0
        Lk.new(tc2.outputs["Object"], vo.inputs["Vector"])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["Factor"].default_value = spangle
        mix.inputs["A"].default_value = colour; Lk.new(vo.outputs["Color"], mix.inputs["B"])
        if edge: Lk.new(mix.outputs["Result"], mx.inputs["A"])
        else: Lk.new(mix.outputs["Result"], b.inputs["Base Color"])
    _mats[name] = m; return m


def finish(name):
    """material for a finish name from the style ([finishes.<name>]), cached."""
    F = ST["finishes"][name]
    return steel_mat("finish_" + name, STYLE.rgba(F["colour"]), F.get("metallic", 0.5), F.get("roughness", 0.5), F.get("noise", 0.0), F.get("spangle", 0.0),
                     F.get("coat", 0.0), F.get("edge", 0.0))


def finish_for(designation):
    """the finish a catalogue designation gets by default: its grade if mapped, else its type, else hot_rolled."""
    r = SEC_DB.find(designation); fo = ST.get("finish_of", {})
    key = fo.get(str(r.get("grade", ""))) or fo.get(r["type"]) or "hot_rolled"
    return finish(key)


def mats():
    """the palette of the active style sheet: steel (main members), light (secondary: purlins, girts, diagonals),
    dark (bolts), accent (ONE subject per figure), sheet, weld, conc, grout. Names mapped in [finish_of] get the
    corresponding steel finish; the rest are flat colours."""
    out = {}
    fo = ST.get("finish_of", {})
    for k, v in ST["colours"].items():
        if k == "line": continue
        out[k] = finish(fo[k]) if k in fo and "finishes" in ST else mat(k, STYLE.rgba(v))
    return out


def hatch_mat(name, base, ink, pitch=0.0022, angle=45, plane="xz"):
    """section hatching for cut faces: diagonal lines at `pitch` (m) in the given plane ("xz" when the cut is seen
    along y, "yz" along x, "xy" from above). base / ink: RGB tuples. Apply to the solid that is cut."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.8
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    a = math.radians(angle); ax = {"xz": ("X", "Z"), "yz": ("Y", "Z"), "xy": ("X", "Y")}[plane]
    m1 = N.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; m1.inputs[1].default_value = math.cos(a) / pitch
    m2 = N.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = math.sin(a) / pitch
    L.new(sep.outputs[ax[0]], m1.inputs[0]); L.new(sep.outputs[ax[1]], m2.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"; L.new(m1.outputs[0], add.inputs[0]); L.new(m2.outputs[0], add.inputs[1])
    fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; L.new(add.outputs[0], fr.inputs[0])
    lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.16; L.new(fr.outputs[0], lt.inputs[0])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*base[:3], 1); mix.inputs["B"].default_value = (*ink[:3], 1)
    L.new(lt.outputs[0], mix.inputs["Factor"]); L.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    _mats[name] = m; return m


# ---------------------------------------------------------------- section catalogue
# Dimensions come from steelfig/sections.py (data/*.csv). SEC keeps the old (d, bf, tf, tw) mm tuples for scripts
# written against the first version; new code uses member() with a designation.
class _SecTable(dict):
    def __missing__(self, k):
        r = SEC_DB.find(k); return (r["d"], r["bf"], r["tf"], r["tw"])
SEC = _SecTable()


def section(designation):
    """catalogue row (mm) for a designation, e.g. section("310UB46.2")["d"]."""
    return SEC_DB.find(designation)


# ---------------------------------------------------------------- mesh plumbing
def _obj(name, bm, material):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    if material: ob.data.materials.append(material)
    return ob


def frame(p0, p1, up=Vector((0, 1, 0))):
    """local axes of a member: ex along p0->p1, ey = `up` made perpendicular, ez = ex x ey."""
    ex = (Vector(p1) - Vector(p0)).normalized(); up = Vector(up)
    ey = (up - up.dot(ex) * ex).normalized(); ez = ex.cross(ey)
    return ex, ey, ez


def rot_frame(ex, ey, ez):
    return Matrix((ex, ey, ez)).transposed()


def _cut(p, ex, plane):
    """slide p along ex onto the plane (point, normal); None = no cut."""
    if plane is None: return p
    q, n = Vector(plane[0]), Vector(plane[1]); s = (q - p).dot(n) / ex.dot(n)
    return p + s * ex


def prism(name, p0, p1, profile, material, up=Vector((0, 1, 0)), cut0=None, cut1=None):
    """closed profile [(u, v)] in the (ey, ez) plane extruded from p0 to p1; the ends may be cut by planes
    (point, normal) so that a member meets a sloping face flush (column top under a rafter, haunch end)."""
    ex, ey, ez = frame(p0, p1, Vector(up)); p0, p1 = Vector(p0), Vector(p1)
    bm = bmesh.new()
    a = [bm.verts.new(_cut(p0 + u * ey + v * ez, ex, cut0)) for u, v in profile]
    b = [bm.verts.new(_cut(p1 + u * ey + v * ez, ex, cut1)) for u, v in profile]
    n = len(profile)
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(a[::-1]); bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material)


extrude_profile = prism


def _tube(name, p0, p1, outer, inner, material, up, cut0=None, cut1=None):
    """hollow member: outer and inner closed profiles with the same point count; open ends show the wall."""
    ex, ey, ez = frame(p0, p1, Vector(up)); p0, p1 = Vector(p0), Vector(p1)
    bm = bmesh.new()
    mk = lambda P, pts, cut: [bm.verts.new(_cut(P + u * ey + v * ez, ex, cut)) for u, v in pts]
    oa, ob_, ia, ib = mk(p0, outer, cut0), mk(p1, outer, cut1), mk(p0, inner, cut0), mk(p1, inner, cut1)
    n = len(outer)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((oa[k], oa[j], ob_[j], ob_[k])); bm.faces.new((ia[j], ia[k], ib[k], ib[j]))
        bm.faces.new((oa[j], oa[k], ia[k], ia[j])); bm.faces.new((ob_[k], ob_[j], ib[j], ib[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material)


# ---------------------------------------------------------------- members
MEMBERS = {}          # name -> (p0, p1, designation) of every member() call, for automatic anchors
PARTS = {}            # name -> centre of every plate() call


def member_anchors(prefix="m."):
    """anchors for every member drawn with member(): <prefix><name> = midpoint, .a / .b = ends; plates get
    <prefix><name> = centre."""
    out = {}
    for n, (a, b, d) in MEMBERS.items():
        out[prefix + n] = tuple((a + b) / 2); out[prefix + n + ".a"] = tuple(a); out[prefix + n + ".b"] = tuple(b)
    for n, c in PARTS.items():
        out.setdefault(prefix + n, tuple(c))
    return out


def shs(name, p0, p1, b, t, material, up=Vector((0, 1, 0)), cut0=None, cut1=None):
    """square hollow section, outer b, wall t (true thickness)."""
    return rhs(name, p0, p1, b, b, t, material, up, cut0, cut1)


def rhs(name, p0, p1, b, d, t, material, up=Vector((0, 1, 0)), cut0=None, cut1=None):
    """rectangular hollow section: b along ey (= `up`), d along ez."""
    o = [(-b / 2, -d / 2), (b / 2, -d / 2), (b / 2, d / 2), (-b / 2, d / 2)]
    i_ = [(-b / 2 + t, -d / 2 + t), (b / 2 - t, -d / 2 + t), (b / 2 - t, d / 2 - t), (-b / 2 + t, d / 2 - t)]
    return _tube(name, p0, p1, o, i_, material, up, cut0, cut1)


def chs(name, p0, p1, d, t, material, segments=32, cut0=None, cut1=None):
    """circular hollow section, outside diameter d, wall t."""
    ring = lambda r: [(r * math.cos(2 * math.pi * k / segments), r * math.sin(2 * math.pi * k / segments)) for k in range(segments)]
    up = Vector((0, 0, 1)) if abs((Vector(p1) - Vector(p0)).normalized().z) < 0.9 else Vector((0, 1, 0))
    ob = _tube(name, p0, p1, ring(d / 2), ring(d / 2 - t), material, up, cut0, cut1)
    for f in ob.data.polygons: f.use_smooth = True
    return ob


def isec(name, p0, p1, sec, material, up=(0, 0, 1), cut0=None, cut1=None, top=False):
    """I section on the line p0 -> p1, web in the plane of ex and `up` (flanges perpendicular to `up`).
    sec: a key of SEC or a tuple (d, bf, tf, tw) in mm. top=True puts the line on the top flange face (the section
    hangs below it, handy for rafters whose top surface is the roof line); otherwise the line is the centroid."""
    d, bf, tf, tw = (x / 1000 for x in (SEC[sec] if isinstance(sec, str) else sec))
    o = -d / 2 if top else 0
    h, w = d / 2, bf / 2
    prof = [(-h, -w), (-h, w), (-h + tf, w), (-h + tf, tw / 2), (h - tf, tw / 2), (h - tf, w), (h, w), (h, -w),
            (h - tf, -w), (h - tf, -tw / 2), (-h + tf, -tw / 2), (-h + tf, -w)]
    return prism(name, p0, p1, [(u + o, v) for u, v in prof], material, up, cut0, cut1)


def secondary(ob):
    """mark an object as secondary (purlins, girts, sheeting): thinner outlines, see setup()."""
    col = bpy.data.collections.get("secondary") or bpy.data.collections.new("secondary")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    for c in list(ob.users_collection): c.objects.unlink(ob)
    col.objects.link(ob); return ob


def member(name, p0, p1, designation, material, up=(0, 0, 1), cut0=None, cut1=None, align="centroid", flip=False, min_t=0.003, secondary_=False):
    """any catalogue section on the line p0 -> p1. up: direction of the profile's u axis (web of an I section or
    channel, long leg of an angle, depth of an RHS, web of a Z/C purlin). align: where the line sits on the profile,
    "centroid" (default), "top" / "bottom" (the line is the top / bottom face, for rafters and purlins on a roof
    line), "heel" (angles and purlins: the line is the heel / bottom flange, which is the profile origin).
    flip mirrors the profile across the u axis (Z purlins alternating, channel toes the other way)."""
    P = SEC_DB.profile(designation, min_t=min_t)
    MEMBERS[name] = (Vector(p0), Vector(p1), designation)
    if material is None and "finishes" in ST: material = finish_for(designation)
    us = [u for u, v in P.get("pts", P.get("outer"))]
    off = {"centroid": 0.0, "top": -max(us), "bottom": -min(us), "heel": 0.0}[align]
    if align == "centroid" and P["row"]["type"] in ("EA", "UA", "Z", "C", "PFC"):
        off = -(max(us) + min(us)) / 2
    sgn = -1 if flip else 1
    fix = lambda pts: [(u + off, sgn * v) for u, v in pts]
    if P["kind"] == "hollow":
        ob = _tube(name, p0, p1, fix(P["outer"]), fix(P["inner"]), material, Vector(up), cut0, cut1)
        if P.get("round"):
            for f in ob.data.polygons: f.use_smooth = True
    else:
        ob = prism(name, p0, p1, fix(P["pts"]), material, Vector(up), cut0, cut1)
    return secondary(ob) if secondary_ else ob


def zsec(name, p0, p1, material, up, h=0.25, f=0.075, t=0.003, flip=False):
    """cold-formed Z section (lips omitted), bottom flange ON the line p0 -> p1, web pointing along `up`.
    Default Z250 (e.g. Stramit EZ25). t is drawn slightly thick so it reads at report scale."""
    s = -1 if flip else 1
    out = [(0, -f), (0, t / 2), (h - t, t / 2), (h - t, f), (h, f), (h, -t / 2), (t, -t / 2), (t, -f)]
    return prism(name, p0, p1, [(u, s * v) for u, v in out], material, up)


def z_purlin(name, x, y0, y1, z_base, h=0.25, f=0.075, t=0.0024, material=None):
    """Z purlin running along global Y at x, bottom flange on z_base (compatibility wrapper around zsec)."""
    return zsec(name, (x, y0, z_base), (x, y1, z_base), material, up=(0, 0, 1), h=h, f=f, t=max(t, 0.003))


def angle(name, p0, p1, leg=0.05, t=0.005, material=None, up=Vector((0, 0, 1))):
    """equal angle (fly braces, cleats); the heel sits a third of a leg off the line."""
    prof = [(0, 0), (leg, 0), (leg, t), (t, t), (t, leg), (0, leg)]
    return prism(name, p0, p1, [(u - leg / 3, v - leg / 3) for u, v in prof], material, up=up)


def box(name, center, size, material, rot=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if rot is not None:
        for v in bm.verts: v.co = rot @ v.co
    for v in bm.verts: v.co += Vector(center)
    return _obj(name, bm, material)


def plate(name, center, ex, ey, size, material):
    """plate centred on center; sides size[0] along ex, size[1] along ey, size[2] (thickness) along ex x ey."""
    ex = Vector(ex).normalized(); ey = Vector(ey).normalized(); ez = ex.cross(ey)
    PARTS[name] = Vector(center)
    return box(name, center, size, material, rot=rot_frame(ex, ey, ez))


def solid_prism(name, p0, p1, b, up=Vector((0, 1, 0))):
    """solid square prism on the line (a boolean cutter: e.g. trim diagonals at a chord face)."""
    ex, ey, ez = frame(p0, p1, up); c = (Vector(p0) + Vector(p1)) / 2
    return box(name, c, ((Vector(p1) - Vector(p0)).length, b, b), None, rot=rot_frame(ex, ey, ez))


def cyl(name, center, axis, r, h, material, segments=24):
    """cylinder (hex prism with segments=6) of length h centred on center, along axis."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r, radius2=r, depth=h)
    R = Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized()).to_matrix()
    for v in bm.verts: v.co = R @ v.co + Vector(center)
    return _obj(name, bm, material)


def bolt(name, center, axis, dia, grip, material):
    """bolt through a joint: shank of grip + 2 nut heights, hex head one side, hex nut the other, centred on center."""
    ax = Vector(axis).normalized(); c = Vector(center); nh = 0.8 * dia; s = 1.6 * dia
    sh = cyl(name + "_shank", c, ax, dia / 2, grip + 2 * nh + 0.5 * dia, material, segments=16); sh["clash_ok"] = 1
    cyl(name + "_head", c - ax * (grip / 2 + nh / 2), ax, s / math.sqrt(3), nh, material, segments=6)
    cyl(name + "_nut", c + ax * (grip / 2 + nh / 2), ax, s / math.sqrt(3), nh, material, segments=6)


def anchor_bolt(name, base, dia, above=0.03, below=0.30, material=None):
    """holding-down bolt at `base` (top of base plate): shank below, washer + nut above."""
    b = Vector(base)
    sh = cyl(name, b + Vector((0, 0, (above - below) / 2)), (0, 0, 1), dia / 2, above + below, material, segments=16); sh["clash_ok"] = 1
    cyl(name + "_wsh", b + Vector((0, 0, 0.003)), (0, 0, 1), 1.25 * dia, 0.006, material, segments=24)
    cyl(name + "_nut", b + Vector((0, 0, 0.006 + 0.4 * dia)), (0, 0, 1), dia, 0.8 * dia, material, segments=6)


def sheeting(name, x0, x1, y0, y1, z, rib=0.041, pitch=0.19, material=None, th=0.002):
    """flat trapezoidal sheeting at height z, ribs running along x (profile across y). Schematic rib spacing."""
    pts = []; y = y0
    while y < y1 - 1e-6:
        pts += [(y, 0), (y + 0.06, 0), (y + 0.085, rib), (y + 0.105, rib), (y + 0.13, 0)]; y += pitch
    pts.append((y1, 0))
    bm = bmesh.new()
    A = [bm.verts.new((x0, yy, z + zz)) for yy, zz in pts]; B_ = [bm.verts.new((x1, yy, z + zz)) for yy, zz in pts]
    A2 = [bm.verts.new((x0, yy, z + zz + th)) for yy, zz in pts]; B2 = [bm.verts.new((x1, yy, z + zz + th)) for yy, zz in pts]
    for k in range(len(pts) - 1):
        bm.faces.new((A[k], A[k + 1], B_[k + 1], B_[k])); bm.faces.new((A2[k + 1], A2[k], B2[k], B2[k + 1]))
    return _obj(name, bm, material)


def sheet_slope(name, a, b, y0, y1, n, material, rib=0.041, pitch=0.333, th=0.003):
    """trapezoidal sheeting on the sloping line a -> b (in the xz plane), lifted by the unit normal n, from y0 to
    y1; ribs run down the slope. rib=0 gives a plain sheet (reads better from far away)."""
    a, b, n = Vector(a), Vector(b), Vector(n)
    pts = []; y = y0
    while y < y1 - 1e-6:
        pts += [(y, 0), (y + 0.12, 0), (y + 0.15, rib), (y + 0.18, rib), (y + 0.21, 0)]; y += pitch
    pts.append((y1, 0))
    bm = bmesh.new()
    mk = lambda P, dz: [bm.verts.new(P + Vector((0, yy, 0)) + n * (zz + dz)) for yy, zz in pts]
    A, Bb, A2, B2 = mk(a, 0), mk(b, 0), mk(a, th), mk(b, th)
    for k in range(len(pts) - 1):
        for f, want in ((bm.faces.new((A[k], A[k + 1], Bb[k + 1], Bb[k])), -1), (bm.faces.new((A2[k], A2[k + 1], B2[k + 1], B2[k])), 1)):
            f.normal_update()
            if f.normal.dot(n) * want < 0: f.normal_flip()
    return _obj(name, bm, material)


# ---------------------------------------------------------------- joints: cutting, welds
def boolean_cut(target, cutters, op="DIFFERENCE"):
    """apply boolean DIFFERENCE (or INTERSECT) of each cutter on target (exact solver), modifiers applied."""
    for c in cutters:
        m = target.modifiers.new("cut", "BOOLEAN"); m.operation = op; m.object = c; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=m.name)


def split_long_faces(step=0.4, longer_than=1.0):
    """cut long members across their length into coplanar pieces. Freestyle loses occluders that are very long and
    thin, and the hidden edges behind them then show through; the extra edges are flat, so they draw no lines."""
    for ob in all_meshes():
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = [min(p[k] for p in pts) for k in range(3)]; hi = [max(p[k] for p in pts) for k in range(3)]
        k = max(range(3), key=lambda q: hi[q] - lo[q])
        if hi[k] - lo[k] <= longer_than: continue
        no = Vector((0, 0, 0)); no[k] = 1.0
        bm = bmesh.new(); bm.from_mesh(ob.data)
        c = lo[k] + step
        while c < hi[k]:
            co = Vector((0, 0, 0)); co[k] = c
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=ob.matrix_world.inverted() @ co, plane_no=no)
            c += step
        bm.to_mesh(ob.data); bm.free()


def delete(objs):
    for o in objs: bpy.data.objects.remove(o, do_unlink=True)


def edge_hits(p0, p1, b, plane_z, up=Vector((0, 1, 0))):
    """where the four outer edges of an SHS (axis p0 -> p1) cross the horizontal plane z = plane_z: the footprint
    corners of a branch on a chord face. Returns (corners, unit axis)."""
    ex, ey, ez = frame(p0, p1, up); p0 = Vector(p0); out = []
    for u, v in ((-b / 2, -b / 2), (b / 2, -b / 2), (b / 2, b / 2), (-b / 2, b / 2)):
        q = p0 + u * ey + v * ez; s = (plane_z - q.z) / ex.z; out.append(q + s * ex)
    return out, ex


def weld_ring(name, corners, axis, w, material):
    """fillet weld bead (leg w) around a branch footprint on a horizontal face; axis points away from the face."""
    c = sum(corners, Vector()) / len(corners)
    bm = bmesh.new(); n = len(corners); A = []
    for p in corners:
        d = p - c; d.z = 0
        d = Vector((math.copysign(1, d.x) if abs(d.x) > 1e-9 else 0, math.copysign(1, d.y) if abs(d.y) > 1e-9 else 0, 0))
        A.append(bm.verts.new(p + w * d))
    Bv = [bm.verts.new(p + w * axis) for p in corners]; C = [bm.verts.new(p) for p in corners]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((A[i], A[j], Bv[j], Bv[i])); bm.faces.new((C[i], C[j], A[j], A[i])); bm.faces.new((Bv[i], Bv[j], C[j], C[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(name, bm, material); ob["clash_ok"] = 1; return ob


def weld_line(name, p0, p1, leg, ey, ez, material):
    """straight fillet weld from p0 to p1: triangular bead with legs along ey (on the first face) and ez (up the
    second face); root on the line."""
    ey, ez = Vector(ey).normalized(), Vector(ez).normalized()
    prof = [(0, 0), (leg, 0), (0, leg)]
    ex = (Vector(p1) - Vector(p0)).normalized()
    bm = bmesh.new()
    a = [bm.verts.new(Vector(p0) + u * ey + v * ez) for u, v in prof]; b = [bm.verts.new(Vector(p1) + u * ey + v * ez) for u, v in prof]
    for i in range(3): bm.faces.new((a[i], a[(i + 1) % 3], b[(i + 1) % 3], b[i]))
    bm.faces.new(a[::-1]); bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, material)


def explode(objs, vector):
    """exploded view: move objects by a vector (metres) after modelling, e.g. a splice plate pulled off its wall."""
    for o in objs: o.location = o.location + Vector(vector)


def section_cut(objs, point, normal, hatch=None, size=50.0, apply=True):
    """cut away everything on the +normal side of the plane through `point`; the new cut faces get the `hatch`
    material (make it with hatch_mat) so the section reads as a drawing section. objs: list of mesh objects.
    apply=False keeps the cut as live modifiers (for one view only): call uncut() with the returned handle
    after rendering to restore the scene."""
    n = Vector(normal).normalized(); c = Vector(point) + n * (size / 2)
    ex = n.orthogonal().normalized(); ey = n.cross(ex)
    cutter = box("cutter", c, (size, size, size), hatch, rot=rot_frame(ex, ey, n)); cutter.hide_render = True
    mods = []
    for o in objs:
        if o.type != 'MESH' or o is cutter: continue
        m = o.modifiers.new("section", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = cutter; m.solver = "EXACT"
        try: m.material_mode = "TRANSFER"
        except Exception: pass
        if apply:
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=m.name)
        else: mods.append((o, m.name))
    if apply: delete([cutter]); return None
    return (cutter, mods)


def uncut(handle):
    if not handle: return
    cutter, mods = handle
    for o, name in mods:
        m = o.modifiers.get(name)
        if m: o.modifiers.remove(m)
    delete([cutter])


def export_glb(path):
    """export every mesh to a .glb in Blender's own axes (z up, metres) for the browser viewer; flat colours only."""
    for o in bpy.context.scene.objects: o.select_set(o.type == 'MESH')
    kw = dict(filepath=path, export_format='GLB', export_yup=False, export_apply=True, use_selection=True,
              export_materials='EXPORT', export_image_format='NONE', export_animations=False, export_skins=False, export_lights=False, export_cameras=False)
    try: bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        for k in ("export_image_format", "export_skins", "export_animations", "export_lights", "export_cameras"): kw.pop(k, None)
        bpy.ops.export_scene.gltf(**kw)
    print("glb", path)


def all_meshes():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def check_clashes(objs=None, min_cm3=0.05, skip_ok=True):
    """find pairs of solids that occupy the same space (members passing through each other). For every pair whose
    bounding boxes overlap, the exact boolean intersection volume is computed; pairs above min_cm3 are returned
    as (name_a, name_b, cm3) and printed as CLASH lines. Objects tagged ob["clash_ok"] (bolt shanks, welds) are
    skipped. Touching faces (a purlin sitting on a flange) have zero volume and do not count."""
    objs = [o for o in (objs or all_meshes()) if not (skip_ok and o.get("clash_ok"))]
    def bbox(o):
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return Vector(map(min, zip(*pts))), Vector(map(max, zip(*pts)))
    boxes = {o.name: bbox(o) for o in objs}
    sec = {o.name: (o.users_collection and o.users_collection[0].name == "secondary") for o in objs}
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); trees = {}

    def tree(o):
        """BVH of the solid inset by 1 mm along the vertex normals: touching faces come apart, penetrations stay."""
        if o.name in trees: return trees[o.name]
        bm = bmesh.new(); bm.from_mesh(o.evaluated_get(dg).to_mesh()); bm.transform(o.matrix_world)
        bm.normal_update()
        for v in bm.verts: v.co -= v.normal * 0.001
        bm.faces.ensure_lookup_table(); bmesh.ops.triangulate(bm, faces=bm.faces)
        t = BVHTree.FromBMesh(bm); bm.free(); trees[o.name] = t; return t

    out = []
    for i, a in enumerate(objs):
        for b in objs[i + 1:]:
            if sec[a.name] and sec[b.name]: continue                 # purlin-purlin, girt-girt: parallel, never cross
            (a0, a1), (b0, b1) = boxes[a.name], boxes[b.name]
            if any(a1[k] < b0[k] - 1e-4 or b1[k] < a0[k] - 1e-4 for k in range(3)): continue
            ov = [min(a1[k], b1[k]) - max(a0[k], b0[k]) for k in range(3)]
            if min(ov) < 2e-3: continue                              # a real penetration overlaps in all three directions
            if not tree(a).overlap(tree(b)): continue                # surfaces of the inset solids do not cross
            c = a.copy(); c.data = a.data.copy(); bpy.context.scene.collection.objects.link(c)
            m = c.modifiers.new("x", "BOOLEAN"); m.operation = "INTERSECT"; m.object = b; m.solver = "EXACT"
            bpy.context.view_layer.objects.active = c
            where = None
            try:
                bpy.ops.object.modifier_apply(modifier=m.name)
                bm = bmesh.new(); bm.from_mesh(c.data); bm.transform(c.matrix_world); vol = abs(bm.calc_volume())
                if bm.verts: where = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
                bm.free()
            except Exception:
                vol = 0.0
            bpy.data.objects.remove(c, do_unlink=True)
            cm3 = vol * 1e6
            if cm3 > min_cm3: out.append((a.name, b.name, cm3, where))
    for a, b, v, w in sorted(out, key=lambda r: -r[2]):
        print("CLASH %s x %s: %.1f cm3 near (%.3f, %.3f, %.3f)" % (a, b, v, *(w or Vector())))
    if not out: print("clash check: no overlapping solids")
    return out


# ---------------------------------------------------------------- camera, lights, line art
def setup(cam_loc, target, lens=40, res=None, ortho=None, line=None, quick=False, cam=None, line_color=None):
    """white world, two suns, Freestyle outlines, transparent film. ortho = ortho_scale for an orthographic view.
    quick=True halves the resolution and thins the line for composition checks. cam = (x,y,z,tx,ty,tz,lens)
    from the command line overrides cam_loc / target / lens (see args())."""
    if cam: cam_loc, target, lens = tuple(cam[0:3]), tuple(cam[3:6]), cam[6]
    R = ST["render"]; res = tuple(res or R["resolution"]); line = line or R["line_width"]
    if line_color is None: line_color = STYLE.rgba(ST["colours"]["line"])[:3]
    if quick: q = R["quick_scale"]; res = (int(res[0] * q), int(res[1] * q)); line = max(0.8, line * q * 1.3)
    sc = bpy.context.scene
    world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = R["background_strength"]
    W = ST.get("world")
    if W:                                                     # sky-to-ground gradient: gives metal something to reflect
        nt = world.node_tree; N = nt.nodes; Lk = nt.links
        tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Generated"], sp.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.3; mr.inputs["From Max"].default_value = 0.8
        Lk.new(sp.outputs["Z"], mr.inputs["Value"])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.inputs["A"].default_value = STYLE.rgba(W["ground"]); mix.inputs["B"].default_value = STYLE.rgba(W["sky"])
        Lk.new(mr.outputs["Result"], mix.inputs["Factor"]); Lk.new(mix.outputs["Result"], bg.inputs[0]); bg.inputs[1].default_value = W.get("strength", 0.75)
    camo = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(camo)
    camo.location = cam_loc; d = Vector(target) - Vector(cam_loc); camo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    camo.data.lens = lens
    if ortho: camo.data.type = 'ORTHO'; camo.data.ortho_scale = ortho
    sc.camera = camo
    LG = ST.get("lighting", {})
    rig = (("key", LG.get("key", 2.4), (math.radians(LG.get("key_elev", 50)), 0, math.radians(LG.get("key_azim", 35))), LG.get("key_soft", 6), True),
           ("fill", LG.get("fill", 0.9), (math.radians(65), 0, math.radians(-140)), 40, False),
           ("rim", LG.get("rim", 0.7), (math.radians(30), 0, math.radians(180)), 20, False))
    for nm, energy, rot, soft, shadow in rig:
        if energy <= 0: continue
        L = bpy.data.lights.new(nm, 'SUN'); L.energy = energy; L.angle = math.radians(soft); L.use_shadow = shadow
        o = bpy.data.objects.new(nm, L); o.rotation_euler = rot; sc.collection.objects.link(o)
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.render.resolution_x, sc.render.resolution_y = res
    e = sc.eevee
    e.taa_render_samples = int(R.get("samples", 64) * (0.5 if quick else 1))
    for attr, val in (("use_fast_gi", R.get("fast_gi", True)), ("use_shadows", R.get("shadows", True)),
                      ("shadow_resolution_scale", R.get("shadow_quality", 1.0)), ("shadow_ray_count", 2), ("shadow_step_count", 4),
                      ("use_gtao", R.get("fast_gi", True))):                      # use_gtao: EEVEE legacy (Blender < 4.2)
        try: setattr(e, attr, val)
        except (AttributeError, TypeError): pass
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'; sc.render.line_thickness = line
    vl = sc.view_layers[0]; fs = vl.freestyle_settings
    fs.crease_angle = math.radians(135)
    LN = ST.get("lines", {}); sec_col = bpy.data.collections.get("secondary")
    # depth range for the fade: distances of all mesh vertices from the camera
    ds = []
    for ob in sc.objects:
        if ob.type == 'MESH':
            for c in ob.bound_box: ds.append((ob.matrix_world @ Vector(c) - Vector(cam_loc)).length)
    d0, d1 = (min(ds), max(ds)) if ds else (1.0, 10.0)

    def lineset(name, kinds, thick, collection=None, exclusive=False):
        ls = fs.linesets.new(name)
        ls.select_by_visibility = True; ls.visibility = 'VISIBLE'; ls.select_by_edge_types = True
        ls.select_silhouette = "silhouette" in kinds; ls.select_border = "border" in kinds
        ls.select_crease = "crease" in kinds; ls.select_external_contour = "contour" in kinds
        if collection is not None:
            ls.select_by_collection = True; ls.collection = collection; ls.collection_negation = 'EXCLUSIVE' if exclusive else 'INCLUSIVE'
        st = bpy.data.linestyles.new("ls_" + name); st.color = line_color; st.thickness = thick; st.chaining = 'PLAIN'
        if LN.get("fade", 1.0) < 1.0 and d1 > d0:
            m = st.thickness_modifiers.new("fade", 'DISTANCE_FROM_CAMERA'); m.range_min, m.range_max = d0, d1
            m.value_min, m.value_max = 1.0, LN["fade"]; m.blend = 'MULTIPLY'
        ls.linestyle = st; return ls

    c_, k_, s_ = LN.get("contour", 1.0), LN.get("crease", 1.0), LN.get("secondary", 1.0)
    if sec_col is not None and len(sec_col.objects):
        lineset("contour", ("contour", "silhouette", "border"), line * c_, sec_col, exclusive=True)
        lineset("crease", ("crease",), line * k_, sec_col, exclusive=True)
        lineset("contour2", ("contour", "silhouette", "border"), line * c_ * s_, sec_col)
        lineset("crease2", ("crease",), line * k_ * s_, sec_col)
    else:
        lineset("contour", ("contour", "silhouette", "border"), line * c_)
        lineset("crease", ("crease",), line * k_)
    return camo


def auto_ortho(camo, look, fit=None, fill=0.9, margin=0.0):
    """orthographic view that fits the `fit` objects (default all): ortho_scale from the projected extent,
    centred on the fit. Returns (scale, at)."""
    objs = fit or all_meshes(); sc = bpy.context.scene
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo, hi = Vector(map(min, zip(*pts))), Vector(map(max, zip(*pts))); at = (lo + hi) / 2
    axes = {"+x": (1, 2), "-x": (1, 2), "+y": (0, 2), "-y": (0, 2), "-z": (0, 1)}[look]
    w, h = hi[axes[0]] - lo[axes[0]], hi[axes[1]] - lo[axes[1]]
    aspect = sc.render.resolution_x / sc.render.resolution_y
    scale = max(w, h * aspect) / fill
    ortho_view(camo, look, scale, at); bpy.context.view_layer.update()
    return scale, at


def auto_camera(focus=None, fit=None, direction=(0.65, -1.0, 0.36), lens=45.0, fill=0.8, aspect=None, quick=False, line=None):
    """recommend a camera: look at the centre of the `focus` objects (default: accent-material objects, else all)
    from `direction` (unit vector from the target towards the camera), at the distance that fits the `fit`
    objects (default: all meshes) within `fill` of the frame. Returns (cam_loc, target, lens) and leaves the
    camera set up (setup() has been called)."""
    objs = all_meshes()
    if focus is None:
        focus = [o for o in objs if o.data.materials and o.data.materials[0].name in ("finish_accent", "accent")] or objs
    fit = fit or objs
    def bbox(obs):
        pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
        return Vector(map(min, zip(*pts))), Vector(map(max, zip(*pts)))
    f0, f1 = bbox(focus); target = (f0 + f1) / 2
    a0, a1 = bbox(fit); d = Vector(direction).normalized(); dist = max((a1 - a0).length, 1.0) * 1.2
    camo = setup(cam_loc=tuple(target + d * dist), target=tuple(target), lens=lens, quick=quick, line=line)
    sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
    for _ in range(8):
        us, vs = [], []
        for ob in fit:
            me = ob.evaluated_get(dg).to_mesh()
            for v in me.vertices:
                co = world_to_camera_view(sc, camo, ob.matrix_world @ v.co); us.append(co.x); vs.append(co.y)
        w, h = max(us) - min(us), max(vs) - min(vs)
        k = max(w, h) / fill
        cu, cv = (max(us) + min(us)) / 2 - 0.5, (max(vs) + min(vs)) / 2 - 0.5     # frame-centre offset of the fit
        # shift target sideways so the fit is centred, then scale the distance
        view = -d                                                             # the camera looks along -d
        right = view.cross(Vector((0, 0, 1))).normalized(); upv = right.cross(view).normalized()
        span = 2 * dist * (18 / lens)                                         # horizontal frame width at the target (sensor 36 mm)
        target = target + right * (cu * span) + upv * (cv * span / (sc.render.resolution_x / sc.render.resolution_y))
        dist = dist * min(3.0, max(0.3, k))
        camo.location = target + d * dist; camo.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()                                       # world_to_camera_view reads matrix_world
        if abs(k - 1) < 0.02 and abs(cu) < 0.01 and abs(cv) < 0.01: break
    return [round(v, 3) for v in camo.location] + [round(v, 3) for v in target] + [lens]


def ortho_view(camo, look, scale, at, dist=20.0):
    """turn the camera into an orthographic drawing view: look = "+x" (looking east), "-x", "+y" (looking north),
    "-y", "-z" (plan, looking down); scale = ortho_scale (metres across the wider image side); at = point in view."""
    camo.data.type = 'ORTHO'; camo.data.ortho_scale = scale
    d = {"+x": Vector((1, 0, 0)), "-x": Vector((-1, 0, 0)), "+y": Vector((0, 1, 0)), "-y": Vector((0, -1, 0)), "-z": Vector((0, 0, -1))}[look]
    camo.location = Vector(at) - d * dist
    camo.rotation_euler = d.to_track_quat('-Z', 'Y' if look == "-z" else 'Z').to_euler()
    return camo


# ---------------------------------------------------------------- anchors and rendering
def dim3(anch, name, p, q, off):
    """record a 3D dimension between p and q, dimension line offset by the vector off; the overlay draws
    ("dim3", name, text, side). Keep off in the plane of the measured face so the line reads as 3D."""
    p, q, off = Vector(p), Vector(q), Vector(off)
    anch[name + "_a"], anch[name + "_b"] = tuple(p), tuple(q)
    anch[name + "_a2"], anch[name + "_b2"] = tuple(p + off), tuple(q + off)


def dim3_auto(anch, name, p, q, dists=(0.45, 0.8, 1.2, 1.7)):
    """a 3D dimension whose offset is chosen later by the overlay: candidates are the four directions
    perpendicular to the measured line (horizontal and vertical perpendiculars, both signs) at three distances;
    the overlay keeps the one that stays off the steel, inside the picture and away from other annotation."""
    p, q = Vector(p), Vector(q); d = (q - p).normalized()
    h = d.cross(Vector((0, 0, 1)))
    if h.length < 1e-6: h = d.cross(Vector((0, 1, 0)))
    h.normalize(); vv = h.cross(d).normalized()
    anch[name + "_a"], anch[name + "_b"] = tuple(p), tuple(q)
    k = 0
    dirs = [h, -h, vv, -vv] + [(a + b).normalized() for a in (h, -h) for b in (vv, -vv)]     # 8 directions in the perpendicular plane
    for u in dirs:
        for dist in dists:
            anch["%s_c%d_a2" % (name, k)] = tuple(p + u * dist); anch["%s_c%d_b2" % (name, k)] = tuple(q + u * dist); k += 1
    anch[name + "_ncand"] = (k, 0, 0)


def wave(p, q, amp, side, n=20):
    """buckled-shape polyline from p to q bowing by amp along unit vector side (exaggerated, drawn dashed)."""
    p, q, side = Vector(p), Vector(q), Vector(side).normalized()
    return [tuple(p + (q - p) * u + side * amp * math.sin(math.pi * u)) for u in [i / n for i in range(n + 1)]]


def _id_colour(i):
    """index 1.. -> distinct sRGB colour (1575 ids), returned as (sRGB tuple, linear rgba). Never black, which is what a
    transparent background reads as; blue steps of 34 because readers compare colours by luminance (weight 0.114)."""
    i = int(i) - 1
    if i >= 1575: raise ValueError("more than 1575 objects in the scene: the ID render cannot tell them apart")
    r, g, b = (i % 15 + 1) * 17, ((i // 15) % 15 + 1) * 17, ((i // 225) % 7 + 1) * 34
    lin = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4
    return (r, g, b), (lin(r), lin(g), lin(b), 1.0)


def render_ids(path):
    """flat-colour render of the same view (Workbench, no outlines, no anti-aliasing): every mesh object in its own
    colour, so the overlay can tint or outline a member after the fact. Returns {object name: [r, g, b]} sRGB."""
    sc = bpy.context.scene; keep = dict(engine=sc.render.engine, fs=sc.render.use_freestyle, fp=sc.render.filepath, dither=sc.render.dither_intensity)
    ids = {}
    for i, ob in enumerate(o for o in sc.objects if o.type == 'MESH'):
        srgb, lin = _id_colour(i + 1); ob.color = lin; ids[ob.name] = list(srgb)
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.use_freestyle = False; sc.render.dither_intensity = 0
    sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'OBJECT'; sh.show_object_outline = False
    sh.show_shadows = False; sh.show_cavity = False; sh.show_xray = False
    sc.display.render_aa = 'OFF'
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    sc.render.engine = keep["engine"]; sc.render.use_freestyle = keep["fs"]; sc.render.filepath = keep["fp"]; sc.render.dither_intensity = keep["dither"]
    return ids


def render(out_dir, name, anchors=None, margin=0.02, bounds_extra=(), crop_pts=None, ids=True):
    """render to <out_dir>/<name>.png cropped to the projected meshes (+ extra points, + margin) and write
    <out_dir>/<name>.json with the image size and every anchor mapped to (u, v) in [0, 1] of the cropped image
    (v up). Anchors may be a point or a list of points (polylines, arrow pairs). crop_pts fixes the crop instead."""
    sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get(); anchors = anchors or {}
    us, vs = [], []
    for ob in sc.objects:
        if ob.type != 'MESH' or ob.hide_render: continue
        me = ob.evaluated_get(dg).to_mesh()
        for v in me.vertices:
            co = world_to_camera_view(sc, sc.camera, ob.matrix_world @ v.co); us.append(co.x); vs.append(co.y)
    for p in bounds_extra:
        co = world_to_camera_view(sc, sc.camera, Vector(p)); us.append(co.x); vs.append(co.y)
    if crop_pts:
        us, vs = [], []
        for p in crop_pts:
            co = world_to_camera_view(sc, sc.camera, Vector(p)); us.append(co.x); vs.append(co.y)
        margin = 0
    u0, u1 = max(0, min(us) - margin), min(1, max(us) + margin); v0, v1 = max(0, min(vs) - margin), min(1, max(vs) + margin)
    sc.render.use_border = True; sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = u0, u1, v0, v1
    os.makedirs(out_dir, exist_ok=True)
    sc.render.filepath = os.path.join(out_dir, name + ".png")
    bpy.ops.render.render(write_still=True)
    def m(p):
        co = world_to_camera_view(sc, sc.camera, Vector(p)); return [(co.x - u0) / (u1 - u0), (co.y - v0) / (v1 - v0)]
    out = {}
    for k, p in anchors.items():
        p = list(p) if not isinstance(p, Vector) else p
        out[k] = [m(q) for q in p] if isinstance(p, list) and p and not isinstance(p[0], (int, float)) else m(p)
    res = [round(sc.render.resolution_x * (u1 - u0)), round(sc.render.resolution_y * (v1 - v0))]
    a3 = {k: ([list(q) for q in p] if isinstance(p, list) and p and not isinstance(p[0], (int, float)) else list(p))
          for k, p in ((k, list(p) if not isinstance(p, Vector) else list(p)) for k, p in anchors.items())}
    idmap = render_ids(os.path.join(out_dir, name + "_id.png")) if ids else {}
    bg = [o.name for o in sc.objects if o.type == 'MESH' and o.data.materials and o.data.materials[0].name in ("conc", "grout", "sheet", "finish_galvanised") and not o.name.startswith(("pur", "girt"))]
    json.dump(dict(res=res, anchors=out, anchors3d=a3, ortho=sc.camera.data.type == 'ORTHO', ids=idmap, background=bg), open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8"), indent=1)
    print("rendered", os.path.join(out_dir, name + ".png"), res)


render2 = lambda path, anchors, json_path, **kw: render(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0], anchors, **kw)


def args():
    """command line after "--": <out_dir> [quick] [cam=x,y,z,tx,ty,tz,lens] [key=value ...].
    Returns (out_dir, quick, opts) with opts["cam"] a float list when given, other key=value as strings."""
    import tempfile
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [os.path.join(tempfile.gettempdir(), "bfig")]
    out = a[0]; quick = "quick" in a; opts = {}
    for t in a[1:]:
        if "=" in t:
            k, v = t.split("=", 1); opts[k] = [float(x) for x in v.split(",")] if k == "cam" else v
    return out, quick, opts
