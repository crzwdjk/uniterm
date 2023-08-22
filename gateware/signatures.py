from amaranth.lib.wiring import Signature, In, Out

class VideoPosSig(Signature):
    def __init__(self, timings):
        super().__init__({
            "hctr": Out(timings.hctr_shape()),
            "vctr": Out(timings.vctr_shape()),
        })

class MemWriterSig(Signature):
    def __init__(self, *, addrbits, databits):
        super().__init__({
            "addr": Out(addrbits),
            "en": Out(1),
            "data": Out(databits),
        })
