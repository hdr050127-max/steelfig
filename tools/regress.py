#!/usr/bin/env python3
"""Deterministic regression: build every example scene with --quick --check and require a silent build
(no WARNING / CLASH / REALISM / ERROR), the figure fragment, the preview PDF and the rationale file.
    python3 tools/regress.py [out_root]          (default: /tmp/steelfig_regress)
Exit code 1 if any scene fails. Run it after every change to the tool, the style or the examples."""
import os, sys, glob, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_root = sys.argv[1] if len(sys.argv) > 1 else "/tmp/steelfig_regress"
scenes = sorted(p for p in glob.glob(os.path.join(ROOT, "examples", "*", "*.toml")) if not os.path.basename(p).startswith("brief"))
rows, bad = [], 0
for sc in scenes:
    name = os.path.splitext(os.path.basename(sc))[0]; od = os.path.join(out_root, name); rep = os.path.join(od, "rep")
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join(ROOT, "steelfig", "cli.py"), "build", sc, od, "--report", rep, "--quick", "--check"],
                       capture_output=True, text=True)
    log = r.stdout + r.stderr
    flags = [l.strip() for l in log.splitlines() if l.startswith(("overlay WARNING", "CLASH", "REALISM", "ERROR")) or "Traceback" in l]
    frag = glob.glob(os.path.join(rep, "figures", "fig_*.tex")); prev = glob.glob(os.path.join(rep, "preview", "prev_*.pdf")); rat = glob.glob(os.path.join(od, "*_rationale.md"))
    ok = r.returncode == 0 and not flags and frag and prev and rat
    bad += not ok
    rows.append((name, "ok" if ok else "FAIL", "%.0fs" % (time.time() - t), flags[:3] + ([] if frag else ["no fragment"]) + ([] if prev else ["no preview"]) + ([] if rat else ["no rationale"])))
print("%-16s %-5s %5s  %s" % ("scene", "", "time", "problems"))
for n, st, tm, pr in rows: print("%-16s %-5s %5s  %s" % (n, st, tm, "; ".join(pr)))
print("\n%d scene(s), %d failing" % (len(rows), bad))
sys.exit(1 if bad else 0)
