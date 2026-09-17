import model as m

class Vm:
    def __init__(self):
        self.r, self.g, self.b = 255, 0, 0
        self.warn = False
        self.sync_from_rgb()

    def sync_from_rgb(self):
        self.c, self.mm, self.y, self.k, _ = m.rgb_to_cmyk(self.r, self.g, self.b)
        self.h, self.l, self.s, _ = m.rgb_to_hls(self.r, self.g, self.b)

    def set_rgb(self, r, g, b):
        self.r, self.g, self.b, self.warn = m.rgb_clip(r, g, b)
        self.sync_from_rgb()

    def set_cmyk(self, c, mm, y, k):
        self.r, self.g, self.b, self.warn = m.cmyk_to_rgb(c, mm, y, k)
        self.sync_from_rgb()

    def set_hls(self, h, l, s):
        self.r, self.g, self.b, self.warn = m.hls_to_rgb(h, l, s)
        self.sync_from_rgb()

    def report(self):
        return {
            "rgb": (self.r, self.g, self.b),
            "cmyk": (self.c, self.mm, self.y, self.k),
            "hls": (self.h, self.l, self.s),
            "warn": self.warn,
        }
