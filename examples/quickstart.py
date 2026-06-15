"""Build a small hierarchical GDS, print its metrics report card, and save the per-layer chart.

Run from the repo root:  python examples/quickstart.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gdstk

import load
import report


def main():
    # A leaf cell with two shapes, arrayed 5x5 by a top cell that also holds one shape of its own.
    lib = gdstk.Library("demo")
    leaf = lib.new_cell("leaf")
    leaf.add(gdstk.rectangle((0, 0), (1, 1), layer=1, datatype=0))
    leaf.add(gdstk.rectangle((0, 0), (1, 1), layer=2, datatype=0))
    top = lib.new_cell("top")
    top.add(gdstk.Reference(leaf, (0, 0), columns=5, rows=5, spacing=(2, 2)))
    top.add(gdstk.rectangle((0, 0), (20, 20), layer=10, datatype=0))

    rep = report.build(load.from_gdstk_library(lib))
    print(report.to_markdown(rep))

    out = os.path.join(os.path.dirname(__file__), "layers.png")
    report.figure(rep, out)
    print(f"\nlayer chart written to {out}")


if __name__ == "__main__":
    main()
