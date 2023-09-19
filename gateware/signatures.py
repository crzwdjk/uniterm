from amaranth.lib.wiring import Signature, In, Out

def videoPosSig(timings):
    return Signature({
        "hctr": Out(timings.hctr_shape()),
        "vctr": Out(timings.vctr_shape()),
    })

def memWriterSig(addrbits, databits):
    return Signature({
        "addr": Out(addrbits),
        "en": Out(1),
        "data": Out(databits),
    })

def streamSig(datashape):
    return Signature({
        "data": Out(datashape),
        "rdy": Out(1),
        "ack": In(1),
    })
