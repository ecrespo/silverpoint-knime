# KN-T-02 — findings so far

Exercised with KNIME's own Python API, **knime-extension 5.9.0** (from the `knime` conda channel) and
its `knime.extension.testing` contexts — not yet in a KNIME Analytics Platform.

| Question | Finding |
|---|---|
| View API | `@knext.output_view` + `knext.view_html(html, svg_or_png=svg)`: the HTML must be self-contained, which `Chart.to_html(render="client")` is (the script inlined). With an SVG, the view is report-ready. |
| Image port | `@knext.output_image` with `ImagePortObjectSpec(ImageFormat.SVG)`. The API has **no inactive port**: without Node.js the port holds a notice SVG and the node warns (KN-D1). |
| Column filters | `ColumnParameter(column_filter=…, include_none_column=…)`, `MultiColumnParameter` for multiple roles. |
| Flow variables | every parameter is controllable by a flow variable by default (KN-REQ-007). |
| Generated nodes | 56 nodes in 9 family modules import in about 0.4 s in the test environment; loading time in the AP is the open half. |
| pandas | KNIME 5.x environments carry pandas 2; the testing module refuses pandas 3's string dtype. |

## In the Analytics Platform (2026-11-22)

KNIME Analytics Platform **5.12.0** (Linux x86_64), `/home/ernesto/knime_5.12.0`.

| Step | Finding |
|---|---|
| Install | The local update site (built for 5.9 with `--update-sites-version 5.9`) installs with the p2 director (`-installIU io.github.ecrespo.features.silverpoint.feature.group`): "Overall install request is satisfiable", 65 s. The plugin requires `[5.9.0,6.0.0)`, so 5.9–5.12 resolve it. |
