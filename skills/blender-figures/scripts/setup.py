#!/usr/bin/env python3
"""Make sure the steelfig repository is present and current, say where it is, and (on request) install what is
missing. Safe to run every time; works with any Python 3 (3.8+), no third-party modules.
    python3 setup.py              -> get/update steelfig, print STEELFIG_HOME=<path> and the doctor report
    python3 setup.py --install    -> also install what the doctor reports missing (see below)
    python3 setup.py --install --no-tex --no-blender   -> install only the Python side
Location: $STEELFIG_HOME if set, else an existing ~/steelfig or ~/Developer/steelfig, else a fresh copy at ~/steelfig
(git clone, or a zip download from GitHub when git is not installed). Updates a clone with a fast-forward pull.
--install does, in this order, only for things that are missing:
  Python 3.11+   needed by steelfig (tomllib). Looks for python3.11/3.12/3.13 in the usual places and records the
                 one to use in <path>/.python; otherwise Homebrew (macOS) or winget (Windows) installs 3.12.
  Pillow, PyMuPDF   pip install --user (about 25 MB): JPEG flattening, PNG annotation without LaTeX, PDF -> PNG.
  TinyTeX        pdflatex + the tikz/standalone packages, in the user's home (about 120 MB): LaTeX fragments and
                 PDF previews. Without it figures are still produced as annotated PNGs. (Windows: MiKTeX via winget)
  Blender        Homebrew cask (macOS), winget (Windows) or snap (Linux), about 350 MB. Without a package
                 manager it prints the download link.
Nothing is installed system-wide except Blender through the platform's package manager."""
import os, sys, subprocess, shutil, platform, glob, io, zipfile, urllib.request

REPO = "https://github.com/hdr050127-max/steelfig"
ZIP = REPO + "/archive/refs/heads/main.zip"
home = os.path.expanduser("~"); mac, win = sys.platform == "darwin", os.name == "nt"
flags = set(sys.argv[1:]); install = "--install" in flags
candidates = [os.environ.get("STEELFIG_HOME"), os.path.join(home, "steelfig"), os.path.join(home, "Developer", "steelfig")]
path = next((p for p in candidates if p and os.path.isdir(os.path.join(p, "steelfig"))), None)
git = shutil.which("git")


def sh(cmd, **kw):
    print("$", " ".join(cmd), flush=True); return subprocess.run(cmd, **kw)


# ---------------------------------------------------------------- 1. the repository
if path is None:
    path = candidates[0] or os.path.join(home, "steelfig")
    cloned = False
    if git:
        print("cloning steelfig to", path); cloned = sh([git, "clone", "--depth", "1", REPO, path]).returncode == 0
        if not cloned: shutil.rmtree(path, ignore_errors=True); print("git clone failed (no command line tools?); falling back to a zip download")
    if not cloned:
        print("downloading", ZIP, "to", path)
        data = urllib.request.urlopen(ZIP, timeout=120).read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            top = z.namelist()[0].split("/")[0]
            for m in z.infolist():
                rel = m.filename[len(top) + 1:]
                if not rel: continue
                dst = os.path.join(path, rel)
                if m.is_dir(): os.makedirs(dst, exist_ok=True); continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with z.open(m) as src, open(dst, "wb") as fh: fh.write(src.read())
                if rel.startswith("bin/"): os.chmod(dst, 0o755)
        print("unpacked (no git: re-run setup.py after deleting the folder to update)")
elif git and os.path.isdir(os.path.join(path, ".git")):
    r = subprocess.run([git, "-C", path, "pull", "--ff-only", "--quiet"], capture_output=True, text=True)
    print("updated" if r.returncode == 0 else "not updated (local changes or offline): " + r.stderr.strip()[:200])
print("STEELFIG_HOME=" + path, flush=True)
for d in ("catalogues", "details", "models", "styles", "local"): os.makedirs(os.path.join(path, "resources", d), exist_ok=True)


# ---------------------------------------------------------------- 2. a Python that can run steelfig (3.11+)
def py_ok(exe):
    try:
        r = subprocess.run([exe, "-c", "import sys; print(sys.version_info[0] * 100 + sys.version_info[1])"], capture_output=True, text=True, timeout=20)
        return r.returncode == 0 and int(r.stdout.strip()) >= 311
    except Exception: return False


def find_python():
    names = ["python3.13", "python3.12", "python3.11", "python3", "python"]
    places = [shutil.which(n) for n in names]
    places += glob.glob("/opt/homebrew/bin/python3.1[1-9]") + glob.glob("/usr/local/bin/python3.1[1-9]")
    places += glob.glob("/Library/Frameworks/Python.framework/Versions/3.1[1-9]/bin/python3")
    places += glob.glob(os.path.join(home, "AppData", "Local", "Programs", "Python", "Python31[1-9]*", "python.exe"))
    places += glob.glob(os.path.join(home, ".pyenv", "versions", "3.1[1-9]*", "bin", "python3"))
    for p in [sys.executable] + places:
        if p and os.path.exists(p) and "WindowsApps" not in p and py_ok(p): return p
    return None


py = find_python()
if py is None and install:
    if mac and shutil.which("brew"): sh(["brew", "install", "python@3.12"]); py = find_python()
    elif win and shutil.which("winget"): sh(["winget", "install", "-e", "--id", "Python.Python.3.12", "--accept-package-agreements", "--accept-source-agreements"]); py = find_python()
if py is None:
    print("Python : MISSING a 3.11+ interpreter (steelfig needs tomllib). Install Python 3.12 from https://www.python.org/downloads/ (or `brew install python@3.12`) and re-run.")
    py = sys.executable
else:
    open(os.path.join(path, ".python"), "w", encoding="utf-8").write(py + "\n"); print("Python :", py)


# ---------------------------------------------------------------- 3. Python packages
def has(mod):
    return subprocess.run([py, "-c", "import " + mod], capture_output=True).returncode == 0


need = [m for m, pkg in (("PIL", "pillow"), ("fitz", "pymupdf")) if not has(m)]
if need and install:
    pkgs = ["pillow" if m == "PIL" else "pymupdf" for m in need]
    if subprocess.run([py, "-m", "pip", "--version"], capture_output=True).returncode != 0: sh([py, "-m", "ensurepip", "--user"])
    r = sh([py, "-m", "pip", "install", "--user", "--quiet"] + pkgs, capture_output=True, text=True)
    if r.returncode != 0 and "externally-managed" in (r.stderr + r.stdout): r = sh([py, "-m", "pip", "install", "--user", "--quiet", "--break-system-packages"] + pkgs)
    if r.returncode != 0: print("pip failed:", (r.stderr or "")[-400:])


# ---------------------------------------------------------------- 4. LaTeX (optional)
def tex_bins():
    return [p for p in [shutil.which("pdflatex"), "/Library/TeX/texbin/pdflatex"] + glob.glob(os.path.join(home, "Library", "TinyTeX", "bin", "*", "pdflatex"))
            + glob.glob(os.path.join(home, ".TinyTeX", "bin", "*", "pdflatex")) + glob.glob(os.path.join(home, "AppData", "Roaming", "TinyTeX", "bin", "*", "pdflatex.exe"))
            + glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX", "miktex", "bin", "*", "pdflatex.exe")) + glob.glob(r"C:\Program Files\MiKTeX*\miktex\bin\*\pdflatex.exe") if p and os.path.exists(p)]


if not tex_bins() and install and "--no-tex" not in flags:
    if win:
        if shutil.which("winget"):
            sh(["winget", "install", "-e", "--id", "MiKTeX.MiKTeX", "--accept-package-agreements", "--accept-source-agreements"])
            tb = tex_bins()
            if tb:                                  # let MiKTeX fetch packages on its own, and fetch the ones tikz needs now
                d = os.path.dirname(tb[0])
                sh([os.path.join(d, "initexmf.exe"), "--set-config-value", "[MPM]AutoInstall=1"])
                sh([os.path.join(d, "miktex.exe"), "packages", "install", "pgf", "standalone", "lm", "xcolor", "amsmath", "graphics", "tools"])
            else: print("MiKTeX installed but pdflatex not found yet: open a new terminal and re-run the doctor")
        else: print("TeX: install MiKTeX from https://miktex.org/download (it fetches tikz on first use)")
    else:
        print("installing TinyTeX into your home folder (about 120 MB)")
        r = subprocess.run("sh -c \"$(curl -fsSL https://yihui.org/tinytex/install-bin-unix.sh)\"", shell=True)
        tl = glob.glob(os.path.join(home, "Library", "TinyTeX", "bin", "*", "tlmgr")) + glob.glob(os.path.join(home, ".TinyTeX", "bin", "*", "tlmgr"))
        if tl: sh([tl[0], "install", "standalone", "pgf", "lm", "xcolor", "amsmath", "graphics", "tools"])
        else: print("TinyTeX install did not finish:", r.returncode)


# ---------------------------------------------------------------- 5. Blender (optional, large)
def blender_bin():
    for p in (os.environ.get("BLENDER"), "/Applications/Blender.app/Contents/MacOS/Blender", shutil.which("blender"),
              r"C:\Program Files\Blender Foundation\Blender\blender.exe") + tuple(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe")):
        if p and os.path.exists(p): return p


if not blender_bin() and install and "--no-blender" not in flags:
    if mac and shutil.which("brew"): sh(["brew", "install", "--cask", "blender"])
    elif win and shutil.which("winget"): sh(["winget", "install", "-e", "--id", "BlenderFoundation.Blender", "--accept-package-agreements", "--accept-source-agreements"])
    elif shutil.which("snap"): sh(["sudo", "snap", "install", "blender", "--classic"])
    else: print("Blender: no package manager found; download it from https://www.blender.org/download/ (macOS: drag to /Applications)")

# ---------------------------------------------------------------- report
sys.stdout.flush(); subprocess.run([py, os.path.join(path, "steelfig", "cli.py"), "doctor"])
res = os.path.join(path, "resources"); n = sum(len(f) for _, _, f in os.walk(res))
print("resources:", res, "(%d file(s); drop catalogues, standard details, models and styles there)" % n)
if not install: print("missing items above can be installed with: python3 %s --install" % os.path.abspath(__file__))
