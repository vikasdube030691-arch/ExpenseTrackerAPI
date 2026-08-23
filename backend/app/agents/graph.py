"""Builds the LangGraph state graph implementing:

    User Query -> Intent Detection -> Supervisor -> Appropriate Agent
                -> (tools -> data -> analysis -> LLM response, inside the agent)
                -> Generative UI Agent -> END

`build_graph(database)` closes over the request's `AsyncIOMotorDatabase` handle;
`user_id` travels in the graph state (set once by `app/agents/runner.py` from
the authenticated request, read but never written by any LLM-driven node).
"""

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agents.analytics_agent import analytics_agent
from app.agents.budget_agent import budget_agent
from app.agents.domain_agent import DomainAgent
from app.agents.expense_agent import expense_agent
from app.agents.general_agent import general_agent
from app.agents.generative_ui_agent import choose_ui_blocks
from app.agents.intent import classify_intent
from app.agents.memory_agent import memory_agent
from app.agents.report_agent import report_agent
from app.agents.state import AgentState
from app.agents.tool_loop import extract_text
from app.services.user_memory_service import UserMemoryService

AGENTS_BY_INTENT: dict[str, DomainAgent] = {
    "expense": expense_agent,
    "analytics": analytics_agent,
    "budget": budget_agent,
    "report": report_agent,
    "memory": memory_agent,
    "general": general_agent,
}


def _make_load_memories_node(database: AsyncIOMotorDatabase):
    async def load_memories(state: AgentState) -> dict[str, Any]:
        service = UserMemoryService(database)
        memories = await service.recall(state["user_id"], limit=10)
        return {"memories": [memory.content for memory in memories]}

    return load_memories


async def _detect_intent(state: AgentState) -> dict[str, Any]:
    last_human = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    text = extract_text(last_human.content) if last_human is not None else ""
    classification = await classify_intent(text)
    return {"intent": classification.intent}


def _route_by_intent(state: AgentState) -> str:
    return state.get("intent", "general")


def _make_agent_node(agent: DomainAgent, database: AsyncIOMotorDatabase):
    async def run_agent(state: AgentState) -> dict[str, Any]:
        ai_message, tool_messages = await agent.run(
            database, state["user_id"], state["messages"], state.get("memories", [])
        )
        return {
            "messages": [ai_message],
            "agent_reply": extract_text(ai_message.content),
            "tool_messages": tool_messages,
        }

    return run_agent


async def _generative_ui_node(state: AgentState) -> dict[str, Any]:
    blocks = await choose_ui_blocks(state.get("agent_reply", ""), state.get("tool_messages", []))
    return {"ui_blocks": blocks}


def build_graph(database: AsyncIOMotorDatabase) -> CompiledStateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("load_memories", _make_load_memories_node(database))
    graph.add_node("detect_intent", _detect_intent)
    for intent, agent in AGENTS_BY_INTENT.items():
        graph.add_node(intent, _make_agent_node(agent, database))
    graph.add_node("generative_ui", _generative_ui_node)

    graph.set_entry_point("load_memories")
    graph.add_edge("load_memories", "detect_intent")
    graph.add_conditional_edges("detect_intent", _route_by_intent, {intent: intent for intent in AGENTS_BY_INTENT})
    for intent in AGENTS_BY_INTENT:
        graph.add_edge(intent, "generative_ui")
    graph.add_edge("generative_ui", END)

    return graph.compile()
