"""KN-REQ-001, KN-REQ-002, KN-REQ-007, H-3 (KN-T-03): one node per chart, generated."""

import subprocess
import sys

import knime.extension as knext
from conftest import BINDABLE, ROOT

from silverpoint_knime import nodes


def test_one_node_per_bindable_chart_named_and_categorised():
    import knime.extension.nodes as kn

    assert sorted(nodes.NODES) == sorted(c["slug"] for c in BINDABLE)
    line = kn._nodes["line-chart"]
    assert line.name == "Silverpoint Line chart"
    assert line.category == "/community/silverpoint/lines"
    assert nodes.FAMILIES["lines"] == "Lines"


def test_dialog_role_selectors_typed_required_without_none():
    node = type(nodes.NODES["line-chart"]())
    x, value, secondary = node.role_x, node.role_value, node.role_secondary
    assert isinstance(x, knext.ColumnParameter) and x._include_none_column is False
    assert value._include_none_column is False
    assert secondary._include_none_column is True
    assert value._column_filter(knext.Column(knext.double(), "v")) is True
    assert value._column_filter(knext.Column(knext.string(), "s")) is False
    assert x._column_filter(knext.Column(knext.string(), "s")) is True
    # KN-D6: a string role is a label; a number or a date column labels as well (an hour, a year, an id).
    assert x._column_filter(knext.Column(knext.int32(), "hour")) is True
    assert x._column_filter(knext.Column(knext.double(), "year")) is True
    dims = type(nodes.NODES["parallel-coordinates-chart"]()).role_dimensions
    assert isinstance(dims, knext.MultiColumnParameter)


def test_dialog_options_view_and_appearance():
    node = type(nodes.NODES["line-chart"]())
    assert isinstance(node.opt_curve, knext.EnumParameter)
    assert isinstance(node.opt_connect_nulls, knext.BoolParameter)
    for name in ("title", "description", "data_table"):
        assert hasattr(node, f"view_{name}")
    for name in ("ground", "substrate", "mode", "palette"):
        assert isinstance(getattr(node, name), knext.EnumParameter)  # KN-REQ-007: flow-variable controllable


def test_generated_files_are_current():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "make_nodes.py"), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
