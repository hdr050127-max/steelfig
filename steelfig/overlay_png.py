"""Annotation without LaTeX: draws the same balloons, leaders, dimension lines, waves, fills and key straight
onto the picture with Pillow and writes a PNG. Used when pdflatex is missing (Windows laptops, a tutor's
machine) or with `--png-only`. Math in texts is reduced to plain characters ($L_e = 2400$ -> Le = 2400)."""
import os, math, re
from PIL import Image, ImageDraw, ImageFont

ACC = (201, 85, 63)


def _font(size):
    for f in ("DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf", "C:/Windows/Fonts/arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()


def plain_text(t):
    t = re.sub(r"\\ball\{(\d+)\}", r"(\1)", t)
    t = t.replace(r"\times", "x").replace(r"\,", " ").replace(r"\\", " ").replace("$", "").replace(r"\textemdash", "-")
    t = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", t); t = re.sub(r"\\[a-zA-Z]+", "", t)
    t = t.replace("_e", "e").replace("^\\circ", "°").replace("{", "").replace("}", "").replace("--", "-")
    return t.strip()


def render(pic, labels, draw_items, key, out_png, dpi=300):
    """pic: overlay.Pic (its .file is the flattened image; W, H in cm); labels as given to overlay.balloon
    (with dx, dy filled); draw_items as in overlay; key: list of key lines (LaTeX allowed). Writes out_png."""
    im = Image.open(pic.file).convert("RGB"); px = im.width / pic.W          # pixels per cm
    scale = px / (dpi / 2.54)                                               # so that line widths match 300 dpi print
    f_small = _font(max(10, int(8 * px / 28.35 * 2.5)))                     # ~8 pt on the figure
    f_ball = _font(max(9, int(6.5 * px / 28.35 * 2.5)))
    d = ImageDraw.Draw(im, "RGBA")
    P = lambda p: (p[0] * px, (pic.H - p[1]) * px)
    lw = max(1, int(0.35 / 2.54 * dpi / 72 * scale * 2))

    def arrow(a, b, width=lw, colour=(0, 0, 0), head=6):
        d.line([P(a), P(b)], fill=colour, width=width)
        ax, ay = P(a); bx, by = P(b); ang = math.atan2(by - ay, bx - ax); h = head * scale * 3
        d.polygon([(bx, by), (bx - h * math.cos(ang - 0.4), by - h * math.sin(ang - 0.4)), (bx - h * math.cos(ang + 0.4), by - h * math.sin(ang + 0.4))], fill=colour)

    for it in draw_items:
        t = it[0]
        if t in ("line", "fill"):
            pts = sum((pic.pts(k) for k in it[1]), [])
            dashed = "dashed" in it[2]; col = ACC if "acc" in it[2] else (0, 0, 0)
            if t == "fill":
                m = re.search(r"opacity=([0-9.]+)", it[2]); al = int(255 * float(m.group(1))) if m else 60
                d.polygon([P(p) for p in pts], fill=col + (al,))
            else:
                for a, b in zip(pts, pts[1:]):
                    if dashed:
                        L = math.dist(a, b); n = max(1, int(L / 0.18))
                        for i in range(0, n, 2):
                            q0 = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n); q1 = (a[0] + (b[0] - a[0]) * min(n, i + 1) / n, a[1] + (b[1] - a[1]) * min(n, i + 1) / n)
                            d.line([P(q0), P(q1)], fill=col, width=lw * 2)
                    else: d.line([P(a), P(b)], fill=col, width=lw)
        elif t == "arrow":
            a, b = pic.pts(it[1])[0], pic.pts(it[2])[0]; arrow(a, b, lw * 2, ACC if "acc" in it[3] else (0, 0, 0))
            if len(it) > 4: d.text(P(b if len(it) > 6 and it[6] == "b" else a), plain_text(it[4]), fill=(0, 0, 0), font=f_small, anchor="mm")
        elif t in ("dim", "dim3"):
            if t == "dim3":
                nm, text = it[1], it[2]
                if nm + "_a2" not in pic.A and nm + "_c0_a2" in pic.A:
                    from steelfig import overlay as O; O.pick_dim(pic, nm)
                a, b, a2, b2 = (pic.pts(nm + s_)[0] for s_ in ("_a", "_b", "_a2", "_b2"))
            else:
                _, ka, kb, text, off, side = it; a, b = pic.pts(ka)[0], pic.pts(kb)[0]
                dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nx, ny = -dy / L, dx / L
                a2, b2 = (a[0] + off * nx, a[1] + off * ny), (b[0] + off * nx, b[1] + off * ny)
            d.line([P(a), P(a2)], fill=(90, 90, 90), width=lw); d.line([P(b), P(b2)], fill=(90, 90, 90), width=lw)
            arrow(a2, b2, lw, head=4); arrow(b2, a2, lw, head=4)
            mx, my = P(((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2)); txt = plain_text(text)
            tw = d.textlength(txt, font=f_small); d.rectangle([mx - tw / 2 - 3, my - 10 * scale * 2, mx + tw / 2 + 3, my + 10 * scale * 2], fill=(255, 255, 255, 220))
            d.text((mx, my), txt, fill=(0, 0, 0), font=f_small, anchor="mm")
        elif t == "text":
            p = pic.pts(it[1])[0]; d.text(P(p), plain_text(it[2]), fill=(0, 0, 0), font=f_small, anchor="mm")
        elif t == "grid":
            x, y = P(pic.pts(it[1])[0]); r = 9 * scale * 2
            d.rectangle([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=(0, 0, 0), width=lw); d.text((x, y), it[2], fill=(0, 0, 0), font=f_small, anchor="mm")
    n = 0; r = 0.165 * px
    for lab in labels:
        k, text, dx, dy = lab[:4]
        if len(lab) > 4: num = lab[4]
        else: n += 1; num = n
        a = pic.pts(k)[0]; b = (a[0] + dx, a[1] + dy)
        arrow(b, a, lw, head=4)
        x, y = P(b); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255), outline=(0, 0, 0), width=lw)
        d.text((x, y), str(num), fill=(0, 0, 0), font=f_ball, anchor="mm")
    # key below the picture
    lines = [plain_text(k) for k in key]
    if lines:
        lh = int(f_small.size * 1.5); pad = int(0.3 * px); cols = 2 if len(lines) >= 4 and pic.W >= 11 else 1
        per = -(-len(lines) // cols); hk = per * lh + 2 * pad
        out = Image.new("RGB", (im.width, im.height + hk), (255, 255, 255)); out.paste(im, (0, 0)); d2 = ImageDraw.Draw(out)
        for i, t in enumerate(lines):
            c, rI = divmod(i, per); d2.text((pad + c * im.width / cols, im.height + pad + rI * lh), t, fill=(0, 0, 0), font=f_small)
        im = out
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True); im.save(out_png)
    return out_png
