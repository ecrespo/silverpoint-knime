# `silverpoint-knime` — Tasks

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`), content unchanged.

## Tasks

- [x] **KN-T-01** Split this pack into `specs/`; `CLAUDE.md`; create from KNIME's Python extension template. Stop for review. *H-7*
- [ ] **KN-T-02** PoC: three hand-written nodes in a local Analytics Platform — the HTML view renders and reads by keyboard, the dialog's column filters, load time, the image port with and without Node. Record the supported platform versions and the view API used. `specs/poc.md`. *KN-DD-01, KN-DD-02*
- [x] **KN-T-03** `scripts/make_nodes.py` and `--check`. *KN-REQ-001, KN-REQ-002, H-3*
- [x] **KN-T-04** Execution: table → `silverpoint` → view; errors; the row limit. *KN-REQ-003, KN-REQ-004, KN-REQ-005*
- [x] **KN-T-05** The image port and the runtime preference. *KN-REQ-006*
- [x] **KN-T-06** Flow variables; the example workflow. *KN-REQ-007, KN-REQ-008*
- [x] **KN-T-07** CI: the bundled environment, the conformance check, every node against its demo. *KN-REQ-009, H-4*
- [ ] **KN-T-08** Bundle the update site; README; release `0.1.0`; read the Community Hub's requirements and decide on publication. *KN-OQ-1*

## Open questions

- **KN-OQ-1** Community Hub: licence and review requirements for a community extension.
- **KN-OQ-2** Whether the HTML view is shown in KNIME Data Apps on Business Hub as it is locally.

## Bootstrap prompt

````text
This repository will ship a KNIME Analytics Platform extension whose nodes draw silverpoint charts through the `silverpoint` Python package. Its design is in specs/spec-pack.md, written in the silverpoint repository (~/WebstormProjects/silverpoint/changes/feature-007-bi-hosts). Read the pack, that folder's README.md and repositories/README.md §3, the silverpoint-python pack beside it, and KNIME's guide to pure-Python node extensions.

Do KN-T-01 only: split the pack into specs/ without changing its content, write CLAUDE.md, and create the extension from KNIME's template with its example node untouched. Show me the tree and knime.yml, then stop. KN-T-02 is a PoC I run with you in KNIME.
````

## Implementation ledger (2026-11-21)

Built test-first with KNIME's own Python API (knime-extension 5.9.0 and its testing contexts) and the
`silverpoint` package (0.10.1, the sibling checkout). Local run: `ruff check`, `ruff format --check`,
`make_nodes.py --check`, `conformance.py` (76/0 through the package's vendored engine, in Node),
`pytest` — 71 passed: every one of the 56 nodes configured and executed on its catalog demo table,
the dialog's parameters, errors, the row limit, the image port with and without Node.js, no socket
opened during execution. Mutation check: drawing all rows past the limit fails the row-limit test.

### Deviations — to review

- **KN-D1 — no inactive port**: knime-extension 5.9 has none, so without Node.js the image port holds
  a notice SVG and the node warns (KN-REQ-006).
- **KN-D2 — the Node.js runtime is a node setting** (*Node.js executable*, advanced), not an extension
  preference: Python extensions have no preference page. It reaches the package as `SILVERPOINT_NODE`,
  which `silverpoint` 0.10.1 now honours.
- **KN-D3 — development uses `uv`** with KNIME's API extracted from its conda package
  (`scripts/knime_api.py`, digest pinned); the bundled environment is still `pixi.toml` (KN-DD-03).
- **KN-D4 — `silverpoint` from the sibling checkout** (`tool.uv.sources`) until its first PyPI upload.
  *Resolved 2026-11-22: `silverpoint==0.11.0` from PyPI.*

### Open

- KN-T-02's AP half and KN-T-06's example workflow (`.knwf`, authored in the AP; the dataset is in
  `demo/`), KN-T-08 (the update site is built by CI's `bundle` job, not run here; the Community Hub
  decision, KN-OQ-1). KN-OQ-2 untested.


## Ledger — the 0.11 line (2026-11-22)

Following silverpoint 0.11 (H-2's four steps): bump → regenerate → kit → release.

- **Pin**: `silverpoint==0.11.0` from PyPI in `pyproject.toml` and `pixi.toml` (KN-D4 resolved); host
  catalog 0.11.0 regenerates the 56 nodes unchanged but for the version. silverpoint 0.11.1 changed
  only the MCP server's pin (no engine, catalog or kit change for hosts), so the Python package's
  0.11.0 is the line's engine. A test now holds the pixi pin, the uv pin, the package, the engine and
  `nodes.ENGINE_VERSION` to one version, and the README to its line (H-2).
- **Integrity** (H-2): `scripts/conformance.py` checks each vendored standalone file's sha384 against
  `integrity.json` before running the kit (`--integrity` alone); a test runs it.
- **`demo.options`** (pack's *As built in 0.11.0*): KN-REQ-009 sets each demo's options the dialog
  holds (`metric`, `delta`, `axis`, `period`) and checks they reach the spec.
- **Fix — number options**: a number option's text field reached the spec as text (`"12"`, not `12`)
  for all 24 number options. The generator now writes `number_options`; the node reads them as numbers
  and fails configuration on text that is not one (KN-REQ-004).
- **Fix — bundling** (KN-T-08), found by running the `bundle` job's command locally: `knime.yml` lacked
  `group_id` (the bundler refuses it; now `io.github.ecrespo`, extension id
  `io.github.ecrespo.silverpoint`); `pixi run -e build build dest=…` passed `dest=…` literally as the
  path (now positional); the bundler runs its own pixi 0.47, which reads lock files up to v6, so
  `pixi.lock` is written with pixi 0.47 and committed, and CI pins `pixi-version: v0.47.0`, `locked`;
  the environment did not match KNIME's base one (`aws-c-auth` 0.10 vs 0.9), so `pixi.toml` adds
  `knime-python-versions = "5.9.*"`, KNIME's pins for 5.9 (pandas 2.0.3, pyarrow 21, …); the `build`
  feature had resolved Maven 3.10, under which the bundler's Tycho 4.0.7 fails, so it pins Maven 3.9 and
  Python 3.11; the default update sites (`latest`, KNIME 5.11) do not resolve against a 5.9 extension,
  so the task passes `--update-sites-version 5.9`; `--excluded-files` keeps tests, specs and scripts out
  of the plugin. Local run: the update site builds (579 MB: the plugin, the feature, the environment for
  linux-64, win-64, osx-64, osx-arm64); the plugin carries `src/`, `icons/`, `demo/`, the manifests and
  `LICENSE`. Not yet installed into an Analytics Platform (KN-T-02's AP half).
- **Fix — binding errors are the package's** (KN-REQ-004, KN-Art. 1): configuration binds the roles to
  the schema's columns through `silverpoint.Chart` (no rows) and fails with its `SpecError` message
  (`bar-chart needs the role "value"…`, `the data has no column "losses"…`) instead of the node's own
  wording; execution lets the package bind the rows. An empty table reaches the package in column form,
  which keeps the column names (an empty DataFrame loses them: "the data has no column…"), so a scalar
  chart fails with the package's message; any other chart fails on the empty table.
- **The bundled environment runs the tests** (KN-REQ-009, H-4): `pixi run -e test conformance` and
  `pixi run -e test test` (a `test` environment in the default solve group, with Node.js), CI's
  `bundled` job. Local run: Python 3.11.13, pandas 2.0.3, pyarrow 21, Node 24 — integrity ok,
  conformance 76/0, 75 passed, 3 xfailed (KN-D5). The generation check (H-3) stays in the uv job:
  `knime-python-versions` pins ruff 0.13, and `make_nodes.py` formats with uv's.

### Deviations — to review

- **KN-D5 — demo options without a dialog parameter**: `names` (dumbbell, slope) and `nodes` (network)
  are in `demo.options` but are not catalog options. `specFromTable` accepts them; `silverpoint`
  (Python) 0.11.0 raises `SpecError` ("has no option"). The nodes cannot pass them; those three demos
  run without them. A strict `xfail` test shows the gap and fails once the package accepts them — then
  the generator can offer them. Upstream: silverpoint-python.
  *Upstream half resolved 2026-11-22: silverpoint-python#2, fixed in `0.11.0.post1` (the package takes
  every prop `specFromTable` takes). Pin moved to `0.11.0.post1` (engine still 0.11.0), the `xfail`
  removed: the test now passes as a regression test. Open half: the nodes still offer no `names` /
  `nodes` parameter, as the host catalog does not declare them (H-3).*
- **KN-D6 — a string role lists every column**: the catalog's `string` roles are labels (the x of a
  line, the category of a bar); the package and `specFromTable` bind a number or a date there as it is.
  Listing only text columns hid the common case (an hour, a year, an id read as a number by the CSV
  Reader: `demo/hits-per-hour.csv`'s `hour`). Number, date and boolean roles keep their filter.
  KN-REQ-002 reads "filtered by the role's data type"; to review.

## The example workflow (2026-11-22)

- **KN-T-06 / KN-REQ-008**: `workflows_examples/silverpoint-example/` (and its `.knwf`), written by
  `scripts/make_example_workflow.py` from the generated nodes' own parameters: a CSV Reader on the
  bundled `data/hits-per-hour.csv` (`hour` as String) feeding the Line (secondary = baseline), Area
  (sanguine palette) and Step (cyanotype ground) nodes. Imported into KNIME AP 5.12.0 and executed:
  the three views draw. The Batch Executor is not installed in that AP, so the run was in the GUI.
- **Release 0.1.0** (KN-T-08): tag `v0.1.0` on `main`, the update site zip (silverpoint
  0.11.0.post1) attached to the GitHub release. Community Hub: submission by e-mail to
  community-contributions@knime.com (experimental first; trusted needs testflows per node).

