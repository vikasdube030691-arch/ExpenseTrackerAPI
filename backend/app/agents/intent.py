from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_chat_model
from app.agents.state import Intent

_SYSTEM_PROMPT = """You classify a message to an AI expense-tracking assistant into exactly one \
intent category, based on what the user is asking for:

- expense: searching, adding, updating, deleting, or categorizing transactions.
- analytics: monthly analysis, period comparisons, spending trends, top categories, savings analysis.
- budget: budgets, budget usage, overspending, budget recommendations.
- report: generating or retrieving monthly/category reports or period-comparison reports.
- memory: explicitly asking you to remember, recall, update, or forget something about them.
- general: greetings, small talk, or anything unclear/unrelated to the above.

Pick the single best match."""


class IntentClassification(BaseModel):
    intent: Intent = Field(description="The single best-matching intent category.")


async def classify_intent(message: str) -> IntentClassification:
    model = get_chat_model().with_structured_output(IntentClassification)
    result = await model.ainvoke(
        [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=message)],
        config={"tags": ["intent-detection"]},
    )
    assert isinstance(result, IntentClassification)  # narrows with_structured_output's Any-ish return type
    return result
