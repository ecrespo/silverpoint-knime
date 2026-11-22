"""KN-REQ-001, KN-Art. 2, KN-REQ-009 (KN-T-07): the extension as KNIME loads it, offline."""

import importlib.util
import re
import socket
import subprocess
import sys
import tomllib

import knime.extension.nodes as kn
import silverpoint
import yaml
from conftest import BINDABLE, ROOT


def test_extension_module_registers_every_node():
    spec = importlib.util.spec_from_file_location("extension", ROOT / "src" / "extension.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert {c["slug"] for c in BINDABLE} <= set(kn._nodes)
    assert (ROOT / "icons" / "silverpoint.png").read_bytes()[1:4] == b"PNG"


def test_manifest_points_at_the_module_and_the_environment():
    manifest = yaml.safe_load((ROOT / "knime.yml").read_text())
    assert manifest["extension_module"] == "src/extension"
    assert manifest["pixi_toml_path"] == "pixi.toml"
    # KN-T-08: the keys KNIME's bundler (knime-extension-bundling 5.9) refuses to build without.
    for key in ("name", "author", "description", "group_id", "version"):
        assert manifest.get(key), key
    assert (
        str(manifest["version"]) == tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    )


def test_pixi_lock_is_one_the_bundler_reads():
    """KN-T-08: knime-extension-bundling 5.9 runs pixi 0.47, which reads lock files up to version 6,
    and the lock holds the pinned silverpoint."""
    lock = yaml.safe_load((ROOT / "pixi.lock").read_text())
    assert lock["version"] <= 6
    assert f"silverpoint-{silverpoint.__version__}-py3-none-any.whl" in (ROOT / "pixi.lock").read_text()


def test_one_version_of_one_line():
    """H-2, KN-DD-03: the bundled environment, the development pin, the installed package, the engine
    and the generated nodes name one silverpoint version; the README names its line."""
    from silverpoint_knime import nodes

    pixi = tomllib.loads((ROOT / "pixi.toml").read_text())["pypi-dependencies"]["silverpoint"]
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    dev = next(d for d in deps if d.startswith("silverpoint"))
    version = silverpoint.__version__
    assert pixi == dev.removeprefix("silverpoint") == f"=={version}"
    # A post-release (0.11.0.post1) is the package's; the engine it vendors keeps the release's version.
    engine = re.match(r"\d+\.\d+\.\d+", version).group(0)
    assert silverpoint.SILVERPOINT_VERSION == nodes.ENGINE_VERSION == engine
    line = ".".join(version.split(".")[:2])
    assert re.search(rf"silverpoint {re.escape(line)}\b", (ROOT / "README.md").read_text())


def test_execution_makes_no_network_call(monkeypatch):
    """KN-Art. 2: a node's execute runs with sockets forbidden (Node runs as a child process)."""
    import knime.extension as knext
    import knime.extension.testing as ktest
    import pandas as pd

    from silverpoint_knime import nodes

    def refuse(*args, **kwargs):
        raise AssertionError("network call during execution")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    node = nodes.NODES["bar-chart"]()
    node.role_x, node.role_value = "team", "wins"
    image, view = node.execute(
        ktest.TestingExecutionContext(), knext.Table.from_pandas(pd.DataFrame({"team": ["A"], "wins": [1]}))
    )
    assert "data-sp-embed" in view.html


def test_engine_matches_its_integrity():
    """H-2: the engine the package carries is the one the hosts kit's integrity.json names."""
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "conformance.py"), "--integrity"],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stdout + out.stderr
    assert "silverpoint-embed.full.mjs: sha384 ok" in out.stdout


def test_conformance_kit_in_the_environment():
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "conformance.py")], capture_output=True, text=True
    )
    assert out.returncode == 0, out.stdout + out.stderr
    assert "0 failed" in out.stdout
