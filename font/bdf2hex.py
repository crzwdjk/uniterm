#!/usr/bin/env python3

import argparse, bz2, gzip, lzma, re
from enum import Enum

class ParseState(Enum):
    NONE=0
    SKIPCHAR=1
    CHAR=2
    BITMAP=3

class Char():
    def expected_len(self):
        return self.width * 4

    def output(self, f):
        if self.code >= 65536:
            f.write("%06X" % self.code)
        else:
            f.write("%04X" % self.code)
        f.write(":")
        f.write(self.data)
        f.write("\n")

def parse_bdf(f, of, *, height=16, width=8):
    char = None
    state = ParseState.NONE
    for line in f:
        words = line.rstrip().split(" ")
        if state == ParseState.NONE:
            if words[0] == "STARTCHAR":
                char = Char()
                state = ParseState.CHAR
        elif state == ParseState.CHAR:
            if words[0] == "ENCODING":
                char.code = int(words[1])
                print(char.code, end="\r")
            elif words[0] == "BBX":
                char.width = int(words[1])
                char.height = int(words[2])
                if char.height != height:
                    raise Exception("Bad char height {}", char.height)
                if char.width == width:
                    char.type = "single"
                elif char.width == width * 2:
                    char.type = "double"
                else:
                    raise Exception("Bad char width {}", width)
            elif words[0] == "BITMAP":
                state = ParseState.BITMAP
                char.data = ""
        elif state == ParseState.BITMAP:
            if words[0] == "ENDCHAR":
                if len(char.data) != char.expected_len():
                    raise Exception("Bad char length {}", len(char.data))
                char.output(of)
                state = ParseState.NONE
            else:
                # TODO: radical simplification!!!
                char.data += line.rstrip()

        elif state == ParseState.SKIPCHAR:
            if words[0] == "ENDCHAR":
                state = ParseState.NONE



# read a BDF file (optionally compressed) and output a .hex file
# in unifont's .hex format.
def main():
    a = argparse.ArgumentParser(
            description="Convert a BDF file with monospace characters to unifont HEX format. " +
            "The font should have all characters be the same height, and a consistent single " +
            "or double width.",
            epilog="The files can be plain, or in gz, bz2, or xz compressed format")
    a.add_argument("files", metavar="input.bdf", nargs="*",
            help="BDF files to process")
    a.add_argument("--height", type=int, default=16,
            help="font height")
    a.add_argument("--width", type=int, default=8,
            help="basic width of font")
    options = a.parse_args()

    if len(options.files) == 0:
        f = sys.stdin
        of = sys.stdout
    else:
        for fn in options.files:
            if fn[-3:] == ".gz":
                # use gzip
                ofn = re.sub("(\.bdf)?.gz$", ".hex.gz", fn, count=1)
                f = gzip.open(fn, "r")
                of = gzip.open(ofn, "w")
            elif fn[-4:] == ".bz2":
                # use bz2
                ofn = re.sub("(\.bdf)?.bz2", ".hex.bz2", fn, count=1)
                f = bzip2.open(fn, "r")
                of = bzip2.open(ofn, "w")
            elif fn[-3:] == ".xz":
                # use lzma
                ofn = re.sub("(\.bdf)?.xz", ".hex.xz", fn, count=1)
                f = lzma.open(fn, "r")
                of = lzma.open(ofn, "w")
            else:
                ofn = re.sub('(\.bdf)?$', '.hex', fn, count=1)
                f = open(fn, "r")
                of = open(ofn, "w")

    parse_bdf(f, of, width=options.width, height=options.height)


if __name__ == "__main__":
    main()
