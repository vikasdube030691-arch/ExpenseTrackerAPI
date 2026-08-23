"""Safe Generative UI schema.

The AI-completion provider (currently the placeholder in
`app/services/ai/chat_completion.py`; swap in a real LLM later without
touching this file) never returns Angular, HTML, JavaScript, or a URL. It
returns plain JSON shaped like one of the `UIComponent` variants below, which
`validate_ui_blocks` treats as **untrusted input** — the same way a request
body from an anonymous client would be treated — before it ever reaches an
API response or gets persisted.

Every model here is built so that:

- an **unknown `component` value** is rejected by `validate_ui_blocks` before
  it is ever handed to a variant model (see `_COMPONENT_MODELS`);
- an **unknown/extra prop** on a known component is rejected because every
  model below sets `extra="forbid"` (`SafeModel`);
- **free text can never contain `<` or `>`** — no tag, script, or attribute
  injection is representable at all (`_clean_text` / `SafeTitle` / `SafeBody`);
- there is **deliberately no URL field anywhere in this schema**. Icons are a
  whitelisted glyph-name pattern (`SafeIconName`, letters/digits/underscore
  only), and the one place that could plausibly want a link —
  `action_button` — points at a fixed `ActionKey` enum that the frontend maps
  to a real Angular route. "Validate the URL" is replaced by "there is no URL
  to validate."

`validate_ui_blocks` never raises: a malformed block (bad enum value,
mismatched chart-series length, an unknown component, a stray `<script>`)
is dropped and recorded in `.rejected` — it does not take down the other,
valid blocks in the same AI response, and it does not take down the chat
request itself.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError, model_validator

_MAX_TITLE_LENGTH = 240
_MAX_BODY_LENGTH = 600
_MAX_CELL_LENGTH = 240
_DISALLOWED_CHARS = re.compile(r"[<>]")
_ICON_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,49}$")
_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

MAX_UI_BLOCKS = 12


def _clean_text(value: str, *, max_length: int) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("must not be empty")
    if len(trimmed) > max_length:
        raise ValueError(f"must be at most {max_length} characters")
    if _DISALLOWED_CHARS.search(trimmed):
        raise ValueError("must not contain '<' or '>' (no markup or scripts allowed)")
    return trimmed


def _title(value: str) -> str:
    return _clean_text(value, max_length=_MAX_TITLE_LENGTH)


def _body(value: str) -> str:
    return _clean_text(value, max_length=_MAX_BODY_LENGTH)


def _icon_name(value: str) -> str:
    candidate = value.strip().lower()
    if not _ICON_NAME_PATTERN.match(candidate):
        raise ValueError("must be a lowercase Material Symbols icon name (letters, digits, underscore)")
    return candidate


def _hex_color(value: str) -> str:
    candidate = value.strip()
    if not _COLOR_PATTERN.match(candidate):
        raise ValueError("must be a 6-digit hex color, e.g. #4287f5")
    return candidate


SafeTitle = Annotated[str, AfterValidator(_title)]
SafeBody = Annotated[str, AfterValidator(_body)]
SafeIconName = Annotated[str, AfterValidator(_icon_name)]
SafeColor = Annotated[str, AfterValidator(_hex_color)]

Tone = Literal["neutral", "positive", "negative"]
TrendDirection = Literal["up", "down", "flat"]
AlertSeverity = Literal["info", "warning", "error", "success"]
Priority = Literal["low", "medium", "high"]


class ActionKey(str, Enum):
    """The only "links" a generative UI block can carry — symbolic keys the
    frontend maps to a real Angular route via a fixed whitelist. There is no
    way for an AI response to specify an arbitrary href or route."""

    NAVIGATE_DASHBOARD = "navigate_dashboard"
    NAVIGATE_TRANSACTIONS = "navigate_transactions"
    NAVIGATE_ADD_TRANSACTION = "navigate_add_transaction"
    NAVIGATE_BUDGETS = "navigate_budgets"
    NAVIGATE_CATEGORIES = "navigate_categories"
    NAVIGATE_REPORTS = "navigate_reports"
    NAVIGATE_SETTINGS = "navigate_settings"


class SafeModel(BaseModel):
    """Base for every generative-UI model: an unknown field is a hard
    validation error, never silently dropped or ignored."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class MetricCardComponent(SafeModel):
    component: Literal["metric_card"] = "metric_card"
    title: SafeTitle
    value: SafeTitle
    change_percent: float | None = Field(default=None, ge=-1000, le=1000)
    trend: TrendDirection | None = None
    tone: Tone = "neutral"
    icon: SafeIconName | None = None


class ChartSeries(SafeModel):
    name: SafeTitle
    data: list[float] = Field(min_length=1, max_length=50)
    color: SafeColor | None = None


class BarChartComponent(SafeModel):
    component: Literal["bar_chart"] = "bar_chart"
    title: SafeTitle
    categories: list[SafeTitle] = Field(min_length=1, max_length=50)
    series: list[ChartSeries] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def _series_match_categories(self) -> "BarChartComponent":
        for series in self.series:
            if len(series.data) != len(self.categories):
                raise ValueError(
                    f"series '{series.name}' has {len(series.data)} data points "
                    f"but there are {len(self.categories)} categories"
                )
        return self


class LineChartComponent(SafeModel):
    component: Literal["line_chart"] = "line_chart"
    title: SafeTitle
    categories: list[SafeTitle] = Field(min_length=2, max_length=100)
    series: list[ChartSeries] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def _series_match_categories(self) -> "LineChartComponent":
        for series in self.series:
            if len(series.data) != len(self.categories):
                raise ValueError(
                    f"series '{series.name}' has {len(series.data)} data points "
                    f"but there are {len(self.categories)} categories"
                )
        return self


class PieSlice(SafeModel):
    label: SafeTitle
    value: float = Field(ge=0)
    color: SafeColor | None = None


class PieChartComponent(SafeModel):
    component: Literal["pie_chart"] = "pie_chart"
    title: SafeTitle
    slices: list[PieSlice] = Field(min_length=1, max_length=20)


TableCell = Union[str, float, int, bool, None]


class DataTableComponent(SafeModel):
    component: Literal["data_table"] = "data_table"
    title: SafeTitle
    columns: list[SafeTitle] = Field(min_length=1, max_length=10)
    rows: list[list[TableCell]] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def _rows_match_columns(self) -> "DataTableComponent":
        for row in self.rows:
            if len(row) != len(self.columns):
                raise ValueError(f"row has {len(row)} cells but there are {len(self.columns)} columns")
            for cell in row:
                if isinstance(cell, str):
                    if len(cell) > _MAX_CELL_LENGTH:
                        raise ValueError("cell text is too long")
                    if _DISALLOWED_CHARS.search(cell):
                        raise ValueError("cell text must not contain '<' or '>'")
        return self


class InsightCardComponent(SafeModel):
    component: Literal["insight_card"] = "insight_card"
    title: SafeTitle
    body: SafeBody
    icon: SafeIconName | None = None
    tone: Tone = "neutral"


class RecommendationComponent(SafeModel):
    component: Literal["recommendation"] = "recommendation"
    title: SafeTitle
    body: SafeBody
    action_label: SafeTitle | None = None
    priority: Priority = "medium"


class AlertComponent(SafeModel):
    component: Literal["alert"] = "alert"
    severity: AlertSeverity
    message: SafeBody


class ActionButtonComponent(SafeModel):
    component: Literal["action_button"] = "action_button"
    label: SafeTitle
    action: ActionKey


UIComponent = Annotated[
    Union[
        MetricCardComponent,
        BarChartComponent,
        LineChartComponent,
        PieChartComponent,
        DataTableComponent,
        InsightCardComponent,
        RecommendationComponent,
        AlertComponent,
        ActionButtonComponent,
    ],
    Field(discriminator="component"),
]

_COMPONENT_MODELS: dict[str, type[SafeModel]] = {
    "metric_card": MetricCardComponent,
    "bar_chart": BarChartComponent,
    "line_chart": LineChartComponent,
    "pie_chart": PieChartComponent,
    "data_table": DataTableComponent,
    "insight_card": InsightCardComponent,
    "recommendation": RecommendationComponent,
    "alert": AlertComponent,
    "action_button": ActionButtonComponent,
}


class GenerativeUiSelection(SafeModel):
    """Structured-output target for the Generative UI Agent
    (`app/agents/generative_ui_agent.py`): binding the LLM call to this model
    (via `.with_structured_output`) forces the model into this exact schema —
    the same one `validate_ui_blocks` enforces for every other path data
    reaches the UI through, so there is only ever one definition of "safe" in
    this codebase, not a parallel one for the agent path."""

    blocks: list[UIComponent] = Field(default_factory=list, max_length=MAX_UI_BLOCKS)


class UIBlockRejection(BaseModel):
    index: int
    component: str | None
    reason: str


class UIBlockValidationResult(BaseModel):
    blocks: list[UIComponent] = Field(default_factory=list)
    rejected: list[UIBlockRejection] = Field(default_factory=list)


def validate_ui_blocks(raw_blocks: Any) -> UIBlockValidationResult:
    """Validates a list of untrusted, LLM-shaped JSON dicts into safe UI
    components. Never raises — anything that fails to validate is recorded in
    `.rejected` (with the block's index, the component name it claimed to be
    if any, and a human-readable reason) and skipped, so one malformed block
    never drops the other valid blocks in the same response.
    """
    if not isinstance(raw_blocks, list):
        return UIBlockValidationResult(
            rejected=[UIBlockRejection(index=0, component=None, reason="ui_blocks must be a list")]
        )

    blocks: list[UIComponent] = []
    rejected: list[UIBlockRejection] = []

    for index, raw in enumerate(raw_blocks):
        if index >= MAX_UI_BLOCKS:
            rejected.append(
                UIBlockRejection(index=index, component=None, reason=f"exceeds max of {MAX_UI_BLOCKS} blocks per response")
            )
            continue

        if not isinstance(raw, dict):
            rejected.append(UIBlockRejection(index=index, component=None, reason="block must be a JSON object"))
            continue

        component_name = raw.get("component")
        model_cls = _COMPONENT_MODELS.get(component_name) if isinstance(component_name, str) else None
        if model_cls is None:
            rejected.append(
                UIBlockRejection(
                    index=index,
                    component=component_name if isinstance(component_name, str) else None,
                    reason=f"unknown component type: {component_name!r}",
                )
            )
            continue

        try:
            validated = model_cls.model_validate(raw)
        except ValidationError as exc:
            reason = "; ".join(f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors())
            rejected.append(UIBlockRejection(index=index, component=component_name, reason=reason))
            continue

        blocks.append(validated)

    return UIBlockValidationResult(blocks=blocks, rejected=rejected)
