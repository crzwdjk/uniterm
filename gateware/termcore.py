from amaranth import *
from amaranth.lib.wiring import *
from cursor import cursorControlsSig, CursorShape
from signatures import *

class TerminalCore(Component):
    """
    The core processing engine of the terminal, responsible for actually putting things
    into the glyphbuffer. Starts in the appropriately named "RESET" state to clear the contents
    of the glyphbuffer.
    """
    def __init__(self, timings):
        self.rows = timings.rows
        self.cols = timings.cols
        super().__init__()

    @property
    def signature(self):
        return Signature({
            "gbuf_write": Out(Signature({
                "row": Out(range(self.rows)),
                "col": Out(range(self.cols)),
                "en": Out(1),
                "data": Out(16),
                "ack": In(1),
            })),
            "scroll_offset": Out(range(self.rows)),
            "serial_in": In(streamSig(8)),
            "cursor": Out(cursorControlsSig(rows=self.rows, cols=self.cols)),
        })


    def elaborate(self, platform):
        m = Module()

        char = Signal(16)
        m.d.comb += self.cursor.shape.eq(CursorShape.BOX)

        with m.FSM(reset="RESET"):
            with m.State("IDLE"):
                with m.If(self.serial_in.rdy):
                    m.d.comb += self.serial_in.ack.eq(1)
                    m.d.sync += char.eq(self.serial_in.data - 32)
                    m.next = "PRINT"

            with m.State("PRINT"):
                m.d.comb += [
                    self.gbuf_write.en.eq(1),
                    self.gbuf_write.row.eq(self.cursor.row),
                    self.gbuf_write.col.eq(self.cursor.col),
                    self.gbuf_write.data.eq(char),
                ]
                with m.If(self.gbuf_write.ack):
                    with m.If(self.cursor.col == self.cols - 1):
                        with m.If(self.cursor.row == self.rows - 1):
                            m.d.sync += self.cursor.row.eq(0)
                        with m.Else():
                            m.d.sync += self.cursor.row.eq(self.cursor.row + 1)
                        m.d.sync += self.cursor.col.eq(0)
                    with m.Else():
                        m.d.sync += self.cursor.col.eq(self.cursor.col + 1)
                    m.next = "IDLE"

            with m.State("RESET"):
                m.d.comb += self.gbuf_write.en.eq(1)
                m.d.comb += self.gbuf_write.data.eq(0)
                m.d.comb += self.gbuf_write.row.eq(self.cursor.row)
                m.d.comb += self.gbuf_write.col.eq(self.cursor.col)
                with m.If(self.gbuf_write.ack):
                    with m.If(self.cursor.col == self.cols - 1):
                        with m.If(self.cursor.row == self.rows - 1):
                            m.d.sync += self.cursor.col.eq(0)
                            m.d.sync += self.cursor.row.eq(0)
                            m.next = "IDLE"
                        with m.Else():
                            m.d.sync += self.cursor.col.eq(0)
                            m.d.sync += self.cursor.row.eq(self.cursor.row + 1)
                    with m.Else():
                        m.d.sync += self.cursor.col.eq(self.cursor.col + 1)


        return m

