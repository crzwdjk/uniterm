from amaranth import *
from amaranth.lib.fifo import SyncFIFO
from amaranth.lib.wiring import *
from signatures import *
from serial import *

class BufSerial(Component):
    rx: Out(streamSig(8))
    tx: In(streamSig(8))
    def __init__(self, divisor, bufdepth=16):
        self.divisor = divisor
        self.bufdepth = bufdepth
        super().__init__()

    def elaborate(self, platform):
        m = Module()

        pins = platform.request("uart")
        m.submodules.uart = uart = AsyncSerial(pins = pins, divisor = self.divisor)
        m.d.comb += uart.divisor.eq(self.divisor)

        m.submodules.rx_fifo = rx_fifo = SyncFIFO(width = 8, depth = self.bufdepth)
        m.d.comb += [
            rx_fifo.w_en.eq(uart.rx.rdy),
            rx_fifo.w_data.eq(uart.rx.data),
            uart.rx.ack.eq(rx_fifo.w_rdy),
            self.rx.rdy.eq(rx_fifo.r_rdy),
            self.rx.data.eq(rx_fifo.r_data),
            rx_fifo.r_en.eq(self.rx.ack),
        ]

        m.submodules.tx_fifo = tx_fifo = SyncFIFO(width = 8, depth = self.bufdepth)
        m.d.comb += [
            tx_fifo.w_en.eq(self.tx.ack),
            tx_fifo.w_data.eq(self.tx.data),
            self.tx.rdy.eq(tx_fifo.w_rdy),
            uart.tx.data.eq(tx_fifo.r_data),
            uart.tx.ack.eq(tx_fifo.r_rdy),
            tx_fifo.r_en.eq(uart.tx.rdy),
        ]

        return m
