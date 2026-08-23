"""A `DomainAgent` bundles a system prompt with a tool factory. All five
tool-using agents (expense, analytics, budget, report, memory) are just
configuration on top of the shared loop in `app/agents/tool_loop.py`.
"""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agents.tool_loop import run_tool_calling_agent, stream_tool_calling_agent

ToolFactory = Callable[[AsyncIOMotorDatabase, str], list[BaseTool]]


@dataclass(frozen=True)
class DomainAgent:
    name: str
    system_prompt: str
    build_tools: ToolFactory

    def _full_system_prompt(self, memories: list[str]) -> str:
        if not memories:
            return self.system_prompt
        memory_block = "\n".join(f"- {memory}" for memory in memories)
        return f"{self.system_prompt}\n\nRemembered context about this user:\n{memory_block}"

    async def run(
        self,
        database: AsyncIOMotorDatabase,
        user_id: str,
        messages: list[BaseMessage],
        memories: list[str],
    ) -> tuple[AIMessage, list[ToolMessage]]:
        tools = self.build_tools(database, user_id)
        return await run_tool_calling_agent(
            self._full_system_prompt(memories), tools, messages, tags=[f"agent:{self.name}", "final-response"]
        )

    def stream(
        self,
        database: AsyncIOMotorDatabase,
        user_id: str,
        messages: list[BaseMessage],
        memories: list[str],
        *,
        collected_tool_messages: list[ToolMessage] | None = None,
    ) -> AsyncIterator[str]:
        tools = self.build_tools(database, user_id)
        return stream_tool_calling_agent(
            self._full_system_prompt(memories),
            tools,
            messages,
            tags=[f"agent:{self.name}", "final-response"],
            collected_tool_messages=collected_tool_messages,
        )
