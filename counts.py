"""Raw count metrics over the cell definitions: how many cells, reference statements, polygons, vertices, and
labels the library holds, and the polygon and vertex totals per layer. These are definition counts (each cell
counted once); the flattened, placement-aware counts live in hierarchy.py.
"""
from __future__ import annotations
import argparse

import load as _load


def cell_counts(info):
    """Per-cell counts: polygons, vertices, labels, and reference statements."""
    return {"polygons": info.n_polygons, "vertices": info.n_vertices,
            "labels": info.n_labels, "references": len(info.refs)}


def totals(lib):
    """Library-wide definition counts plus a per-layer polygon / vertex breakdown."""
    per_layer = {}
    n_poly = n_vert = n_lab = n_ref = 0
    for info in lib.cells.values():
        n_lab += info.n_labels
        n_ref += len(info.refs)
        for layer, c in info.polys_by_layer.items():
            d = per_layer.setdefault(layer, {"polygons": 0, "vertices": 0})
            d["polygons"] += c
            n_poly += c
        for layer, v in info.verts_by_layer.items():
            per_layer.setdefault(layer, {"polygons": 0, "vertices": 0})["vertices"] += v
            n_vert += v
    return {"cells": len(lib.cells), "references": n_ref, "polygons": n_poly,
            "vertices": n_vert, "labels": n_lab, "per_layer": per_layer}


def _validate():
    lib = _load.from_gdstk_library(_load._build_demo_library())

    t = totals(lib)
    ok_cells = t["cells"] == 2
    ok_refs = t["references"] == 1                          # one reference statement (the 2x3 array)
    ok_poly = t["polygons"] == 2 and t["vertices"] == 8 and t["labels"] == 1
    ok_layers = (t["per_layer"][(1, 0)] == {"polygons": 1, "vertices": 4}
                 and t["per_layer"][(2, 0)] == {"polygons": 1, "vertices": 4})

    leaf = cell_counts(lib.cells["leaf"])
    ok_cell = leaf == {"polygons": 1, "vertices": 4, "labels": 1, "references": 0}

    for label, cond in [("cell total", ok_cells), ("reference statements", ok_refs),
                        ("polygon/vertex/label totals", ok_poly), ("per-layer breakdown", ok_layers),
                        ("per-cell counts", ok_cell)]:
        print(f"[{label}]  {'PASS' if cond else 'FAIL'}")
    print("RESULT:", "PASS" if all([ok_cells, ok_refs, ok_poly, ok_layers, ok_cell]) else "FAIL")


def main():
    ap = argparse.ArgumentParser(description="raw count metrics over the cell definitions")
    ap.add_argument("--validate", action="store_true")
    ap.parse_args(); _validate()


if __name__ == "__main__":
    main()
