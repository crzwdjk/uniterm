from flashreader import *
from amaranth import *
from amaranth.asserts import *
from amaranth.lib.wiring import *

def arbClientSig(clientSig):
    return Signature({
        "request": Out(1),
        "ok":      In(1),
        "client":  Out(clientSig),
    })

class FlashArbiter(Elaboratable):
    def __init__(self, *clients):
        self.clients = clients
        self._flashmod = FlashReader(4)

    def elaborate(self, platform):
        m = Module()

        m.submodules.flashmod = flashmod = self._flashmod
        for c in self.clients:
            m.d.comb += c.ok.eq(0)

        with m.FSM():
            with m.State("IDLE"):
                for i, c in enumerate(self.clients):
                    with m.If(c.request):
                        m.next = "CLIENT" + str(i)

            for i, c in enumerate(self.clients):
                with m.State("CLIENT" + str(i)):
                    m.d.comb += c.ok.eq(1)
                    connect(m, c.client, flashmod)
                    with m.If(~c.request):
                        m.next = "IDLE"
        return m

    @classmethod
    def formal(cls):
        class DummyClient(Component):
            signature = arbClientSig(flashReaderSig())
            def __init__(self):
                super().__init__()
            def elaborate(self, platform):
                return Module()

        m = Module()
        dummy1 = DummyClient()
        dummy2 = DummyClient()
        m.submodules += [dummy1, dummy2]
        clk = ClockSignal("sync")
        rst = ResetSignal("sync")
        m.d.comb += Assume(clk == ~Past(clk))
        m.d.comb += Assume(~rst)
        prev_d1_request = Signal()
        prev_d2_request = Signal()
        m.d.sync += prev_d1_request.eq(dummy1.request)
        m.d.sync += prev_d2_request.eq(dummy2.request)

        m.d.comb += Assert(~(dummy1.ok & dummy2.ok))
        with m.If(dummy1.ok & clk):
            m.d.comb += Assert(prev_d1_request)
        with m.If(dummy2.ok & clk):
            m.d.comb += Assert(prev_d2_request)
        m.submodules.arb = arb = cls(dummy1, dummy2)

        m.d.comb += Cover(dummy1.ok)
        m.d.comb += Cover(dummy2.ok)
        m.d.comb += Cover(dummy1.request & ~prev_d1_request
                          & dummy2.request & ~prev_d2_request)

        m.d.comb += Assert(~dummy1.ok | (dummy1.client.addr == arb._flashmod.addr))
        m.d.comb += Assert(~dummy2.ok | (dummy2.client.addr == arb._flashmod.addr))


        return m, [clk, dummy1.request, dummy2.request]

if __name__ == "__main__":
    from amaranth.back import rtlil
    from amaranth.hdl import Fragment
    design, ports = FlashArbiter.formal()
    fragment = Fragment.get(design, None)
    output = rtlil.convert(fragment, ports=ports)
    with open("formal/flasharb.il", "w") as f:
        f.write(output)
