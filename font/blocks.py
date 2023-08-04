import functools

def block(start, end):
    return set(range(start, end + 1))

CHARSETS_CORE = [
    block(32,126),                      # Basic Latin
    block(0xa0,0xff) - {0xad},          # Latin-1, minus soft hyphen control code
    block(0x100,0x17f),                 # Latin Extended A
    block(0x180,0x24f),                 # Latin Extended B
    block(0x250,0x2ff),                 # IPA extensions, spacing modifier letters
    # greek
    block(0x370,0x3ff) - {0x378, 0x379, 0x380, 0x381, 0x382, 0x383, 0x38b,
0x38d, 0x3a2},
    block(0x400,0x4ff) - block(0x483,0x489), # Cyrillic, non-combiners
    block(0x500,0x52f),                 # more cyrillic
    block(0x531,0x58f) - {0x557, 0x558, 0x58b, 0x58c}, # Armenian
    block(0x5d0,0x5ea) | {0x5c0, 0x5c3, 0x5c6} | block(0x5ef, 0x5f4), # Hebrew
    block(0x10a0,0x10ff) - block(0x10c8, 0x10cc) - {0x10c6, 0x10ce, 0x10cf}, # georgian
    block(0x1100, 0x11ff) - {0x115f, 0x1160}, # hangul jamo
    block(0x1200, 0x137c) - {0x12c1, 0x12c6, 0x12c7, 0x12d7, 0x1311} -
        {0x1316, 0x1317, 0x131b, 0x131c}, # Ethiopic
    block(0x1380, 0x1399),              # Ethiopic supplement
    block(0x13a0, 0x13fd) - {0x13f6, 0x13f7}, # cherokee
    block(0x1400, 0x167f),              # canadian aboriginal syllabics
    block(0x1680, 0x169c),              # ogham
    block(0x16a0, 0x16f8),              # runic
    block(0x18b0, 0x18f5),              # canadian aboriginal syllabics extended
    block(0x1c80, 0x1c88),              # cyrillic extended C
    block(0x1c90, 0x1cbf) - {0x1cbb, 0x1cbc}, # georgian extended
    block(0x1d00, 0x1d7f),              # phonetic extensions
    block(0x1d80, 0x1dbf),              # phonetic extensions supplement
    block(0x1e00, 0x1eff),              # Latin extended additional
    # greek extended
    block(0x1f00, 0x1ffe) - {0x1f16, 0x1f17, 0x1f1e, 0x1f1f, 0x1f46, 0x1f47, 0x1f4e, 0x1f4f,
        0x1f58, 0x1f5a, 0x1f5c, 0x1f5e, 0x1f7e, 0x1f7f, 0x1fb5, 0x1fc5, 0x1fd4, 0x1fd5,
        0x1fdc, 0x1ff0, 0x1ff1, 0x1ff5},
    block(0x2010, 0x2027) | block(0x2030, 0x205f), # general punctuation
    block(0x2070, 0x209c) - {0x2072, 0x2073, 0x208f}, # super and subscripts
    block(0x20a0, 0x20c0),              # currency symbols
    block(0x2100, 0x214f),              # letterlike symbols
    block(0x2150, 0x218b),              # number forms
    block(0x2190, 0x21ff),              # arrows
    block(0x2200, 0x22ff),              # mathematical operators
    block(0x2300, 0x23ff),              # miscallaneous technical
    block(0x2400, 0x2426),              # control pictures
    block(0x2440, 0x244a),              # optical character recognition
    block(0x2460, 0x24ff),              # enclosed alphanumerics
    block(0x2500, 0x25ff),              # box drawing etc.
    block(0x2600, 0x26ff),              # miscellaneous symbols
    block(0x2700, 0x27bf),              # dingbats
    block(0x27c0, 0x27ef),              # misc mathematical symbols A
    block(0x27f0, 0x27ff),              # supplemental arrows A
    block(0x2800, 0x28ff),              # braille patterns
    block(0x2900, 0x297f),              # supplemental arrows B
    block(0x2980, 0x29ff),              # misc mathematical symbols B
    block(0x2a00, 0x2aff),              # supplemental math operators
    block(0x2b00, 0x2bff) - {0x2b74, 0x2b75, 0x2b96}, # misc symbols and arrows
    block(0x2c00, 0x2c5f),              # glagolitic
    block(0x2c60, 0x2c7f),              # Latin extended C
    block(0x2c80, 0x2cee) | {0x2cf2, 0x2cf3} | block(0x2cf9, 0x2cff), # coptic
    block(0x2d00, 0x2d25) | {0x2d27, 0x2d27}, # georgian supplement
    block(0x2d30, 0x2d67) | {0x2d6f, 0x2d70}, # Tifinagh
    block(0x2d80, 0x2d96) | block(0x2da0, 0x2dde) - # ethiopic supplement
        { 0x2da7, 0x2daf, 0x2db7, 0x2dbf, 0x2dc7, 0x2dcf, 0x2dd7, 0x2ddf },
    block(0x3000, 0x303f),              # CJK Symbols and punctuation
    block(0x3041, 0x309f) - block(0x3097, 0x309a), # hiragana
    block(0x30a0, 0x30ff),              # katakana
    block(0x3131, 0x318e),              # hangul compatibility jamo
    block(0x3190, 0x319f),              # kanbun
    block(0x31f0, 0x31ff),              # katakana phonetic extensions
    block(0x3300, 0x33ff),              # CJK compatibility
    block(0x4dc0, 0x4dff),              # yijing hexagram symbols
    block(0xa4d0, 0xa4ff),              # Lisu
    block(0xa500, 0xa62b),              # Vai
    block(0xa6a0, 0xa6f7) - {0xa6f0, 0xa6f1}, # bamum
    block(0xa640, 0xa66e) | block(0xa680, 0xa69d), # cyrillic extended B
    block(0xa700, 0xa71f),              # tone letters
    block(0xa720, 0xa7ca) | block(0xa7d0, 0xa7d9) |
        block(0xa7f2, 0xa7ff) - {0xa7d2, 0xa7d4}, # latin extended D
    block(0xa840, 0xa877),              # phags-pa
    block(0xa960, 0xa97c),              # hangul jamo extended A
    block(0xab30, 0xab6b),              # latin extended E
    block(0xac00, 0xd7a3),              # hangul syllables
    block(0xd7b0, 0xd7bf) - block(0xd7c7, 0xd7ca), # hangul jamo extended B
    block(0xfb00, 0xfb06) | block(0xfb13, 0xfb17) | # alphabetic presentation forms
        block(0xfb1d, 0xfb4f) - {0xfb1e, 0xfb37, 0xfb3d, 0xfb3f, 0xfb42, 0xfb45},
    block(0xe000, 0xe033) | block(0xe040, 0xe06e) -
        {0xe059, 0xe05b} - block(0xe05e, 0xe061), # tengwar
    block(0xe080, 0xe0eb),              # cirth
    block(0xf8d0, 0xf8e9) | block(0xf8f0, 0xf8f9) | block(0xf8fd, 0xf8ff), # klingon
    block(0xfe10, 0xfe19),              # vertical forms
    block(0xfe30, 0xfe4f),              # CJK compatibility forms
    block(0xfe50, 0xfe6b) - {0xfe53, 0xfe67}, # small form variants
    block(0xff01, 0xffee) - {0xffbf, 0xffc0, 0xffc1, 0xffc8, 0xffc9} -
        {0xffd0, 0xffd1, 0xffd8, 0xffd9, 0xffdd, 0xffde, 0xffdf, 0xffe7},
    {0xfffd},
]

CHARSETS_EXTENDED = [
    block(0x2e80, 0x2ef3) - {0x2e9a},   # CJK radicals supplement
    block(0x2f00, 0x2fd5),              # Kangxi radicals
    block(0x3105, 0x312f),              # bopomofo
    block(0x31a0, 0x31bf),              # bopomofo extended
    block(0x31c0, 0x313e),              # CJK strokes
    block(0x3200, 0x32ff) - {0x321f},   # enclosed CJK letters and months
    block(0x3400, 0x4dbf),              # CJK Unified ideographs extension A
    block(0x4e00, 0x9fff),              # CJK Unified ideographs
]

CHARSETS_EMOJI = [
# TODO
]

CHARS_CORE = sorted(functools.reduce(lambda a, b: a.union(b), CHARSETS_CORE))
CHARS_FULL = sorted(functools.reduce(lambda a, b: a.union(b), CHARSETS_CORE + CHARSETS_EXTENDED, set()))
CHARS_EMOJI = sorted(functools.reduce(lambda a, b: a.union(b), CHARSETS_EMOJI, set()))

__all__ = ["CHARS_CORE", "CHARS_FULL", "CHARS_EMOJI"]
