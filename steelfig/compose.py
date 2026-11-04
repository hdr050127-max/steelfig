"""Page composition for figures: decide the size and place of every view from the figure's layout, then put the
pieces (annotated TikZ pictures or plain images) into a tidy arrangement with consistent captions and a key.
Used by both the plain (geometry) preview and the annotated figure, so the two look the same on the page.

Layouts ("auto" picks by the number of views):
  stack  one view per row, centred                          (1 view, or tall views)
  row    views side by side at EQUAL HEIGHT, filling the width  (2-3 views)
  grid2  two columns, each row at equal height                 (4+ views)
Sizes: the figure width (default 15.6 cm = A4 text width with 25 mm margins); a view's own width_cm / height_cm
overrides the plan. Captions: "(a) …" is added automatically when there is more than one view and the caption
does not already start with "(". Key: 1 or 2 columns by its length and the figure width."""
import json, os, math

GAP = 0.4           # cm between views in a row
MAX_H = 9.5         # cm, tallest a row may be
CAP_H = 0.55        # cm reserved under a view for its caption


def aspects(sc, out_dir):
    out = {}
    for v in sc.get("view", []):
        jp = os.path.join(out_dir, v["name"] + ".json")
        if os.path.exists(jp):
            rx, ry = json.load(open(jp))["res"]; out[v["name"]] = rx / ry
    return out


def plan(sc, out_dir):
    """returns (layout, rows) where rows = [[(view, width_cm, height_cm), …], …]"""
    views = [v for v in sc.get("view", []) if os.path.exists(os.path.join(out_dir, v["name"] + ".png"))]
    F = sc.get("figure", {}); W = float(F.get("width_cm", 15.6)); layout = F.get("layout", "auto"); A = aspects(sc, out_dir)
    n = len(views)
    if layout == "auto":
        layout = "stack" if n <= 1 else ("row" if n <= 3 else "grid2")
    if layout == "row" and n > 3: layout = "grid2"
    per_row = {"stack": 1, "row": n or 1, "grid2": 2}[layout]
    rows = []
    for i in range(0, n, per_row):
        group = views[i:i + per_row]; m = len(group)
        if m == 1:
            v = group[0]; a = A.get(v["name"], 1.5)
            w = min(float(v.get("width_cm", W)), W)
            if "height_cm" in v: w = min(w, float(v["height_cm"]) * a)
            rows.append([(v, w, w / a)])
        else:
            avail = W - GAP * (m - 1); asum = sum(A.get(v["name"], 1.5) for v in group)
            h = min(avail / asum, MAX_H)
            rows.append([(v, h * A.get(v["name"], 1.5), h) for v in group])
    return layout, rows


def caption(i, n, text):
    if not text: return "(%s)" % "abcdefghij"[i] if n > 1 else ""
    return text if text.lstrip().startswith("(") or n <= 1 else "(%s) %s" % ("abcdefghij"[i], text)


def figure(rows, pieces, W, key=None, key_cols=None, title=None):
    """pieces: {view name: tikz or includegraphics string}; returns the LaTeX body of the whole figure."""
    n = sum(len(r) for r in rows); k = 0; out = []
    for r in rows:
        cells = []
        for v, w, h in r:
            cap = caption(k, n, v.get("caption", "")); k += 1
            cells.append(r"\begin{minipage}[t]{%.2fcm}\centering %s%s\end{minipage}" % (w, pieces[v["name"]],
                         (r"\\[0.8mm]{\small %s}" % cap) if cap else ""))
        out.append((r"\hfill".join(cells)) if len(cells) > 1 else r"\centerline{%s}" % cells[0])
    body = ("\n\n" + r"\vspace{3.5mm}" + "\n").join(out)
    if key:
        cols = key_cols or (2 if (len(key) >= 4 and W >= 11) else 1)
        from steelfig import overlay as O
        body += "\n\n" + r"\vspace{2.5mm}" + "\n" + O.keycols(key, W, cols)
    return r"\begin{minipage}{%.2fcm}\centering" % W + "\n" + body + "\n" + r"\end{minipage}"


def page(body, title, note=None, W=15.6):
    """an A4 page with the report's text width, the figure centred, a caption line below: what the person sees."""
    from steelfig import overlay as O
    cap = r"\vspace{3mm}{\small\textbf{Figure} %s%s}" % (title, (" \\textemdash\\ " + note) if note else "")
    return (r"\documentclass[11pt,a4paper]{article}" "\n" r"\usepackage[margin=25mm]{geometry}\usepackage{lmodern}\usepackage[T1]{fontenc}"
            r"\usepackage{tikz,graphicx,amsmath}\usetikzlibrary{arrows.meta}\pagestyle{empty}" "\n"
            r"\definecolor{acc}{rgb}{%s}" % O.ACC + "\n" + O.PRE + "\n" r"\begin{document}\begin{center}" "\n" + body + "\n\n" + cap + "\n"
            r"\end{center}\end{document}" "\n")
