"""Load a GDS file or a gdsfactory Component into the small hierarchy model the metrics run on: per cell, the
polygon and vertex counts by layer, the label count, and the references it makes (child cell and how many
copies). The metrics work on this model, so they do not depend on the gdsfactory version.

A GDS file and a Component are read best-effort through gdstk; a library constructed directly with gdstk is the
robust path used in the tests.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, field


@dataclass
class CellInfo:
    name: str
    polys_by_layer: dict = field(default_factory=dict)     # {(layer, datatype): polygon count}
    verts_by_layer: dict = field(default_factory=dict)     # {(layer, datatype): vertex count}
    n_labels: int = 0
    refs: list = field(default_factory=list)               # [(child_name, n_copies)]

    @property
    def n_polygons(self):
        return sum(self.polys_by_layer.values())

    @property
    def n_vertices(self):
        return sum(self.verts_by_layer.values())


@dataclass
class Library:
    cells: dict = field(default_factory=dict)              # {name: CellInfo}
    top: list = field(default_factory=list)                # top-level cell names


def _ref_copies(ref):
    """Number of placed copies of a reference, counting array repetitions."""
    rep = getattr(ref, "repetition", None)
    if rep is None:
        return 1
    rows = getattr(rep, "rows", None)
    cols = getattr(rep, "columns", None)
    if rows and cols:
        return int(rows) * int(cols)
    for attr in ("offsets", "x_offsets", "y_offsets"):
        off = getattr(rep, attr, None)
        if off is not None:
            return len(off) + 1
    return 1


def _cell_info(cell):
    info = CellInfo(name=cell.name)
    for poly in cell.polygons:
        key = (int(poly.layer), int(poly.datatype))
        info.polys_by_layer[key] = info.polys_by_layer.get(key, 0) + 1
        info.verts_by_layer[key] = info.verts_by_layer.get(key, 0) + len(poly.points)
    info.n_labels = len(cell.labels)
    for ref in cell.references:
        child = ref.cell.name if hasattr(ref.cell, "name") else str(ref.cell)
        info.refs.append((child, _ref_copies(ref)))
    return info


def from_gdstk_library(lib):
    cells = {c.name: _cell_info(c) for c in lib.cells}
    top = [c.name for c in lib.top_level()] if hasattr(lib, "top_level") else []
    return Library(cells, top)


def from_gds(path):
    import gdstk
    return from_gdstk_library(gdstk.read_gds(path))


def from_component(component):
    """Best-effort: use the Component's gdstk library if present, else write a temporary GDS and read it."""
    cell = getattr(component, "_cell", None)
    if cell is not None and hasattr(cell, "polygons"):
        lib = cell.library if getattr(cell, "library", None) is not None else None
        if lib is not None:
            return from_gdstk_library(lib)
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "c.gds")
        component.write_gds(path)
        return from_gds(path)


def _build_demo_library():
    """A 2-cell library: a leaf with one rectangle, and a top that arrays it 2x3 plus its own rectangle."""
    import gdstk
    lib = gdstk.Library("demo")
    leaf = lib.new_cell("leaf")
    leaf.add(gdstk.rectangle((0, 0), (1, 1), layer=1, datatype=0))
    leaf.add(gdstk.Label("p", (0.5, 0.5)))
    top = lib.new_cell("top")
    top.add(gdstk.Reference(leaf, (0, 0), columns=3, rows=2, spacing=(2, 2)))
    top.add(gdstk.rectangle((0, 0), (5, 5), layer=2, datatype=0))
    return lib


def _validate():
    lib = from_gdstk_library(_build_demo_library())

    ok_cells = set(lib.cells) == {"leaf", "top"}
    ok_top = lib.top == ["top"]
    leaf = lib.cells["leaf"]
    ok_leaf = leaf.polys_by_layer == {(1, 0): 1} and leaf.verts_by_layer == {(1, 0): 4} and leaf.n_labels == 1
    top = lib.cells["top"]
    ok_top_polys = top.polys_by_layer == {(2, 0): 1}
    ok_refs = top.refs == [("leaf", 6)]

    for label, cond in [("cells loaded", ok_cells), ("top cell", ok_top), ("leaf polys/verts/labels", ok_leaf),
                        ("top polygon", ok_top_polys), ("array reference 2x3 = 6", ok_refs)]:
        print(f"[{label}]  {'PASS' if cond else 'FAIL'}")
    print("RESULT:", "PASS" if all([ok_cells, ok_top, ok_leaf, ok_top_polys, ok_refs]) else "FAIL")


def main():
    ap = argparse.ArgumentParser(description="load a GDS / Component into the gdsstats hierarchy model")
    ap.add_argument("--validate", action="store_true")
    ap.parse_args(); _validate()


if __name__ == "__main__":
    main()
