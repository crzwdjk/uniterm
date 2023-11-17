from amaranth import *
from amaranth.lib.wiring import *
import enum
from signatures import *

__all__ = ["CursorShape", "cursorControlsSig", "Cursor"]
class CursorShape(enum.Enum):
    UNDERLINE = 1
    SOLID = 2
    VERTICAL = 3
    BOX = 4

def cursorControlsSig(rows, cols):
    return Signature({
        "col": Out(range(cols)),
        "row": Out(range(rows)),
        "shape": Out(CursorShape),
        "blink": Out(1, reset = 1),
        "doublewide": Out(1),
    })

class Cursor(Component):
    def __init__(self, timings):
        self.timings = timings
        super().__init__()

    @property
    def signature(self):
        return Signature({
            "controls": In(cursorControlsSig(rows=self.timings.rows, cols=self.timings.cols)),
            "pos": In(videoPosSig(self.timings)),
            "output": Out(1),
        })

    def elaborate(self, platform):
        m = Module()

        blinkctrval = Const(int(self.timings.pclk * 1e6 * 0.5))

        col = Signal.like(self.controls.col)
        row = Signal.like(self.controls.row)
        ctr = Signal(blinkctrval.shape())
        cursor_on = Signal()

        row_pix = self.pos.vctr[0:4]
        col_pix = self.pos.hctr[0:3]
        m.d.comb += col.eq(self.pos.hctr >> 3)
        m.d.comb += row.eq(self.pos.vctr >> 4)

        # counter for the blink
        with m.If(ctr == blinkctrval):
            m.d.sync += ctr.eq(0)
            m.d.sync += cursor_on.eq(~cursor_on)
        with m.Else():
            m.d.sync += ctr.eq(ctr + 1)

        # output before any blink is applied
        pre_output = Signal()
        m.d.comb += pre_output.eq(0)

        # Apply cursor style
        cursor_left = (col == self.controls.col)
        cursor_right = Mux(self.controls.doublewide, col == self.controls.col + 1, col == self.controls.col)
        with m.If((cursor_left | cursor_right) & (row == self.controls.row)):
            with m.Switch(self.controls.shape):
                with m.Case(CursorShape.BOX):
                    m.d.comb += pre_output.eq(1)
                with m.Case(CursorShape.VERTICAL):
                    m.d.comb += pre_output.eq(col_pix == 0)
                with m.Case(CursorShape.UNDERLINE):
                    m.d.comb += pre_output.eq((row_pix == 13) | (row_pix == 14))
                with m.Case(CursorShape.BOX):
                    m.d.comb += pre_output.eq((col_pix == 0) | (col_pix == 7) |
                                               (cursor_left & (row_pix == 0)) |
                                               (cursor_right & (row_pix == 15)))

        m.d.comb += self.output.eq(pre_output & (cursor_on | ~self.controls.blink))

        return m

if __name__ == "__main__":
    from amaranth.sim import *
    dut = Cursor()
    sim = Simulator(dut)
    sim.add_clock(40e-9)
    hctr = vctr = 0
    def proc():
        yield dut.shape.eq(CursorShape.UNDERLINE)
        yield dut.blink.eq(0)
        for vctr in range(0, 16):
            for hctr in range(0, 100):
                yield dut.hctr.eq(hctr)
                yield dut.vctr.eq(vctr)
                yield Tick()
    sim.add_sync_process(proc)
    with sim.write_vcd("waves/cursor.vcd"):
        sim.run()
