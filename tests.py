import unittest
import model as m

class Test(unittest.TestCase):
    def close(self, a, b, eps=1e-2):
        self.assertTrue(abs(a - b) < eps, f"{a} != {b}")

    def test_rgb_red_to_cmyk(self):
        c, mm, y, k, w = m.rgb_to_cmyk(255, 0, 0)
        self.close(c, 0); self.close(mm, 1); self.close(y, 1); self.close(k, 0)
        self.assertFalse(w)

    def test_rgb_red_to_hls(self):
        h, l, s, w = m.rgb_to_hls(255, 0, 0)
        self.close(h, 0); self.close(l, 0.5); self.close(s, 1)
        self.assertFalse(w)

    def test_cmyk_black_to_rgb(self):
        r, g, b, w = m.cmyk_to_rgb(0, 0, 0, 1)
        self.assertEqual((r, g, b), (0, 0, 0))
        self.assertFalse(w)

    def test_hls_white_to_rgb(self):
        r, g, b, w = m.hls_to_rgb(0, 1, 0)
        self.assertEqual((r, g, b), (255, 255, 255))
        self.assertFalse(w)

    def test_round_trip_rgb_cmyk_rgb(self):
        for rgb in [(10, 200, 77), (0, 0, 0), (255, 255, 255), (123, 45, 200)]:
            c, mm, y, k, _ = m.rgb_to_cmyk(*rgb)
            r2, g2, b2, w = m.cmyk_to_rgb(c, mm, y, k)
            self.assertFalse(w)
            self.close(r2, rgb[0], 1); self.close(g2, rgb[1], 1); self.close(b2, rgb[2], 1)

    def test_round_trip_rgb_hls_rgb(self):
        for rgb in [(10, 200, 77), (0, 0, 0), (255, 255, 255), (123, 45, 200)]:
            h, l, s, _ = m.rgb_to_hls(*rgb)
            r2, g2, b2, w = m.hls_to_rgb(h, l, s)
            self.assertFalse(w)
            self.close(r2, rgb[0], 1); self.close(g2, rgb[1], 1); self.close(b2, rgb[2], 1)

    def test_out_of_range_warns(self):
        r, g, b, w = m.cmyk_to_rgb(0, 0, 0, 1.5)
        self.assertTrue(w)
        h, l, s, w2 = m.hls_to_rgb(400, 0.5, 0.5)
        self.assertTrue(w2)

if __name__ == "__main__":
    unittest.main()
