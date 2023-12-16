from amaranth import *
from amaranth.lib.wiring import *
from signatures import *

READ_ARRAY = 0x0B
READ_ARRAY_SLOW = 0x03
DUAL_OUTPUT_READ = 0x3B
DUAL_IO_READ = 0xBB
QUAD_IO_READ = 0xEB
QUAD_OUTPUT_READ = 0x6B

__all__ = ["flashReaderSig", "FlashReader"]

def flashReaderSig():
    return Signature({
        "addr": Out(24),
        "read_size": Out(16),
        "read_trigger": Out(1),
        "data": In(8),
        "valid": In(1),
    })

class FlashReader(Component):
    COMMANDS = {1: READ_ARRAY, 2: DUAL_IO_READ, 4: QUAD_IO_READ}
    def __init__(self, width=1):
        if width not in (1,2,4):
            raise Exception(f"invalid width {width}")
        self.width = width
        super().__init__(flashReaderSig().flip())
        # how to use: set read_trigger to 1 and addr to desired address.
        # once the SPI starts talking, read data_out when valid is high
        # and it will clock out

    def elaborate(self, platform):
        m = Module()

        if platform is not None:
            spipins = platform.request(f"spi_flash_{self.width}x", 0)
        else:
            spipins = DummySPI(self.width)

        # BASIC THEORY OF OPERATION
        # the SPI flash reads data on the rising edge, we can change it on the falling edge.
        # we use the inverted clock as the SPI clock, gated by CS.
        cs = Signal()
        m.d.comb += spipins.clk.o.eq(cs & ~ClockSignal("sync"))
        m.d.comb += spipins.cs.o.eq(cs)

        # Now we have a state machine. We start with basic SPI mode. We count on the icepack
        # option to disable the SPI flash sleep mode.

        ctr = Signal(range(24))

        addr_latched = Signal(24)
        size_latched = Signal(16)

        shiftreg = Signal(24)
        m.d.comb += self.data.eq(shiftreg)
        with m.FSM():
            with m.State("IDLE"):
                with m.If(self.read_trigger):
                    m.d.sync += cs.eq(1)
                    m.d.sync += ctr.eq(7)
                    m.d.sync += addr_latched.eq(self.addr)
                    m.d.sync += size_latched.eq(self.read_size)
                    m.d.sync += shiftreg.eq(self.COMMANDS[self.width])
                    m.next = "WRITECMD"
                with m.Else():
                    m.d.sync += cs.eq(0)

            with m.State("WRITECMD"):
                if self.width == 1:
                    m.d.comb += spipins.copi.o.eq(shiftreg[7])
                else:
                    m.d.comb += spipins.dq.oe[0].eq(1)
                    m.d.comb += spipins.dq.o[0].eq(shiftreg[7])
                with m.If(ctr == 0):
                    if self.width == 4:
                        m.d.sync += ctr.eq(28)
                    else:
                        m.d.sync += ctr.eq(24 - self.width)
                    m.d.sync += shiftreg.eq(addr_latched)
                    m.next = "WRITEADDR"
                with m.Else():
                    m.d.sync += shiftreg.eq(shiftreg << 1)
                    m.d.sync += ctr.eq(ctr - 1)

            with m.State("WRITEADDR"):
                if self.width == 1:
                    m.d.comb += spipins.copi.o.eq(shiftreg[23])
                else:
                    m.d.comb += spipins.dq.oe.eq(Const(1).replicate(self.width))
                    m.d.comb += spipins.dq.o.eq(shiftreg[24-self.width:24])
                with m.If(ctr == 0):
                    if self.width == 4:
                        m.d.sync += ctr.eq(12)
                    else:
                        m.d.sync += ctr.eq(8 - self.width)
                    m.next = "DATAWAIT"
                with m.Else():
                    m.d.sync += ctr.eq(ctr - self.width)
                    m.d.sync += shiftreg.eq(shiftreg << self.width)

            with m.State("DATAWAIT"):
                with m.If(ctr == 0):
                    m.d.sync += ctr.eq(8 - self.width)
                    m.next = "DATAREAD"
                with m.Else():
                    m.d.sync += ctr.eq(ctr - self.width)
            with m.State("DATAREAD"):
                if self.width == 1:
                    m.d.sync += shiftreg.eq(Cat(spipins.cipo.i, shiftreg[0:7]))
                else:
                    m.d.comb += spipins.dq.oe.eq(0)
                    m.d.sync += shiftreg.eq(Cat(spipins.dq.i, shiftreg[0:8-self.width]))
                m.d.sync += ctr.eq(ctr - self.width)
                with m.If(ctr == 0):
                    m.d.sync += ctr.eq(8 - self.width)
                    m.d.sync += size_latched.eq(size_latched - 1)
                    m.d.sync += self.valid.eq(1)
                with m.Else():
                    m.d.sync += self.valid.eq(0)
                with m.If(size_latched == 0):
                    m.d.sync += cs.eq(0)
                    m.next = "IDLE"

        return m

class DummyPin():
  def __init__( self, name, width=1 ):
    self.o = Signal(width, name = '%s_o'%name )
    self.oe = Signal(width, name = '%s_oe'%name )
    self.i = Signal(width, name = '%s_i'%name )

class DummySPI():
  def __init__(self, width=1):
    self.cs   = DummyPin( 'cs' )
    self.clk  = DummyPin( 'clk' )
    if width == 1:
        self.copi = DummyPin( 'copi' )
        self.cipo = DummyPin( 'cipo' )
    else:
        self.dq = DummyPin('dq', width)

from amaranth.sim import *

def test_spiflash(dut, clocks):
    yield dut.addr.eq(0x50000)
    yield dut.read_size.eq(16)
    yield dut.read_trigger.eq(1)
    yield Tick()
    yield Settle()
    yield dut.read_trigger.eq(0)
    for i in range(clocks):
        yield Tick()

# Timing analysis: we need to load 80 characters per 800 * 16 = 12800 pixel clocks.
# This is 80 reads of 8 * 16 = 128 bits.
# Each read needs 1 clk for CS, 8 clks command, 24-bits address, 8 dummy bits.
# 80 * (1 + 8 + 24 + 8 + 128 + 1) = 13600 clks, too much.

# DSPI needs 1 clk for CS, 8 clks cmd, 12 clk address, 4 clk dummy, 64 clk data
# 80 * (1 + 8 + 12 + 8 + 64 + 1) = 7200 clks, good.

# QSPI needs 1 clk CS, 8 clk cmd, 6 clk address, 2 clk mode, 4 clk dummy, 32 clk data
# 80 * (1 + 8 + 6 + 2 + 4 + 32 + 1) = 3680 clks. Excellent. We have 9120 clks free.

def simulate_width(width):
    dut = FlashReader(width)
    print(f"Simulating {width}")
    sim = Simulator(dut)
    sim.add_clock(40e-9)
    def proc():
        yield from test_spiflash(dut, 256//width)
    sim.add_sync_process(proc)
    with sim.write_vcd(f"waves/flashreader{width}.vcd"):
        sim.run()


if __name__ == "__main__":
    simulate_width(1)
    simulate_width(2)
    simulate_width(4)

