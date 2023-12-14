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
            "serial_in": In(streamSig(21)),
            "cursor": Out(cursorControlsSig(rows=self.rows, cols=self.cols)),
            "charmap": In(Signature({
                "codepoint": In(21),
                "glyphid": Out(16),
                "en": In(1),
                "valid": Out(1),
            })),
        })


    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.cursor.shape.eq(CursorShape.BOX)
        m.d.comb += self.gbuf_write.en.eq(0)

        m.d.comb += self.gbuf_write.row.eq(self.cursor.row)
        m.d.comb += self.gbuf_write.col.eq(self.cursor.col)
        m.d.comb += self.gbuf_write.data.eq(self.charmap.glyphid)

        glyphid = Signal(16)
        with m.FSM(reset="RESET"):
            with m.State("IDLE"):
                with m.If(self.serial_in.rdy):
                    m.d.comb += self.serial_in.ack.eq(1)
                    m.d.comb += self.charmap.en.eq(1)
                    m.d.sync += self.charmap.codepoint.eq(self.serial_in.data)
                    m.next = "CHARMAP_WAIT"

            with m.State("CHARMAP_WAIT"):
                with m.If(self.charmap.valid):
                    m.next = "PRINT"

            with m.State("PRINT"):
                m.d.comb += self.gbuf_write.en.eq(1)
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

