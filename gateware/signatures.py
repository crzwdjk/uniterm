from amaranth.lib.wiring import Signature, In, Out

class VideoPosSig(Signature):
    def __init__(self, timings):
        super().__init__({
            "hctr": Out(timings.hctr_shape()),
            "vctr": Out(timings.vctr_shape()),
        })

