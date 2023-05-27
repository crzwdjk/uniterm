#!/usr/bin/env python3
import argparse
from amaranth.build import *
from amaranth_boards.tinyfpga_bx import *
from amaranth_boards.upduino_v3 import *

import toplevel
from vgatimings import TIMINGS

class PlatformData():
    """A container for platform-specific configuration data, including the
    amaranth Platform object itself."""
    def __init__(self, name):
        if name == "upduino":
            self.platform = UpduinoV3Platform()
            self.platform.add_resources(
                    [Resource("clk12e", 0, Pins("35", dir="i"),
                              Clock(12e6), Attrs(IO_STANDARD="SB_LVCMOS"))])
            self.clkresource = "clk12e"
        elif name == "tinyfpga":
            self.platform = TinyFPGABXPlatform()
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

    pdata.platform.build(toplevel.Toplevel(pdata, timings),
                         do_program=options.flash)


if __name__ == "__main__":
    main()
