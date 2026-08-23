from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from app.agents import tool_loop
from tests.agents.fakes import FakeToolCallingChatModel


@tool
def get_summary() -> dict:
    """Returns a fake spending summary."""
    return {"total_expense": 100}


async def test_run_tool_calling_agent_executes_a_tool_then_returns_final_answer(monkeypatch):
    fake_model = FakeToolCallingChatModel(
        responses=[
            AIMessage(content="", tool_calls=[{"name": "get_summary", "args": {}, "id": "call_1"}]),
            AIMessage(content="You spent $100 this month."),
        ]
    )
    monkeypatch.setattr(tool_loop, "get_chat_model", lambda: fake_model)

    final_message, tool_messages = await tool_loop.run_tool_calling_agent(
        "system prompt", [get_summary], [HumanMessage(content="how much did I spend?")]
    )

    assert final_message.content == "You spent $100 this month."
    assert len(tool_messages) == 1
    assert "100" in tool_messages[0].content


async def test_run_tool_calling_agent_reports_unknown_tool_without_crashing(monkeypatch):
    fake_model = FakeToolCallingChatModel(
        responses=[
            AIMessage(content="", tool_calls=[{"name": "does_not_exist", "args": {}, "id": "call_1"}]),
            AIMessage(content="Sorry, I couldn't do that."),
        ]
    )
    monkeypatch.setattr(tool_loop, "get_chat_model", lambda: fake_model)

    final_message, tool_messages = await tool_loop.run_tool_calling_agent(
        "system prompt", [get_summary], [HumanMessage(content="do the impossible")]
    )

    assert final_message.content == "Sorry, I couldn't do that."
    assert "error" in tool_messages[0].content.lower()


async def test_run_tool_calling_agent_terminates_at_the_iteration_cap(monkeypatch):
    # Every response calls a tool, never giving a plain-text answer — the loop
    # must still terminate (via the cap-hit fallback call) rather than looping forever.
    fake_model = FakeToolCallingChatModel(
        responses=[AIMessage(content="", tool_calls=[{"name": "get_summary", "args": {}, "id": "call_1"}])]
    )
    monkeypatch.setattr(tool_loop, "get_chat_model", lambda: fake_model)

    final_message, _ = await tool_loop.run_tool_calling_agent(
        "system prompt", [get_summary], [HumanMessage(content="loop forever")]
    )

    # The cap-hit fallback call reuses the same cycling fake model, so it
    # returns the same scripted (tool-calling) message — the important
    # assertion is just that the loop returned at all instead of hanging.
    assert final_message is not None


async def test_stream_tool_calling_agent_yields_final_text_and_collects_tool_messages(monkeypatch):
    fake_model = FakeToolCallingChatModel(
        responses=[
            AIMessage(content="", tool_calls=[{"name": "get_summary", "args": {}, "id": "call_1"}]),
            AIMessage(content="You spent $100 this month."),
        ]
    )
    monkeypatch.setattr(tool_loop, "get_chat_model", lambda: fake_model)

    collected: list = []
    chunks = [
        chunk
        async for chunk in tool_loop.stream_tool_calling_agent(
            "system prompt",
            [get_summary],
            [HumanMessage(content="how much did I spend?")],
            collected_tool_messages=collected,
        )
    ]

    assert "".join(chunks) == "You spent $100 this month."
    assert len(collected) == 1
