#!/usr/bin/env python3
"""Make sure the steelfig repository is present and current, and say where it is. Run this once at the start of
a figure task; it is safe to run every time.
    python3 setup.py            -> prints STEELFIG_HOME=<path> and the doctor report
Location: $STEELFIG_HOME if set, else an existing ~/steelfig or ~/Developer/steelfig, else a fresh clone at ~/steelfig.
Updates an existing clone with a fast-forward pull (never discards local changes)."""
import os, sys, subprocess, shutil

REPO = "https://github.com/hdr050127-max/steelfig"
home = os.path.expanduser("~")
candidates = [os.environ.get("STEELFIG_HOME"), os.path.join(home, "steelfig"), os.path.join(home, "Developer", "steelfig")]
path = next((p for p in candidates if p and os.path.isdir(os.path.join(p, "steelfig"))), None)
git = shutil.which("git")
if path is None:
    path = candidates[0] or os.path.join(home, "steelfig")
    if not git: sys.exit("git is not installed: install git, or download %s as a zip and unpack it to %s" % (REPO, path))
    print("cloning steelfig to", path); subprocess.run([git, "clone", "--depth", "1", REPO, path], check=True)
elif git and os.path.isdir(os.path.join(path, ".git")):
    r = subprocess.run([git, "-C", path, "pull", "--ff-only", "--quiet"], capture_output=True, text=True)
    print("updated" if r.returncode == 0 else "not updated (local changes or offline): " + r.stderr.strip()[:200])
print("STEELFIG_HOME=" + path)
for d in ("catalogues", "details", "models", "styles", "local"): os.makedirs(os.path.join(path, "resources", d), exist_ok=True)
subprocess.run([sys.executable, os.path.join(path, "steelfig", "cli.py"), "doctor"])
res = os.path.join(path, "resources"); n = sum(len(f) for _, _, f in os.walk(res))
print("resources:", res, "(%d file(s); drop catalogues, standard details, models and styles there)" % n)
