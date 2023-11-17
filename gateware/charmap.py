from amaranth import *
from amaranth.lib.wiring import *
from flasharb import arbClientSig, flashReaderSig
from build.flash_map import *

assert ((CHARMAP_SIZE - 1) & CHARMAP_OFFSET) == 0
CHARMAP_MASK = CHARMAP_SIZE - 1

class CharMap(Component):
    ctrl: Out(Signature({
        "codepoint": In(21),
        "glyphid": Out(16),
        "en": In(1),
        "valid": Out(1),
    }))
    flash: Out(arbClientSig(flashReaderSig()))
    def __init__(self):
        super().__init__()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += [
            self.flash.client.read_size.eq(2),
            self.flash.client.addr.eq(CHARMAP_OFFSET | ((self.ctrl.codepoint[0:16] << 1) & CHARMAP_MASK)),
        ]

        with m.FSM():
            with m.State("IDLE"):
                with m.If(self.ctrl.en):
                    m.next = "REQUEST"
                    m.d.sync += self.flash.request.eq(1)

            with m.State("REQUEST"):
                with m.If(self.flash.ok):
                    m.d.comb += self.flash.client.read_trigger.eq(1)
                    m.next = "WAIT1"

            with m.State("WAIT1"):
                with m.If(self.flash.client.valid):
                    m.d.sync += self.ctrl.glyphid[0:8].eq(self.flash.client.data)
                    m.next = "WAIT2"

            with m.State("WAIT2"):
                with m.If(self.flash.client.valid):
                    m.d.sync += self.ctrl.glyphid[8:16].eq(self.flash.client.data)
                    m.d.sync += self.ctrl.valid.eq(1)
                    m.d.sync += self.flash.request.eq(0)
                    m.next = "DONE"

            with m.State("DONE"):
                m.d.sync += self.ctrl.valid.eq(0)
                m.next = "IDLE"

        return m

if __name__ == "__main__":
    from amaranth.sim import *
    dut = CharMap()
    sim = Simulator(dut)
    sim.add_clock(1e-6)
    def proc():
        yield dut.codepoint.eq(0x262d)
        yield Tick()
        yield dut.en.eq(1)
        for i in range(8):
            yield Tick()
        yield dut.flash_ok.eq(1)
        for i in range(20):
            yield Tick()
        yield dut.flash_data_valid.eq(1)
        yield dut.flash_data.eq(42)
        yield Settle()
        yield Tick()
        yield dut.flash_data_valid.eq(0)
        yield Tick()
        yield dut.flash_data_valid.eq(1)
        yield Tick()
        yield dut.flash_data_valid.eq(0)
        yield Tick()
        yield Tick()
        yield Tick()

    sim.add_sync_process(proc)
    with sim.write_vcd("waves/charmap.vcd"):
        sim.run()


