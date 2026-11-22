"""What every generated node shares (KN-Art. 1: the extension is glue): read the table and the dialog,
call the `silverpoint` package, return its HTML view and, with Node.js, its SVG."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import knime.extension as knext
import silverpoint
from silverpoint import RuntimeUnavailable, SpecError

ROOT_CATEGORY = knext.category(
    path="/community",
    level_id="silverpoint",
    name="Silverpoint",
    description="silverpoint charts: hand-drawn, accessible views of a table.",
    icon="icons/silverpoint.png",
)
DEFAULT_ROW_LIMIT = 10_000


@dataclass(frozen=True)
class Role:
    id: str
    label: str
    kind: str
    data_type: str
    required: bool
    multiple: bool


def _type_name(column: knext.Column) -> str:
    return str(column.ktype).lower()


def numeric(column: knext.Column) -> bool:
    return any(t in _type_name(column) for t in ("double", "int", "long", "number"))


def textual(column: knext.Column) -> bool:
    return "string" in _type_name(column)


def temporal(column: knext.Column) -> bool:
    return any(t in _type_name(column) for t in ("date", "time", "zoned")) or textual(column)


def labelling(column: knext.Column) -> bool:
    """A string role is a label: text, and also a number or a date (an hour, a year, an id), which the
    package binds as it is (KN-D6)."""
    return textual(column) or numeric(column) or temporal(column) or "bool" in _type_name(column)


def column_filter(data_type: str):
    """KN-REQ-002: a role's selector lists the columns of its data type."""
    return {"number": numeric, "date": temporal, "boolean": lambda c: "bool" in _type_name(c)}.get(
        data_type, labelling
    )


SVG_NOTICE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="60" viewBox="0 0 480 60" role="img">'
    "<title>No SVG: Node.js was not found</title>"
    '<text x="12" y="34" font-family="Georgia, serif" font-size="14">'
    "The SVG needs Node.js 20+ (Node.js executable, or PATH); the view has the chart."
    "</text></svg>"
)


def as_number(text: str) -> int | float:
    """A number option's text field, read as the number it holds (ValueError otherwise)."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        number = float(text)
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(text)
    return number


class ChartNode:
    """Mixed into each generated node: ``chart`` (slug), ``roles``, ``option_names`` (parameter →
    catalog name), ``number_options`` (parameter → label: a text field read as a number) and
    ``enum_values`` (parameter → member → catalog value) are set by the generator."""

    chart: str = ""
    roles: Sequence[Role] = ()
    option_names: Mapping[str, str] = {}
    number_options: Mapping[str, str] = {}
    enum_values: Mapping[str, Mapping[str, str]] = {}

    def _role_columns(self) -> dict[str, str | list[str]]:
        out: dict[str, str | list[str]] = {}
        for role in self.roles:
            value = getattr(self, f"role_{role.id}", None)
            if role.multiple:
                columns = [c for c in (value or []) if c]
                if columns:
                    out[role.id] = columns
            elif value:
                out[role.id] = value
        return out

    def _check_roles(self, schema: knext.Schema) -> dict[str, str | list[str]]:
        """KN-REQ-004 at configuration: the package binds the roles to the schema's columns (no rows),
        and its SpecError message is the node's. Errors that need the rows wait for execution."""
        roles = self._role_columns()
        try:
            silverpoint.Chart(self.chart, {"columns": list(schema.column_names), "values": []}, roles=roles)
        except SpecError as error:
            if error.kind in ("role", "chart", "prop", "value"):
                raise knext.InvalidParametersError(str(error)) from error
        return roles

    def _value(self, parameter: str):
        value = getattr(self, parameter, None)
        members = self.enum_values.get(parameter)
        if members is not None:
            return members.get(value) if value not in (None, "", "DEFAULT") else None
        if parameter in self.number_options:
            return None if value is None or not str(value).strip() else as_number(str(value))
        return None if value in (None, "") else value

    def _check_numbers(self) -> None:
        wrong = []
        for parameter, label in self.number_options.items():
            try:
                self._value(parameter)
            except ValueError:
                wrong.append(f"{label} ({getattr(self, parameter)!r})")
        if wrong:
            raise knext.InvalidParametersError(f"Not a number: {', '.join(wrong)}.")

    def configure(self, config_context, input_schema):
        self._check_roles(input_schema)
        self._check_numbers()
        return knext.ImagePortObjectSpec(knext.ImageFormat.SVG)

    def execute(self, exec_context, input_table):
        df = input_table.to_pandas()
        roles = self._role_columns()  # the package binds them to the rows below (KN-REQ-004)
        self._check_numbers()
        limit = int(getattr(self, "row_limit", DEFAULT_ROW_LIMIT) or DEFAULT_ROW_LIMIT)
        if len(df) > limit:
            exec_context.set_warning(f"Drawing the first {limit} of {len(df)} rows (Row limit).")
            df = df.head(limit)
        df = df.reset_index(drop=True)
        options = {
            catalog: v
            for parameter, catalog in self.option_names.items()
            if (v := self._value(parameter)) is not None
        }
        appearance = {key: self._value(key) for key in ("ground", "substrate", "mode", "palette")}
        # An empty frame reaches the package as a column-form table, which keeps its column names.
        data = {"columns": list(df.columns), "values": []} if len(df) == 0 else df
        try:
            chart = silverpoint.Chart(
                self.chart, data, roles=roles, options=options, id=f"knime-{self.chart}", **appearance
            )
        except SpecError as error:
            raise ValueError(str(error)) from error
        if len(df) == 0:
            raise ValueError(f"{self.chart}: the input table is empty.")
        html = chart.to_html(full_document=True, script="inline", render="client")
        runtime = getattr(self, "node_executable", "") or ""
        previous = os.environ.get("SILVERPOINT_NODE")
        try:
            if runtime:
                os.environ["SILVERPOINT_NODE"] = runtime
            svg = chart.to_svg(embed_fonts=True)
        except RuntimeUnavailable:
            exec_context.set_warning(
                "The SVG output holds a notice: Node.js 20+ was not found (Node.js executable, or PATH)."
            )
            return SVG_NOTICE.encode("utf-8"), knext.view_html(html)
        finally:
            if runtime:
                if previous is None:
                    os.environ.pop("SILVERPOINT_NODE", None)
                else:
                    os.environ["SILVERPOINT_NODE"] = previous
        return svg.encode("utf-8"), knext.view_html(html, svg_or_png=svg)
