# `silverpoint-knime` — Technical design

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`), content unchanged.

## Design decisions

- **KN-DD-01 — One node per chart, generated.** KNIME's own views are one node per chart, and a
  static dialog with a column selector per role is what users expect. A single node with a chart
  picker would need a dialog that reshapes itself. `scripts/make_nodes.py` writes the node modules
  from the host catalog (H-3). *PoC first (KN-T-02), with three nodes by hand, to confirm that some
  sixty generated nodes load acceptably; the fallback is one node per family.*
- **KN-DD-02 — HTML view always, SVG when possible.** silverpoint DD-069: an SVG needs a JavaScript
  runtime. The view never does.
- **KN-DD-03 — Depend on `silverpoint`, do not vendor again.** The pin (H-2) is the `silverpoint`
  version in `pixi.toml`; the engine arrives inside it.
