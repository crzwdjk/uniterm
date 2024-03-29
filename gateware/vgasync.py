from amaranth import *
from amaranth.lib.wiring import *
from signatures import *

__all__ = ["VGASync"]

class VGASync(Component):
    """
    VGA sync generator, with configurable timings.

    outputs hctr, vctr, hsync, vsync
    active is asserted when hctr and vctr are in the active region
    """
    def __init__(self, timings):
        self.timings = timings
        super().__init__({
            "hs": Out(1),
            "vs": Out(1),
            "active": Out(1),
            "pos": Out(videoPosSig(self.timings)),
        })

    def elaborate(self, platform):
        m = Module()

        hactive = Signal(reset = 1)
        vactive = Signal(reset = 1)
        hctr = Signal.like(self.pos.hctr)
        vctr = Signal.like(self.pos.vctr)
        m.d.sync += [
            self.pos.hctr.eq(hctr),
            self.pos.vctr.eq(vctr),
        ]
        with m.If(hctr == self.timings.hsync_end - 1):
            m.d.sync += hctr.eq(-self.timings.hback)
            with m.If(vctr == self.timings.vsync_end - 1):
                m.d.sync += vctr.eq(-self.timings.vback)
                m.d.sync += self.vs.eq(0)
            with m.Else():
                m.d.sync += vctr.eq(vctr + 1)
        with m.Else():
            m.d.sync += hctr.eq(hctr + 1)

        with m.If(hctr == 0):
            m.d.sync += hactive.eq(1)
        with m.Elif(hctr == self.timings.hactive):
            m.d.sync += hactive.eq(0)
        with m.Elif(hctr == self.timings.hsync_start):
            m.d.sync += self.hs.eq(1)
        with m.Elif(hctr == -self.timings.hback):
            m.d.sync += self.hs.eq(0)

        with m.If(vctr == 0):
            m.d.sync += vactive.eq(1)
        with m.Elif(vctr == self.timings.vactive):
            m.d.sync += vactive.eq(0)
        with m.Elif(vctr == self.timings.vsync_start):
            m.d.sync += self.vs.eq(1)
        with m.Elif(vctr == -self.timings.vback):
            m.d.sync += self.vs.eq(0)

        m.d.comb += self.active.eq(hactive & vactive)
        return m

if __name__ == "__main__":
    import vgatimings
    from amaranth.sim import *
    timings = vgatimings.Timings(10.0, hactive = 10, hfront = 3, hsync = 4, hback = 4,
            vactive = 6, vfront = 2, vsync = 1, vback = 2)
    dut = VGASync(timings)

    sim = Simulator(dut)
    sim.add_clock(40e-9)
    def proc():
        for i in range(400):
            yield Tick()
    sim.add_sync_process(proc)

    with sim.write_vcd("waves/vgasync.vcd"):
        sim.run()

