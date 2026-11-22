# Changelog

## 0.1.0 — 2026-11-22

First release: the extension `io.github.ecrespo.silverpoint` for KNIME Analytics Platform 5.9–5.x.

- 56 view nodes, one per silverpoint chart a table can feed, under **Community › Silverpoint** in 9
  families, generated from the pinned host catalog (KN-REQ-001, H-3).
- Each dialog: a column per role, filtered by the role's type; the chart's options (enum and number
  options checked at configuration); view and appearance settings (ground, substrate, mode, palette);
  every setting controllable by a flow variable (KN-REQ-002, KN-REQ-007).
- Execution: table → `silverpoint` package → a self-contained, accessible HTML view; the package's
  own error messages; a row limit that warns with both counts (KN-REQ-003..005).
- An SVG image port with Node.js 20+; without Node.js it holds a notice and the node warns
  (KN-REQ-006, KN-D1).
- Draws with silverpoint 0.11 (`silverpoint==0.11.0.post1`, engine 0.11.0), verified against
  `integrity.json` and the conformance kit (76/0); no network call at execution (KN-Art. 2).
- Known deviations: KN-D5 (the dialog offers no `names` / `nodes`), KN-D6 (a string role accepts
  number, date and boolean columns). See `specs/tasks.md`.
