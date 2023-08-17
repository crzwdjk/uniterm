from amaranth import *
from amaranth.lib.wiring import *
import icepll, videoout

# XXX: test only
from rowbuftest import *

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

        m.submodules.videoout = out = videoout.VideoOut(self.timings)

        rowbuf = Memory(width = 8, depth = self.timings.cols * 16 * 2, init = ROWBUFTEST)
        m.submodules.rowbuf_read = rowbuf_read = rowbuf.read_port(transparent = False)
        m.d.comb += [
            rowbuf_read.addr.eq(out.rowbuf_addr),
            rowbuf_read.en.eq(out.rowbuf_en),
            out.rowbuf_data.eq(rowbuf_read.data),
        ]

        return m
