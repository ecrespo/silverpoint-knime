# silverpoint-knime — context for agents

Read [`specs/constitution.md`](specs/constitution.md) before proposing or writing code. It inherits
H-1..H-8 from silverpoint (`changes/feature-007-bi-hosts/repositories/README.md` §3: one engine, a
pinned line, generated manifests, conformance, nothing lost on the way in, the host's rules, specs as
the source, shown not inferred) and adds:

- **KN-Art. 1 — The extension is glue.** Node code SHALL read the table and the dialog, call the `silverpoint` Python package and return its output. Binding, reshaping and markup are the package's.
- **KN-Art. 2 — Works offline.** The bundled environment SHALL hold everything the nodes need; a node SHALL make no network call at execution.

Draws with: PyPI `silverpoint` (which vendors the standalone file).

Stack: KNIME's pure-Python extension template; `knime-extension` for the supported Analytics Platform versions; pixi; `pytest`.

Specs: `specs/prd.md` (KN-REQ-001..KN-REQ-009), `specs/technical-design.md`, `specs/tasks.md`.
`specs/spec-pack.md` is the pack as written in silverpoint's `changes/feature-007-bi-hosts/repositories/`;
the four files are its split, unchanged.

## Status

Implemented 2026-11-21: KN-T-01, -03, -04, -05, -07 (ledger in `specs/tasks.md`, findings in
`specs/poc.md`). 2026-11-22: the 0.11 line (`silverpoint==0.11.0.post1` from PyPI, engine 0.11.0), the tests in the bundled
environment (`pixi run -e test test`), the update site builds locally (`pixi run -e build build`, pixi
0.47). Open: the Analytics Platform half of KN-T-02, the example workflow (KN-T-06), the release and
the Community Hub decision (KN-T-08, KN-OQ-1); KN-D5: the dialog offers no `names` / `nodes` (not in the host catalog).

Commands: `uv sync`, `uv run python scripts/knime_api.py`, `uv run python scripts/make_nodes.py
--check`, `uv run python scripts/conformance.py`, `uv run pytest`, `uv run ruff check .`.

- `src/silverpoint_knime/nodes/` is written only by `scripts/make_nodes.py`; shared behaviour is in
  `src/silverpoint_knime/base.py` (glue only: KN-Art. 1).

## Working rules

- Test-first; every task and test cites the KN-REQ it implements or verifies (H-7, H-8).
- Every list of charts, roles, options and appearance values is generated from the pinned
  `host-catalog.json`, with a `--check` CI runs (H-3). Nothing in those lists is typed by hand.
- The engine is one pinned version of one silverpoint line, verified against `integrity.json` (H-2);
  the hosts kit is the zip attached to each silverpoint GitHub release.
- Specs and code are written in English.
