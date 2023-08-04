import gzip, bz2, lzma

def filetype(fn):
    if fn[-3:] == ".gz":
        return "gzip"
    if fn[-4:] == ".bz2":
        return "bzip2"
    if fn[-3:] == ".xz":
        return "xzip"
    else:
        return ""


def magic_open(fn, mode):
    ft = filetype(fn)
    if ft == "gzip":
        return gzip.open(fn, mode)
    if ft == "bzip2":
        return bz2.open(fn, mode)
    if ft == "xzip":
        return lzma.open(fn, mode)
    return open(fn, mode)
