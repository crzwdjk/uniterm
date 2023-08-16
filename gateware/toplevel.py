from amaranth import *
import icepll, vgasync

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

        m.submodules.vgasync = vgs = vgasync.VGASync(self.timings)

        output = platform.request("vga")
        m.d.comb += [
            output.hs.eq(vgs.hs),
            output.vs.eq(vgs.vs),
            output.r.eq(Mux(vgs.active, 23, 0)),
            output.g.eq(Mux(vgs.active, 20, 0)),
            output.b.eq(Mux(vgs.active, 31, 0)),
        ]

        # Not all platforms need the pclk/den outputs, so it's okay if the
        # request fails.
        try:
            pclk = platform.request("pclk")
            m.d.comb += pclk.eq(ClockSignal("sync"))
            den = platform.request("den")
            m.d.comb += den.eq(vgs.active)
        except:
            pass

        return m
