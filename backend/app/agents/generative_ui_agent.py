"""The Generative UI Agent: chooses which of the 9 supported component types,
if any, should accompany a domain agent's reply, using structured output
bound directly to `app/schemas/generative_ui.py`'s existing safe schema —
there is only one definition of "safe" in this codebase, and the LLM is
constrained into it by construction rather than by a parallel prompt-only
convention.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.agents.llm import get_chat_model
from app.schemas.generative_ui import GenerativeUiSelection, validate_ui_blocks

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You choose which visual components, if any, should accompany an AI expense \
assistant's reply. You will be given the assistant's reply text and the raw data its tools \
returned this turn. Choose zero or more components from: metric_card, bar_chart, line_chart, \
pie_chart, data_table, insight_card, recommendation, alert, action_button.

Rules:
- Only use numbers that actually appear in the tool data below — never invent or estimate a \
figure that isn't there.
- Prefer metric_card for a single headline number, bar_chart/pie_chart for a breakdown across \
categories, line_chart for a trend over time, data_table for a list of individual records, \
insight_card for a one-off observation, recommendation for actionable advice, alert for a \
warning (e.g. over budget), and action_button to suggest a next step in the app.
- Return zero components (an empty list) if the reply is purely conversational and no data \
merits a visual — don't force one.
- Keep it to at most 3 components."""


def _tool_data_summary(tool_messages: list[ToolMessage]) -> str:
    if not tool_messages:
        return "(no tool data was retrieved this turn)"
    return "\n".join(str(message.content) for message in tool_messages)


async def choose_ui_blocks(reply_text: str, tool_messages: list[ToolMessage]) -> list[dict]:
    """Returns raw, already-validated UI block dicts ready to attach to the
    assistant message's metadata. Never raises: any failure — including a
    structured-output validation error, in case a future model swap enforces
    the schema less strictly than Claude does — means no UI blocks are
    attached, not a broken chat turn."""
    if not tool_messages:
        return []

    try:
        model = get_chat_model().with_structured_output(GenerativeUiSelection)
        selection = await model.ainvoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Assistant's reply:\n{reply_text}\n\n"
                        f"Tool data from this turn:\n{_tool_data_summary(tool_messages)}"
                    )
                ),
            ],
            config={"tags": ["generative-ui"]},
        )
        assert isinstance(selection, GenerativeUiSelection)
    except Exception:  # noqa: BLE001 - a UI-selection failure should never break the chat reply
        logger.warning("generative UI agent failed; continuing without UI blocks", exc_info=True)
        return []

    # Re-validate through the same untrusted-input pipeline the rest of the
    # app uses, even though `with_structured_output` already enforced the
    # schema once — cheap insurance against a future provider that doesn't.
    raw = [block.model_dump(mode="json") for block in selection.blocks]
    result = validate_ui_blocks(raw)
    if result.rejected:
        logger.warning("generative UI agent produced %d invalid block(s): %s", len(result.rejected), result.rejected)
    return [block.model_dump(mode="json") for block in result.blocks]
