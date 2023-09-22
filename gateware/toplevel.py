from amaranth import *
from amaranth.lib.wiring import *
from amaranth.lib.fifo import SyncFIFO
import bufserial, flasharb, glyphbuffer, icepll, rowfiller, videoout
from flashreader import *
from rowbuftest import *
from termcore import *

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

        m.submodules.rowfiller = rowfill = rowfiller.RowFiller(self.timings)
        row_to_fill = Signal(range(self.timings.rows))

        m.submodules.glyphbuf = glyphbuf = glyphbuffer.GlyphBuffer(self.timings)
        connect(m, glyphbuf.read, rowfill.gbuf_rd)

        m.d.sync += [
            row_to_fill.eq((out.pos.vctr >> 4) + 1),
        ]
        m.d.comb += [
            rowfill.char_row.eq(row_to_fill),
            rowfill.start_fill.eq((row_to_fill >= 0) &
                                  (out.pos.vctr[0:4] == 0) &
                                  (out.pos.hctr == 0)),
            rowbuf_write.addr.eq(rowfill.rowbuf_wr.addr),
            rowbuf_write.data.eq(rowfill.rowbuf_wr.data),
            rowbuf_write.en.eq(rowfill.rowbuf_wr.en),
        ]

        m.submodules.termcore = terminalcore = TerminalCore(self.timings)

        freq = m.submodules.pll.params.f_out
        m.submodules.serial = serialport = bufserial.BufSerial(divisor = int(freq // 115200))
        connect(m, serialport.rx, terminalcore.serial_in)
        connect(m, terminalcore.gbuf_write, glyphbuf.write)
        connect(m, out.cursor, terminalcore.cursor)

        m.submodules.flasharb = flasharb.FlashArbiter(rowfill.flash, terminalcore.flash)

        return m
