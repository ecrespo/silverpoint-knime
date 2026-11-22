"""KN-REQ-003..006, KN-REQ-009, H-4 (KN-T-04, KN-T-05, KN-T-07): configure and execute every node."""

import json
import re
import shutil

import knime.extension as knext
import knime.extension.testing as ktest
import pandas as pd
import pytest
import silverpoint
from conftest import BINDABLE, demo_rows, demo_settings

from silverpoint_knime import nodes

HAS_NODE = shutil.which("node") is not None


def configured(slug, roles, options=None):
    node = nodes.NODES[slug]()
    for role, column in roles.items():
        setattr(node, f"role_{role}", column)
    for name, value in (options or {}).items():
        setattr(node, name, value)
    return node


def schema_of(df):
    return knext.Table.from_pandas(df).schema


def view_props(html):
    """The chart's props as the view carries them (the spec is the embed's JSON payload)."""
    match = re.search(r'<script type="application/json"[^>]*>(.*?)</script>', html, re.S)
    assert match, "the view carries its spec"
    return json.loads(match.group(1))["props"]


@pytest.mark.parametrize("chart", BINDABLE, ids=[c["slug"] for c in BINDABLE])
def test_every_node_runs_on_its_demo(chart):
    """KN-REQ-009 (as built in 0.11.0): configure and execute against the catalog's demo table, with the
    demo's options the dialog holds."""
    df = pd.DataFrame(demo_rows(chart))
    node = configured(chart["slug"], chart["demo"]["roles"])
    settings, _ = demo_settings(chart, node)
    for name, value in settings.items():
        setattr(node, name, value)
    spec = node.configure(ktest.TestingConfigurationContext(), schema_of(df))
    assert spec.format == knext.ImageFormat.SVG.value or spec.format == knext.ImageFormat.SVG
    image, view = node.execute(ktest.TestingExecutionContext(), knext.Table.from_pandas(df))
    assert view.html.startswith("<!doctype html>")
    assert "data-sp-embed" in view.html and "<script>" in view.html  # KN-REQ-003: self-contained
    assert image.lstrip().startswith(b"<svg")
    props = view_props(view.html)
    for name, value in (chart["demo"].get("options") or {}).items():
        if node.option_names and name in node.option_names.values():
            assert props[name] == value, name  # the number options arrive as numbers, not as text


UNDECLARED = [c for c in BINDABLE if demo_settings(c, nodes.NODES[c["slug"]]())[1]]


@pytest.mark.parametrize("chart", UNDECLARED, ids=[c["slug"] for c in UNDECLARED])
def test_demo_options_without_a_dialog_parameter_reach_the_package(chart):
    """KN-REQ-009, KN-D5: the demo's options that are not catalog options (names, nodes) — the package
    takes them since 0.11.0.post1 (silverpoint-python#2); the dialog has no parameter for them."""
    demo = chart["demo"]
    silverpoint.Chart(chart["slug"], demo_rows(chart), roles=demo["roles"], options=demo["options"])


def test_number_option_reaches_the_chart_as_a_number():
    """KN-REQ-002, KN-REQ-003: a number option's text field is read as a number."""
    df = pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "rain": [3.0, 5.5, 2.0]})
    node = configured("polar-line-chart", {"angle": "month", "value": "rain"}, {"opt_period": "12"})
    _, view = node.execute(ktest.TestingExecutionContext(), knext.Table.from_pandas(df))
    assert view_props(view.html)["period"] == 12


def test_number_option_that_is_not_a_number_fails_configuration():
    """KN-REQ-004: a setting the chart cannot take fails configuration with a message."""
    df = pd.DataFrame({"month": ["Jan"], "rain": [3.0]})
    node = configured("polar-line-chart", {"angle": "month", "value": "rain"}, {"opt_period": "twelve"})
    with pytest.raises(knext.InvalidParametersError, match="Period"):
        node.configure(ktest.TestingConfigurationContext(), schema_of(df))


def test_view_is_report_ready_with_node():
    if not HAS_NODE:
        pytest.skip("Node is not on PATH")
    df = pd.DataFrame({"team": ["A", "B"], "wins": [3, 5]})
    image, view = configured("bar-chart", {"x": "team", "value": "wins"}).execute(
        ktest.TestingExecutionContext(), knext.Table.from_pandas(df)
    )
    assert b'class="sp-chart' in image
    assert view.render() is not None or view.svg_or_png is not None


def test_without_node_the_image_is_a_notice_and_a_warning(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.delenv("SILVERPOINT_NODE", raising=False)
    ctx = ktest.TestingExecutionContext()
    warnings = []
    ctx.set_warning = warnings.append
    df = pd.DataFrame({"team": ["A", "B"], "wins": [3, 5]})
    image, view = configured("bar-chart", {"x": "team", "value": "wins"}).execute(
        ctx, knext.Table.from_pandas(df)
    )
    assert b"Node.js" in image
    assert any("Node.js" in w for w in warnings)
    assert "data-sp-embed" in view.html


def test_required_column_unset_fails_configuration_with_the_spec_error():
    """KN-REQ-004: the package's SpecError message, at configuration."""
    df = pd.DataFrame({"team": ["A"], "wins": [3]})
    node = configured("bar-chart", {"x": "team"})
    with pytest.raises(knext.InvalidParametersError, match='bar-chart needs the role "value"'):
        node.configure(ktest.TestingConfigurationContext(), schema_of(df))


def test_missing_column_fails_configuration_with_the_spec_error():
    """KN-REQ-004: a column the table does not have (a flow variable can set one)."""
    df = pd.DataFrame({"team": ["A"], "wins": [3]})
    node = configured("bar-chart", {"x": "team", "value": "losses"})
    with pytest.raises(knext.InvalidParametersError, match='the data has no column "losses"'):
        node.configure(ktest.TestingConfigurationContext(), schema_of(df))


def test_empty_table_fails_execution_with_the_spec_error():
    """KN-REQ-004: an empty table for a scalar chart — the package's message."""
    df = pd.DataFrame({"percent": pd.Series([], dtype="float64")})
    node = configured("gauge-arc", {"percent": "percent"})
    with pytest.raises(ValueError, match="gauge-arc draws one value from the table's first row"):
        node.execute(ktest.TestingExecutionContext(), knext.Table.from_pandas(df))


def test_empty_table_fails_execution_where_the_package_draws_nothing():
    """KN-REQ-004: an empty table fails even where the package would draw an empty chart."""
    df = pd.DataFrame({"t": pd.Series([], dtype="object"), "v": pd.Series([], dtype="float64")})
    node = configured("line-chart", {"x": "t", "value": "v"})
    with pytest.raises(ValueError, match="empty"):
        node.execute(ktest.TestingExecutionContext(), knext.Table.from_pandas(df))


def test_appearance_reaches_the_view():
    """KN-REQ-002, KN-REQ-007: the appearance settings reach the chart."""
    df = pd.DataFrame({"team": ["A", "B"], "wins": [3, 5]})
    node = configured(
        "bar-chart", {"x": "team", "value": "wins"}, {"ground": "CYANOTYPE", "substrate": "OCHRE"}
    )
    image, view = node.execute(ktest.TestingExecutionContext(), knext.Table.from_pandas(df))
    assert '"ground":"cyanotype"' in view.html


def test_row_limit_draws_the_first_rows_and_warns():
    df = pd.DataFrame({"team": [f"T{i}" for i in range(30)], "wins": list(range(30))})
    ctx = ktest.TestingExecutionContext()
    warnings = []
    ctx.set_warning = warnings.append
    node = configured("bar-chart", {"x": "team", "value": "wins"}, {"row_limit": 10})
    image, view = node.execute(ctx, knext.Table.from_pandas(df))
    assert '"team":"T9"' in view.html and '"team":"T10"' not in view.html
    assert any("10" in w and "30" in w for w in warnings)
