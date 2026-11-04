"""Annotation layout and layout checks, working on the picture in cm and the ID render as an occupancy mask.
  Occupancy(pic)                mask of pixels covered by any object (from <view>_id.png), queried in cm
  place_balloons(pic, labels)   choose (dx, dy) for labels that have none: off the members, apart from each other,
                                short leaders that do not cross, inside the figure box (a little outside is fine)
  check(pic, balloons, draws)   findings: balloon over a member, leaders crossing, anchor outside the picture,
                                key / balloon number mismatch, dimension line over a member
Costs are in cm so they do not depend on the render resolution."""
import math, os

R_BALL = 0.17          # balloon radius, cm (3.3 mm diameter + line)


class Occupancy:
    """where the steel is on the picture: every object of the ID render except the ones the render lists as
    background (concrete, grout, sheeting), which annotation may run across."""
    def __init__(self, pic):
        from PIL import Image, ImageChops
        self.W, self.H = pic.W, pic.H
        try:
            im = Image.open(pic.idpng).convert("RGBA")
            bg = set(getattr(pic, "background", []) or [])
            if bg and pic.ids:
                rgb = im.convert("RGB"); mask = Image.new("L", im.size, 0)
                for name, (r, g, b) in pic.ids.items():
                    if name in bg: continue
                    d = ImageChops.difference(rgb, Image.new("RGB", im.size, (r, g, b))).convert("L").point(lambda v: 255 if v < 3 else 0)
                    mask = ImageChops.lighter(mask, d)
                self.im = mask
            else:
                self.im = im.split()[3].point(lambda a: 255 if a > 0 else 0).convert("L")
            self.px = self.im.load(); self.w, self.h = self.im.size; self.ok = True
        except Exception:
            self.ok = False

    def covered(self, x, y):
        """1 if a member is under (x, y) cm (y up), 0 if empty or outside."""
        if not self.ok: return 0
        i = int(x / self.W * self.w); j = int((1 - y / self.H) * self.h)
        if 0 <= i < self.w and 0 <= j < self.h: return 1 if self.px[i, j] else 0
        return 0

    def disc(self, x, y, r, n=24):
        """fraction of a disc of radius r (cm) that lies over members."""
        hits = 0; tot = 0
        for k in range(n):
            a = 2 * math.pi * k / n
            for f in (0.45, 0.9):
                tot += 1; hits += self.covered(x + r * f * math.cos(a), y + r * f * math.sin(a))
        return hits / tot

    def segment(self, a, b, step=0.08):
        """fraction of a segment (cm) running over members."""
        L = math.dist(a, b); n = max(2, int(L / step)); hits = 0
        for k in range(n + 1):
            t = k / n; hits += self.covered(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        return hits / (n + 1)


def _cross(a, b, c, d):
    """do segments ab and cd cross (strictly)?"""
    def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and min(abs(o1), abs(o2), abs(o3), abs(o4)) > 1e-9


def place_balloons(pic, labels, occ=None, margin=0.45, radii=(0.9, 1.3, 1.8, 2.4, 3.2, 4.5, 6.0), n_dir=16, fixed=()):
    """labels: list of (anchor_key, text, dx, dy[, num]) where dx / dy may be None -> chosen here.
    fixed: extra (x, y) points to stay clear of (e.g. dimension texts). Returns the labels with dx, dy filled."""
    occ = occ or Occupancy(pic)
    placed = []                       # (ax, ay, bx, by) of balloons already placed (anchor, balloon)
    out = []
    cx, cy = pic.W / 2, pic.H / 2
    # labels with explicit positions first, so automatic ones avoid them
    order = sorted(range(len(labels)), key=lambda i: 0 if labels[i][2] is not None else 1)
    res = [None] * len(labels)
    for i in order:
        lab = labels[i]; k, text = lab[0], lab[1]; ax, ay = pic.pts(k)[0]
        if lab[2] is not None and lab[3] is not None:
            bx, by = ax + lab[2], ay + lab[3]; placed.append((ax, ay, bx, by)); res[i] = tuple(lab); continue
        best = None
        away = math.atan2(ay - cy, ax - cx)          # prefer outward from the picture centre
        for r in radii:
            for d in range(n_dir):
                a = 2 * math.pi * d / n_dir; bx, by = ax + r * math.cos(a), ay + r * math.sin(a)
                cost = 0.0
                cost += 6.0 * occ.disc(bx, by, R_BALL * 1.3)                              # balloon over steel
                cost += 1.5 * occ.segment((ax, ay), (bx, by))                             # leader over steel
                cost += 0.55 * r                                                          # short leaders (the look depends on it)
                cost += 0.6 * (1 - math.cos(a - away))                                    # outward
                ox = max(0, -margin - bx, bx - pic.W - margin); oy = max(0, -margin - by, by - pic.H - margin)
                cost += 8.0 * (ox + oy)                                                   # outside the box
                for (pax, pay, pbx, pby) in placed:
                    dd = math.dist((bx, by), (pbx, pby))
                    if dd < 2.6 * R_BALL: cost += 6.0
                    elif dd < 0.8: cost += 1.5 * (0.8 - dd)
                    if _cross((ax, ay), (bx, by), (pax, pay), (pbx, pby)): cost += 15.0      # crossing leaders are never acceptable
                    if math.dist((bx, by), (pax, pay)) < 0.4: cost += 2.0
                for (fx, fy) in fixed:
                    if math.dist((bx, by), (fx, fy)) < 0.7: cost += 3.0
                if best is None or cost < best[0]: best = (cost, bx, by)
        _, bx, by = best; placed.append((ax, ay, bx, by))
        res[i] = (k, text, round(bx - ax, 2), round(by - ay, 2)) + tuple(lab[4:])
    # second pass: each automatic balloon is re-chosen against the final positions of all the others
    auto_idx = [i for i in range(len(labels)) if labels[i][2] is None or labels[i][3] is None]
    for i in auto_idx:
        k = res[i][0]; ax, ay = pic.pts(k)[0]
        others = [(pic.pts(res[j][0])[0][0], pic.pts(res[j][0])[0][1], pic.pts(res[j][0])[0][0] + res[j][2], pic.pts(res[j][0])[0][1] + res[j][3]) for j in range(len(res)) if j != i]
        best = None
        for r in radii:
            for d in range(n_dir):
                a = 2 * math.pi * d / n_dir; bx, by = ax + r * math.cos(a), ay + r * math.sin(a)
                cost = 6.0 * occ.disc(bx, by, R_BALL * 1.3) + 1.5 * occ.segment((ax, ay), (bx, by)) + 0.55 * r + 0.6 * (1 - math.cos(a - away))
                ox = max(0, -margin - bx, bx - pic.W - margin); oy = max(0, -margin - by, by - pic.H - margin); cost += 8.0 * (ox + oy)
                for (pax, pay, pbx, pby) in others:
                    dd = math.dist((bx, by), (pbx, pby))
                    if dd < 2.6 * R_BALL: cost += 6.0
                    elif dd < 0.8: cost += 1.5 * (0.8 - dd)
                    if _cross((ax, ay), (bx, by), (pax, pay), (pbx, pby)): cost += 15.0
                    if math.dist((bx, by), (pax, pay)) < 0.4: cost += 2.0
                for (fx, fy) in fixed:
                    if math.dist((bx, by), (fx, fy)) < 0.7: cost += 3.0
                if best is None or cost < best[0]: best = (cost, bx, by)
        _, bx, by = best
        res[i] = (k, res[i][1], round(bx - ax, 2), round(by - ay, 2)) + tuple(res[i][4:])
    return res


def check(pic, labels, draws=(), key=None, occ=None):
    """findings (strings) about an annotated picture; empty when all is well."""
    occ = occ or Occupancy(pic); out = []; leaders = []
    nums = []
    n = 0
    for lab in labels:
        k, text, dx, dy = lab[:4]
        if len(lab) > 4: num = lab[4]
        else: n += 1; num = n
        ax, ay = pic.pts(k)[0]; bx, by = ax + dx, ay + dy
        if not (-0.6 <= bx <= pic.W + 0.6 and -0.6 <= by <= pic.H + 0.6): out.append("balloon %d (%s) is outside the picture by more than 6 mm" % (num, k))
        if not (0 <= ax <= pic.W and 0 <= ay <= pic.H): out.append("anchor %r of balloon %d is outside the picture (widen the crop with `bounds`)" % (k, num))
        cov = occ.disc(bx, by, R_BALL)
        if cov > 0.35: out.append("balloon %d (%s) sits on a member (%.0f%% covered)" % (num, k, cov * 100))
        for (m, a, b) in leaders:
            if _cross((ax, ay), (bx, by), a, b): out.append("leaders of balloons %d and %d cross" % (num, m))
        for (m, a, b) in leaders:
            if math.dist((bx, by), b) < 2 * R_BALL: out.append("balloons %d and %d overlap" % (num, m))
        leaders.append((num, (ax, ay), (bx, by)))
        if text: nums.append(num)
    if key is not None:
        import re
        in_key = [int(x) for x in re.findall(r"\\ball\{(\d+)\}", "\n".join(key))]
        for m in nums:
            if m not in in_key: out.append("balloon %d has no key line" % m)
    for d in draws:
        if d[0] == "dim3":
            try:
                a2, b2 = pic.pts(d[1] + "_a2")[0], pic.pts(d[1] + "_b2")[0]
                if occ.segment(a2, b2) > 0.85: out.append("dimension %r runs over a member for almost its whole length; move its offset" % d[2])
            except KeyError: pass
    return out
