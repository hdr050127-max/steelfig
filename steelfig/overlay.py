"""overlay: vector annotation (TikZ) on top of a bfig render, placed from the 3D anchors in the render JSON.
Nothing is written on the picture itself: parts get a numbered balloon beside them and a key below; the
engineering content (dimension lines, centrelines, buckled shapes, load arrows, tributary areas, grid names)
is drawn as lines because that is what the figure exists to show.

    import overlay as O
    P = O.Pic("images/blender/knee.jpg", "renders/knee.json", 14.0)        # path as the report sees it, JSON, width cm
    tik, key = O.balloon(P, [("col", "610UB113 column", 1.2, -0.4), ...],  # (anchor, text, dx_cm, dy_cm[, number])
                         [("dim3", "le", r"$L_e = 2400$", "above"), ("line", ["wave"], O.WAVE)])
    body = tik + r"\\\\[1mm]" + O.keylist(key, 14.0)
    O.emit("figures/fig_knee.tex", body); O.preview(body, "/tmp/prev", "knee")   # fragment for the report + check PDF

Anchor keys: "name" (a point), "name#i" (point i of a list anchor), "mid:a,b" (midpoint of two anchors).
draw items:
  ("line", [keys], tikz_style)                  polyline through the anchors (each may be a list)
  ("fill", [keys], tikz_style)                  closed area (tributary strip, section)
  ("arrow", keyA, keyB, style[, text, anchor[, "b"]])  arrow A -> B, text at A (or B with "b")
  ("dim", keyA, keyB, text, offset_cm, side)    2D dimension in image space (orthographic views only)
  ("dim3", name, text, side)                    3D dimension recorded with bfig.dim3(anch, name, p, q, off)
  ("angle", centre, dir1, dir2, r_cm, text)     angle arc between two directions (orthographic views)
  ("text", key, text, anchor[, dx, dy])         a word at an anchor, white backing (section marks "A", grid names)
  ("grid", key, label)                          boxed grid name at the end of a grid line
  ("letter", key, "a", dx, dy)                  boxed letter with a leader (sub-figure references)
  ("detail", key, r_cm, label, dx, dy)          detail circle with a lettered bubble (sub-figure reference)
  ("cutline", keyA, keyB, "A", side)            section line A-A with viewing arrows (orthographic views)
  ("support", key, "pin"|"roller"|"fixed", cm)  support symbol under a node (orthographic views)
  ("raw", tikz)                                 anything else
Every dim / dim3 text is checked against the model distance stored in the render JSON (anchors3d); a mismatch
prints a WARNING (set overlay.STRICT = True to make it an error). A 2D "dim" on a perspective render warns too.
The report preamble needs: \\usepackage{tikz,graphicx,amsmath} \\usetikzlibrary{arrows.meta}
\\definecolor{acc}{rgb}{0.62,0.16,0.10} and the \\ball macro (PRE below)."""
import json, math, os, re, subprocess, shutil, sys

STRICT = False          # True: a dimension whose text disagrees with the model raises instead of warning
_warn = []


def warn(msg):
    _warn.append(msg); print("overlay WARNING:", msg, file=sys.stderr)
    if STRICT: raise ValueError(msg)

FONT = r"\footnotesize"
PRE = (r"\newcommand\ball[1]{\tikz[baseline=(c.base)]\node[circle, draw, line width=0.4pt, inner sep=0pt, minimum size=3.3mm,"
       r" font=\sffamily\tiny](c){#1};}")
ACC = "0.62,0.16,0.10"
# ready-made line styles
WAVE = "line width=0.8pt, densely dashed, acc"                                   # buckled shape
CL = "line width=0.35pt, dash pattern=on 6pt off 1.5pt on 1pt off 1.5pt"       # centreline
FARROW = r"line width=0.9pt, -{Stealth[length=2.2mm]}"                          # force arrow
QARROW = r"line width=0.4pt, -{Stealth[length=1.3mm]}, black!75"                 # distributed-load arrow
GRIDL = CL


class Pic:
    def __init__(self, png, json_path, width_cm):
        J = json.load(open(json_path)); rx, ry = J["res"]
        self.png, self.A, self.W = png, J["anchors"], width_cm; self.H = width_cm * ry / rx
        self.A3 = J.get("anchors3d", {}); self.ortho = J.get("ortho", False)

    def p3(self, key):
        """3D point (metres) of an anchor, when the render stored it."""
        if "#" in key:
            k, i = key.split("#"); return self.A3[k][int(i)]
        if key.startswith("mid:"):
            a, b = (self.p3(k) for k in key[4:].split(",")); return [(a[i] + b[i]) / 2 for i in range(3)]
        return self.A3.get(key)

    def check_dim(self, text, pa, pb):
        """compare the first number in a dimension text with the model distance (mm or m); warn on > 0.5 %."""
        if pa is None or pb is None: return
        L = math.dist(pa, pb)
        m = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", "").replace(r"\,", ""))
        if not m: return
        v = float(m.group(1)); ok = abs(v - L * 1000) <= max(1.0, 0.005 * L * 1000) or abs(v - L) <= max(0.0005, 0.005 * L)
        if not ok: warn("dimension %r: text says %s but the model measures %.1f mm" % (text, m.group(1), L * 1000))

    def pts(self, key):
        if key.startswith("mid:"):
            a, b = key[4:].split(","); p, q = self.pts(a)[0], self.pts(b)[0]
            return [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)]
        i = None
        if "#" in key: key, i = key.split("#"); i = int(i)
        a = self.A[key]
        P = [(u * self.W, v * self.H) for u, v in a] if a and isinstance(a[0], list) else [(a[0] * self.W, a[1] * self.H)]
        return [P[i]] if i is not None else P


def pic_by_height(png, json_path, height_cm, max_width_cm):
    rx, ry = json.load(open(json_path))["res"]
    return Pic(png, json_path, min(max_width_cm, height_cm * rx / ry))


c = lambda p: "(%.3f,%.3f)" % p


def _draw(pic, items):
    o = []
    for it in items:
        t = it[0]
        if t == "line":
            pts = sum((pic.pts(k) for k in it[1]), [])
            o.append(r"\draw[%s] %s;" % (it[2], " -- ".join(c(p) for p in pts)))
        elif t == "fill":
            pts = sum((pic.pts(k) for k in it[1]), [])
            o.append(r"\fill[%s] %s -- cycle;" % (it[2], " -- ".join(c(p) for p in pts)))
        elif t == "arrow":
            a, b = pic.pts(it[1])[0], pic.pts(it[2])[0]
            o.append(r"\draw[%s] %s -- %s;" % (it[3], c(a), c(b)))
            if len(it) > 4: o.append(r"\node[anchor=%s, inner sep=1.5pt] at %s {%s};" % (it[5], c(b if len(it) > 6 and it[6] == "b" else a), it[4]))
        elif t == "dim":
            _, ka, kb, text, off, side = it; a, b = pic.pts(ka)[0], pic.pts(kb)[0]
            if not pic.ortho: warn("2D dimension %r drawn on a perspective view; use dim3 or an orthographic view" % text)
            pic.check_dim(text, pic.p3(ka), pic.p3(kb))
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
            a2 = (a[0] + off * nx, a[1] + off * ny); b2 = (b[0] + off * nx, b[1] + off * ny); e = 0.1 * (1 if off >= 0 else -1)
            o.append(r"\draw[line width=0.25pt] %s -- (%.3f,%.3f) %s -- (%.3f,%.3f);" % (c(a), a2[0] + e * nx, a2[1] + e * ny, c(b), b2[0] + e * nx, b2[1] + e * ny))
            o.append(r"\draw[line width=0.3pt, {Stealth[length=1.3mm]}-{Stealth[length=1.3mm]}] %s -- %s node[midway, %s, inner sep=1.5pt] {%s};" % (c(a2), c(b2), side, text))
        elif t == "dim3":
            _, nm, text, side = it
            a, b, a2, b2 = (pic.pts(nm + s_)[0] for s_ in ("_a", "_b", "_a2", "_b2"))
            pic.check_dim(text, pic.p3(nm + "_a"), pic.p3(nm + "_b"))
            def ext(p, q):
                dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1
                return (q[0] + 0.12 * dx / L, q[1] + 0.12 * dy / L), (p[0] + 0.06 * dx / L, p[1] + 0.06 * dy / L)
            (ea, sa), (eb, sb) = ext(a, a2), ext(b, b2)
            o.append(r"\draw[line width=0.25pt, gray!70!black] %s -- %s %s -- %s;" % (c(sa), c(ea), c(sb), c(eb)))
            o.append(r"\draw[line width=0.35pt, {Stealth[length=1.4mm]}-{Stealth[length=1.4mm]}] %s -- %s node[midway, sloped, %s, inner sep=1.5pt, fill=white, fill opacity=0.85, text opacity=1] {%s};" % (c(a2), c(b2), side, text))
        elif t == "angle":
            _, kc, k1, k2, r, text = it; p0 = pic.pts(kc)[0]; p1 = pic.pts(k1)[0]; p2 = pic.pts(k2)[0]
            a1 = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])); a2 = math.degrees(math.atan2(p2[1] - p0[1], p2[0] - p0[0]))
            if a2 < a1: a1, a2 = a2, a1
            o.append(r"\draw[line width=0.3pt] (%.3f,%.3f) arc[start angle=%.2f, end angle=%.2f, radius=%.3f];" % (p0[0] + r * math.cos(math.radians(a1)), p0[1] + r * math.sin(math.radians(a1)), a1, a2, r))
            am = math.radians((a1 + a2) / 2)
            o.append(r"\node[inner sep=1pt] at (%.3f,%.3f) {%s};" % (p0[0] + (r + 0.28) * math.cos(am), p0[1] + (r + 0.28) * math.sin(am), text))
        elif t == "text":
            p = pic.pts(it[1])[0]; dx, dy = (it[4], it[5]) if len(it) > 4 else (0, 0)
            o.append(r"\node[anchor=%s, inner sep=1.2pt, fill=white, fill opacity=0.85, text opacity=1, align=left] at (%.3f,%.3f) {%s};" % (it[3], p[0] + dx, p[1] + dy, it[2]))
        elif t == "grid":
            p = pic.pts(it[1])[0]
            o.append(r"\node[draw, line width=0.4pt, fill=white, rounded corners=1.5pt, inner sep=1.5pt] at %s {%s};" % (c(p), it[2]))
        elif t == "letter":
            _, k, txt, dx, dy = it; p = pic.pts(k)[0]; q = (p[0] + dx, p[1] + dy)
            o.append(r"\draw[line width=0.35pt, -{Stealth[length=1.5mm, width=1.1mm]}] %s -- %s;" % (c(q), c(p)))
            o.append(r"\node[draw, line width=0.5pt, fill=white, rounded corners=1pt, inner sep=1.4pt, font=\sffamily\scriptsize\bfseries] at %s {%s};" % (c(q), txt))
        elif t == "detail":                                  # ("detail", key, r_cm, label, dx, dy)
            _, k, r, label, dx, dy = it; p = pic.pts(k)[0]
            o.append(r"\draw[line width=0.5pt] %s circle (%.3f);" % (c(p), r))
            q = (p[0] + dx, p[1] + dy); ang = math.atan2(dy, dx)
            o.append(r"\draw[line width=0.35pt] (%.3f,%.3f) -- %s;" % (p[0] + r * math.cos(ang), p[1] + r * math.sin(ang), c(q)))
            o.append(r"\node[draw, circle, line width=0.5pt, fill=white, inner sep=1.2pt, font=\sffamily\scriptsize\bfseries] at %s {%s};" % (c(q), label))
        elif t == "cutline":                                 # ("cutline", keyA, keyB, label, side): section line A-A
            _, ka, kb, label, side = it; a, b = pic.pts(ka)[0], pic.pts(kb)[0]
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
            sg = 1 if side == "left" else -1
            o.append(r"\draw[line width=0.6pt, dash pattern=on 8pt off 2pt on 2pt off 2pt] %s -- %s;" % (c(a), c(b)))
            for p in (a, b):
                o.append(r"\draw[line width=0.6pt, -{Stealth[length=2mm]}] %s -- (%.3f,%.3f);" % (c(p), p[0] + sg * 0.45 * nx, p[1] + sg * 0.45 * ny))
                o.append(r"\node[font=\sffamily\footnotesize\bfseries, inner sep=1pt] at (%.3f,%.3f) {%s};" % (p[0] + sg * 0.75 * nx, p[1] + sg * 0.75 * ny, label))
        elif t == "support":                                 # ("support", key, "pin"|"roller"|"fixed", size_cm)
            _, k, kind, sz = it; p = pic.pts(k)[0]; x, y = p
            if kind == "fixed":
                o.append(r"\draw[line width=0.6pt] (%.3f,%.3f) -- (%.3f,%.3f);" % (x - sz, y, x + sz, y))
                o.append(r"\foreach \i in {0,...,5} \draw[line width=0.3pt] (%.3f+\i*%.3f,%.3f) -- (%.3f+\i*%.3f,%.3f);" % (x - sz, sz / 2.5, y, x - sz - sz / 3, sz / 2.5, y - sz / 3))
            else:
                o.append(r"\draw[line width=0.5pt] (%.3f,%.3f) -- (%.3f,%.3f) -- (%.3f,%.3f) -- cycle;" % (x, y, x - sz * 0.6, y - sz, x + sz * 0.6, y - sz))
                if kind == "roller":
                    o.append(r"\draw[line width=0.5pt] (%.3f,%.3f) circle (%.3f) (%.3f,%.3f) circle (%.3f);" % (x - sz * 0.3, y - sz * 1.3, sz * 0.25, x + sz * 0.3, y - sz * 1.3, sz * 0.25))
                    o.append(r"\draw[line width=0.6pt] (%.3f,%.3f) -- (%.3f,%.3f);" % (x - sz, y - sz * 1.6, x + sz, y - sz * 1.6))
                else:
                    o.append(r"\draw[line width=0.6pt] (%.3f,%.3f) -- (%.3f,%.3f);" % (x - sz, y - sz, x + sz, y - sz))
        elif t == "raw":
            o.append(it[1])
    return o


def _spread(ys, heights, top, bottom):
    n = len(ys); y = list(ys)
    for _ in range(200):
        for i in range(n):
            y[i] = min(y[i], top - heights[i] / 2); y[i] = max(y[i], bottom + heights[i] / 2)
        moved = False
        for i in range(n - 1):
            need = (heights[i] + heights[i + 1]) / 2 + 0.18
            if y[i] - y[i + 1] < need:
                d = (need - (y[i] - y[i + 1])) / 2; y[i] += d; y[i + 1] -= d; moved = True
        if not moved: break
    return y


def _head(pic, font):
    return [r"\begin{tikzpicture}[font=%s]" % font,
            r"\node[anchor=south west, inner sep=0] at (0,0) {\includegraphics[width=%.3fcm]{%s}};" % (pic.W, pic.png)]


def rail(pic, labels, draw=(), gap=0.35, font=FONT, line_h=0.42):
    """text labels in aligned columns left / right of the picture with straight leaders (few labels only).
    labels: (key, text[, "L"/"R"])."""
    o = _head(pic, font) + _draw(pic, draw)
    for side in "LR":
        L = []
        for lab in labels:
            k, text = lab[0], lab[1]; p = pic.pts(k)[0]
            s = lab[2] if len(lab) > 2 else ("L" if p[0] < pic.W / 2 else "R")
            if s == side: L.append((p, text))
        if not L: continue
        L.sort(key=lambda r: -r[0][1])
        hs = [line_h * (t.count(r"\\") + 1) for _, t in L]
        ys = _spread([p[1] for p, _ in L], hs, pic.H, 0)
        xt = -gap if side == "L" else pic.W + gap
        for (p, text), y in zip(L, ys):
            anc = "east" if side == "L" else "west"
            o.append(r"\fill %s circle (0.75pt);" % c(p))
            o.append(r"\draw[line width=0.3pt] %s -- (%.3f,%.3f) -- (%.3f,%.3f);" % (c(p), xt + (0.25 if side == "L" else -0.25), y, xt, y))
            o.append(r"\node[anchor=%s, align=%s, inner sep=1pt] at (%.3f,%.3f) {%s};" % (anc, "right" if side == "L" else "left", xt, y, text))
    o.append(r"\end{tikzpicture}")
    return "\n".join(o)


def balloon(pic, labels, draw=(), start=1, font=FONT):
    """numbered balloons: labels = (anchor, text, dx_cm, dy_cm[, number]). The balloon sits at anchor + (dx, dy)
    with an arrow back to the anchor. A label with text "" and an explicit number repeats an earlier balloon
    (the same part seen twice) and adds nothing to the key. Returns (tikz, key_lines)."""
    o = _head(pic, font) + _draw(pic, draw)
    key = []; n = start - 1
    for lab in labels:
        k, text, dx, dy = lab[:4]
        if len(lab) > 4: num = lab[4]
        else: n += 1; num = n
        p = pic.pts(k)[0]; q = (p[0] + dx, p[1] + dy)
        o.append(r"\draw[line width=0.35pt, -{Stealth[length=1.5mm, width=1.1mm]}] %s -- %s;" % (c(q), c(p)))
        o.append(r"\node[circle, draw, line width=0.4pt, fill=white, inner sep=0pt, minimum size=3.3mm, font=\sffamily\tiny] at %s {%d};" % (c(q), num))
        if text: key.append(r"\ball{%d}\ %s" % (num, text))
    o.append(r"\end{tikzpicture}")
    return "\n".join(o), key


def keylist(items, width_cm):
    """the key under / beside a figure: one hanging-indent line per item."""
    return (r"\begin{minipage}[c]{%.2fcm}%s\raggedright\setlength{\parskip}{2pt}" % (width_cm, FONT)
            + "\n".join(r"\hangindent=4.5mm\hangafter=1 " + s + r"\par" for s in items) + r"\end{minipage}")


def keycols(items, total_width_cm, cols=2, gap_cm=0.4):
    """the key split into columns (long keys under a wide figure)."""
    w = (total_width_cm - gap_cm * (cols - 1)) / cols; n = len(items); per = -(-n // cols)
    return (r"\hspace{%.2fcm}" % gap_cm).join(keylist(items[i * per:(i + 1) * per], w) for i in range(cols) if items[i * per:(i + 1) * per])


swatch = lambda style: r"\tikz[baseline=-0.6ex]\fill[%s] (0,-0.12) rectangle (0.5,0.12);" % style      # key entry for a fill
dash = lambda style: r"\tikz[baseline=-0.6ex]\draw[%s] (0,0) -- (0.6,0);" % style                      # key entry for a line style


def row(parts, gap_cm=0.3, align="b"):
    """put figure pieces side by side (each a tikz string or minipage); align b = bottoms level."""
    return (r"\hspace{%.2fcm}" % gap_cm).join(r"\begin{tabular}[%s]{@{}c@{}}%s\end{tabular}" % (align, p) for p in parts)


def captioned(part, text, width_cm):
    return r"\begin{minipage}[c]{%.2fcm}\centering %s\\[0.5mm]{\footnotesize %s}\end{minipage}" % (width_cm, part, text)


def warnings():
    return list(_warn)


def standalone(body, width_cm=16.0):
    return (r"\documentclass[border=3pt]{standalone}" "\n" r"\usepackage{lmodern}\usepackage[T1]{fontenc}\usepackage{tikz,graphicx,amsmath}"
            r"\usetikzlibrary{arrows.meta}" "\n" r"\definecolor{acc}{rgb}{%s}" % ACC + "\n" + PRE + "\n" r"\begin{document}" "\n"
            r"\begin{minipage}{%.1fcm}" % width_cm + body + r"\end{minipage}" "\n" r"\end{document}" "\n")


def flatten(png, jpg, quality=92):
    """transparent render -> white-backed JPEG for the report (much smaller than the PNG)."""
    from PIL import Image
    im = Image.open(png).convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
    os.makedirs(os.path.dirname(jpg) or ".", exist_ok=True); bg.convert("RGB").save(jpg, quality=quality)
    return jpg


def emit(path, body, generator=None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    head = "%% generated by %s; do not edit\n" % (generator or "overlay.py")
    open(path, "w").write(head + body + "\n")


def pdflatex():
    for p in (shutil.which("pdflatex"), os.path.expanduser("~/Library/TinyTeX/bin/universal-darwin/pdflatex"), "/Library/TeX/texbin/pdflatex"):
        if p and os.path.exists(p): return p
    raise FileNotFoundError("pdflatex not found (TinyTeX ~/Library/TinyTeX/bin/universal-darwin)")


def preview(body, out_dir, name, cwd=None, width_cm=16.0):
    """compile the figure body alone to <out_dir>/prev_<name>.pdf (image paths resolve from cwd) for checking."""
    os.makedirs(out_dir, exist_ok=True)
    tex = os.path.join(out_dir, "prev_%s.tex" % name); open(tex, "w").write(standalone(body, width_cm))
    r = subprocess.run([pdflatex(), "-interaction=nonstopmode", "-halt-on-error", "-output-directory", out_dir, tex],
                       cwd=cwd or os.getcwd(), capture_output=True, text=True)
    pdf = os.path.join(out_dir, "prev_%s.pdf" % name)
    if r.returncode or not os.path.exists(pdf):
        raise RuntimeError("pdflatex failed:\n" + r.stdout[-3000:])
    return pdf
