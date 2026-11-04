#!/usr/bin/env python3
"""Write the example analysis model (an original single-span portal frame) as nodes.csv + members.csv:
24 m span, 6.0 m eaves, 5 deg pitch, 410UB53.7 columns, 460UB67.1 haunches 2.6 m long, 360UB44.7 rafters.
    python3 tools/make_example_model.py resources/models/portal-24m
writes <prefix>-nodes.csv and <prefix>-members.csv (the CSV reader finds the members file from the nodes file)."""
import csv, math, sys, os
pre = sys.argv[1] if len(sys.argv) > 1 else "resources/models/portal-24m"
L, H, pitch, hl = 24.0, 6.0, math.radians(5.0), 2.6
z = lambda x: H + (x if x <= L / 2 else L - x) * math.tan(pitch)
nodes = {1: (0, 0, 0), 2: (L, 0, 0), 11: (0, 0, H), 12: (hl, 0, z(hl)), 13: (L / 2, 0, z(L / 2)), 14: (L - hl, 0, z(L - hl)), 15: (L, 0, H)}
members = [(1, 1, 11, "410UB53.7"), (2, 2, 15, "410UB53.7"), (101, 11, 12, "460UB67.1"), (102, 12, 13, "360UB44.7"),
           (103, 13, 14, "360UB44.7"), (104, 14, 15, "460UB67.1")]
os.makedirs(os.path.dirname(pre) or ".", exist_ok=True)
with open(pre + "-nodes.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "x", "y", "z"]); [w.writerow([i, "%.4f" % x, "%.4f" % y, "%.4f" % zz]) for i, (x, y, zz) in nodes.items()]
with open(pre + "-members.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "a", "b", "section"]); w.writerows(members)
print("wrote", pre + "-nodes.csv", pre + "-members.csv")
