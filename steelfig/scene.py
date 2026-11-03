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
import os, sys, json, subprocess, tomllib, shutil

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)


def load(path):
    with open(path, "rb") as fh: return tomllib.load(fh)


def blender():
    for p in (os.environ.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender"),
              r"C:\Program Files\Blender Foundation\Blender\blender.exe"):
        if p and os.path.exists(p): return p
    sys.exit("Blender not found: install it or set BLENDER=/path/to/blender")


def run_blender(script, out_dir, extra=()):
    cmd = [blender(), "--background", "--python-expr", "import sys; sys.path.insert(0, %r)" % os.path.join(ROOT, "blender"),
           "--python", os.path.abspath(script), "--", os.path.abspath(out_dir), *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = r.stdout + r.stderr
    bad = r.returncode != 0 or "Traceback" in log
    lines = [l for l in log.splitlines() if l.strip() and not l.startswith(("Blender ", "Read prefs", "Fra:"))]
    print("\n".join(lines[-40:] if bad else [l for l in lines if l.startswith(("rendered", "built", "WARNING"))]))
    if bad: sys.exit("Blender failed on %s" % script)


def build(scene_path, out_dir, report_dir=None, quick=False, preview=True, png=False):
    """geometry + renders (Blender), then annotation (overlay) for every view; returns the figure body.
    png=True also rasterises the preview PDF (300 dpi) for Word / slides users."""
    sc = load(scene_path); os.makedirs(out_dir, exist_ok=True)
    base = os.path.dirname(os.path.abspath(scene_path))
    for md in sc.get("model", []):                                   # model paths are relative to the scene file
        if not os.path.isabs(md["path"]): md["path"] = os.path.join(base, md["path"])
    if sc.get("style"): os.environ["STEELFIG_STYLE"] = sc["style"] if os.path.isabs(sc["style"]) or "/" not in sc["style"] else os.path.join(base, sc["style"])
    spec = os.path.join(out_dir, "scene.json"); json.dump(sc, open(spec, "w"), indent=1)
    run_blender(os.path.join(ROOT, "blender", "build_scene.py"), out_dir, [spec] + (["quick"] if quick else []))
    body = annotate(sc, out_dir, report_dir or out_dir, preview or png)
    if png: to_png(os.path.join(report_dir or out_dir, "preview", "prev_%s.pdf" % (sc.get("figure", {}).get("name") or "figure")))
    return body


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


def annotate(sc, out_dir, rep, preview=True):
    sys.path.insert(0, ROOT)
    from steelfig import overlay as O
    name = sc.get("figure", {}).get("name") or os.path.splitext(os.path.basename(out_dir))[0]
    img_dir = sc.get("figure", {}).get("image_dir", "images/steelfig")
    parts, key_all = [], []
    for v in sc.get("view", []):
        vn = v["name"]
        O.flatten(os.path.join(out_dir, vn + ".png"), os.path.join(rep, img_dir, vn + ".jpg"))
        jp = os.path.join(out_dir, vn + ".json")
        P = O.pic_by_height(os.path.join(img_dir, vn + ".jpg"), jp, v["height_cm"], v.get("max_width_cm", 16)) if "height_cm" in v \
            else O.Pic(os.path.join(img_dir, vn + ".jpg"), jp, v.get("width_cm", 14))
        labels = [(l["anchor"], l.get("text", ""), l.get("dx", 0.8), l.get("dy", 0.8)) + ((l["num"],) if "num" in l else ()) for l in v.get("label", [])]
        draw = [tuple(d) for d in v.get("draw", [])]
        tik, key = O.balloon(P, labels, draw, start=len(key_all) + 1 if v.get("continue_numbers", True) else 1)
        key_all += key
        part = O.captioned(tik, v["caption"], P.W + 0.4) if v.get("caption") else tik
        parts.append((part, P))
    for k in sc.get("figure", {}).get("key_extra", []): key_all.append(k)
    F = sc.get("figure", {}); W = F.get("width_cm", max(p.W for _, p in parts) if parts else 14)
    layout = F.get("layout", "stack")
    if layout == "row": body = O.row([p for p, _ in parts])
    else: body = ("\n\n" + r"\vspace{2mm}" + "\n").join(p for p, _ in parts)
    key = O.keycols(key_all, W, F.get("key_cols", 1)) if key_all else ""
    if F.get("key_beside") and len(parts) > 1:
        body = ("\n\n" + r"\vspace{2mm}" + "\n").join(p for p, _ in parts[:-1]) + "\n\n" + r"\vspace{2mm}" + "\n" + parts[-1][0] + r"\hfill" + O.keylist(key_all, W - parts[-1][1].W - 0.8)
    else:
        body = body + ("\n\n" + r"\vspace{2mm}" + "\n" + key if key else "")
    O.emit(os.path.join(rep, "figures", "fig_%s.tex" % name), body, "steelfig build")
    if preview:
        pdf = O.preview(body, os.path.join(rep, "preview"), name, cwd=rep, width_cm=W + 1)
        print("preview", pdf)
    if O.warnings(): print("%d warning(s): check the dimensions above" % len(O.warnings()))
    return body
