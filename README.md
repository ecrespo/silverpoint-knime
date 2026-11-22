# silverpoint for KNIME

KNIME nodes that draw [silverpoint](https://github.com/ecrespo/silverpoint) charts from a table: one
view node per chart (56 of them) under **Community › Silverpoint**, grouped by family. Each node
shows a self-contained, accessible HTML view — keyboard reading, a readout, a tabular alternative —
and, with Node.js 20+, writes the chart as SVG on an image port so the view is report-ready.

Draws with **silverpoint 0.11** (the `silverpoint` Python package 0.11.0.post1 from PyPI, engine 0.11.0, pinned in `pixi.toml`
and `pyproject.toml`; its engine is verified against the hosts kit's `integrity.json`).

## Install

1. Download `silverpoint-knime-<version>-update-site.zip` from the
   [releases](https://github.com/ecrespo/silverpoint-knime/releases).
2. In KNIME Analytics Platform (5.9 or later): *File › Preferences › Install/Update › Available
   Software Sites › Add… › Archive…*, pick the zip.
3. *File › Install KNIME Extensions…*, search for *silverpoint*, install and restart. The first use
   creates the extension's Python environment (offline: everything is in the zip).

## Using a node

1. Drag *Silverpoint Line chart* (or any other) onto the canvas and connect a table.
2. In the dialog, pick a column for each role (*X*, *Value*, …) — each list holds the columns of the
   role's type, and optional roles accept *none* — and set the chart's options, the view (title,
   description, data table) and the appearance (ground, substrate, mode, palette).
3. Execute. The view shows the chart. *Row limit* (advanced, default 10,000) draws the first rows of a
   longer table and warns with both counts. *Node.js executable* (advanced) points at Node.js for the
   SVG port; without Node.js the port holds a notice and the node warns.

Every setting is controllable by a flow variable — ground, mode and palette among them. Nothing is
fetched at execution: the chart's script travels inside the view. `demo/hits-per-hour.csv` is a small
dataset to try the line, area and step charts on.

## Development

```sh
uv sync
uv run python scripts/knime_api.py        # KNIME's Python API, for its testing module
uv run python scripts/make_nodes.py       # the node modules, from silverpoint's host catalog
uv run python scripts/make_nodes.py --check
uv run python scripts/conformance.py      # integrity.json, then the conformance kit (needs Node.js)
uv run pytest                             # every node's configure and execute on its demo table
pixi run -e build build                   # the update site in ./local-update-site, as KNIME bundles it
```

The bundler (knime-extension-bundling 5.9) runs pixi 0.47, which reads lock files up to v6: update
`pixi.lock` with pixi 0.47 (`pixi lock`), as CI does.

Licence: see `LICENSE`.
