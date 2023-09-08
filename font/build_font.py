#!/usr/bin/env python3
import os, pathlib, struct, sys

from blocks import *
import magicopen

"""
Build the font binaries to be flashed. The binaries are output to the build/
directory. There are two variants: a reduced character set for parts with 1M
of flash, and the full character set covering most of the Unicode characters
that can be represented in a character grid.
Each variant produces 3 files:
* font1-$variant.bin for single-wide characters
* font2-$variant.bin for double-wide characters
* charmap-$variant.bin as a character map, mapping unicode codepoints to
  indices into the above files.
"""
class Char():
    def __init__(self, code, hexdata):
        if len(hexdata) == 32:
            self.type = "single"
        elif len(hexdata) == 64:
            self.type = "double"
        else:
            raise Exception("Bad character length %d" % len(hexdata))

        self.data = bytearray() 
        if self.type == "single":
            for i in range(0, len(hexdata), 2):
                self.data.append(int('{:08b}'.format(int(hexdata[i:i+2], 16))[::-1],2))
        else:
            for i in range(0, len(hexdata), 4):
                datum = int('{:016b}'.format(int(hexdata[i:i+4], 16))[::-1], 2)
                self.data.append(datum & 0xff)
                self.data.append(datum >> 8)

        self.code = code

def read_hex(chars, charset, infile):
    ctr = 0
    for line in infile:
        (hexcode, data) = line.rstrip().split(":")
        charnum = int(hexcode, 16)
        if charnum in charset and charnum not in chars:
            chars[charnum] = Char(charnum, data)
        ctr = ctr + 1
        if ctr % 100 == 0:
            print(ctr, end="\r")

def write_blobs(chars, charset, *, singlefile, doublefile, charmapfile):
    single_idx = double_idx = emoji_idx = 0
    charmap = [0xffff] * 65536
    # TODO: deduplicate images
    for chnum in charset:
        if chnum not in chars: continue
        char = chars[chnum]
        if char.type == 'single':
            # write single
            if single_idx >= 16384:
                raise Exception("Too many single-wides!")
            charmap[char.code] = single_idx
            single_idx = single_idx + 1
            singlefile.write(char.data)
        elif char.type == 'double':
            if double_idx >= 49151:
                raise Exception("Too many double-wides!")
            charmap[char.code] = double_idx + 16384
            double_idx = double_idx + 1
            doublefile.write(char.data)
        else:
            raise Exception("Uknown character type")
    # write charmap
    for ch in charmap:
        charmapfile.write(struct.pack('<H', ch))

WARNING = "\e[1;31mWARNING\e[0m"

def main():
    chars = {}
    status = 0

    if len(sys.argv) < 2:
        print("usage: build.py fontfile.hex [fontfile.hex ...]")
        sys.exit(1)
    for fn in sys.argv[1:]:
        f = magicopen.magic_open(fn, "rt")
        read_hex(chars, set(CHARS_FULL), f)

    builddir = pathlib.Path("build")
    if not builddir.exists():
        builddir.mkdir()

    with open(builddir/"font1-core.bin", "wb") as singles, \
         open(builddir/"font2-core.bin", "wb") as doubles, \
         open(builddir/"charmap-core.bin", "wb") as charmap:
        write_blobs(chars, CHARS_CORE, singlefile=singles,
                    doublefile=doubles, charmapfile=charmap)
        print("core chars:")
        print(f" singles: {singles.tell()} bytes," +
              f" doubles: {doubles.tell()} bytes")
        if doubles.tell() > 512*1024:
            print(WARNING + " doublewide font too big! Packing will fail.")
            status = 1
        if doubles.tell() + singles.tell() + charmap.tell() > 704*1024:
            print(WARNING + " total size too big! Packing will fail.")
            status = 1

    with open(builddir/"font1-full.bin", "wb") as singles, \
         open(builddir/"font2-full.bin", "wb") as doubles, \
         open(builddir/"charmap-full.bin", "wb") as charmap:
        write_blobs(chars, CHARS_FULL, singlefile=singles,
                    doublefile=doubles, charmapfile=charmap)
        print("full charset:")
        print(f" singles: {singles.tell()} bytes," +
              f" doubles: {doubles.tell()} bytes")

    sys.exit(status)

if __name__ == "__main__":
    main()
