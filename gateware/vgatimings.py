from amaranth import *

CHARWIDTH = 8
CHARHEIGHT = 16

class Timings:
    def __init__(self, pclk, *, hactive, vactive, hfront, hsync, hback, vfront, vsync, vback):
        self.hactive = hactive
        self.hfront = hfront
        self.hsync = hsync
        self.hback = hback

        self.vactive = vactive
        self.vfront = vfront
        self.vsync = vsync
        self.vback = vback

        self.pclk = pclk

        self.htotal = hactive + hfront + hsync + hback
        self.vtotal = vactive + vfront + vsync + vback
        self.hsync_start = hactive + hfront
        self.hsync_end = hactive + hfront + hsync
        self.vsync_start = vactive + vfront
        self.vsync_end = vactive + vfront + vsync
        self.cols = hactive // CHARWIDTH
        self.rows = vactive // CHARHEIGHT

    def hctr_shape(self):
        return Shape.cast(range(-self.hback, self.hsync_end))

    def vctr_shape(self):
        return Shape.cast(range(-self.vback, self.vsync_end))

TIMINGS={
    "640x480": Timings(
        pclk = 25.175,
        hactive = 640,
        hfront = 16,
        hsync = 96,
        hback = 48,
        vactive = 480,
        vfront = 10,
        vsync = 2,
        vback = 33),
    "800x480": Timings(
        pclk = 33.33,
        hactive = 800,
        hfront = 210,
        hsync = 40,
        hback = 46,
        vactive = 480,
        vfront = 22,
        vsync = 1,
        vback = 23),
    "800x480_RB": Timings(
        hactive = 800,
        hfront = 40,
        hsync = 10,
        hback = 46,
        vactive = 480,
        vfront = 10,
        vsync = 2,
        vback = 23,
        pclk = 27.686)
}

