# Uniterm - a unicode terminal

No, not a terminal emulator, an actual old-school hardware terminal that
aims to support as much Unicode as fits into the fixed-cell terminal model,
including single and double width characters and eventually emoji as well.

The terminal is designed to target the iCE40UP5K FPGA from Lattice, using
the open source toolchain, however there is also some support for using
the iCE40 LP8k in the TinyFPGA BX platform as well.

## Building.

Download the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build/releases).
After setting up the OSS CAD Suite environment, run `python3 gateware/build.py`
to build and optionally program the bitstream.
