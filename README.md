# gdsstats - a layout metrics report card for gdsfactory

![license](https://img.shields.io/badge/license-MIT-blue.svg)

`gdsstats` reads a GDS layout (or a gdsfactory `Component`) and prints a one-page report card: how many cells,
references, polygons, vertices, and labels it holds, how the cell tree nests, which cells and layers dominate,
and what a full flatten would cost. It answers "what is in this layout, and is the hierarchy buying anything"
at a glance, which makes it useful as a CI artifact attached to every layout change.

The headline metric is the **reuse factor**: the polygon count after a full flatten divided by the raw
definition count. A layout that arrays one cell a thousand times has a tiny definition but a huge flatten cost,
and the ratio shows how much the hierarchy is saving (and warns when a flatten would explode).

## Install

```
pip install -r requirements.txt
```

`gdstk` and `matplotlib` are the dependencies. `gdsfactory` is optional and used only to read a `Component`; a
GDS file works without it.

## Use

From the command line, on a GDS file:

```
python cli.py layout.gds -o out/ --top 10
```

It writes `report.json`, `report.md`, and `layers.png` (a per-layer polygon bar chart).

From Python, on a GDS or a gdsfactory `Component`:

```python
import load, report

rep = report.build(load.from_gds("layout.gds"))
print(report.to_markdown(rep))
report.figure(rep, "layers.png")

# from a gdsfactory Component:
# report.build(load.from_component(component))
```

A runnable example is in `examples/quickstart.py`.

## Sample report

```
# gdsstats

## Totals

- cells: 2
- references: 1
- polygons: 3
- vertices: 12
- labels: 0
- avg vertices per polygon: 4.00

## Hierarchy

- max depth: 1
- polygons flattened: 51
- reuse factor (flattened / raw): 17.00

## Top cells by polygons

- leaf: 2
- top: 1

## Layers

| layer | polygons | vertices |
|---|---|---|
| (1, 0) | 1 | 4 |
| (2, 0) | 1 | 4 |
| (10, 0) | 1 | 4 |
```

## Metrics

| Metric | Where |
|---|---|
| cell / reference / polygon / vertex / label counts, per layer | `counts.py` |
| max hierarchy depth, fan-in / fan-out, flatten cost, reuse factor | `hierarchy.py` |
| top cells by polygons / vertices, busiest layers, avg vertices per polygon | `extremes.py` |

## Modules

| Module | What it does |
|---|---|
| `load.py` | read a GDS / Component into a per-cell count model (polygons, vertices, labels, references) |
| `counts.py` | per-cell and library totals, with a per-layer breakdown |
| `hierarchy.py` | depth, reuse, and the flatten cost (array-aware, memoised) |
| `extremes.py` | the heaviest cells and busiest layers |
| `report.py` | JSON, Markdown, and a per-layer bar chart |
| `cli.py` | `python cli.py layout.gds` end to end |

## Test

```
python run_checks.py validate <name>   # one module's self-check
python run_checks.py validate-all      # every module's self-check
python run_checks.py suite             # pytest tests/
```

Every metric is validated against a constructed library with known counts: a leaf arrayed 2x3 gives a flatten
cost of `1 + 6*1 = 7`, a reuse factor of `3.5`, and exact per-layer polygon and vertex totals.

## Scope

gdsstats reports structural and complexity metrics. It does not measure filled area or density (that is a
geometry question for a density tool) and it is not a DRC. The metrics pass is cheap (a few milliseconds even
for thousands of cells); the cost is dominated by reading the GDS.
