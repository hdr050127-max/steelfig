"""Build and render a scene.json (compiled from a steelfig TOML scene) inside Blender.
Run by steelfig/scene.py: Blender --background --python build_scene.py -- <out_dir> <scene.json> [quick]"""
import sys, os, json, math
import bpy
import bfig as B, assembly as A, connections as CN, rationale as R
from mathutils import Vector
from steelfig import sections as SEC_DB

out, quick, opt = B.args()
spec = [a for a in sys.argv[sys.argv.index("--") + 1:] if a.endswith(".json")][0]
sc = json.load(open(spec))
WHERE = ["scene"]


def fail(e):
    """one line saying where in the scene file and what, instead of a Python traceback."""
    msg = str(e).strip("'\"")
    if isinstance(e, NameError): msg += " (names you can use: V, math, sec, m.<member>, " + ", ".join(sorted(k for k in NS if k not in ("V", "math", "m", "sec"))) + ")"
    print("ERROR in %s: %s" % (WHERE[-1], msg)); sys.stdout.flush(); sys.exit(1)


class _at:
    def __init__(self, w): self.w = w
    def __enter__(self): WHERE.append(self.w)
    def __exit__(self, t, e, tb):
        if e is not None and not isinstance(e, SystemExit): fail(e)
        WHERE.pop(); return False
B.reset(); M = B.mats(); R.reset()
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


def mat(name, default="steel"):
    """palette material by name; None lets member() choose the finish from the section type."""
    return M[name] if name else (M[default] if default else None)


ys = sc.get("frames", [0.0])
msec = {mb["name"]: mb["section"] for mb in sc.get("member", [])}
conns = []
for cn in sc.get("connection", []):
  with _at('[[connection]] type = "%s" name = "%s"' % (cn.get("type"), cn.get("name", cn.get("type")))):
    typ = cn["type"]; nm = cn.get("name", typ); L = lines[cn["line"]] if "line" in cn else None
    kw = {k: (num(v) if isinstance(v, str) and k not in ("bolt",) and k.endswith(("_t", "_ext", "_in", "_off", "x", "y", "z0")) else v) for k, v in cn.items()
          if k not in ("type", "name", "line", "column", "rafter", "a", "b", "member", "primary", "secondary", "a0", "a1", "b0", "b1", "normal", "along", "host", "section")}
    if typ == "knee":
        conns.append(CN.knee(nm, L, num(cn["x"]), cn["column"], msec[cn["column"]], cn["rafter"], msec[cn["rafter"]], M, **{k: v for k, v in kw.items() if k != "x"}))
    elif typ == "splice":
        conns.append(CN.splice(nm, L, num(cn["x"]), cn["a"], msec[cn["a"]], cn["b"], msec[cn["b"]], M, **{k: v for k, v in kw.items() if k != "x"}))
    elif typ == "cap":
        conns.append(CN.cap(nm, L, num(cn["x"]), cn["column"], msec[cn["column"]], msec[cn["rafter"]], M, **{k: v for k, v in kw.items() if k != "x"}))
    elif typ == "base":
        conns.append(CN.base(nm, num(cn["x"]), cn["column"], msec[cn["column"]], M, **{k: v for k, v in kw.items() if k != "x"}))
    elif typ == "xbrace":
        conns.append(CN.xbrace(nm, pt(cn["a0"]), pt(cn["a1"]), pt(cn["b0"]), pt(cn["b1"]), vec(cn["normal"]), msec[cn["host"]], cn["section"], M, **kw))
    elif typ == "strut":
        conns.append(CN.strut(nm, pt(cn["a"]), pt(cn["b"]), vec(cn["normal"]), vec(cn["along"]), cn["section"], M, **kw))
    elif typ == "wsp":
        ms = next(q for q in sc["member"] if q["name"] == cn["secondary"]); a, b = pt(ms["from"]), pt(ms["to"]); y0 = num(cn["y"])
        if ms.get("align") != "top" or abs(a.x - b.x) > 1e-6: raise ValueError("the secondary must run along y with align = \"top\"")
        near = "cut0" if abs(a.y - y0) <= abs(b.y - y0) else "cut1"
        side = 1 if (b.y if near == "cut0" else a.y) > y0 else -1
        toes = (1 if b.y > a.y else -1) * (-1 if ms.get("flip") else 1)            # the profile's +v is ex x ey = +x for a member running towards +y
        conns.append(CN.wsp(nm, a.x, y0, side, near, toes, cn["secondary"], ms["section"], msec[cn["primary"]], a.z, members, M,
                            **{k: v for k, v in kw.items() if k not in ("x", "y")}))
    else:
        raise ValueError("unknown connection type " + typ)
conn_anchors = {}
auto_cuts = {}
for c in conns:
    for mname, cuts in c["cuts"].items(): auto_cuts.setdefault(mname, {}).update(cuts)
for mb in sc.get("member", []):
  with _at('[[member]] name = "%s"' % mb.get("name", "?")):
    a, b = pt(mb["from"]), pt(mb["to"])
    ac = auto_cuts.get(mb["name"], {})
    c0 = plane(mb.get("cut0")) if "cut0" in mb else ac.get("cut0"); c1 = plane(mb.get("cut1")) if "cut1" in mb else ac.get("cut1")
    for y in (ys if mb.get("per_frame") else [0.0]):
        off = Vector((0, y, 0))
        sh = lambda pl: (pl[0] + off, pl[1]) if pl else None
        ob = B.member("%s_%g" % (mb["name"], y) if y else mb["name"], a + off, b + off, mb["section"], mat(mb.get("material"), None),
                      up=vec(mb.get("up")), cut0=sh(c0), cut1=sh(c1), align=mb.get("align", "centroid"), flip=mb.get("flip", False),
                      secondary_=mb.get("secondary", False))
        if not y:
            members[mb["name"]] = ob; e = _Ends(); e.a, e.b = a, b; setattr(mem_ns, mb["name"], e)
for c, cn in zip(conns, sc.get("connection", [])):
  with _at('[[connection]] name = "%s" (building its parts)' % cn.get("name", cn["type"])):
    c["build"]()
    for k, v in c["anchors"].items(): conn_anchors["%s.%s" % (cn.get("name", cn["type"]), k)] = v
for pl in sc.get("plate", []):
  with _at('[[plate]] name = "%s"' % pl.get("name", "?")):
    B.plate(pl["name"], pt(pl["centre"]), vec(pl.get("ex", [1, 0, 0])), vec(pl.get("ey", [0, 1, 0])), pl["size"], mat(pl.get("material")))
for bg in sc.get("bolts", []):
  with _at('[[bolts]] name = "%s"' % bg.get("name", "?")):
    A.bolt_rows(bg["name"], pt(bg["centre"]), vec(bg.get("axis", [1, 0, 0])), vec(bg.get("up", [0, 0, 1])), vec(bg.get("side", [0, 1, 0])),
                nums(bg["rows"]), nums(bg["cols"]), bg.get("bolt", "M20"), num(bg.get("grip", 0.04)), mat(bg.get("material", "dark")))
for st in sc.get("stiffeners", []):
    A.stiffeners(st["name"], pt(st["column_pt"]), st["section"], nums(st["levels"]), mat(st.get("material", "light")), st.get("t", 0.012), vec(st.get("up", [1, 0, 0])))
purlin_pts = {}
for pu in sc.get("purlins", []):
  with _at('[[purlins]] name = "%s"' % pu.get("name", "pur")):
    res = A.purlins_on(pu.get("name", "pur"), lines[pu["line"]], num(pu["spacing"]), num(pu["y0"]), num(pu["y1"]), pu["section"], mat(pu.get("material", "light")),
                       num(pu.get("start", 0.0)), num(pu["until"]) if "until" in pu else None, from_end=pu.get("from_end", False), flip_alternate=pu.get("flip_alternate", False), flip=pu.get("flip", False))
    purlin_pts[pu.get("name", "pur")] = [p for p, _ in res]
    NS[pu.get("name", "pur")] = [p for p, _ in res]
    if pu.get("cleats"): CN.purlin_cleats(pu.get("name", "pur") + "_cl", [p for p, _ in res], pu["section"], lines[pu["line"]], M, frames=nums(pu.get("cleat_frames", [0.0])), flip=pu.get("flip", False))
    for _, ob in res: B.secondary(ob)
for gi in sc.get("girts", []):
  with _at('[[girts]] name = "%s"' % gi.get("name", "girt")):
    for _, ob in A.girts_on(gi.get("name", "girt"), num(gi["x"]), nums(gi["levels"]), num(gi["y0"]), num(gi["y1"]), gi["section"], mat(gi.get("material", "light")), vec(gi.get("outward", [-1, 0, 0]))): B.secondary(ob)
    if "cleat_frames" in gi: CN.girt_cleats(gi.get("name", "girt") + "_cl", num(gi["x"]), nums(gi["levels"]), nums(gi["cleat_frames"]), gi["section"], vec(gi.get("outward", [-1, 0, 0])), M)
fly_anchors = {}
for fb in sc.get("fly_brace", []):
    if "purlins" in fb:                                     # built form: against the purlin web, bolt, cleat
        pu = next(x for x in sc["purlins"] if x.get("name", "pur") == fb["purlins"]); L = lines[pu["line"]]
        pts = [p + Vector((0, num(fb.get("y", 0.0)), 0)) for p in purlin_pts[fb["purlins"]]]; x0 = pts[0].x if pts else 0.0
        mp = SEC_DB.profile(members[fb["member"]].name if False else fb["section_of"]) if "section_of" in fb else None
        d_m, b_m = (num(fb["member_depth"]), num(fb["member_bf"])) if "member_depth" in fb else (mp["d"], mp["b"])
        _, fa = A.fly_braces_on(fb.get("name", "fb"), pts, pu["section"], d_m, b_m, mat(fb.get("material", "dark")), mat("dark"),
                                fb.get("section"), normal=L.normal(x0 + 0.01), which=fb.get("at"), both_sides=fb.get("both_sides", True),
                                cleat=fb.get("cleat", True), line_tangent=L.tangent(x0 + 0.01) * (-1 if pu.get("flip") else 1), bolt=fb.get("bolt"), reach=num(fb["reach"]) if "reach" in fb else None,
                                sides=fb.get("sides"), member_tf=mp["tf"] if mp else None, member_tw=mp["tw"] if mp else None)
        fly_anchors.update(fa)
    else:                                                   # legacy: straight angle between two points
        A.fly_brace(fb["name"], pt(fb["flange_pt"]), pt(fb["purlin_pt"]), mat(fb.get("material", "dark")), fb.get("section", "75x75x6 EA"), fb.get("both_sides", True))
for sh in sc.get("sheeting", []):
  with _at('[[sheeting]]'):
    L = lines[sh["line"]]; n = L.normal(sh["x0"] + 0.01)
    B.secondary(B.sheet_slope(sh.get("name", "sheet"), L.at(sh["x0"]) + n * sh.get("lift", 0.25), L.at(sh["x1"]) + n * sh.get("lift", 0.25), sh["y0"], sh["y1"], n,
                  mat(sh.get("material", "sheet")), rib=sh.get("rib", 0.041), pitch=sh.get("pitch", 0.333)))
for md in sc.get("model", []):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from steelfig import readers
    model = readers.read(md["path"])
    for y in md.get("frames", [0.0]):
        res = A.build_model(model, md.get("sections", {}), M, default=md.get("default"), accent=md.get("accent", []) if y == md.get("frames", [0.0])[0] else [],
                            skip=md.get("skip", []), xmax=md.get("xmax"), y=y, top_lift=md.get("top_lift"), connections=md.get("connections", True))
        if y == md.get("frames", [0.0])[0]: conn_anchors.update(res.get("_anchors", {}))
for cut in sc.get("section_cut", []):
    H = B.hatch_mat("hatch", (0.78, 0.78, 0.78), (0.1, 0.1, 0.1), pitch=cut.get("pitch", 0.012), plane=cut.get("plane", "xz"))
    B.section_cut(B.all_meshes(), pt(cut["point"]), vec(cut["normal"]), hatch=H)
for ex in sc.get("explode", []):
    B.explode([o for o in B.all_meshes() if o.name in ex["objects"] or o.name.split("_")[0] in ex["objects"]], ex["vector"])

# anchors: automatic ones for every member (m.<name>, m.<name>.a, m.<name>.b), fly braces (fb<k>+1 ...), then the scene's own
An = B.member_anchors(); An.update(fly_anchors); An.update(conn_anchors)
for k, v in sc.get("anchors", {}).items():
    with _at("[anchors] %s" % k):
        An[k] = tuple(pt(v)) if not (isinstance(v, list) and v and isinstance(v[0], (list, str))) else [tuple(pt(q)) for q in v]
for d in sc.get("dim", []):
    with _at('[[dim]] name = "%s"' % d.get("name", "?")):
        if d.get("off", "auto") == "auto": B.dim3_auto(An, d["name"], pt(d["a"]), pt(d["b"]))
        else: B.dim3(An, d["name"], pt(d["a"]), pt(d["b"]), pt(d["off"]))
for w in sc.get("wave", []):
    with _at('[[wave]] name = "%s"' % w.get("name", "?")):
        An[w["name"]] = B.wave(pt(w["a"]), pt(w["b"]), w.get("amp", 0.3), vec(w.get("side", [0, -1, 0])))
print("built", len(B.all_meshes()), "objects")
R.dump(os.path.join(out, (sc.get("figure", {}).get("name") or "figure") + "_rationale.md"), sc.get("title", ""))
B.export_glb(os.path.join(out, "scene.glb"))
if sc.get("check", False) or "check" in opt:
    B.check_clashes(min_cm3=float(sc.get("check_min_cm3", 5.0)))

B.split_long_faces()
for v in sc.get("view", []):
  with _at('[[view]] name = "%s"' % v.get("name", "?")):
    cam_list = None
    if v.get("camera") == "auto" or "auto" in v or ("camera" not in v and "ortho" not in v):
        a = v.get("auto", {}) if isinstance(v.get("auto"), dict) else {}
        focus = [o for o in B.all_meshes() if any(o.name == f or o.name.startswith(f + "_") for f in a.get("focus", []))] or None
        fit = [o for o in B.all_meshes() if any(o.name == f or o.name.startswith(f + "_") for f in a.get("fit", []))] or None
        cam_list = B.auto_camera(focus, fit, a.get("dir", [0.65, -1.0, 0.36]), a.get("lens", 45), a.get("fill", 0.8), quick=quick, line=v.get("line"))
        print("camera %s = [%s]   (auto; paste into the scene to fix it)" % (v["name"], ", ".join("%g" % x for x in cam_list)))
    elif "camera" in v:
        c = v["camera"]; cam = B.setup(cam_loc=c[0:3], target=c[3:6], lens=c[6], res=v.get("res"), line=v.get("line"), quick=quick, cam=opt.get("cam")); cam_list = list(c)
    else:
        o = v["ortho"]; cam = B.setup(cam_loc=(0, -10, 0), target=(0, 0, 0), res=v.get("res"), line=v.get("line"), quick=quick)
        if o.get("auto") or "scale" not in o:
            fit = [ob for ob in B.all_meshes() if any(ob.name == f or ob.name.startswith(f + "_") for f in o.get("fit", []))] or None
            scale, at = B.auto_ortho(cam, o["look"], fit, o.get("fill", 0.9))
            print("ortho %s = { look = \"%s\", scale = %.2f, at = [%.2f, %.2f, %.2f] }   (auto)" % (v["name"], o["look"], scale, *at))
        else:
            B.ortho_view(cam, o["look"], num(o["scale"]), pt(o["at"]))
    extra = []
    for k in v.get("bounds", []):
        a = An[k]; extra += a if isinstance(a, list) else [a]
    for d in v.get("draw", []):
        if d[0] == "dim3":
            if d[1] + "_a2" in An: extra += [An[d[1] + "_a2"], An[d[1] + "_b2"]]
            else: extra += [An[d[1] + "_c%d_a2" % k] for k in range(int(An[d[1] + "_ncand"][0])) if k % 4 == 1] + [An[d[1] + "_c%d_b2" % k] for k in range(int(An[d[1] + "_ncand"][0])) if k % 4 == 1]
        if d[0] in ("line", "fill"):
            for k in d[1]:
                k = k.split("#")[0]
                if k in An: extra += An[k] if isinstance(An[k], list) else [An[k]]
    crop = [tuple(pt(q)) for q in v["crop"]] if "crop" in v else None
    handle = None
    if "cut" in v:                                        # section cut for this view only: everything on the +normal side goes
        cu = v["cut"]; H = B.hatch_mat("hatch_view", (0.78, 0.78, 0.78), (0.1, 0.1, 0.1), pitch=cu.get("pitch", 0.012), plane=cu.get("plane", "xz"))
        objs = [ob for ob in B.all_meshes() if not cu.get("objects") or any(ob.name == f or ob.name.startswith(f + "_") for f in cu["objects"])]
        handle = B.section_cut(objs, pt(cu["point"]), vec(cu["normal"]), hatch=H if cu.get("hatch", True) else None, apply=False)
        bpy.context.view_layer.update()
    B.render(out, v["name"], An, bounds_extra=extra, crop_pts=crop, margin=v.get("margin", 0.02))
    B.uncut(handle)
    if cam_list:
        jp = os.path.join(out, v["name"] + ".json"); J = json.load(open(jp)); J["camera"] = cam_list; json.dump(J, open(jp, "w"), indent=1)
    # the camera is rebuilt per view: remove it and the lights so the next setup() starts clean
    import bpy
    for ob in [o for o in bpy.context.scene.objects if o.type in ("CAMERA", "LIGHT")]: bpy.data.objects.remove(ob, do_unlink=True)
