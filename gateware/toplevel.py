from amaranth import *
from amaranth.lib.wiring import *
import icepll, rowfiller, videoout
from flashreader import *
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
        m.submodules.rowbuf_write = rowbuf_write = rowbuf.write_port()
        m.d.comb += [
            rowbuf_read.addr.eq(out.rowbuf_addr),
            rowbuf_read.en.eq(out.rowbuf_en),
            out.rowbuf_data.eq(rowbuf_read.data),
        ]

        m.submodules.flashreader = flashrd = FlashReader(4)
        m.submodules.rowfiller = rowfill = rowfiller.RowFiller(self.timings)
        connect(m, rowfill.flash, flashrd)
        row_to_fill = Signal(range(self.timings.rows))

        glyphbuf = Memory(width = 16, depth = 3000, init = [x for x in range(3000)])
        m.submodules.gbuf_read = gbuf_read = glyphbuf.read_port(transparent = False)

        m.d.sync += [
            row_to_fill.eq((out.pos.vctr >> 4) + 1),
        ]
        m.d.comb += [
            rowfill.gbuf_data.eq(gbuf_read.data),
            gbuf_read.addr.eq(row_to_fill * self.timings.cols + rowfill.gbuf_col),
            gbuf_read.en.eq(rowfill.gbuf_en),
            rowfill.char_row.eq(row_to_fill),
            rowfill.start_fill.eq((row_to_fill >= 0) &
                                  (out.pos.vctr[0:4] == 0) &
                                  (out.pos.hctr == 0)),
            rowbuf_write.addr.eq(rowfill.rowbuf_wr.addr),
            rowbuf_write.data.eq(rowfill.rowbuf_wr.data),
            rowbuf_write.en.eq(rowfill.rowbuf_wr.en),
        ]

        return m
