import os, sys, json, unittest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from steelfig import overlay as O


def make_pic(tmp):
    """a 40x20 'render' with two fake objects in the ID image and matching anchors."""
    from PIL import Image
    im = Image.new("RGB", (40, 20), (200, 200, 200)); im.save(os.path.join(tmp, "v.jpg"))
    idm = Image.new("RGBA", (40, 20), (0, 0, 0, 0))
    for x in range(5, 15):
        for y in range(5, 15): idm.putpixel((x, y), (51, 0, 0, 255))
    for x in range(25, 35):
        for y in range(5, 15): idm.putpixel((x, y), (102, 0, 0, 255))
    idm.save(os.path.join(tmp, "v_id.png"))
    J = dict(res=[40, 20], anchors={"a": [0.25, 0.5], "b": [0.75, 0.5], "poly": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9]]},
             anchors3d={"a": [0, 0, 0], "b": [2.4, 0, 0]}, ortho=True, ids={"beam": [51, 0, 0], "col_11.3": [102, 0, 0]})
    json.dump(J, open(os.path.join(tmp, "v.json"), "w"))
    return O.Pic("v.jpg", os.path.join(tmp, "v.json"), 10.0, file=os.path.join(tmp, "v.jpg"))


class Overlay(unittest.TestCase):
    def test_balloon_and_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            P = make_pic(tmp)
            tik, key = O.balloon(P, [("a", "a beam", 0.5, 0.5), ("b", "", 0.5, 0.5, 1)], [("fill", ["poly"], "acc, opacity=0.2")])
            self.assertIn(r"\includegraphics[width=10.000cm]{v.jpg}", tik)
            self.assertEqual(len(key), 1)
            self.assertIn(r"\fill[acc, opacity=0.2]", tik)

    def test_dim_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            P = make_pic(tmp); n = len(O.warnings())
            O._draw(P, [("dim", "a", "b", "2400", 0.5, "above")]); self.assertEqual(len(O.warnings()), n)
            O._draw(P, [("dim", "a", "b", "2500", 0.5, "above")]); self.assertEqual(len(O.warnings()), n + 1)

    def test_highlight(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            P = make_pic(tmp)
            self.assertEqual(P.objects(["col"]), ["col_11.3"])        # prefix matches the frame copy
            P.highlight(["beam"], colour="#ff0000", alpha=1.0, outline=0, dim=0.0)
            im = Image.open(P.file).convert("RGB")
            near = lambda p, q: all(abs(a - b) <= 8 for a, b in zip(p, q))   # JPEG tolerance
            self.assertTrue(near(im.getpixel((10, 10)), (255, 0, 0)), im.getpixel((10, 10)))      # inside the beam: tinted
            self.assertTrue(near(im.getpixel((30, 10)), (200, 200, 200)), im.getpixel((30, 10)))  # the other object: untouched
            self.assertTrue(P.png.endswith("v_hl.jpg"))


if __name__ == "__main__":
    unittest.main()
