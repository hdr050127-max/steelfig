#!/usr/bin/env python3
"""Make sure the steelfig repository is present and current, say where it is, and (on request) install what is
missing. Safe to run every time; works with any Python 3.8+ and no third-party modules. Command line only:
nothing here needs a browser or an installer window.
    python3 setup.py              -> get/update steelfig, print STEELFIG_HOME=<path> and the doctor report
    python3 setup.py --install    -> also install what the doctor reports missing (see below)
    python3 setup.py --install --no-tex --no-blender   -> only the Python side
    python3 setup.py --dry-run    -> with --install: say what would be installed from where, change nothing
(Windows: run it with `python` or `py -3`.)
Location: $STEELFIG_HOME if set, else an existing ~/steelfig or ~/Developer/steelfig, else a fresh copy at ~/steelfig
(git clone, or a zip download from GitHub when git is missing or fails). Updates a clone with a fast-forward pull.
--install does, in this order, only for things that are missing:
  Python         3.9+ is enough (3.11+ preferred). Looks in the usual places, records the choice in <path>/.python;
                 below 3.11 it adds the `tomli` package. Nothing found: Homebrew / winget install 3.12 when present.
  Pillow, PyMuPDF   pip install --user (about 25 MB): JPEG flattening, PNG annotation without LaTeX, PDF -> PNG.
  TeX            TinyTeX in the user's home (about 120 MB; macOS, Linux and Windows) with the tikz packages, or MiKTeX
                 through winget. Optional: without it the annotated figures are PNGs instead of LaTeX fragments.
  Blender        Homebrew cask / winget / snap when that manager exists; otherwise the official build from
                 download.blender.org (about 350 MB): macOS DMG copied to /Applications (or ~/Applications),
                 Windows zip and Linux tarball unpacked under the user's profile. The path is recorded in <path>/.blender.
Nothing needs administrator rights except a package manager's own installer."""
import os, sys, subprocess, shutil, platform, glob, io, re, zipfile, tarfile, tempfile, urllib.request

REPO = "https://github.com/hdr050127-max/steelfig"
ZIP = REPO + "/archive/refs/heads/main.zip"
BLENDER_RELEASES = "https://download.blender.org/release/"
home = os.path.expanduser("~"); mac, win = sys.platform == "darwin", os.name == "nt"
flags = set(sys.argv[1:]); install = "--install" in flags; dry = "--dry-run" in flags
candidates = [os.environ.get("STEELFIG_HOME"), os.path.join(home, "steelfig"), os.path.join(home, "Developer", "steelfig")]
path = next((p for p in candidates if p and os.path.isdir(os.path.join(p, "steelfig"))), None)
git = shutil.which("git")


def say(*a): print(*a, flush=True)


def sh(cmd, **kw):
    say("$", " ".join(cmd))
    if dry: return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, **kw)


def fetch(url, to=None):
    """download url; returns bytes, or the file path when `to` is given (progress on stderr)."""
    say("downloading", url)
    if dry: return b"" if to is None else to
    req = urllib.request.Request(url, headers={"User-Agent": "steelfig-setup"})
    with urllib.request.urlopen(req, timeout=120) as r:
        total = int(r.headers.get("Content-Length") or 0); got = 0; last = -1; buf = io.BytesIO() if to is None else open(to, "wb")
        while True:
            chunk = r.read(1 << 20)
            if not chunk: break
            buf.write(chunk); got += len(chunk)
            if total:
                pct = got * 10 // total
                if pct != last: last = pct; sys.stderr.write("  %d%%\r" % (pct * 10)); sys.stderr.flush()
    if to is None: return buf.getvalue()
    buf.close(); return to


# ---------------------------------------------------------------- 1. the repository
if path is None:
    path = candidates[0] or os.path.join(home, "steelfig")
    cloned = False
    if git:
        say("cloning steelfig to", path); cloned = sh([git, "clone", "--depth", "1", REPO, path]).returncode == 0
        if not cloned: shutil.rmtree(path, ignore_errors=True); say("git clone failed (no command line tools?); falling back to a zip download")
    if not cloned:
        data = fetch(ZIP)
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
        say("unpacked (no git: delete the folder and re-run setup.py to update)")
elif git and os.path.isdir(os.path.join(path, ".git")):
    r = subprocess.run([git, "-C", path, "pull", "--ff-only", "--quiet"], capture_output=True, text=True)
    say("updated" if r.returncode == 0 else "not updated (local changes or offline): " + r.stderr.strip()[:200])
say("STEELFIG_HOME=" + path)
for d in ("catalogues", "details", "models", "styles", "local"): os.makedirs(os.path.join(path, "resources", d), exist_ok=True)


# ---------------------------------------------------------------- 2. a Python that can run steelfig (3.9+, 3.11+ preferred)
def py_ver(exe):
    try:
        r = subprocess.run([exe, "-c", "import sys; print(sys.version_info[0] * 100 + sys.version_info[1])"], capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip()) if r.returncode == 0 else 0
    except Exception: return 0


def find_python():
    names = ["python3.13", "python3.12", "python3.11", "python3", "python", "python3.10", "python3.9"]
    places = [shutil.which(n) for n in names]
    places += glob.glob("/opt/homebrew/bin/python3.1[1-9]") + glob.glob("/usr/local/bin/python3.1[1-9]")
    places += glob.glob("/Library/Frameworks/Python.framework/Versions/3.1[1-9]/bin/python3")
    places += glob.glob(os.path.join(home, "AppData", "Local", "Programs", "Python", "Python31[1-9]*", "python.exe"))
    places += glob.glob(os.path.join(home, ".pyenv", "versions", "3.1[1-9]*", "bin", "python3"))
    places += ["/usr/bin/python3"]
    best, bv = None, 0
    for p in [sys.executable] + places:
        if not p or not os.path.exists(p) or "WindowsApps" in p: continue
        v = py_ver(p)
        if v >= 311: return p, v
        if v >= 309 and v > bv: best, bv = p, v
    return best, bv


py, pv = find_python()
if py is None and install:
    if mac and shutil.which("brew"): sh(["brew", "install", "python@3.12"]); py, pv = find_python()
    elif win and shutil.which("winget"): sh(["winget", "install", "-e", "--id", "Python.Python.3.12", "--accept-package-agreements", "--accept-source-agreements"]); py, pv = find_python()
if py is None:
    say("Python : MISSING (3.9+ needed). macOS: `xcode-select --install` gives python3 3.9; or install 3.12 from https://www.python.org/downloads/ ; Windows: `winget install Python.Python.3.12`. Then re-run.")
    py, pv = sys.executable, 0
else:
    if not dry: open(os.path.join(path, ".python"), "w", encoding="utf-8").write(py + "\n")
    say("Python :", py, "(%d.%d)" % (pv // 100, pv % 100))


# ---------------------------------------------------------------- 3. Python packages
def has(mod):
    return subprocess.run([py, "-c", "import " + mod], capture_output=True).returncode == 0


wanted = [("PIL", "pillow"), ("fitz", "pymupdf")] + ([("tomli", "tomli")] if 0 < pv < 311 else [])
need = [pkg for mod, pkg in wanted if not has(mod)]
if need and install:
    if subprocess.run([py, "-m", "pip", "--version"], capture_output=True).returncode != 0: sh([py, "-m", "ensurepip", "--user"])
    r = sh([py, "-m", "pip", "install", "--user", "--quiet"] + need, capture_output=True, text=True)
    if r.returncode != 0 and "externally-managed" in (r.stderr + r.stdout): r = sh([py, "-m", "pip", "install", "--user", "--quiet", "--break-system-packages"] + need)
    if r.returncode != 0: say("pip failed:", (r.stderr or "")[-400:])
elif need: say("Python packages missing for %s: %s" % (py, " ".join(need)))


# ---------------------------------------------------------------- 4. TeX (optional)
def tex_bins():
    pats = [os.path.join(home, "Library", "TinyTeX", "bin", "*", "pdflatex"), os.path.join(home, ".TinyTeX", "bin", "*", "pdflatex"),
            os.path.join(home, "AppData", "Roaming", "TinyTeX", "bin", "*", "pdflatex.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX", "miktex", "bin", "*", "pdflatex.exe"), r"C:\Program Files\MiKTeX*\miktex\bin\*\pdflatex.exe"]
    found = [shutil.which("pdflatex"), "/Library/TeX/texbin/pdflatex"] + sum((glob.glob(p) for p in pats), [])
    return [p for p in found if p and os.path.exists(p)]


TEX_PKGS = ["standalone", "pgf", "lm", "xcolor", "amsmath", "graphics", "tools"]
if not tex_bins() and install and "--no-tex" not in flags:
    if win and shutil.which("winget"):
        sh(["winget", "install", "-e", "--id", "MiKTeX.MiKTeX", "--accept-package-agreements", "--accept-source-agreements"])
        tb = tex_bins()
        if tb:
            d = os.path.dirname(tb[0])
            sh([os.path.join(d, "initexmf.exe"), "--set-config-value", "[MPM]AutoInstall=1"])
            sh([os.path.join(d, "miktex.exe"), "packages", "install"] + TEX_PKGS)
        else: say("MiKTeX installed but pdflatex not found yet: open a new terminal and re-run the doctor")
    elif win:
        say("installing TinyTeX into %APPDATA% (about 120 MB)")
        bat = os.path.join(tempfile.gettempdir(), "install-bin-windows.bat"); fetch("https://yihui.org/tinytex/install-bin-windows.bat", bat)
        sh(["cmd", "/c", bat])
        tl = glob.glob(os.path.join(home, "AppData", "Roaming", "TinyTeX", "bin", "*", "tlmgr.bat"))
        if tl: sh([tl[0], "install"] + TEX_PKGS)
    else:
        say("installing TinyTeX into your home folder (about 120 MB)")
        script = os.path.join(tempfile.gettempdir(), "install-bin-unix.sh"); fetch("https://yihui.org/tinytex/install-bin-unix.sh", script)
        r = sh(["sh", script])
        tl = glob.glob(os.path.join(home, "Library", "TinyTeX", "bin", "*", "tlmgr")) + glob.glob(os.path.join(home, ".TinyTeX", "bin", "*", "tlmgr"))
        if tl: sh([tl[0], "install"] + TEX_PKGS)
        elif not dry: say("TinyTeX install did not finish:", r.returncode)


# ---------------------------------------------------------------- 5. Blender (optional to install here, required to draw)
def blender_bin():
    rec = os.path.join(path, ".blender")
    rec = open(rec, encoding="utf-8").read().strip() if os.path.exists(rec) else None
    ps = [os.environ.get("BLENDER"), rec, "/Applications/Blender.app/Contents/MacOS/Blender", os.path.join(home, "Applications", "Blender.app", "Contents", "MacOS", "Blender"),
          shutil.which("blender"), r"C:\Program Files\Blender Foundation\Blender\blender.exe"]
    ps += sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"), reverse=True)
    ps += sorted(glob.glob(os.path.join(home, "AppData", "Local", "Programs", "blender*", "blender.exe")), reverse=True)
    ps += sorted(glob.glob(os.path.join(home, ".local", "opt", "blender*", "blender")), reverse=True)
    for p in ps:
        if p and os.path.exists(p): return p


def blender_url():
    """newest official build for this machine from download.blender.org (no package manager needed)."""
    idx = fetch(BLENDER_RELEASES).decode("utf-8", "replace") if not dry else ""
    dirs = sorted({(int(a), int(b)) for a, b in re.findall(r'href="Blender(\d+)\.(\d+)/"', idx)}) or [(4, 5)]
    arch = platform.machine().lower()
    if mac: tag = "macos-" + ("arm64" if arch in ("arm64", "aarch64") else "x64"); ext = "dmg"
    elif win: tag = "windows-" + ("arm64" if "arm" in arch else "x64"); ext = "zip"
    else: tag = "linux-x64"; ext = "tar.xz"
    for a, b in reversed(dirs):                                   # newest series that has a build for us
        d = "%sBlender%d.%d/" % (BLENDER_RELEASES, a, b)
        lst = fetch(d).decode("utf-8", "replace") if not dry else ""
        vers = sorted({tuple(int(x) for x in v.split(".")) for v in re.findall(r'href="blender-(\d+\.\d+\.\d+)-%s\.%s"' % (tag, ext.replace(".", r"\.")), lst)})
        if vers or dry:
            v = ".".join(map(str, vers[-1])) if vers else "%d.%d.0" % (a, b)
            return d + "blender-%s-%s.%s" % (v, tag, ext), v
    raise SystemExit("no Blender build found for %s at %s" % (tag, BLENDER_RELEASES))


def install_blender_official():
    url, v = blender_url(); say("Blender %s official build (about 350 MB)" % v)
    f = fetch(url, os.path.join(tempfile.gettempdir(), os.path.basename(url)))
    if dry: return
    if mac:
        mnt = tempfile.mkdtemp(prefix="blender-dmg-")
        subprocess.run(["hdiutil", "attach", "-nobrowse", "-quiet", "-mountpoint", mnt, f], check=True)
        try:
            dest_dir = "/Applications" if os.access("/Applications", os.W_OK) else os.path.join(home, "Applications")
            os.makedirs(dest_dir, exist_ok=True); dest = os.path.join(dest_dir, "Blender.app")
            if os.path.exists(dest): shutil.rmtree(dest)
            subprocess.run(["cp", "-R", os.path.join(mnt, "Blender.app"), dest], check=True)
        finally: subprocess.run(["hdiutil", "detach", "-quiet", mnt])
        exe = os.path.join(dest, "Contents", "MacOS", "Blender")
    elif win:
        dest_dir = os.path.join(home, "AppData", "Local", "Programs"); os.makedirs(dest_dir, exist_ok=True)
        with zipfile.ZipFile(f) as z: top = z.namelist()[0].split("/")[0]; z.extractall(dest_dir)
        exe = os.path.join(dest_dir, top, "blender.exe")
    else:
        dest_dir = os.path.join(home, ".local", "opt"); os.makedirs(dest_dir, exist_ok=True)
        with tarfile.open(f) as t: top = t.getnames()[0].split("/")[0]; t.extractall(dest_dir)
        exe = os.path.join(dest_dir, top, "blender")
    os.remove(f)
    open(os.path.join(path, ".blender"), "w", encoding="utf-8").write(exe + "\n"); say("Blender :", exe)


if "--blender-url" in flags: say(blender_url()[0]); sys.exit(0)
if not blender_bin() and install and "--no-blender" not in flags:
    if mac and shutil.which("brew"): sh(["brew", "install", "--cask", "blender"])
    elif win and shutil.which("winget"): sh(["winget", "install", "-e", "--id", "BlenderFoundation.Blender", "--accept-package-agreements", "--accept-source-agreements"])
    elif not mac and not win and shutil.which("snap"): sh(["sudo", "snap", "install", "blender", "--classic"])
    else: install_blender_official()
    b = blender_bin()
    if b and not dry: open(os.path.join(path, ".blender"), "w", encoding="utf-8").write(b + "\n")
elif blender_bin() and not dry: open(os.path.join(path, ".blender"), "w", encoding="utf-8").write(blender_bin() + "\n")

# ---------------------------------------------------------------- report
sys.stdout.flush(); subprocess.run([py, os.path.join(path, "steelfig", "cli.py"), "doctor"])
res = os.path.join(path, "resources"); n = sum(len(f) for _, _, f in os.walk(res))
say("resources:", res, "(%d file(s); drop catalogues, standard details, models and styles there)" % n)
if not install: say("missing items above can be installed with: %s %s --install" % (os.path.basename(sys.executable), os.path.abspath(__file__)))
