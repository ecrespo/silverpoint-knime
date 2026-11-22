"""KN-REQ-009, H-2, H-4: the engine inside the extension's environment — first its standalone files
against the hosts kit's integrity.json (H-2), then the conformance kit: the `silverpoint` package's
vendored module build, run in Node, over the package's pinned conformance.json (H-4).

    uv run python scripts/conformance.py              # integrity, then the kit (needs Node.js)
    uv run python scripts/conformance.py --integrity  # integrity only
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import sys

import silverpoint

RUNNER = """
import * as sp from %s;
import { readFileSync } from 'node:fs';
const cases = JSON.parse(readFileSync(%s, 'utf8'));
const r = await sp.conformance((spec) => sp.renderToSVG(spec).value.svg, undefined, cases);
console.log(JSON.stringify({ version: cases.version, engine: sp.version, passed: r.passed, failed: r.failed.map((f) => f.name) }));
"""


def integrity() -> bool:
    """H-2: each standalone file the package carries has the sha384 integrity.json gives it."""
    vendor = silverpoint.static_path()
    expected = json.loads((vendor / "integrity.json").read_text(encoding="utf-8"))
    carried = sorted(p.name for p in vendor.glob("silverpoint-embed*.*js"))
    ok = bool(carried)
    for name in carried:
        digest = hashlib.sha384((vendor / name).read_bytes()).digest()
        actual = "sha384-" + base64.b64encode(digest).decode("ascii")
        good = expected.get(name) == actual
        ok = ok and good
        print(f"{name}: sha384 {'ok' if good else 'differs from integrity.json'}")
    return ok


def main() -> int:
    if not integrity():
        print(f"the engine in silverpoint {silverpoint.__version__} is not the one integrity.json names")
        return 1
    if "--integrity" in sys.argv:
        return 0
    node = shutil.which("node")
    if node is None:
        print("Node.js 20+ is needed to run the conformance kit")
        return 1
    vendor = silverpoint.static_path()
    code = RUNNER % (
        json.dumps((vendor / "silverpoint-embed.full.mjs").as_uri()),
        json.dumps(str(vendor / "conformance.json")),
    )
    out = json.loads(
        subprocess.run(
            [node, "--input-type=module", "-e", code], capture_output=True, text=True, check=True
        ).stdout
    )
    print(
        f"conformance {out['version']} (silverpoint {silverpoint.__version__}, engine {out['engine']}): "
        f"{out['passed']} passed, {len(out['failed'])} failed"
    )
    for name in out["failed"]:
        print("  failed:", name)
    return 0 if not out["failed"] and out["engine"] == out["version"] else 1


if __name__ == "__main__":
    sys.exit(main())
