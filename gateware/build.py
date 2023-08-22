#!/usr/bin/env python3
import argparse, shutil
from amaranth.build import *
from amaranth_boards.tinyfpga_bx import *
from amaranth_boards.upduino_v3 import *
from amaranth_boards.resources import *

from vgatimings import TIMINGS

class PlatformData():
    """A container for platform-specific configuration data, including the
    amaranth Platform object itself."""
    def __init__(self, name):
        if name == "upduino":
            self.platform = UpduinoV3Platform()
            self.platform.add_resources([
                Resource("clk12e", 0, Pins("35", dir="i"), Clock(12e6),
                    Attrs(IO_STANDARD="SB_LVCMOS")),
                VGAResource(0, r="2 46 47 45 48", g="3 4 44 6 9", b="28 38 42 36 43",
                    hs="11", vs="18", attrs=Attrs(IO_STANDARD="SB_LVCMOS33")),
                UARTResource(0, rx="34", tx="37",
                    attrs=Attrs(IO_STANDARD="SB_LVCMOS33")),
                PS2Resource(0, clk="19", dat="13",
                    attrs=Attrs(IO_STANDARD="SB_LVCMOS33")),
                Resource("pclk", 0, Pins("19", dir="o", invert=True),
                    Attrs(IO_STANDARD="SB_LVCMOS33")),
                Resource("den", 0, Pins("13", dir="o"),
                    Attrs(IO_STANDARD="SB_LVCMOS33")),
            ])
            self.clkresource = "clk12e"
        elif name == "tinyfpga":
            self.platform = TinyFPGABXPlatform()
            self.platform.add_resources([
                VGAResource(0, r="1 2 3 4", g="5 6 7 8", b="9 10 11 12", hs="13", vs="14",
                    conn=("gpio", 0), attrs=Attrs(IO_STANDARD="SB_LVCMOS")),
                UARTResource(0, rx="23", tx="24",
                    conn=("gpio", 0), attrs=Attrs(IO_STANDARD="SB_LVCMOS")),
                PS2Resource(0, clk="21", dat="22",
                    conn=("gpio", 0), attrs=Attrs(IO_STANDARD="SB_LVCMOS")),
                *LEDResources("dbgled", pins="15 16 17 18",
                    conn=("gpio", 0), attrs=Attrs(IO_STANDARD="SB_LVCMOS")),
            ])

            self.clkresource = "clk16"
        else:
            raise Exception("Unknown platform", name)


def parse_args():
    parser = argparse.ArgumentParser(
            description="Build the gateware for uniterm",
            epilog="bottom text")

    parser.add_argument("-p", "--platform", choices=["upduino","tinyfpga"],
            default="upduino")
    parser.add_argument("-r", "--resolution", choices=TIMINGS.keys(),
            default="640x480")
    parser.add_argument("-f", "--flash",
            action="store_true")

    return parser.parse_args()

def main():
    options = parse_args()

    print(f"building for {options.platform} with {options.resolution}")
    timings = TIMINGS[options.resolution]
    pdata = PlatformData(options.platform)

    if options.platform == "upduino":
        flashmapfile = "../font/build/flash_map_full.py"
    else:
        flashmapfile = "../font/build/flash_map_core.py"
    # copy file to build/
    shutil.copy(flashmapfile, "build/flash_map.py")
    import toplevel
    pdata.platform.build(toplevel.Toplevel(pdata, timings),
                         do_program=options.flash)


if __name__ == "__main__":
    main()
