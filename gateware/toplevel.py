from amaranth import *
import icepll
from vgasync import *
from cursor import *

class Toplevel(Elaboratable):
    """ The top level of the terminal, everything goes under here. """
    def __init__(self, pdata, timings):
        self.timings = timings
        self.pdata = pdata

    def elaborate(self, platform):
        m = Module()

        f_in = platform.lookup(self.pdata.clkresource).clock.frequency
        m.submodules.pll = icepll.ICEPLL(f_in, self.timings.pclk * 1e6,
                                      self.pdata.clkresource)

        m.submodules.vgasync = vgs = VGASync(self.timings)

        m.submodules.cursor = cursor = Cursor(self.timings)
        bgcolor = [23, 20, 31]
        fgcolor = [31, 31, 31]
        color = [Mux(cursor.output, c[0], c[1]) for c in zip(fgcolor, bgcolor)]
        m.d.comb += cursor.controls.shape.eq(CursorShape.UNDERLINE)
        m.d.comb += cursor.hctr.eq(vgs.hctr)
        m.d.comb += cursor.vctr.eq(vgs.vctr)

        output = platform.request("vga")
        m.d.comb += [
            output.hs.eq(vgs.hs),
            output.vs.eq(vgs.vs),
            output.r.eq(Mux(vgs.active, color[0], 0)),
            output.g.eq(Mux(vgs.active, color[1], 0)),
            output.b.eq(Mux(vgs.active, color[2], 0)),
        ]

        # Not all platforms need the pclk/den outputs, so it's okay if the request fails.
        try:
            pclk = platform.request("pclk")
            m.d.comb += pclk.eq(ClockSignal("sync"))
            den = platform.request("den")
            m.d.comb += den.eq(vgs.active)
        except:
            pass

        return m
