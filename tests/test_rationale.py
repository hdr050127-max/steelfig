import os, sys, unittest, tempfile, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rationale", os.path.join(HERE, "..", "blender", "rationale.py"))
RA = importlib.util.module_from_spec(spec); spec.loader.exec_module(RA)


class Rationale(unittest.TestCase):
    def test_notes_checks_and_file(self):
        RA.reset()
        RA.note("fb", "angle 50x50x5", "by depth", "assume")
        self.assertTrue(RA.check(True, "fb", "ok", "edge")); self.assertFalse(RA.check(False, "fb bolt", "too close", "edge"))
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "r.md"); text = RA.dump(p, "t")
            self.assertIn("ASSUMPTION", text); self.assertIn("AS 4100:2020 Table 9.5.2", text); self.assertIn("too close", text)
            self.assertTrue(os.path.exists(p))


if __name__ == "__main__":
    unittest.main()
