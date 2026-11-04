"""Readers for analysis models, so any analysed structure can be drawn without retyping its geometry.
Microstran .arc and a plain CSV pair (<name>-nodes.csv + <name>-members.csv). Result: a Model with nodes
{id: (x, y, z)} in metres, z up (Microstran's vertical axis is mapped to z), members [{id, a, b, prop, name}],
props {id: name}. Sections are assigned by a mapping {prop name or member id: designation}."""
import csv, os


class Model:
    def __init__(self):
        self.nodes, self.members, self.props, self.restraints, self.title = {}, [], {}, {}, ""

    def member_line(self, m):
        return self.nodes[m["a"]], self.nodes[m["b"]]

    def section_of(self, m, mapping):
        """designation for a member: by member id, then by property name, then by property id, else None."""
        for k in (m["id"], str(m["id"]), self.props.get(m["prop"]), m["prop"], str(m["prop"])):
            if k in mapping: return mapping[k]
        return None

    def bbox(self):
        xs, ys, zs = zip(*self.nodes.values())
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def summary(self):
        (x0, y0, z0), (x1, y1, z1) = self.bbox()
        return "%s: %d nodes, %d members, %d properties; extent x %.3f..%.3f, y %.3f..%.3f, z %.3f..%.3f m\nprops: %s" % (
            self.title or "model", len(self.nodes), len(self.members), len(self.props), x0, x1, y0, y1, z0, z1,
            ", ".join("%s=%s" % kv for kv in self.props.items()))


def read_arc(path):
    """Microstran archive (.arc). VERT 2 means Y is vertical in the file: mapped to z up here (x, y, z) <- (x, z, y)."""
    M = Model(); vert = 2; unit = 1.0
    with open(path, errors="replace") as fh:
        lines = fh.read().splitlines()
    for i, l in enumerate(lines):
        t = l.split()
        if not t: continue
        if l.startswith("*") and not M.title: M.title = l[1:].strip()
        k = t[0]
        if k == "VERT": vert = int(t[1])
        elif k == "UNIT": unit = {"m": 1.0, "mm": 0.001, "cm": 0.01}.get(t[2], 1.0)
        elif k == "NODE":
            x, y, z = (float(v) * unit for v in t[2:5])
            M.nodes[int(t[1])] = (x, z, y) if vert == 2 else (x, y, z)
            if len(t) > 5: M.restraints[int(t[1])] = t[5]
        elif k == "MEMB":
            M.members.append(dict(id=int(t[1]), a=int(t[2]), b=int(t[3]), axis=t[4], prop=int(t[5]), matl=int(t[6]) if len(t) > 6 else 1,
                                  rel=t[7:9]))
        elif k == "PROP":
            M.props[int(t[1])] = " ".join(t[4:]).strip() if len(t) > 4 else str(t[1])
    return M


def read_csv(nodes_csv, members_csv):
    """nodes.csv: id,x,y,z (metres, z up); members.csv: id,a,b,section (section = designation or property name)."""
    M = Model()
    with open(nodes_csv, newline="") as fh:
        for r in csv.DictReader(fh):
            M.nodes[int(r["id"])] = (float(r["x"]), float(r.get("y", 0) or 0), float(r["z"]))
    with open(members_csv, newline="") as fh:
        for r in csv.DictReader(fh):
            M.members.append(dict(id=int(r["id"]), a=int(r["a"]), b=int(r["b"]), prop=r.get("section", ""), axis="", rel=[]))
            M.props.setdefault(r.get("section", ""), r.get("section", ""))
    return M


def read(path, members_csv=None):
    if path.lower().endswith(".arc"): return read_arc(path)
    if path.lower().endswith(".csv"): return read_csv(path, members_csv or path.replace("nodes", "members"))   # x-nodes.csv + x-members.csv
    raise ValueError("unknown model format: " + path)


if __name__ == "__main__":
    import sys
    print(read(sys.argv[1]).summary())
