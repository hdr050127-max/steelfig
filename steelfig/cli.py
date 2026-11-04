"""steelfig command line.
  steelfig build <scene.toml> <out_dir> [--report <dir>] [--quick] [--no-preview] [--png] [--check]
                                              TOML scene -> renders, fig_<name>.tex, preview PDF (+ PNG for Word);
                                              --check reports members that pass through each other (CLASH lines)
  steelfig annotate <scene.toml> <out_dir> [--report <dir>] [--png]                 redo labels / highlights only (no Blender)
  steelfig render <fig.py> <out_dir> [quick] [cam=...]                               run a Python figure script in Blender
  steelfig sections <query>                                                          search the catalogue (e.g. "360UB", "SHS", "x8 EA")
  steelfig model <file.arc|nodes.csv>                                                summarise an analysis model
  steelfig doctor                                                                    check Blender, Pillow, pdflatex"""
import os, sys, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path: sys.path.insert(0, ROOT)


def main(argv=None):
    a = list(argv if argv is not None else sys.argv[1:])
    if not a or a[0] in ("-h", "--help"): print(__doc__); return 0
    cmd = a.pop(0)
    if cmd == "build":
        from steelfig import scene
        rep = None; quick = False; prev = True
        if "--report" in a: i = a.index("--report"); rep = a[i + 1]; del a[i:i + 2]
        if "--quick" in a: a.remove("--quick"); quick = True
        if "--no-preview" in a: a.remove("--no-preview"); prev = False
        png = "--png" in a
        if png: a.remove("--png")
        chk = "--check" in a
        if chk: a.remove("--check")
        scene.build(a[0], a[1], rep, quick, prev, png, chk); return 0
    if cmd == "annotate":
        from steelfig import scene
        rep = None
        if "--report" in a: i = a.index("--report"); rep = a[i + 1]; del a[i:i + 2]
        png = "--png" in a
        if png: a.remove("--png")
        scene.annotate_file(a[0], a[1], rep, True, png); return 0
    if cmd == "render":
        from steelfig import scene
        scene.run_blender(a[0], a[1], a[2:]); return 0
    if cmd == "sections":
        from steelfig import sections as S
        for q in a or ["UB"]:
            for d in S.search(q):
                r = S.find(d); print("%-18s %-4s %s" % (d, r["type"], " ".join("%s=%g" % (k, r[k]) for k in ("d", "b", "bf", "tf", "tw", "t", "b1", "b2", "mass_kg_m") if k in r)))
        return 0
    if cmd == "model":
        from steelfig import readers
        print(readers.read(a[0]).summary()); return 0
    if cmd == "doctor":
        from steelfig import scene, overlay
        try: print("Blender :", scene.blender())
        except SystemExit as e: print("Blender : MISSING -", e)
        try: import PIL; print("Pillow  :", PIL.__version__)
        except ImportError: print("Pillow  : MISSING (pip install pillow) - needed to flatten renders to JPEG")
        try: print("pdflatex:", overlay.pdflatex())
        except FileNotFoundError as e: print("pdflatex: MISSING -", e, "(only needed for preview PDFs / LaTeX reports)")
        print("Python  :", sys.version.split()[0]); return 0
    print("unknown command", cmd); print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
