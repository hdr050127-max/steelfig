"""Scene files: describe a figure in TOML instead of Python. `steelfig build scene.toml out/` runs Blender on the
geometry, renders every view, draws the annotation and writes the figure fragment + preview PDF.

Points are [x, y, z] in metres, or a string expression evaluated with these names: the lines declared in
[[line]] (roof.at(x), roof.along(s), roof.normal(x), roof.tangent(x)), V(x, y, z), sec("310UB46.2") (profile dict
with d, b, tf, tw, t in metres), math, and m.<member name>.a / .b (its end points). Example (metres):

    title = "West knee"
    [[line]]  name = "roof"  points = [[0, 10.51], [6.278, 10.795], [21.993, 11.508]]  lift = 0.2665
    [[member]] name = "col" section = "610UB113" from = [0, 0, 2.5] to = "roof.at(0) + V(0, 0, 0.5)"
               up = [1, 0, 0] cut1 = ["roof.at(0)", "roof.normal(0)"] material = "accent"
    [[member]] name = "raf" section = "530UB92.4" from = "roof.at(0.33)" to = "roof.at(6.0)" up = "roof.normal(1)" align = "top"
    [[purlins]] line = "roof" spacing = 1.2 y0 = -1.5 y1 = 1.8 section = "Z25019" material = "light"
    [anchors] col = [0.3, -0.11, 4.0]  raf = "roof.at(4.2) - roof.normal(1) * 0.2 + V(0, -0.1, 0)"
    [[dim]] name = "le" a = "roof.at(0.33) - roof.normal(1) * 0.533" b = "roof.at(2.73) - roof.normal(1) * 0.533" off = [0, -0.3, -0.5]
    [[view]] name = "knee" camera = [7.5, -8, 4.2, 1.8, 0.2, 5.6, 40] width_cm = 14
      [[view.label]] anchor = "col" text = "610UB113 column" dx = 1.3 dy = -0.5
      draw = [["dim3", "le", "$L_e = 2400$", "below"]]
    [figure] name = "knee" key_cols = 2

The TOML is compiled to JSON (Blender has no TOML reader for arbitrary paths? it does: tomllib) and executed by
blender/build_scene.py; the annotation runs here with overlay.py."""
import os, sys, json, subprocess, tomllib, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)


def load(path):
    with open(path, "rb") as fh: return tomllib.load(fh)


def blender():
    for p in (os.environ.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender"),
              r"C:\Program Files\Blender Foundation\Blender\blender.exe", *sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"), reverse=True)):
        if p and os.path.exists(p): return p
    sys.exit("Blender not found: install it or set BLENDER=/path/to/blender")


def run_blender(script, out_dir, extra=()):
    cmd = [blender(), "--background", "--python-expr", "import sys; sys.path.insert(0, %r)" % os.path.join(ROOT, "blender"),
           "--python", os.path.abspath(script), "--", os.path.abspath(out_dir), *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = r.stdout + r.stderr
    bad = r.returncode != 0 or "Traceback" in log
    lines = [l for l in log.splitlines() if l.strip() and not l.startswith(("Blender ", "Read prefs", "Fra:"))]
    err = [l for l in lines if l.startswith("ERROR")]
    if err: sys.exit("\n".join(err))
    print("\n".join(lines[-40:] if bad else [l for l in lines if l.startswith(("rendered", "built", "WARNING", "CLASH", "clash check", "camera ", "glb", "REALISM", "rationale"))]))
    if bad: sys.exit("Blender failed on %s" % script)


def build(scene_path, out_dir, report_dir=None, quick=False, preview=True, png=False, check=False, annotate_=True):
    """geometry + renders (Blender), then annotation (overlay) for every view; returns the figure body.
    png=True also rasterises the preview PDF (300 dpi) for Word / slides users; annotate_=False = plain renders only."""
    return build_from(load(scene_path), os.path.dirname(os.path.abspath(scene_path)), out_dir, report_dir, quick, preview, png, check, annotate_)


def to_png(pdf, dpi=300):
    """preview PDF -> PNG next to it (poppler's pdftoppm, or PyMuPDF if installed)."""
    out = pdf[:-4]
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-singlefile", pdf, out], check=True); print("png", out + ".png"); return out + ".png"
    try:
        import fitz
        doc = fitz.open(pdf); pix = doc[0].get_pixmap(dpi=dpi); pix.save(out + ".png"); print("png", out + ".png"); return out + ".png"
    except ImportError:
        print("no pdftoppm (brew install poppler) or PyMuPDF: PNG not written; the PDF is at", pdf)


def png_figure(sc, out_dir, rep, pieces_png):
    """annotated PNG per view, drawn with Pillow (no LaTeX needed)."""
    from steelfig import overlay_png as OP
    for vn, P, labels, draw, key in pieces_png:
        out = os.path.join(rep, "preview", "%s_annotated.png" % vn)
        OP.render(P, labels, draw, key, out); print("annotated png", out)


def annotate_file(scene_path, out_dir, report_dir=None, preview=True, png=False):
    """redo only the annotation of an earlier build (labels, highlights, dims) without running Blender."""
    sc = load(scene_path)
    body = annotate(sc, out_dir, report_dir or out_dir, preview or png)
    if png: to_png(os.path.join(report_dir or out_dir, "preview", "prev_%s.pdf" % (sc.get("figure", {}).get("name") or "figure")))
    return body


def annotate(sc, out_dir, rep, preview=True):
    sys.path.insert(0, ROOT)
    from steelfig import overlay as O, compose as C, layout as LY
    name = sc.get("figure", {}).get("name") or os.path.splitext(os.path.basename(out_dir))[0]
    img_dir = sc.get("figure", {}).get("image_dir", "images/steelfig"); F = sc.get("figure", {})
    layout, rows = C.plan(sc, out_dir); W = float(F.get("width_cm", 15.6)); pieces, key_all = {}, []; pieces_png = []
    for r in rows:
        for v, w, h in r:
            vn = v["name"]; jp = os.path.join(out_dir, vn + ".json"); jf = os.path.join(rep, img_dir, vn + ".jpg")
            O.flatten(os.path.join(out_dir, vn + ".png"), jf)
            P = O.Pic(os.path.join(img_dir, vn + ".jpg"), jp, w); P.file = jf
            for i, hl in enumerate(v.get("highlight", [])):
                P.highlight(hl["objects"], hl.get("colour", "#c9553f"), hl.get("alpha", 0.45), hl.get("outline", 0), hl.get("dim", 0.0),
                            out=os.path.join(rep, img_dir, "%s_hl%s.jpg" % (vn, i or "")))
                P.png = os.path.join(img_dir, "%s_hl%s.jpg" % (vn, i or ""))
            labels = [(l["anchor"], l.get("text", ""), l.get("dx"), l.get("dy")) + ((l["num"],) if "num" in l else ()) for l in v.get("label", [])]
            draw = [tuple(d) for d in v.get("draw", [])]
            for l in labels:
                if l[0].split("#")[0].replace("mid:", "").split(",")[0] not in P.A:
                    sys.exit("ERROR in [[view]] name = \"%s\": label anchor %r is not an anchor of this render; define it under [anchors] "
                             "(expressions are not allowed in `anchor`). Known: %s" % (vn, l[0], ", ".join(sorted(P.A))[:400]))
            occ = LY.Occupancy(P); P._occ = occ; fixed = []
            for d in draw:
                if d[0] == "dim3" and d[1] + "_a2" not in P.A and d[1] + "_c0_a2" in P.A: O.pick_dim(P, d[1])
            for d in draw:
                if d[0] == "dim3":
                    try: a2, b2 = P.pts(d[1] + "_a2")[0], P.pts(d[1] + "_b2")[0]; fixed.append(((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2))
                    except KeyError: pass
            if any(l[2] is None or l[3] is None for l in labels):
                labels = LY.place_balloons(P, labels, occ, fixed=fixed)
                print("auto balloons [%s]: %s" % (vn, ", ".join("%s (%+.1f, %+.1f)" % (l[0], l[2], l[3]) for l in labels)))
            start = len(key_all) + 1 if v.get("continue_numbers", True) else 1
            tik, key = O.balloon(P, labels, draw, start=start)
            numbered, n = [], start - 1
            for l in labels:
                if len(l) > 4: numbered.append(tuple(l))
                else: n += 1; numbered.append(tuple(l[:4]) + (n,))
            for f in LY.check(P, numbered, draw, key, occ): O.warn("[%s] %s" % (vn, f))
            key_all += key; pieces[vn] = tik; pieces_png.append((vn, P, numbered, draw, key))
    key_all += list(F.get("key_extra", []))
    body = C.figure(rows, pieces, W, key_all, F.get("key_cols"))
    O.emit(os.path.join(rep, "figures", "fig_%s.tex" % name), body, "steelfig build")
    if preview:
        try:
            pdf = O.preview_doc(C.page(body, sc.get("title", name), None, W), os.path.join(rep, "preview"), name, cwd=rep)
            print("preview", pdf)
        except FileNotFoundError:
            print("no pdflatex: writing the annotated figure as PNG instead (preview/<view>_annotated.png)")
            png_figure(sc, out_dir, rep, pieces_png)
    print("layout %s: %s" % (layout, "; ".join(" + ".join("%s %.1fx%.1f cm" % (v["name"], w, h) for v, w, h in r) for r in rows)))
    if O.warnings(): print("%d warning(s): check the lines above" % len(O.warnings()))
    return body


def build_all(target, out_root, report_dir=None, quick=False, check=False):
    """build every scene of a figure set with one style and shared defaults, so the figures of a report match.
    target: a folder (every *.toml in it) or a set file:
        style = "default"                 # applied to every scene
        [defaults]  width_cm = 15.6  key_cols = 2      # [figure] values a scene does not set itself
        scenes = ["knee/knee.toml", "connections/connections.toml"]
    Prints one line per figure with its warnings and clashes."""
    import glob
    if os.path.isdir(target):
        paths, st, defaults = sorted(glob.glob(os.path.join(target, "**", "*.toml"), recursive=True)), None, {}
    else:
        S = load(target); base = os.path.dirname(os.path.abspath(target))
        defaults = S.get("defaults", {}); scenes = S.get("scenes") or defaults.pop("scenes", None)
        if not scenes: sys.exit("set file: no `scenes = [...]` list (put it above any [table] header)")
        paths = [p if os.path.isabs(p) else os.path.join(base, p) for p in scenes]; st = S.get("style")
    rows = []
    for p in paths:
        sc = load(p); name = sc.get("figure", {}).get("name") or os.path.splitext(os.path.basename(p))[0]
        if st: sc["style"] = st
        sc.setdefault("figure", {})
        for k, v in defaults.items(): sc["figure"].setdefault(k, v)
        od = os.path.join(out_root, name); os.makedirs(od, exist_ok=True)
        tmp = os.path.join(od, "scene_set.toml")
        import tomllib  # noqa
        # write the merged scene back as TOML-free JSON path: build() expects a TOML, so keep the original and pass overrides
        from steelfig import overlay as O
        O._warn.clear()
        try:
            build_from(sc, os.path.dirname(os.path.abspath(p)), od, report_dir or od, quick, True, False, check)
            rows.append((name, "ok", len(O.warnings())))
        except SystemExit as e:
            rows.append((name, "FAILED: %s" % e, 0))
    print("\nfigure set:")
    for n, st_, w in rows: print("  %-20s %s%s" % (n, st_, "  (%d warning%s)" % (w, "s" if w != 1 else "") if w else ""))
    return rows


def plain(sc, out_dir, rep):
    """the geometry checkpoint: every view flattened to <rep>/images/steelfig/<view>.jpg and laid out on an A4
    page exactly as the annotated figure will be (same layout, sizes and captions), with nothing drawn on it."""
    sys.path.insert(0, ROOT)
    from steelfig import overlay as O, compose as C
    img_dir = sc.get("figure", {}).get("image_dir", "images/steelfig"); name = sc.get("figure", {}).get("name") or "figure"
    layout, rows = C.plan(sc, out_dir); W = float(sc.get("figure", {}).get("width_cm", 15.6)); pieces = {}; paths = []
    for r in rows:
        for v, w, h in r:
            jpg = os.path.join(rep, img_dir, v["name"] + ".jpg"); O.flatten(os.path.join(out_dir, v["name"] + ".png"), jpg); paths.append(jpg)
            pieces[v["name"]] = r"\includegraphics[width=%.2fcm]{%s}" % (w, os.path.join(img_dir, v["name"] + ".jpg"))
    body = C.figure(rows, pieces, W)
    try:
        pdf = O.preview_doc(C.page(body, sc.get("title", name), "geometry check, no annotation", W), os.path.join(rep, "preview"), name + "_plain", cwd=rep)
        print("plain preview", pdf)
    except Exception as e:
        print("plain preview not built (%s)" % str(e)[:300])
    for p_ in paths: print("plain", p_)
    print("layout %s: %s" % (layout, "; ".join(" + ".join("%s %.1fx%.1f cm" % (v["name"], w, h) for v, w, h in r) for r in rows)))
    return paths


def build_from(sc, base, out_dir, report_dir, quick=False, preview=True, png=False, check=False, annotate_=True):
    """build() for an already-loaded scene dict (paths relative to `base`). annotate_=False stops after the
    renders and writes the plain views only (geometry checkpoint)."""
    os.makedirs(out_dir, exist_ok=True)
    for md in sc.get("model", []):
        if md["path"].startswith("res:"): md["path"] = os.path.join(ROOT, "resources", md["path"][4:])      # the shared resources folder
        elif not os.path.isabs(md["path"]): md["path"] = os.path.join(base, md["path"])
    if sc.get("style"): os.environ["STEELFIG_STYLE"] = sc["style"] if os.path.isabs(sc["style"]) or "/" not in sc["style"] else os.path.join(base, sc["style"])
    spec = os.path.join(out_dir, "scene.json"); json.dump(sc, open(spec, "w"), indent=1)
    run_blender(os.path.join(ROOT, "blender", "build_scene.py"), out_dir, [spec] + (["quick"] if quick else []) + (["check=1"] if check else []))
    if not annotate_:
        paths = plain(sc, out_dir, report_dir or out_dir)
        if png: to_png(os.path.join(report_dir or out_dir, "preview", "prev_%s_plain.pdf" % (sc.get("figure", {}).get("name") or "figure")))
        return paths
    body = annotate(sc, out_dir, report_dir or out_dir, preview or png)
    if png: to_png(os.path.join(report_dir or out_dir, "preview", "prev_%s.pdf" % (sc.get("figure", {}).get("name") or "figure")))
    return body
