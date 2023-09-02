from amaranth import *
from amaranth.lib.wiring import *
import enum
from signatures import *

__all__ = ["CursorShape", "CursorControlsSig", "Cursor"]
class CursorShape(enum.Enum):
    UNDERLINE = 1
    SOLID = 2
    VERTICAL = 3
    BOX = 4

class CursorControlsSig(Signature):
    def __init__(self, *, rows, cols):
        return super().__init__({
            "cursor_x": Out(range(cols)),
            "cursor_y": Out(range(rows)),
            "shape": Out(CursorShape),
            "blink": Out(1, reset = 1),
            "doublewide": Out(1),
        })

class Cursor(Elaboratable):
    def __init__(self, timings):
        self.signature = Signature({
            "controls": In(CursorControlsSig(rows=timings.rows, cols=timings.cols)),
            "pos": In(videoPosSig(timings)),
            "output": Out(1),
        })
        self.__dict__.update(self.signature.members.create())
        self.blinkctrval = Const(int(timings.pclk * 1e6 * 0.5))

    def elaborate(self, platform):
        m = Module()

        col = Signal.like(self.controls.cursor_x)
        row = Signal.like(self.controls.cursor_y)
        ctr = Signal(32)
        cursor_on = Signal()

        row_pix = self.pos.vctr[0:4]
        col_pix = self.pos.hctr[0:3]
        m.d.comb += col.eq(self.pos.hctr >> 3)
        m.d.comb += row.eq(self.pos.vctr >> 4)

        # counter for the blink
        with m.If(ctr == self.blinkctrval):
            m.d.sync += ctr.eq(0)
            m.d.sync += cursor_on.eq(~cursor_on)
        with m.Else():
            m.d.sync += ctr.eq(ctr + 1)

        # output before any blink is applied
        pre_output = Signal()
        m.d.comb += pre_output.eq(0)

        # Apply cursor style
        cursor_left = (col == self.controls.cursor_x)
        cursor_right = Mux(self.controls.doublewide, col == self.controls.cursor_x + 1, col == self.controls.cursor_x)
        with m.If((cursor_left | cursor_right) & (row == self.controls.cursor_y)):
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
