# `silverpoint-knime` — Prd

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`), content unchanged.

## Scope

**In:** view nodes with a table input, a self-contained HTML view, an optional SVG image output.
**Out:** JavaScript-view nodes written against KNIME's UI extension framework; interactive selection
events back into the workflow; components for Data Apps beyond what a view gives for free.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| KN-REQ-001 | THE EXTENSION SHALL provide one view node per chart of the pinned host catalog whose `binding` is not `none`, named *Silverpoint <Title>*, in a *Silverpoint* category with one sub-category per family, each node generated from the catalog. | MUST |
| KN-REQ-002 | EACH NODE'S dialog SHALL have one column selector per role —filtered by the role's data type, required roles without a "none" choice—, the chart's options, the common view options and the appearance. | MUST |
| KN-REQ-003 | WHEN executed, THE NODE SHALL build the chart with `silverpoint` from the selected columns and return its self-contained HTML document as the node's view. | MUST |
| KN-REQ-004 | IF the table is empty, a required column is unset or binding fails, THEN THE NODE SHALL fail configuration or execution with the package's `SpecError` message. | MUST |
| KN-REQ-005 | IF the table has more rows than the node's *Row limit* (default 10,000), THEN THE NODE SHALL draw the first rows up to the limit and set a node warning with both counts. | MUST |
| KN-REQ-006 | WHERE a Node.js runtime is configured in the extension's preferences or found on `PATH`, THE NODE SHALL also fill an image output port with the chart's SVG, making the view report-ready; otherwise the port SHALL be inactive and the node description SHALL say why. | MUST |
| KN-REQ-007 | THE NODE SHALL expose ground, mode and palette as flow-variable-controllable settings. | SHOULD |
| KN-REQ-008 | THE EXTENSION SHALL ship an example workflow using three nodes on a bundled dataset. | MUST |
| KN-REQ-009 | CI SHALL run the `silverpoint` package's conformance check inside the extension's bundled environment, and execute each generated node's `configure` and `execute` against its demo table. | MUST |
