from amaranth import *
from amaranth.lib.wiring import *
from signatures import *
from flashreader import *

import build.flash_map as flash_map
assert ((flash_map.FONT1_SIZE - 1) & flash_map.FONT1_OFFSET) == 0
#FONT1_MASK = flash_map.FONT1_SIZE - 1
FONT1_MASK = 0x1ffff
assert ((flash_map.FONT2_SIZE - 1) & flash_map.FONT2_OFFSET) == 0
FONT2_MASK = 0x1fffff
#FONT2_MASK = flash_map.FONT2_SIZE - 1

class RowFiller(Elaboratable):
    def __init__(self, timings):
        self.rowbuf_chars = timings.cols
        self.signature = Signature({
            "rowbuf_wr": Out(MemWriterSig(addrbits = range(timings.cols * 32), databits = 8)),
            "gbuf_col": Out(Shape.cast(range(timings.cols))),
            "gbuf_en": Out(1),
            "gbuf_data": In(16),
            "start_fill": In(1),
            "char_row": In(range(timings.rows)),
            "flash": Out(FlashReaderSig()),
        }).freeze()
        self.__dict__.update(self.signature.members.create())

    def gen_addr(self, *, row, col):
        return ((self.char_row[0] << 4) * self.rowbuf_chars +
                col + row * self.rowbuf_chars)

    def elaborate(self, platform):
        m = Module()

        charctr = Signal(range(self.rowbuf_chars))
        rowctr = Signal(4)
        # convenience signal for the doublewide bit of the current char.
        chwidth = Signal()
        m.d.comb += [
            self.flash.read_trigger.eq(0),
            self.rowbuf_wr.data.eq(self.flash.data),
            self.rowbuf_wr.en.eq(self.flash.valid),
            chwidth.eq(self.gbuf_data[15] != 0),
        ]

        with m.FSM():
            with m.State("IDLE"):
                with m.If(self.start_fill):
                    m.d.sync += charctr.eq(0)
                    #m.d.sync += self.flash_request.eq(1)
                    m.d.comb += self.gbuf_col.eq(0)
                    m.d.comb += self.gbuf_en.eq(1)
                    m.next = "WAIT_FLASH"

            with m.State("WAIT_FLASH"):
                #with m.If(self.flash_ok):
                    m.next = "REQUEST_READ"

            with m.State("REQUEST_READ"):
                swaddr = flash_map.FONT1_OFFSET | ((self.gbuf_data << 4) & FONT1_MASK)
                dwaddr = flash_map.FONT2_OFFSET | ((self.gbuf_data[0:14] << 5) & FONT2_MASK)
                m.d.comb += self.flash.addr.eq(Mux(chwidth, dwaddr, swaddr))
                m.d.comb += self.flash.read_trigger.eq(1)
                m.d.comb += self.flash.read_size.eq(Mux(chwidth, 32, 16))
                m.d.sync += rowctr.eq(0)
                with m.If(chwidth):
                    m.next = "COPYW1"
                with m.Else():
                    m.next = "COPY"

            with m.State("COPY"):
                m.d.comb += self.rowbuf_wr.addr.eq(self.gen_addr(col=charctr, row=rowctr))
                with m.If(self.flash.valid):
                    with m.If(rowctr == 15):
                        with m.If(charctr == self.rowbuf_chars - 1):
                            #m.d.sync += self.flash_request.eq(0)
                            m.next = "IDLE"
                        with m.Else():
                            m.d.sync += charctr.eq(charctr + 1)
                            m.d.comb += self.gbuf_en.eq(1)
                            m.d.comb += self.gbuf_col.eq(charctr + 1)
                            m.next = "REQUEST_READ"
                    with m.Else():
                        m.d.sync += rowctr.eq(rowctr + 1)

            with m.State("COPYW1"):
                m.d.comb += self.rowbuf_wr.addr.eq(self.gen_addr(col=charctr, row=rowctr))
                with m.If(self.flash.valid):
                    with m.If((rowctr == 15) & (charctr == self.rowbuf_chars - 1)):
                        #m.d.sync += self.flash_request.eq(0)
                        m.next = "IDLE"
                    with m.Elif(charctr == self.rowbuf_chars - 1):
                        m.d.sync += rowctr.eq(rowctr + 1)
                    with m.Else():
                        m.next = "COPYW2"

            with m.State("COPYW2"):
                m.d.comb += self.rowbuf_wr.addr.eq(self.gen_addr(col=charctr + 1, row=rowctr))
                with m.If(self.flash.valid):
                    with m.If(rowctr == 15):
                        with m.If(charctr == self.rowbuf_chars - 2):
                            #m.d.sync += self.flash_request.eq(0)
                            m.next = "IDLE"
                        with m.Else():
                            m.d.sync += charctr.eq(charctr + 2)
                            m.d.comb += self.gbuf_en.eq(1)
                            m.d.comb += self.gbuf_col.eq(charctr + 2)
                            m.next = "REQUEST_READ"
                    with m.Else():
                        m.d.sync += rowctr.eq(rowctr + 1)
                        m.next = "COPYW1"

        return m

