"""Build and render a scene.json (compiled from a steelfig TOML scene) inside Blender.
Run by steelfig/scene.py: Blender --background --python build_scene.py -- <out_dir> <scene.json> [quick]"""
import sys, os, json, math
import bfig as B, assembly as A
from mathutils import Vector
from steelfig import sections as SEC_DB

out, quick, opt = B.args()
spec = [a for a in sys.argv[sys.argv.index("--") + 1:] if a.endswith(".json")][0]
sc = json.load(open(spec))
B.reset(); M = B.mats()
lines = {l["name"]: A.Line(l["points"], l.get("lift", 0.0)) for l in sc.get("line", [])}


class _Ends: pass


members = {}; mem_ns = _Ends()
NS = dict(V=lambda *a: Vector(a), math=math, m=mem_ns, sec=lambda d: SEC_DB.profile(d), **lines)


def pt(x):
    """[x, y, z] | [x, z] (y = 0) | expression string -> Vector"""
    if isinstance(x, str): return Vector(eval(x, {"__builtins__": {}}, NS))
    if len(x) == 2: return Vector((x[0], 0.0, x[1]))
    return Vector(x)


def num(x):
    """number or expression string -> float (e.g. "roof.at(0.25).z - 0.009")"""
    return float(eval(x, {"__builtins__": {}}, NS)) if isinstance(x, str) else float(x)


def nums(xs):
    return [num(x) for x in xs]


def vec(x, default=(0, 0, 1)):
    return pt(x) if x is not None else Vector(default)


def plane(c):
    return (pt(c[0]), vec(c[1])) if c else None


def mat(name):
    return M[name or "steel"]


ys = sc.get("frames", [0.0])
for mb in sc.get("member", []):
    a, b = pt(mb["from"]), pt(mb["to"])
    for y in (ys if mb.get("per_frame") else [0.0]):
        off = Vector((0, y, 0))
        ob = B.member("%s_%g" % (mb["name"], y) if y else mb["name"], a + off, b + off, mb["section"], mat(mb.get("material")),
                      up=vec(mb.get("up")), cut0=plane(mb.get("cut0")), cut1=plane(mb.get("cut1")), align=mb.get("align", "centroid"), flip=mb.get("flip", False))
        if not y:
            members[mb["name"]] = ob; e = _Ends(); e.a, e.b = a, b; setattr(mem_ns, mb["name"], e)
for pl in sc.get("plate", []):
    B.plate(pl["name"], pt(pl["centre"]), vec(pl.get("ex", [1, 0, 0])), vec(pl.get("ey", [0, 1, 0])), pl["size"], mat(pl.get("material")))
for bg in sc.get("bolts", []):
    A.bolt_rows(bg["name"], pt(bg["centre"]), vec(bg.get("axis", [1, 0, 0])), vec(bg.get("up", [0, 0, 1])), vec(bg.get("side", [0, 1, 0])),
                nums(bg["rows"]), nums(bg["cols"]), bg.get("bolt", "M20"), num(bg.get("grip", 0.04)), mat(bg.get("material", "dark")))
for st in sc.get("stiffeners", []):
    A.stiffeners(st["name"], pt(st["column_pt"]), st["section"], nums(st["levels"]), mat(st.get("material", "light")), st.get("t", 0.012), vec(st.get("up", [1, 0, 0])))
purlin_pts = {}
for pu in sc.get("purlins", []):
    res = A.purlins_on(pu.get("name", "pur"), lines[pu["line"]], num(pu["spacing"]), num(pu["y0"]), num(pu["y1"]), pu["section"], mat(pu.get("material", "light")),
                       num(pu.get("start", 0.0)), num(pu["until"]) if "until" in pu else None, from_end=pu.get("from_end", False), flip_alternate=pu.get("flip_alternate", False))
    purlin_pts[pu.get("name", "pur")] = [p for p, _ in res]
    NS[pu.get("name", "pur")] = [p for p, _ in res]
for gi in sc.get("girts", []):
    A.girts_on(gi.get("name", "girt"), num(gi["x"]), nums(gi["levels"]), num(gi["y0"]), num(gi["y1"]), gi["section"], mat(gi.get("material", "light")), vec(gi.get("outward", [-1, 0, 0])))
for fb in sc.get("fly_brace", []):
    A.fly_brace(fb["name"], pt(fb["flange_pt"]), pt(fb["purlin_pt"]), mat(fb.get("material", "dark")), fb.get("section", "75x75x6 EA"), fb.get("both_sides", True))
for sh in sc.get("sheeting", []):
    L = lines[sh["line"]]; n = L.normal(sh["x0"] + 0.01)
    B.sheet_slope(sh.get("name", "sheet"), L.at(sh["x0"]) + n * sh.get("lift", 0.25), L.at(sh["x1"]) + n * sh.get("lift", 0.25), sh["y0"], sh["y1"], n,
                  mat(sh.get("material", "sheet")), rib=sh.get("rib", 0.041), pitch=sh.get("pitch", 0.333))
for md in sc.get("model", []):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from steelfig import readers
    model = readers.read(md["path"])
    for y in md.get("frames", [0.0]):
        A.build_model(model, md.get("sections", {}), M, default=md.get("default"), accent=md.get("accent", []) if y == md.get("frames", [0.0])[0] else [],
                      skip=md.get("skip", []), xmax=md.get("xmax"), y=y, top_lift=md.get("top_lift"))
for cut in sc.get("section_cut", []):
    H = B.hatch_mat("hatch", (0.78, 0.78, 0.78), (0.1, 0.1, 0.1), pitch=cut.get("pitch", 0.012), plane=cut.get("plane", "xz"))
    B.section_cut(B.all_meshes(), pt(cut["point"]), vec(cut["normal"]), hatch=H)
for ex in sc.get("explode", []):
    B.explode([o for o in B.all_meshes() if o.name in ex["objects"] or o.name.split("_")[0] in ex["objects"]], ex["vector"])

# anchors: automatic ones for every member (m.<name>, m.<name>.a, m.<name>.b), then the scene's own
An = B.member_anchors()
An.update({k: (tuple(pt(v)) if not (isinstance(v, list) and v and isinstance(v[0], (list, str))) else [tuple(pt(q)) for q in v]) for k, v in sc.get("anchors", {}).items()})
for d in sc.get("dim", []):
    B.dim3(An, d["name"], pt(d["a"]), pt(d["b"]), pt(d["off"]))
for w in sc.get("wave", []):
    An[w["name"]] = B.wave(pt(w["a"]), pt(w["b"]), w.get("amp", 0.3), vec(w.get("side", [0, -1, 0])))
print("built", len(B.all_meshes()), "objects")

for v in sc.get("view", []):
    if "camera" in v:
        c = v["camera"]; cam = B.setup(cam_loc=c[0:3], target=c[3:6], lens=c[6], res=v.get("res"), line=v.get("line"), quick=quick, cam=opt.get("cam"))
    else:
        o = v["ortho"]; cam = B.setup(cam_loc=(0, -10, 0), target=(0, 0, 0), res=v.get("res"), line=v.get("line"), quick=quick)
        B.ortho_view(cam, o["look"], o["scale"], pt(o["at"]))
    extra = []
    for k in v.get("bounds", []):
        a = An[k]; extra += a if isinstance(a, list) else [a]
    for d in v.get("draw", []):
        if d[0] == "dim3": extra += [An[d[1] + "_a2"], An[d[1] + "_b2"]]
        if d[0] in ("line", "fill"):
            for k in d[1]:
                k = k.split("#")[0]
                if k in An: extra += An[k] if isinstance(An[k], list) else [An[k]]
    crop = [tuple(pt(q)) for q in v["crop"]] if "crop" in v else None
    B.render(out, v["name"], An, bounds_extra=extra, crop_pts=crop, margin=v.get("margin", 0.02))
    # the camera is rebuilt per view: remove it and the lights so the next setup() starts clean
    import bpy
    for ob in [o for o in bpy.context.scene.objects if o.type in ("CAMERA", "LIGHT")]: bpy.data.objects.remove(ob, do_unlink=True)
