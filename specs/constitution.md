# `silverpoint-knime` — Constitution

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`), content unchanged.

## Constitution

H-1..H-8, and:

- **KN-Art. 1 — The extension is glue.** Node code SHALL read the table and the dialog, call the
  `silverpoint` Python package and return its output. Binding, reshaping and markup are the
  package's.
- **KN-Art. 2 — Works offline.** The bundled environment SHALL hold everything the nodes need; a
  node SHALL make no network call at execution.

Stack: KNIME's pure-Python extension template; `knime-extension` for the supported Analytics
Platform versions; pixi; `pytest`.

## Identity

| Field | Value |
|---|---|
| **Repository** | `github.com/ecrespo/silverpoint-knime` |
| **Published as** | A zipped KNIME update site on GitHub Releases; KNIME Community Hub later |
| **Licence** | MIT — to confirm against the Hub's publication terms (KN-OQ-1) |
| **Description** | KNIME Analytics Platform extension: view nodes that draw silverpoint charts from a table. |
| **Draws with** | PyPI `silverpoint` (which vendors the standalone file) |
| **Wave** | 3 |
| **Ids** | `KN-REQ-nnn`, `KN-DD-nn`, `KN-T-nn` |
| **Status** | `APPROVED` gate-1 pack, 2026-11-20 (user decision); re-read against the released API in T-328 |
