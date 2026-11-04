import os, sys, json, unittest, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from steelfig import overlay as O, layout as LY


def pic_with_block(tmp):
    """40x20 cm picture (400x200 px) with a solid block of 'steel' in the middle of the ID image."""
    from PIL import Image
    Image.new("RGB", (400, 200), (200, 200, 200)).save(os.path.join(tmp, "v.jpg"))
    idm = Image.new("RGBA", (400, 200), (0, 0, 0, 0))
    for x in range(150, 250):
        for y in range(50, 150): idm.putpixel((x, y), (51, 0, 0, 255))
    idm.save(os.path.join(tmp, "v_id.png"))
    J = dict(res=[400, 200], anchors={"a": [0.5, 0.5], "b": [0.55, 0.5], "edge": [0.05, 0.5]}, anchors3d={}, ortho=False, ids={"block": [51, 0, 0]})
    json.dump(J, open(os.path.join(tmp, "v.json"), "w"))
    return O.Pic("v.jpg", os.path.join(tmp, "v.json"), 40.0, file=os.path.join(tmp, "v.jpg"))


class Layout(unittest.TestCase):
    def test_occupancy(self):
        with tempfile.TemporaryDirectory() as tmp:
            P = pic_with_block(tmp); occ = LY.Occupancy(P)
            self.assertEqual(occ.covered(20, 10), 1)      # centre of the block (cm)
            self.assertEqual(occ.covered(2, 10), 0)
            self.assertGreater(occ.disc(20, 10, 0.5), 0.9); self.assertEqual(occ.disc(2, 10, 0.5), 0)

    def test_auto_placement_avoids_steel(self):
        with tempfile.TemporaryDirectory() as tmp:
            P = pic_with_block(tmp); occ = LY.Occupancy(P)
            labels = LY.place_balloons(P, [("a", "one", None, None), ("b", "two", None, None)], occ)
            for (k, text, dx, dy) in labels:
                ax, ay = P.pts(k)[0]
                self.assertLess(occ.disc(ax + dx, ay + dy, LY.R_BALL), 0.2, "balloon placed on the block")
            self.assertEqual(LY.check(P, [l + (i + 1,) for i, l in enumerate(labels)], occ=occ), [])

    def test_check_finds_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            P = pic_with_block(tmp); occ = LY.Occupancy(P)
            f = LY.check(P, [("a", "x", 0.0, 0.0, 1), ("edge", "y", -3.0, 0.0, 2)], key=[r"\ball{1}\ x"], occ=occ)
            self.assertTrue(any("sits on a member" in m for m in f))
            self.assertTrue(any("outside the picture" in m for m in f))
            self.assertTrue(any("no key line" in m for m in f))


if __name__ == "__main__":
    unittest.main()
