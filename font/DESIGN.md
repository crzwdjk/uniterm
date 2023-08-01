# Fonts in Uniterm

The Uniterm video processor requires fonts to be flashed to its SPI flash
memory. There are several different blobs that comprise the font data,
however there is no filesystem. Instead, the blobs are flashed at offsets,
and a config file with those offsets is passed to the gateware build process
so the offsets get baked into the video processor gateware.

## Design considerations

The video processor uses a basic grid of 8x16 pixel cells, therefore the
fonts used must be bitmap fonts with a basic size of 8x16, and double wide
characters of 16x16. Because the unicode codepoint space is somewhat sparse,
and flash is a limited resource, a level of indirection is used, with
character bitmaps stored contiguously in memory, and a character map blob
containing a mapping of unicode codepoint to bitmap index. The top bits
are used as a flag to both indicate to the video processor whether it is
drawing a single or double wide character, as well as which data blob to
look in for the data. It is these indices that are stored in the glyph buffer.

Emoji present their own challenges. The platform that has been chosen for
the uniterm video processor does not have enough on-FPGA memory for a full
screen bitmap, nor is there enough bandwidth to load color bitmap data
from the SPI flash. Thus, a palette approach is used for emoji, with each
character having 3 planes of 16x16, providing 3 bits of color per pixel.
Each emoji also has its own associated palette.

## The data blobs

The following font-related blobs are created from a fonEmojit:
 * font1.bin - single wide characters, 16 bytes per character
 * font2.bin - double wide characters, 32 bytes per character
 * fonte.bin - emoji, 96 bytes per character
 * epal.bin - emoji palettes, 8 bytes per character
 * charmap.bin - the character map, either 64k or 128k entries, each entry is
   curently 2 bytes.

## Font file processing and subsetting

The input for the font blob build process consists of HEX files of the
format that unifont uses, and CHX files (format documented below)
for emoji which include planar images
and palette data. These can be generated from BDF files using the `bdf2hex.py`
utility. Because we want nice fonts for the terminal, but also as full
coverage of unicode as possible, we allow using multiple font files to build
the blobs, with the fonts being specified in priority order on the command
line. Also, the font processing utilities can take raw files or compressed
ones.

Because we do not want to waste valueable flash space storing data for
unprintable characters, only a specified subset of unicode is taken. Which
subsets to use are encoded in the `blocks.py` file.
These make sure that we don't include nonprintable characters, combining 
characters (not supported due to limitations of the video processor), as
well as scripts that can't work reasonably well on a character grid system.
Also, because not all currently used development platforms have enough flash
for a full character set, there are two options: the basic character set for
platforms with only 1M of flash and the extended character set for platforms
with 4M of flash.

## CHX file format

The resource limitations of the video processor impose certain constraints on
how emoji can be displayed. As a result, a design is chosen where each emoji
has its own palette. This palette is chosen from the 256 standard colors and
is stored in the spare bits of the unused foreground color of the first cell
and the color bits of the second cell, since all emoji are doublewide.
