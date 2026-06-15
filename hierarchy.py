"""Hierarchy metrics: how deep the cell tree nests, how each cell is reused, and what a full flatten would cost.

The flatten cost is the number of polygons the layout would have if every reference were replaced by a copy of
its geometry, counting array repetitions. Comparing it to the raw definition count gives a reuse factor: a
hierarchy that arrays one cell a thousand times has a small definition but a large flatten cost, and the ratio
shows how much the hierarchy is buying. Recursion is memoised and guards against reference cycles.
"""
from __future__ import annotations
import argparse

import load as _load


def depths(lib):
    """Return {cell: nesting depth}, where a leaf is 0 and a parent is 1 + its deepest child."""
    memo = {}

    def d(name, stack):
        if name in memo:
            return memo[name]
        info = lib.cells.get(name)
        if info is None or not info.refs or name in stack:
            return 0
        best = 1 + max(d(child, stack | {name}) for child, _ in info.refs)
        memo[name] = best
        return best

    return {n: d(n, frozenset()) for n in lib.cells}


def flatten_polygons(lib, name, memo=None):
    """Polygons after fully flattening `name`, counting array copies. Memoised across calls if `memo` is given."""
    memo = memo if memo is not None else {}

    def f(n, stack):
        if n in memo:
            return memo[n]
        info = lib.cells.get(n)
        if info is None:
            return 0
        if n in stack:
            return info.n_polygons
        total = info.n_polygons + sum(copies * f(child, stack | {n}) for child, copies in info.refs)
        memo[n] = total
        return total

    return f(name, frozenset())


def fan(lib):
    """Per cell: fan_in (distinct parents), child_cells (reference statements), instances (placed copies)."""
    parents = {}
    for name, info in lib.cells.items():
        for child, _ in info.refs:
            parents.setdefault(child, set()).add(name)
    return {name: {"fan_in": len(parents.get(name, ())), "child_cells": len(info.refs),
                   "instances": sum(c for _, c in info.refs)}
            for name, info in lib.cells.items()}


def summary(lib):
    """Library-wide hierarchy metrics: max depth, raw vs flattened polygons, and the reuse factor."""
    dd = depths(lib)
    tops = lib.top or list(lib.cells)
    memo = {}
    flat = sum(flatten_polygons(lib, t, memo) for t in tops)
    raw = sum(c.n_polygons for c in lib.cells.values())
    return {"max_depth": max((dd[t] for t in tops), default=0), "raw_polygons": raw,
            "flatten_polygons": flat, "reuse_factor": (flat / raw) if raw else 1.0}


def _validate():
    lib = _load.from_gdstk_library(_load._build_demo_library())

    dd = depths(lib)
    ok_depth = dd["leaf"] == 0 and dd["top"] == 1

    memo = {}
    ok_flat = flatten_polygons(lib, "leaf", memo) == 1 and flatten_polygons(lib, "top", memo) == 7

    s = summary(lib)
    ok_summary = (s["max_depth"] == 1 and s["raw_polygons"] == 2
                  and s["flatten_polygons"] == 7 and abs(s["reuse_factor"] - 3.5) < 1e-9)

    fn = fan(lib)
    ok_fan = (fn["leaf"]["fan_in"] == 1 and fn["top"]["instances"] == 6
              and fn["top"]["child_cells"] == 1 and fn["leaf"]["instances"] == 0)

    for label, cond in [("depths", ok_depth), ("flatten cost (top = 1 + 6*1 = 7)", ok_flat),
                        ("summary + reuse 3.5", ok_summary), ("fan in/out", ok_fan)]:
        print(f"[{label}]  {'PASS' if cond else 'FAIL'}")
    print("RESULT:", "PASS" if all([ok_depth, ok_flat, ok_summary, ok_fan]) else "FAIL")


def main():
    ap = argparse.ArgumentParser(description="hierarchy metrics: depth, reuse, flatten cost")
    ap.add_argument("--validate", action="store_true")
    ap.parse_args(); _validate()


if __name__ == "__main__":
    main()
