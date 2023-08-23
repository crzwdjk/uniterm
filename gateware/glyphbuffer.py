from amaranth import *
from amaranth.lib.wiring import *

class GlyphBuffer(Elaboratable):
    def __init__(self, timings):
        self.timings = timings
        self.signature = Signature({
            "read": Out(Signature({
                "row": In(range(timings.rows)),
                "col": In(range(timings.cols)),
                "data": Out(16),
                "en":   In(1),
            })),
            "write": Out(Signature({
                "row": In(range(timings.rows)),
                "col": In(range(timings.cols)),
                "en": In(1),
                "data": In(16),
                "ack": Out(1),
            })),
        })
        self.__dict__.update(self.signature.members.create())

    def elaborate(self, platform):
        m = Module()

        # memory size/stride rounded up to powers of 2, we can afford it with
        # SPRAM.
        memsize = (1 << self.read.row.width) * (1 << self.read.col.width)
        mem = Memory(width = 16, depth = memsize)
        m.submodules.mem_rd = mem_rd = mem.read_port(transparent = False)
        m.submodules.mem_wr = mem_wr = mem.write_port()

        addr = Signal.like(mem_rd.addr)
        m.d.comb += [
            mem_rd.en.eq(self.read.en),
            addr.eq(Mux(self.read.en, Cat(self.read.row, self.read.col),
                                      Cat(self.write.row, self.write.col))),
            self.read.data.eq(mem_rd.data),
            mem_wr.data.eq(self.write.data),
            mem_rd.addr.eq(addr),
            mem_wr.addr.eq(addr),

            mem_wr.en.eq(self.write.en & ~self.read.en),
            self.write.ack.eq(self.write.en & ~self.read.en),
        ]
        return m


class CharGen(Elaboratable):
    def __init__(self, timings):
        self.rows = timings.rows
        self.cols = timings.cols
        self.signature = Signature({
            "row": Out(range(self.rows)),
            "col": Out(range(self.cols)),
            "data": Out(16),
            "en": Out(1),
            "ack": In(1),
        })
        self.__dict__.update(self.signature.members.create())

    def elaborate(self, platform):
        m = Module()

        ctr = Signal(22)
        charidx = Signal(16)
        nextval = Signal(23)
        m.d.comb += nextval.eq(ctr + 1)
        m.d.comb += self.data.eq(charidx)
        with m.If(nextval[22]):
            m.d.sync += ctr.eq(0)
            with m.If(charidx == 5318):
                m.d.sync += charidx.eq(0)
            with m.Else():
                m.d.sync += charidx.eq(charidx + 1)
            # increment address
            with m.If(self.col == self.cols - 1):
                with m.If(self.row == self.rows - 1):
                    m.d.sync += self.row.eq(0)
                with m.Else():
                    m.d.sync += self.row.eq(self.row + 1)
                m.d.sync += self.col.eq(0)
            with m.Else():
                m.d.sync += self.col.eq(self.col + 1)
            m.d.sync += self.en.eq(1)
        with m.Else():
            m.d.sync += ctr.eq(nextval[0:23])

        with m.If(self.en & self.ack):
            m.d.sync += self.en.eq(0)

        return m
