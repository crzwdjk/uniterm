#!/usr/bin/env python3
import argparse, pathlib, os, subprocess

def ctz(i):
    if i == 0: return 0
    cnt = 0
    while i & 1 == 0:
        cnt += 1
        i >>= 1
    return cnt

# Helper function for BlockAllocator
def adjust_block(start, end):
    blocks = []
    blocksize = 1 << ctz(start)
    while start + blocksize <= end:
        blocks.append((start, blocksize))
        start += blocksize
        blocksize = 1 << ctz(start)
    blocksize >>= 1
    while blocksize > 0:
        if start + blocksize <= end:
            blocks.append((start, blocksize))
            start += blocksize
        blocksize >>= 1
    return blocks

class BlockAllocator():
    def __init__(self, start, end):
        self.blocks = adjust_block(start, end) 
        self.block.sort(key = lambda x: x[1])

    def allocate(self, size):
        # blocks are sorted smallest-first
        for i in range(len(self.blocks)):
            start, blocksize = self.blocks[i]
            if blocksize > size:
                self.blocks[i:i+1] = adjust_block(start + size, start + blocksize)
                self.blocks.sort(key = lambda x: x[1])
                return start
        raise Exception(f"Out of blocks, couldn't get size {size}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pack font and other files into one blob for writing to the device's flash"
    )
    parser.add_argument("-p", "--platform", choices=["upduino","tinyfpga"], required=True)
    parser.add_argument("-s", "--size", type=int, help="Flash size in MB", required=True )
    parser.add_argument("-f", "--flash", action="store_true")

    return parser.parse_args()

ITEMS_CORE = ["font1", "font2", "charmap"]
ITEMS_FULL = ["font1", "font2", "charmap"]

class ConfigObject():
    def __init__(self, name, filepath):
        if not filepath.exists():
            raise Exception("File {} not found".format(filepath))
        self.size = filepath.stat().st_size
        self.path = filepath
        self.name = name

def gather_files(builddir, items, suffix, alloc):
    config = [ ConfigObject(item, builddir / (f"{item}-{suffix}.bin")) for item in items]
    config.sort(key=lambda x: x.size, reverse=True)
    for item in config:
        item.offset = alloc.allocate(item.size)
    return config

def write_config(builddir, suffix, config):
    configfile = open(builddir / f"flash_map_{suffix}.py", "w")
    for item in config:
        print("{:06x}\t{:06x}\t{}".format(item.offset, item.size, item.name))
        configfile.write("{}_OFFSET = {:#08x}\n".format(item.name.upper(), item.offset))
        configfile.write("{}_SIZE   = {:#08x}\n".format(item.name.upper(), item.size))

def write_uniblob(builddir, suffix, config, flash_start, flash_end):
    outfile = open(builddir / f"uniblob-{suffix}.bin", "wb")
    outfile.write(bytearray(0xff for _ in range(flash_start, flash_end)))
    for item in config:
        outfile.seek(item.offset - flash_start)
        with open(item.path, "rb") as infile:
            contents = infile.read()
            outfile.write(contents)

def flash_items(config):
    iceprog = os.environ.get("ICEPROG", "iceprog")
    for item in config:
        subprocess.check_call([iceprog, "-o", str(item.offset), item.path])
 
def flash_uniblob(builddir, suffix):
    tinyprog = os.environ.get("TINYPROG", "tinyprog")
    uniblob = builddir / f"uniblob-{suffix}.bin"
    subprocess.check_call([tinyprog, "-u", uniblob])

def main():
    args = parse_args()
    if args.platform == "tinyfpga":
        flash_start = 0x50000
    else:
        flash_start = 0x20000
    if args.size <= 0 or args.size > 16:
        print(f"Unsupported flash size {args.size}MB")
        sys.exit(1)
    suffix = "core" if args.size == 1 else "full"
    items = ITEMS_CORE if args.size == 1 else ITEMS_FULL
    flash_end = args.size * 1024 * 1024
    allocator = BlockAllocator(flash_start, flash_end)
    builddir = pathlib.Path("build")
    config = gather_files(builddir, items, suffix, allocator)
    write_config(builddir, suffix, config)
    if args.flash and args.platform == "upduino":
        flash_items(config)
    elif args.flash and args.platform == "tinyfpga":
        write_uniblob(builddir, suffix, config, flash_start, flash_end)
        flash_uniblob(builddir, suffix)

if __name__ == "__main__":
    main()
