import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from steelfig import sections as S, readers, style


class Sections(unittest.TestCase):
    def test_lookup_forms(self):
        for q in ("310UB46.2", "310ub46.2", "310 UB 46.2", "200x200x9.0 SHS", "200X200X9SHS", "100x100x8EA", "100x100x8 EA"):
            S.find(q)

    def test_dims(self):
        r = S.find("310UB46.2"); self.assertEqual((r["d"], r["bf"], r["tf"], r["tw"]), (307.2, 166, 11.8, 6.7))
        r = S.find("200x200x9SHS"); self.assertEqual((r["grade"], r["t"]), ("C450", 9))
        self.assertEqual(S.find("150x150x9SHS/C350")["grade"], "C350")

    def test_profiles_closed(self):
        for d in ("310UB46.2", "250PFC", "100x100x8 EA", "200x200x9SHS", "219.1x6.4CHS", "Z20019", "C15015"):
            P = S.profile(d)
            pts = P.get("pts") or P["outer"]
            self.assertGreaterEqual(len(pts), 4)
            self.assertAlmostEqual(max(u for u, v in pts) - min(u for u, v in pts), P["d"], places=6)

    def test_unknown(self):
        with self.assertRaises(KeyError): S.find("310UB47")

    def test_bolt(self):
        self.assertAlmostEqual(S.bolt("M20")["hole"], 0.022)


class Readers(unittest.TestCase):
    def test_arc_mapping(self):
        import tempfile
        src = "VERS 5\nTYPE 3\nVERT 2\nUNIT 1 m kN T C\nNODE 1 0.0 0.0 0.0 110000\nNODE 2 3.0 4.0 0.0 000000\nMEMB 1 1 2 X 1 1 000000 000000\nPROP 1 PRIS Nominal 310UB46.2\n"
        with tempfile.NamedTemporaryFile("w", suffix=".arc", delete=False) as f: f.write(src)
        M = readers.read(f.name)
        self.assertEqual(M.nodes[2], (3.0, 0.0, 4.0))          # Microstran Y up -> z up
        self.assertEqual(M.props[1], "310UB46.2")
        self.assertEqual(M.section_of(M.members[0], {"310UB46.2": "310UB46.2"}), "310UB46.2")


class Style(unittest.TestCase):
    def test_default(self):
        st = style.load(); self.assertIn("accent", st["colours"]); self.assertEqual(len(style.rgba(st["colours"]["accent"])), 4)


if __name__ == "__main__":
    unittest.main()


class LineGeometry(unittest.TestCase):
    """the lift rule assembly.Line must follow (it needs mathutils, so the rule is re-stated here in pure Python):
    a line lifted by `lift` along its normal is, at the same horizontal x, lift / cos(slope) higher and NOT
    shifted in x. The 2026-11-04 end-plate clash came from shifting x by -lift*sin(slope)."""
    def test_lift_rule(self):
        import math
        x0, z0, x1, z1, lift = 0.0, 10.5102, 6.278, 10.795, 0.2665
        slope = math.atan2(z1 - z0, x1 - x0); x = 3.0
        z_axis = z0 + (z1 - z0) * (x - x0) / (x1 - x0)
        lifted = (x, z_axis + lift / math.cos(slope))
        # perpendicular distance from the lifted point back to the axis line must equal lift
        nx, nz = -math.sin(slope), math.cos(slope)
        dist = (lifted[0] - x) * nx + (lifted[1] - z_axis) * nz
        self.assertAlmostEqual(dist, lift, places=9)
        self.assertEqual(lifted[0], x)
