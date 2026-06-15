"""Test suite for gdsstats."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json

import load
import counts
import hierarchy
import extremes
import report
import cli


def test_load_demo():
    lib = load.from_gdstk_library(load._build_demo_library())
    assert set(lib.cells) == {"leaf", "top"}
    assert lib.top == ["top"]
    leaf = lib.cells["leaf"]
    assert leaf.polys_by_layer == {(1, 0): 1} and leaf.verts_by_layer == {(1, 0): 4}
    assert leaf.n_labels == 1 and leaf.n_polygons == 1 and leaf.n_vertices == 4
    assert lib.cells["top"].refs == [("leaf", 6)]


def test_counts_totals():
    lib = load.from_gdstk_library(load._build_demo_library())
    t = counts.totals(lib)
    assert t["cells"] == 2 and t["references"] == 1
    assert t["polygons"] == 2 and t["vertices"] == 8 and t["labels"] == 1
    assert t["per_layer"][(1, 0)] == {"polygons": 1, "vertices": 4}
    assert counts.cell_counts(lib.cells["leaf"])["polygons"] == 1


def test_hierarchy_summary():
    lib = load.from_gdstk_library(load._build_demo_library())
    assert hierarchy.depths(lib) == {"leaf": 0, "top": 1}
    assert hierarchy.flatten_polygons(lib, "top") == 7
    s = hierarchy.summary(lib)
    assert s["max_depth"] == 1 and s["raw_polygons"] == 2 and s["flatten_polygons"] == 7
    assert abs(s["reuse_factor"] - 3.5) < 1e-9
    assert hierarchy.fan(lib)["leaf"]["fan_in"] == 1


def test_extremes():
    lib = load.from_gdstk_library(extremes._build_lib())
    tc = extremes.top_cells(lib, by="polygons", n=3)
    assert tc[0] == ("cellA", 3)
    lr = extremes.layer_ranking(lib)
    assert lr[0] == ((1, 0), 3, 12)
    assert abs(extremes.complexity(lib)["avg_vertices_per_polygon"] - 4.0) < 1e-9


def test_report():
    lib = load.from_gdstk_library(load._build_demo_library())
    rep = report.build(lib)
    assert rep["totals"]["cells"] == 2 and abs(rep["hierarchy"]["reuse_factor"] - 3.5) < 1e-9
    assert isinstance(json.loads(report.to_json(rep)), dict)   # tuple layer keys stringified
    md = report.to_markdown(rep)
    assert "# gdsstats" in md and "reuse factor" in md and "max depth: 1" in md


def test_cli(tmp_path):
    gds = str(tmp_path / "demo.gds")
    load._build_demo_library().write_gds(gds)
    out = cli.run(gds, str(tmp_path / "out"))
    assert os.path.exists(out["markdown"]) and os.path.exists(out["json"])
    assert out["figure"] and os.path.exists(out["figure"])
    assert out["cells"] == 2
    assert "reuse factor" in open(out["markdown"], encoding="utf-8").read()


def test_cli_missing_file(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        cli.run(str(tmp_path / "nope.gds"), str(tmp_path / "out"))


def test_empty_library():
    import gdstk
    lib = load.from_gdstk_library(gdstk.Library("empty"))
    rep = report.build(lib)
    assert rep["totals"]["cells"] == 0 and rep["hierarchy"]["reuse_factor"] == 1.0
    assert rep["layers"] == []
    assert "# gdsstats" in report.to_markdown(rep)


def test_cli_no_layers_skips_figure(tmp_path):
    import gdstk
    lib = gdstk.Library("nopoly")
    a = lib.new_cell("a")
    top = lib.new_cell("t")
    top.add(gdstk.Reference(a, (0, 0)))
    gds = str(tmp_path / "np.gds")
    lib.write_gds(gds)
    out = cli.run(gds, str(tmp_path / "out"))
    assert out["figure"] is None and os.path.exists(out["markdown"])
