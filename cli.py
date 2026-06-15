"""Command-line entry point: compute the metrics for a GDS layout and write the report card.

    python cli.py layout.gds [-o out_dir] [--top 10]

Writes report.json, report.md, and layers.png. A gdsfactory Component can be measured through the Python API:
report.build(load.from_component(component)).
"""
from __future__ import annotations
import argparse
import os

import load
import report


def run(source, out_dir=".", top_n=5):
    """Measure a GDS file (or a gdsfactory Component) and write report.json, report.md, and layers.png."""
    if isinstance(source, str):
        if not os.path.exists(source):
            raise SystemExit(f"gdsstats: layout file not found: {source}")
        lib = load.from_gds(source)
    else:
        lib = load.from_component(source)
    rep = report.build(lib, top_n=top_n)

    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "report.json")
    md_path = os.path.join(out_dir, "report.md")
    fig_path = os.path.join(out_dir, "layers.png")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(report.to_json(rep))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report.to_markdown(rep))
    if rep["layers"]:
        report.figure(rep, fig_path)
    else:
        fig_path = None
    return {"json": json_path, "markdown": md_path, "figure": fig_path,
            "cells": rep["totals"]["cells"]}


def _validate():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        gds = os.path.join(d, "demo.gds")
        load._build_demo_library().write_gds(gds)
        out = run(gds, os.path.join(d, "out"))
        ok_md = os.path.exists(out["markdown"]) and os.path.getsize(out["markdown"]) > 0
        ok_json = os.path.exists(out["json"]) and os.path.getsize(out["json"]) > 0
        ok_fig = out["figure"] is not None and os.path.exists(out["figure"])
        md = open(out["markdown"], encoding="utf-8").read()
        ok_content = "# gdsstats" in md and "reuse factor" in md and out["cells"] == 2

    for label, cond in [("report.md written", ok_md), ("report.json written", ok_json),
                        ("layers.png written", ok_fig), ("metrics reported", ok_content)]:
        print(f"[{label}]  {'PASS' if cond else 'FAIL'}")
    print("RESULT:", "PASS" if all([ok_md, ok_json, ok_fig, ok_content]) else "FAIL")


def main():
    ap = argparse.ArgumentParser(description="gdsstats - a layout metrics report card")
    ap.add_argument("layout", nargs="?", help="GDS layout file")
    ap.add_argument("-o", "--out", default=".", help="output directory")
    ap.add_argument("--top", type=int, default=5, help="how many top cells to list")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.validate:
        _validate(); return
    if not args.layout:
        ap.error("provide a GDS layout file, or --validate")
    out = run(args.layout, args.out, top_n=args.top)
    print(f"wrote {out['markdown']}, {out['json']}, and the layer chart ({out['cells']} cells)")


if __name__ == "__main__":
    main()
