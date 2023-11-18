from amaranth import *
from amaranth.lib.wiring import *
from amaranth.asserts import *
from signatures import *

class UTF8Decoder(Component):
    """A streaming UTF-8 parser. Errors are silently ignored.

       Input is provided as bytes via the conventional stream format with
       in_byte, in_rdy, and in_ack.

       Output is provided as 21-bit codepoints, which is all that Unicode
       currently defines, which means only input sequences of up to 4 bytes
       can be parsed. Errors that result in the parser resetting itself
       with no output include: invalid start bytes (including for sequences
       longer than valid codepoints), invalid continuation bytes, and
       valid sequences that are longer than necessary for a valid codepoint.

       Things that are not considered errors are surrogate pairs and other
       non-characters, including characters outside the currently valid
       range of unicode codepoints (as long as they're below U+1FFFFF).

    """
    inp: In(streamSig(8))
    out: Out(streamSig(21))
    def __init__(self):
        self._received_byte = Signal(8)
        super().__init__()

    def read_and_next(self, m, nextstate):
        with m.If(self.inp.rdy):
            m.d.comb += self.inp.ack.eq(1)
            m.d.sync += self._received_byte.eq(self.inp.data)
            m.next = nextstate

    def elaborate(self, platform):
        m = Module()

        bytecount = Signal(3)
        with m.FSM():
            with m.State("IDLE"):
                self.read_and_next(m, "INITIAL")

            with m.State("INITIAL"):
                with m.Switch(self._received_byte):
                    with m.Case("0-------"):
                        m.d.sync += self.out.data.eq(self._received_byte)
                        m.next = "DONE"
                    with m.Case("110-----"):
                        m.d.sync += self.out.data[6:].eq(self._received_byte[0:5])
                        m.d.sync += bytecount.eq(1)
                        # 2 byte overlong sequences are checked immediately.
                        with m.If((self._received_byte == 0xc0) | (self._received_byte == 0xc1)):
                            m.next = "IDLE"
                        with m.Else():
                            self.read_and_next(m, "UNICONT1")
                    with m.Case("1110----"):
                        m.d.sync += self.out.data[12:16].eq(self._received_byte[0:4])
                        m.d.sync += bytecount.eq(2)
                        self.read_and_next(m, "UNICONT2")
                    with m.Case("11110---"):
                        m.d.sync += self.out.data[18:].eq(self._received_byte[0:3])
                        m.d.sync += bytecount.eq(3)
                        self.read_and_next(m, "UNICONT3")
                    with m.Default():
                        m.next = "IDLE"
            with m.State("UNICONT3"):
                with m.If((self._received_byte & 0xc0) == 0x80):
                    m.d.sync += self.out.data[12:18].eq(self._received_byte[0:6])
                    self.read_and_next(m, "UNICONT2")
                with m.Else():
                    m.next = "IDLE"
            with m.State("UNICONT2"):
                # Check for overlong 4-byte sequences now that we have 3 bytes
                with m.If(((self._received_byte & 0xc0) == 0x80) &
                          ((bytecount != 3) | (self.out.data[16:] != 0))):
                    m.d.sync += self.out.data[6:12].eq(self._received_byte[0:6])
                    self.read_and_next(m, "UNICONT1")
                with m.Else():
                    m.next = "IDLE"
            with m.State("UNICONT1"):
                # Check for overlong 3-byte sequences now that we have 3 bytes
                with m.If(((self._received_byte & 0xc0) == 0x80) &
                          ((bytecount != 2) | (self.out.data[11:16] != 0))):
                    m.d.sync += self.out.data[0:6].eq(self._received_byte[0:6])
                    m.next = "DONE"
                with m.Else():
                    m.next = "IDLE"
            with m.State("DONE"):
                m.d.comb += self.out.rdy.eq(1)
                with m.If(self.out.ack):
                    m.next = "IDLE"

        return m

    @classmethod
    def formal(cls):
        m = Module()

        m.submodules.utf8 = c = cls()

        sync_clk = ClockSignal("sync")
        sync_rst = ResetSignal("sync")
        m.d.comb += Assume(sync_clk == ~Past(sync_clk))
        m.d.comb += Assume(~sync_rst)

        bytes_ingested = Signal(8)
        codepoints_output = Signal(8)
        sequence_len = Signal(8)
        with m.If(Fell(sync_clk) & c.in_ack):
            m.d.sync += bytes_ingested.eq(bytes_ingested + 1)
            with m.Switch(c.in_byte):
                with m.Case("0-------", "11------"):
                    m.d.sync += sequence_len.eq(1)
                with m.Case("10------"):
                    m.d.sync += sequence_len.eq(sequence_len + 1)

        with m.If(Rose(c.out_rdy)):
            m.d.sync += codepoints_output.eq(codepoints_output + 1)

        with m.If((codepoints_output == 1) & c.out_rdy):
            m.d.comb += Assert(bytes_ingested > 0)
            with m.If(bytes_ingested == 1):
                m.d.comb += Assert(c.out_codepoint < 0x80)
            with m.If(bytes_ingested == 2):
                m.d.comb += Assert(c.out_codepoint < 0x800)
            with m.If(bytes_ingested == 3):
                m.d.comb += Assert(c.out_codepoint < 0x10000)

            # verify that no overlong sequences are parsed.
            with m.If(c.out_codepoint < 0x80):
                m.d.comb += Assert(sequence_len == 1)
            with m.Elif(c.out_codepoint < 0x800):
                m.d.comb += Assert(sequence_len == 2)
        with m.Elif(c.out_codepoint < 0x10000):
            m.d.comb += Assert(sequence_len == 3)
            with m.Else():
                m.d.comb += Assert(sequence_len == 4)

        with m.If(Rose(sync_clk) & ~Initial()):
            # Check that no invalid bytes are consumed.
            with m.If(c.out_rdy & Past(c.in_rdy, 2) & Past(c.in_ack)):
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xc0)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xc1)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xf8)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xf9)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xfa)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xfb)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xfc)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xfd)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xfe)
                m.d.comb += Assert(Past(c.in_byte, 2) != 0xff)

        # cover some edge cases.
        m.d.comb += [
            Cover(c.out_rdy & (c.out_codepoint == 0x42)),
            Cover(c.out_rdy & (c.out_codepoint == 0x80)),
            Cover(c.out_rdy & (c.out_codepoint == 0x7ff)),
            Cover(c.out_rdy & (c.out_codepoint == 0x800)),
            Cover(c.out_rdy & (c.out_codepoint == 0xffff)),
            Cover(c.out_rdy & (c.out_codepoint == 0x10000)),
            Cover(c.out_rdy & (c.out_codepoint == 0x10ffff)),
        ]

        return m, [sync_clk, sync_rst, c.in_byte, c.in_rdy, c.out_ack]

from amaranth.back import rtlil
from amaranth.hdl import Fragment

if __name__ == "__main__":
    design, ports = UTF8Decoder.formal()
    fragment = Fragment.get(design, None)
    output = rtlil.convert(fragment, ports=ports)
    with open("formal/utf8.il", "w") as f:
        f.write(output)

