"""Extremes and rankings over the count metrics: the heaviest cells, the busiest layers, and how complex the
geometry is on average. These answer "what dominates this layout" at a glance, which is the part of a report
card a reviewer reads first.

This works on the lightweight count model, so it ranks by polygon and vertex counts. Filled-area and density
are a geometry question handled by a density tool, not here.
"""
from __future__ import annotations
import argparse

import load as _load


def top_cells(lib, by="polygons", n=5):
    """The n cells with the most polygons (by='polygons') or vertices (by='vertices'), largest first."""
    key = (lambda info: info.n_polygons) if by == "polygons" else (lambda info: info.n_vertices)
    ranked = sorted(lib.cells.values(), key=key, reverse=True)
    return [(info.name, key(info)) for info in ranked[:n]]


def layer_ranking(lib):
    """Per-layer (polygons, vertices) totals, busiest layer first."""
    per_layer = {}
    for info in lib.cells.values():
        for layer, c in info.polys_by_layer.items():
            per_layer.setdefault(layer, [0, 0])[0] += c
        for layer, v in info.verts_by_layer.items():
            per_layer.setdefault(layer, [0, 0])[1] += v
    rows = [(layer, pv[0], pv[1]) for layer, pv in per_layer.items()]
    return sorted(rows, key=lambda r: r[1], reverse=True)


def complexity(lib):
    """Average vertices per polygon across the library (a 4 means everything is rectangles)."""
    polys = sum(info.n_polygons for info in lib.cells.values())
    verts = sum(info.n_vertices for info in lib.cells.values())
    return {"polygons": polys, "vertices": verts,
            "avg_vertices_per_polygon": (verts / polys) if polys else 0.0}


def _build_lib():
    import gdstk
    lib = gdstk.Library("ext")
    a = lib.new_cell("cellA")
    for i in range(3):
        a.add(gdstk.rectangle((i, 0), (i + 1, 1), layer=1, datatype=0))   # 3 rects on (1,0)
    b = lib.new_cell("cellB")
    b.add(gdstk.rectangle((0, 0), (1, 1), layer=2, datatype=0))           # 1 rect on (2,0)
    top = lib.new_cell("top")
    top.add(gdstk.Reference(a, (0, 0)))
    top.add(gdstk.Reference(b, (5, 0)))
    return lib


def _validate():
    lib = _load.from_gdstk_library(_build_lib())

    tc = top_cells(lib, by="polygons", n=3)
    ok_top = tc[0] == ("cellA", 3) and ("cellB", 1) in tc and ("top", 0) in tc

    lr = layer_ranking(lib)
    ok_layers = lr[0] == ((1, 0), 3, 12) and ((2, 0), 1, 4) in lr

    cx = complexity(lib)
    ok_cx = cx["polygons"] == 4 and cx["vertices"] == 16 and abs(cx["avg_vertices_per_polygon"] - 4.0) < 1e-9

    for label, cond in [("top cells by polygons", ok_top), ("busiest layer first", ok_layers),
                        ("avg vertices per polygon", ok_cx)]:
        print(f"[{label}]  {'PASS' if cond else 'FAIL'}")
    print("RESULT:", "PASS" if all([ok_top, ok_layers, ok_cx]) else "FAIL")


def main():
    ap = argparse.ArgumentParser(description="extremes and rankings over the count metrics")
    ap.add_argument("--validate", action="store_true")
    ap.parse_args(); _validate()


if __name__ == "__main__":
    main()
