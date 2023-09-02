from amaranth import *
from amaranth.lib.wiring import *
from signatures import *
from cursor import *
from vgasync import *

class VideoOut(Elaboratable):
    def __init__(self, timings):
        self.timings = timings
        self.signature = Signature({
            "pos": Out(videoPosSig(timings)),
            "cursor": In(CursorControlsSig(rows=timings.rows, cols=timings.cols)),
            "rowbuf_addr": Out(range(timings.cols * 16 * 2)),
            "rowbuf_en": Out(1),
            "rowbuf_data": In(8),
        })
        self.__dict__.update(self.signature.members.create())

    def elaborate(self, platform):
        m = Module()

        # Create the VGA sync module and wire up its outputs to the rowbuf addr/en
        m.submodules.vgasync = vgs = VGASync(self.timings)
        connect(m, flipped(self.pos), vgs.pos)
        m.d.comb += [
            self.rowbuf_addr.eq(vgs.pos.vctr[0:5] * self.timings.cols + vgs.pos.hctr[3:]),
            self.rowbuf_en.eq(vgs.active),
        ]

        active1 = Signal()
        fetched_byte = Signal(7)
        fetched_bit = Signal()
        with m.If(vgs.pos.hctr[0:3] == 1):
            m.d.sync += fetched_byte.eq(self.rowbuf_data[1:8])
            m.d.comb += fetched_bit.eq(self.rowbuf_data[0])
        with m.Else():
            m.d.sync += fetched_byte.eq(fetched_byte[1:7])
            m.d.comb += fetched_bit.eq(fetched_byte[0])

        m.d.sync += active1.eq(vgs.active)

        # create the cursor and override the shape for now.
        m.submodules.cursor = cursor = Cursor(self.timings)
        connect(m, self.cursor, flipped(cursor.controls))
        m.d.comb += cursor.controls.shape.eq(CursorShape.BOX)
        cursorval = Signal()
        m.d.sync += cursorval.eq(cursor.output)

        #bgcolor = [23, 20, 31]
        bgcolor = [0, 0, 0]
        fgcolor = [31, 31, 31]
        color = [Mux(cursorval ^ fetched_bit, c[0], c[1]) for c in zip(fgcolor, bgcolor)]
        connect(m, cursor.pos, vgs.pos)

        output = platform.request("vga", xdr={"r": 1, "g": 1, "b": 1, "hs": 1, "vs": 1})
        m.d.comb += [
                output.r.o_clk.eq(ClockSignal("sync")),
                output.g.o_clk.eq(ClockSignal("sync")),
                output.b.o_clk.eq(ClockSignal("sync")),
                output.hs.o_clk.eq(ClockSignal("sync")),
                output.vs.o_clk.eq(ClockSignal("sync")),
        ]
        # delay hs, vs by 1 clock and use the delayed active signal too
        m.d.sync += [
            output.hs.o.eq(vgs.hs),
            output.vs.o.eq(vgs.vs),
        ]
        m.d.comb += [
            output.r.o.eq(Mux(active1, color[0], 0)),
            output.g.o.eq(Mux(active1, color[1], 0)),
            output.b.o.eq(Mux(active1, color[2], 0)),
        ]

        # Not all platforms need the pclk/den outputs, so it's okay if the request fails.
        try:
            pclk = platform.request("pclk")
            m.d.comb += pclk.eq(ClockSignal("sync"))
            den = platform.request("den")
            m.d.sync += den.eq(vgs.active)
        except:
            pass

        return m
