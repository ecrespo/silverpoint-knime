"""KN-REQ-008, KN-T-06: write the example workflow `workflows_examples/silverpoint-example/`.

    CSV Reader (demo/hits-per-hour.csv, `hour` read as String)
      ├─ Silverpoint Line chart  (x=hour, value=hits, secondary=baseline)
      ├─ Silverpoint Area chart  (x=hour, value=hits; sanguine palette)
      └─ Silverpoint Step chart  (x=hour, value=hits; cyanotype ground)

Each Silverpoint node's settings are the node's own parameters (knext's `extract_parameters`, so every
parameter the generated node declares is written, with its default unless set below). The CSV file
travels inside the workflow (`data/`), read relative to it (KN-Art. 2: nothing is fetched).

    uv run python scripts/make_example_workflow.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import knime.extension.parameter as kp  # noqa: E402

from silverpoint_knime.nodes.areas import AreaChartNode  # noqa: E402
from silverpoint_knime.nodes.lines import LineChartNode, StepChartNode  # noqa: E402

OUT = ROOT / "workflows_examples" / "silverpoint-example"
CSV = ROOT / "demo" / "hits-per-hour.csv"
MANIFEST = yaml.safe_load((ROOT / "knime.yml").read_text(encoding="utf-8"))
EXTENSION_ID = f"{MANIFEST['group_id']}.{MANIFEST['name']}"
VERSION = MANIFEST["version"]
KNIME = "5.9.0"
PYTHON_FACTORY = "org.knime.python3.nodes.extension.ExtensionNodeSetFactory$DynamicExtensionNodeFactory"
HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<config xmlns="http://www.knime.org/2008/09/XMLConfig" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:schemaLocation="http://www.knime.org/2008/09/XMLConfig '
    'http://www.knime.org/XMLConfig_2008_09.xsd" key={key}>\n'
)

COMMON = {"role_x": "hour", "role_value": "hits"}
CHARTS = [
    (
        2,
        LineChartNode,
        "line-chart",
        "Silverpoint Line chart",
        {
            **COMMON,
            "role_secondary": "baseline",
            "view_title": "Hits per hour",
            "view_description": "Hits against the baseline, every two hours.",
        },
        "Hits and baseline",
    ),
    (
        3,
        AreaChartNode,
        "area-chart",
        "Silverpoint Area chart",
        {**COMMON, "view_title": "Hits per hour", "palette": "SANGUINE"},
        "Sanguine palette",
    ),
    (
        4,
        StepChartNode,
        "step-chart",
        "Silverpoint Step chart",
        {**COMMON, "view_title": "Hits per hour", "ground": "CYANOTYPE"},
        "Cyanotype ground",
    ),
]


def entry(key: str, value, indent: int) -> str:
    pad = " " * indent
    if value is None:
        return f'{pad}<entry key={quoteattr(key)} type="xstring" isnull="true" value=""/>\n'
    kind = {bool: "xboolean", int: "xint", float: "xdouble"}.get(type(value), "xstring")
    text = str(value).lower() if isinstance(value, bool) else str(value)
    return f"{pad}<entry key={quoteattr(key)} type={quoteattr(kind)} value={quoteattr(text)}/>\n"


def config(key: str, body: str, indent: int) -> str:
    pad = " " * indent
    if not body:
        return f"{pad}<config key={quoteattr(key)}/>\n"
    return f"{pad}<config key={quoteattr(key)}>\n{body}{pad}</config>\n"


def values(mapping: dict, indent: int) -> str:
    out = ""
    for key, value in mapping.items():
        if isinstance(value, dict):
            out += config(key, values(value, indent + 4), indent)
        elif isinstance(value, list):
            items = {"array-size": len(value), **{str(i): v for i, v in enumerate(value)}}
            out += config(key, values(items, indent + 4), indent)
        else:
            out += entry(key, value, indent)
    return out


def annotation(text: str, x: int, y: int) -> str:
    return config(
        "nodeAnnotation",
        values(
            {
                "text": text,
                "contentType": "text/plain",
                "bgcolor": 16777215,
                "x-coordinate": x,
                "y-coordinate": y,
                "width": 160,
                "height": 30,
                "alignment": "CENTER",
                "borderSize": 0,
                "borderColor": 16777215,
                "defFontSize": 9,
                "annotation-version": 20151123,
            },
            8,
        )
        + config("styles", "", 8),
        4,
    )


def tail(name: str, factory: str, bundle: dict, factory_settings: str, ports: int) -> str:
    port_cfg = "".join(
        config(f"port_{i}", entry("index", i, 12) + entry("port_dir_location", None, 12), 8)
        for i in range(1, ports + 1)
    )
    return (
        entry("customDescription", None, 4)
        + entry("state", "IDLE", 4)
        + entry("factory", factory, 4)
        + entry("node-name", name, 4)
        + values(bundle, 4)
        + factory_settings
        + entry("name", name, 4)
        + entry("hasContent", False, 4)
        + entry("isInactive", False, 4)
        + config("ports", port_cfg, 4)
        + config("filestores", entry("file_store_location", None, 8) + entry("file_store_id", None, 8), 4)
        + "</config>\n"
    )


def node_head(model: str) -> str:
    return (
        HEAD.format(key='"settings.xml"')
        + entry("node_file", "settings.xml", 4)
        + config("flow_stack", "", 4)
        + config("internal_node_subsettings", entry("memory_policy", "CacheSmallInMemory", 8), 4)
        + model
    )


def chart_settings(cls, node_id: str, name: str, settings: dict, note: str, x: int, y: int) -> str:
    node = cls()
    for key, value in settings.items():
        setattr(node, key, value)
    model = kp.extract_parameters(node)["model"]
    # as KNIME 5.12 saves a Python node: the parameters, then the JSON root's type and the version
    model["json-type_Internals"] = "OBJECT"
    model["extension_version_Internals"] = VERSION
    bundle = {
        "node-bundle-name": MANIFEST["description"],
        "node-bundle-symbolic-name": EXTENSION_ID,
        "node-bundle-vendor": MANIFEST["vendor"],
        "node-bundle-version": VERSION,
        "node-feature-name": MANIFEST["description"],
        "node-feature-symbolic-name": f"{MANIFEST['group_id']}.features.{MANIFEST['name']}.feature.group",
        "node-feature-vendor": MANIFEST["vendor"],
        "node-feature-version": VERSION,
    }
    factory_settings = (
        entry("factory-id-uniquifier", f"{EXTENSION_ID}_!_{node_id}", 4)
        + config("factory_settings", entry("extension_id", EXTENSION_ID, 8) + entry("node_id", node_id, 8), 4)
        + config(
            "node_creation_config", config("Input Table # 0", "", 8) + config("Output SVG # 0", "", 8), 4
        )
    )
    return (
        node_head(config("model", values(model, 8), 4) + config("variables", "", 4))
        + annotation(note, x - 40, y + 70)
        + tail(name, PYTHON_FACTORY, bundle, factory_settings, ports=1)
    )


COLUMNS = [  # name, Java class, KNIME type, converter (hour as String: "00" stays "00")
    (
        "hour",
        "java.lang.String",
        "String",
        "org.knime.core.data.def.StringCell$StringCellFactory.createCell(class java.lang.String)",
    ),
    (
        "hits",
        "java.lang.Integer",
        "Number (integer)",
        "org.knime.core.data.def.IntCell$IntCellFactory.create(class java.lang.Integer)",
    ),
    (
        "baseline",
        "java.lang.Integer",
        "Number (integer)",
        "org.knime.core.data.def.IntCell$IntCellFactory.create(class java.lang.Integer)",
    ),
]
CSV_PATH = "data/hits-per-hour.csv"


def csv_reader_settings(x: int, y: int) -> str:
    reader = {
        "has_column_header": True,
        "has_row_id": False,
        "comment_char": "#",
        "column_delimiter": ",",
        "quote_char": '"',
        "quote_escape_char": '"',
        "row_delimiter": "%%00010",
        "use_line_break_row_delimiter": True,
    }
    advanced = {
        "quote_option": "REMOVE_QUOTES_AND_TRIM",
        "replace_empty_quotes_with_missing": True,
        "limit_data_rows_scanned": True,
        "max_data_rows_scanned": 10000,
        "thousands_separator": "%%00000",
        "decimal_separator": ".",
    }
    limit = {
        "skip_lines": False,
        "number_of_lines_to_skip": 1,
        "skip_data_rows": False,
        "number_of_rows_to_skip": 1,
    }
    filter_options = {
        "filter_files_extension": False,
        "files_extension_expression": "",
        "files_extension_case_sensitive": False,
        "filter_files_name": False,
        "files_name_expression": "*",
        "files_name_case_sensitive": False,
        "files_name_filter_type": "WILDCARD",
        "include_hidden_files": False,
        "include_special_files": True,
        "filter_folders_name": False,
        "folders_name_expression": "*",
        "folders_name_case_sensitive": False,
        "folders_name_filter_type": "WILDCARD",
        "include_hidden_folders": False,
        "follow_links": True,
    }
    settings = {
        "file_selection_Internals": {"SettingsModelID": "SMID_ReaderFileChooser", "EnabledStatus": True},
        "file_selection": {
            "file_system_chooser__Internals": {
                "has_fs_port": False,
                "overwritten_by_variable": False,
                "convenience_fs_category": "RELATIVE",
                "relative_to": "knime.workflow",
                "mountpoint": "LOCAL",
                "spaceId": "",
                "spaceName": "",
                "custom_url_timeout": 1000,
                "connected_fs": True,
            },
            "path": {
                "location_present": True,
                "file_system_type": "RELATIVE",
                "file_system_specifier": "knime.workflow",
                "path": CSV_PATH,
            },
            "filter_mode_Internals": {"SettingsModelID": "SMID_FilterMode", "EnabledStatus": True},
            "filter_mode": {
                "filter_mode": "FILE",
                "include_subfolders": False,
                "filter_options": filter_options,
            },
        },
        "has_column_header": True,
        "has_row_id": False,
        "support_short_data_rows": False,
        "skip_empty_data_rows": False,
        "prepend_file_idx_to_row_id": False,
        "comment_char": "#",
        "column_delimiter": ",",
        "quote_char": '"',
        "quote_escape_char": '"',
        "use_line_break_row_delimiter": True,
        "row_delimiter": "%%00010",
        "autodetect_buffer_size": 1048576,
    }

    def spec(name, cls):
        return {"name": name, "has_type": True, "type": {"class": cls}}

    individual = {
        "num_columns": len(COLUMNS),
        **{str(i): spec(n, c) for i, (n, c, _, _) in enumerate(COLUMNS)},
    }
    columns = {}
    for i, (name, cls, dst, converter) in enumerate(COLUMNS):
        columns[str(i)] = {
            "external_spec": spec(name, cls),
            "name": name,
            "keep": True,
            "position": i,
            "production_path": {
                "_converter": converter,
                "_converter_src": cls,
                "_converter_dst": dst,
                "_converter_name": dst.split(" ")[0] if cls.endswith("String") else "Integer",
                "_converter_config": {},
                "_producer": f"class {cls}->{cls}",
                "_producer_src": cls,
                "_producer_dst": cls,
                "_producer_name": cls,
                "_producer_config": {},
            },
        }
    table_spec = {
        "version": "V4_4",
        "individual_specs": {CSV_PATH: individual},
        "table_transformation": {
            # the column count and the intersection live inside `columns` (TableTransformationSerializer)
            "columns": {
                **columns,
                "num_columns": len(COLUMNS),
                "intersection_indices": list(range(len(COLUMNS))),
            },
            "skip_empty_columns": False,
            "enforce_types": True,
            "column_filter_mode": "UNION",
            "unknown_columns_transformation": {"position": len(COLUMNS), "keep": True, "force_type": False},
        },
        "source_group_id": CSV_PATH,
        "config_id": {
            "multi_table_read": {
                "settings": reader,
                "advanced_settings": advanced,
                "encoding": {"charset": None},
                "limit_rows": limit,
            }
        },
    }
    model = {
        "settings": settings,
        "table_spec_config_Internals": table_spec,
        "advanced_settings": {
            "spec_merge_mode_Internals": "UNION",
            "fail_on_differing_specs": True,
            "append_path_column_Internals": False,
            "path_column_name_Internals": "Path",
            "limit_data_rows_scanned": True,
            "max_data_rows_scanned": 10000,
            "save_table_spec_config_Internals": True,
            "check_table_spec": True,
            "limit_memory_per_column": True,
            "maximum_number_of_columns": 8192,
            "quote_option": "REMOVE_QUOTES_AND_TRIM",
            "replace_empty_quotes_with_missing": True,
            "no_row_delimiters_in_quotes": False,
            "min_chunk_size_in_bytes": 67108864,
            "max_num_chunks_per_file": 4,
            "thousands_separator": "%%00000",
            "decimal_separator": ".",
        },
        "limit_rows": {**limit, "limit_data_rows": False, "max_rows": 50},
        "encoding": {"charset": None},
    }
    # the long-typed entries the reader expects
    body = values(model, 8)
    for key in (
        "max_data_rows_scanned",
        "number_of_lines_to_skip",
        "number_of_rows_to_skip",
        "max_rows",
        "min_chunk_size_in_bytes",
    ):
        body = body.replace(f'key="{key}" type="xint"', f'key="{key}" type="xlong"')
    bundle = {
        "node-bundle-name": "KNIME Base Nodes",
        "node-bundle-symbolic-name": "org.knime.base",
        "node-bundle-vendor": "KNIME AG, Zurich, Switzerland",
        "node-bundle-version": KNIME,
        "node-feature-name": "KNIME Base nodes",
        "node-feature-symbolic-name": "org.knime.features.base.feature.group",
        "node-feature-vendor": "KNIME AG, Zurich, Switzerland",
        "node-feature-version": KNIME,
    }
    creation = config(
        "node_creation_config", config("File System Connection", "", 8) + config("Data Table", "", 8), 4
    )
    return (
        node_head(config("model", body, 4))
        + annotation("hits-per-hour.csv%%00010(hour as String)", x - 40, y + 70)
        + tail(
            "CSV Reader",
            "org.knime.base.node.io.filehandling.csv.reader.CSVTableReaderNodeFactory",
            bundle,
            config("factory_settings", "", 4) + creation,
            ports=1,
        )
    )


def node_entry(node_id: int, folder: str, x: int, y: int) -> str:
    bounds = values({"array-size": 4, "0": x, "1": y, "2": 80, "3": 80}, 16)
    return config(
        f"node_{node_id}",
        entry("id", node_id, 12)
        + entry("node_settings_file", f"{folder}/settings.xml", 12)
        + entry("node_is_meta", False, 12)
        + entry("node_type", "NativeNode", 12)
        + entry("ui_classname", "org.knime.core.node.workflow.NodeUIInformation", 12)
        + config("ui_settings", config("extrainfo.node.bounds", bounds, 16), 12),
        8,
    )


def workflow(nodes: list[tuple[int, str, int, int]], links: list[tuple[int, int]], note: str) -> str:
    connections = "".join(
        config(
            f"connection_{i}",
            entry("sourceID", src, 12)
            + entry("destID", dst, 12)
            + entry("sourcePort", 1, 12)
            + entry("destPort", 1, 12)
            + config("ui_settings", entry("extrainfo.conn.bendpoints_size", 0, 16), 12),
            8,
        )
        for i, (src, dst) in enumerate(links)
    )
    text_annotation = config(
        "annotation_0",
        values(
            {
                "text": note,
                "contentType": "text/plain",
                "bgcolor": 16777215,
                "x-coordinate": 40,
                "y-coordinate": 20,
                "width": 640,
                "height": 90,
                "alignment": "LEFT",
                "borderSize": 10,
                "borderColor": 16766976,
                "defFontSize": 11,
                "annotation-version": 20230412,
            },
            12,
        )
        + config("styles", "", 12),
        8,
    )
    return (
        HEAD.format(key='"workflow.knime"')
        + entry("created_by", KNIME, 4)
        + entry("created_by_nightly", False, 4)
        + entry("version", "5.1.0", 4)
        + entry("name", None, 4)
        + config(
            "authorInformation",
            values(
                {
                    "authored-by": MANIFEST["author"],
                    "authored-when": "2026-11-22 00:00:00 +0000",
                    "lastEdited-by": MANIFEST["author"],
                    "lastEdited-when": "2026-11-22 00:00:00 +0000",
                },
                8,
            ),
            4,
        )
        + entry("customDescription", None, 4)
        + entry("state", "IDLE", 4)
        + config("workflow_credentials", "", 4)
        + config("annotations", text_annotation, 4)
        + config("nodes", "".join(node_entry(*n) for n in nodes), 4)
        + config("connections", connections, 4)
        + "</config>\n"
    )


NOTE = (
    "silverpoint for KNIME — example (KN-REQ-008)%%00010"
    "A CSV Reader feeds three Silverpoint nodes. Open a node's view (right click › Open view) to read "
    "the chart by keyboard; its output port holds the chart as SVG when Node.js 20+ is available.%%00010"
    "Try: change the palette, ground or mode in a dialog, or drive them with flow variables."
)


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    shutil.copyfile(CSV, OUT / "data" / CSV.name)
    nodes = [(1, "CSV Reader (#1)", 80, 260)]
    (OUT / "CSV Reader (#1)").mkdir()
    (OUT / "CSV Reader (#1)" / "settings.xml").write_text(csv_reader_settings(80, 260), encoding="utf-8")
    links = []
    for row, (node_id, cls, slug, name, settings, note) in enumerate(CHARTS):
        x, y = 360, 140 + row * 140
        folder = f"{name} (#{node_id})"
        (OUT / folder).mkdir()
        (OUT / folder / "settings.xml").write_text(
            chart_settings(cls, slug, name, settings, note, x, y), encoding="utf-8"
        )
        nodes.append((node_id, folder, x, y))
        links.append((1, node_id))
    (OUT / "workflow.knime").write_text(workflow(nodes, links, NOTE), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(nodes)} nodes, {len(links)} connections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
