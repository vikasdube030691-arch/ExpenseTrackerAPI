from app.schemas.generative_ui import (
    MAX_UI_BLOCKS,
    ActionButtonComponent,
    AlertComponent,
    BarChartComponent,
    DataTableComponent,
    InsightCardComponent,
    LineChartComponent,
    MetricCardComponent,
    PieChartComponent,
    RecommendationComponent,
    validate_ui_blocks,
)


def test_valid_metric_card_round_trips():
    result = validate_ui_blocks([{"component": "metric_card", "title": "Spent", "value": "$120.00"}])

    assert result.rejected == []
    assert len(result.blocks) == 1
    assert isinstance(result.blocks[0], MetricCardComponent)
    assert result.blocks[0].tone == "neutral"


def test_all_nine_component_types_validate():
    raw = [
        {"component": "metric_card", "title": "Spent", "value": "$1"},
        {"component": "bar_chart", "title": "By category", "categories": ["Food"], "series": [{"name": "Spent", "data": [1.0]}]},
        {
            "component": "line_chart",
            "title": "Trend",
            "categories": ["Jan", "Feb"],
            "series": [{"name": "Spent", "data": [1.0, 2.0]}],
        },
        {"component": "pie_chart", "title": "Split", "slices": [{"label": "Food", "value": 1.0}]},
        {"component": "data_table", "title": "Rows", "columns": ["A"], "rows": [["x"]]},
        {"component": "insight_card", "title": "Insight", "body": "You spent a lot."},
        {"component": "recommendation", "title": "Save more", "body": "Try a budget."},
        {"component": "alert", "severity": "warning", "message": "Over budget"},
        {"component": "action_button", "label": "View", "action": "navigate_transactions"},
    ]

    result = validate_ui_blocks(raw)

    assert result.rejected == []
    assert len(result.blocks) == 9
    assert isinstance(result.blocks[1], BarChartComponent)
    assert isinstance(result.blocks[2], LineChartComponent)
    assert isinstance(result.blocks[3], PieChartComponent)
    assert isinstance(result.blocks[4], DataTableComponent)
    assert isinstance(result.blocks[5], InsightCardComponent)
    assert isinstance(result.blocks[6], RecommendationComponent)
    assert isinstance(result.blocks[7], AlertComponent)
    assert isinstance(result.blocks[8], ActionButtonComponent)


def test_unknown_component_type_is_rejected_not_raised():
    result = validate_ui_blocks([{"component": "raw_html_widget", "html": "<script>alert(1)</script>"}])

    assert result.blocks == []
    assert len(result.rejected) == 1
    assert "unknown component type" in result.rejected[0].reason


def test_unknown_prop_on_known_component_is_rejected():
    result = validate_ui_blocks(
        [{"component": "metric_card", "title": "Spent", "value": "$1", "onclick": "alert(1)"}]
    )

    assert result.blocks == []
    assert result.rejected[0].component == "metric_card"


def test_html_in_text_field_is_rejected():
    result = validate_ui_blocks(
        [{"component": "insight_card", "title": "Hi", "body": "<img src=x onerror=alert(1)>"}]
    )

    assert result.blocks == []
    assert len(result.rejected) == 1


def test_action_button_rejects_arbitrary_action_not_in_whitelist():
    result = validate_ui_blocks(
        [{"component": "action_button", "label": "Go", "action": "javascript:alert(1)"}]
    )

    assert result.blocks == []
    assert len(result.rejected) == 1


def test_action_button_has_no_url_field_at_all():
    assert "url" not in ActionButtonComponent.model_fields
    assert "href" not in ActionButtonComponent.model_fields


def test_bar_chart_rejects_mismatched_series_length():
    result = validate_ui_blocks(
        [
            {
                "component": "bar_chart",
                "title": "Mismatch",
                "categories": ["A", "B"],
                "series": [{"name": "Spent", "data": [1.0]}],
            }
        ]
    )

    assert result.blocks == []
    assert "data points" in result.rejected[0].reason


def test_data_table_rejects_row_with_wrong_column_count():
    result = validate_ui_blocks(
        [{"component": "data_table", "title": "T", "columns": ["A", "B"], "rows": [["x"]]}]
    )

    assert result.blocks == []


def test_pie_chart_rejects_negative_value():
    result = validate_ui_blocks(
        [{"component": "pie_chart", "title": "Split", "slices": [{"label": "Food", "value": -5}]}]
    )

    assert result.blocks == []


def test_one_bad_block_does_not_drop_the_others():
    result = validate_ui_blocks(
        [
            {"component": "metric_card", "title": "Good", "value": "$1"},
            {"component": "not_a_real_component"},
            {"component": "alert", "severity": "warning", "message": "Also good"},
        ]
    )

    assert len(result.blocks) == 2
    assert len(result.rejected) == 1
    assert result.rejected[0].index == 1


def test_too_many_blocks_are_rejected_past_the_cap():
    raw = [{"component": "metric_card", "title": "M", "value": "$1"} for _ in range(MAX_UI_BLOCKS + 3)]

    result = validate_ui_blocks(raw)

    assert len(result.blocks) == MAX_UI_BLOCKS
    assert len(result.rejected) == 3


def test_non_list_input_is_rejected_gracefully():
    result = validate_ui_blocks({"component": "metric_card"})

    assert result.blocks == []
    assert len(result.rejected) == 1


def test_non_dict_block_is_rejected_gracefully():
    result = validate_ui_blocks(["<script>alert(1)</script>"])

    assert result.blocks == []
    assert len(result.rejected) == 1


def test_icon_name_rejects_non_glyph_strings():
    result = validate_ui_blocks(
        [{"component": "metric_card", "title": "M", "value": "$1", "icon": "javascript:alert(1)"}]
    )

    assert result.blocks == []
