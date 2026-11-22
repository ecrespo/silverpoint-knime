import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Could not read plotly")

import silverpoint  # noqa: E402

CATALOG = silverpoint.catalog
BINDABLE = [c for c in CATALOG["charts"] if c["binding"] != "none"]
ROOT = Path(__file__).resolve().parents[1]


def demo_rows(chart):
    return json.loads(json.dumps(chart["demo"]["rows"]))


def demo_settings(chart, node):
    """KN-REQ-009 as built in 0.11.0: ``demo.options`` as the node's dialog holds them (parameter →
    setting), and the demo options the dialog has no parameter for (catalog name → value)."""
    by_catalog = {catalog: parameter for parameter, catalog in node.option_names.items()}
    kinds = {o["name"]: o["kind"] for o in chart["options"]}
    settings, undeclared = {}, {}
    for name, value in (chart["demo"].get("options") or {}).items():
        parameter = by_catalog.get(name)
        if parameter is None:
            undeclared[name] = value
        elif kinds[name] == "enum":
            settings[parameter] = next(m for m, v in node.enum_values[parameter].items() if v == value)
        elif kinds[name] == "number":
            settings[parameter] = str(value)  # a number option's field is text: empty is the chart default
        else:
            settings[parameter] = value
    return settings, undeclared
