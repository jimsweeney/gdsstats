"""Assemble the metrics into a report card: the counts, the hierarchy summary, the heaviest cells, and the
per-layer breakdown, available as a dict, as JSON, and as a Markdown summary, with an optional per-layer
polygon bar chart.
"""
from __future__ import annotations
import argparse
import json

import counts as _counts
import hierarchy as _hierarchy
import extremes as _extremes


def build(lib, top_n=5):
    """Run every metric over a Library and return the combined report card."""
    return {"totals": _counts.totals(lib),
            "hierarchy": _hierarchy.summary(lib),
            "top_cells": _extremes.top_cells(lib, by="polygons", n=top_n),
            "layers": _extremes.layer_ranking(lib),
            "complexity": _extremes.complexity(lib)}


def _stringify_keys(obj):
    """Recursively turn dict keys that are not JSON-native (like (layer, datatype) tuples) into strings."""
    if isinstance(obj, dict):
        return {(str(k) if not isinstance(k, (str, int, float, bool)) and k is not None else k):
                _stringify_keys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_stringify_keys(v) for v in obj]
    return obj


def to_json(report):
    return json.dumps(_stringify_keys(report), indent=2, default=str)


def to_markdown(report):
    t, h, cx = report["totals"], report["hierarchy"], report["complexity"]
    lines = ["# gdsstats", "",
             "## Totals", "",
             f"- cells: {t['cells']}",
             f"- references: {t['references']}",
             f"- polygons: {t['polygons']}",
             f"- vertices: {t['vertices']}",
             f"- labels: {t['labels']}",
             f"- avg vertices per polygon: {cx['avg_vertices_per_polygon']:.2f}",
             "",
             "## Hierarchy", "",
             f"- max depth: {h['max_depth']}",
             f"- polygons flattened: {h['flatten_polygons']}",
             f"- reuse factor (flattened / raw): {h['reuse_factor']:.2f}",
             "",
             "## Top cells by polygons", ""]
    for name, n in report["top_cells"]:
        lines.append(f"- {name}: {n}")
    lines += ["", "## Layers", "", "| layer | polygons | vertices |", "|---|---|---|"]
    for layer, polys, verts in report["layers"]:
        lines.append(f"| {layer} | {polys} | {verts} |")
    return "\n".join(lines)


def figure(report, path):
    """Write a bar chart of per-layer polygon counts to `path`."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = report["layers"]
    labels = [str(layer) for layer, _, _ in rows]
    values = [polys for _, polys, _ in rows]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.bar(range(len(values)), values, color="steelblue")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("polygons"); ax.set_title("polygons per layer")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def _validate():
    import os, tempfile
    import load

    lib = load.from_gdstk_library(load._build_demo_library())
    report = build(lib)

    ok_build = (report["totals"]["cells"] == 2
                and abs(report["hierarchy"]["reuse_factor"] - 3.5) < 1e-9)
    js = to_json(report)
    ok_json = isinstance(json.loads(js), dict)
    md = to_markdown(report)
    ok_md = "# gdsstats" in md and "reuse factor" in md and "## Layers" in md and "max depth: 1" in md

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "layers.png")
        figure(report, p)
        ok_fig = os.path.exists(p) and os.path.getsize(p) > 0

    for label, cond in [("build", ok_build), ("json", ok_json), ("markdown", ok_md),
                        ("figure written", ok_fig)]:
        print(f"[{label}]  {'PASS' if cond else 'FAIL'}")
    print("RESULT:", "PASS" if all([ok_build, ok_json, ok_md, ok_fig]) else "FAIL")


def main():
    ap = argparse.ArgumentParser(description="assemble a layout metrics report card (JSON + Markdown + chart)")
    ap.add_argument("--validate", action="store_true")
    ap.parse_args(); _validate()


if __name__ == "__main__":
    main()
