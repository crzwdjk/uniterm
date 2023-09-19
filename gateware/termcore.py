from amaranth import *
from amaranth.lib.wiring import *
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
            "serial_in": In(streamSig(8))
        })


    def elaborate(self, platform):
        m = Module()

        rowctr = Signal(range(self.rows))
        colctr = Signal(range(self.cols))

        char = Signal(16)

        with m.FSM(reset="RESET"):
            with m.State("IDLE"):
                with m.If(self.serial_in.rdy):
                    m.d.comb += self.serial_in.ack.eq(1)
                    m.d.sync += char.eq(self.serial_in.data - 32)
                    m.next = "PRINT"

            with m.State("PRINT"):
                m.d.comb += [
                    self.gbuf_write.en.eq(1),
                    self.gbuf_write.row.eq(rowctr),
                    self.gbuf_write.col.eq(colctr),
                    self.gbuf_write.data.eq(char),
                ]
                with m.If(self.gbuf_write.ack):
                    with m.If(colctr == self.cols - 1):
                        with m.If(rowctr == self.rows - 1):
                            m.d.sync += rowctr.eq(0)
                        with m.Else():
                            m.d.sync += rowctr.eq(rowctr + 1)
                        m.d.sync += colctr.eq(0)
                    with m.Else():
                        m.d.sync += colctr.eq(colctr + 1)
                    m.next = "IDLE"

            with m.State("RESET"):
                m.d.comb += self.gbuf_write.en.eq(1)
                m.d.comb += self.gbuf_write.data.eq(0)
                m.d.comb += self.gbuf_write.row.eq(rowctr)
                m.d.comb += self.gbuf_write.col.eq(colctr)
                with m.If(self.gbuf_write.ack):
                    with m.If(colctr == self.cols - 1):
                        with m.If(rowctr == self.rows - 1):
                            m.next = "IDLE"
                        with m.Else():
                            m.d.sync += colctr.eq(0)
                            m.d.sync += rowctr.eq(rowctr + 1)
                    with m.Else():
                        m.d.sync += colctr.eq(colctr + 1)


        return m

