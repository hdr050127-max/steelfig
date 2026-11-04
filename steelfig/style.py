"""Style sheets: one TOML per course / report, read by both the Blender side (materials, line weight) and the
overlay (accent colour, fonts). steelfig/styles/default.toml is the CIVL3206 style agreed 2026-10-09."""
import os, tomllib

STYLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")


def load(name_or_path=None):
    p = name_or_path or os.environ.get("STEELFIG_STYLE") or "default"
    if not os.path.exists(p):
        res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "styles", p + ".toml")
        p = res if os.path.exists(res) else os.path.join(STYLES, p + ".toml")
    with open(p, "rb") as fh: return tomllib.load(fh)


def rgba(hexs):
    h = hexs.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4       # sRGB -> linear for Blender
    return (lin(r), lin(g), lin(b), 1.0)


def tikz_rgb(hexs):
    h = hexs.lstrip("#"); return ",".join("%.3f" % (int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
