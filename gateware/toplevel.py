from amaranth import *
import icepll

class Toplevel(Elaboratable):
    """ The top level of the terminal, everything goes under here. """
    def __init__(self, pdata, timings):
        self.timings = timings
        self.pdata = pdata

    def elaborate(self, platform):
        m = Module()

        f_in = platform.lookup(self.pdata.clkresource).clock.frequency
        m.submodules += icepll.ICEPLL(f_in, self.timings.pclk * 1e6,
                                      self.pdata.clkresource)

        # some debug code with an RGB LED.
        led = platform.request("rgb_led")
        clk_freq = platform.default_clk_frequency
        timer = Signal(range(int(clk_freq//2)), reset=int(clk_freq//2) - 1)
        with m.If(timer == 0):
            m.d.sync += timer.eq(timer.reset)
            m.d.sync += led.g.eq(~led.g)
        with m.Else():
            m.d.sync += timer.eq(timer - 1)



        return m
