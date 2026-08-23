from app.agents.domain_agent import DomainAgent

SYSTEM_PROMPT = """You are the assistant for an AI expense tracker app. The user's message wasn't \
about a specific expense, analytics, budget, report, or memory request — greet them, answer \
generally, or ask a clarifying question about their finances. Keep it brief and steer toward what \
the app can help with (tracking transactions, budgets, spending analysis, reports) when relevant."""

# No tools: the router only sends genuinely general/unclear messages here, so
# there is nothing in this agent's own scope for it to look up.
general_agent = DomainAgent(name="general", system_prompt=SYSTEM_PROMPT, build_tools=lambda _database, _user_id: [])
