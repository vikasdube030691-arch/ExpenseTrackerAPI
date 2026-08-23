from mongomock_motor import AsyncMongoMockClient

from app.agents.graph import AGENTS_BY_INTENT, _route_by_intent, build_graph


def test_every_intent_has_a_registered_agent():
    assert set(AGENTS_BY_INTENT) == {"expense", "analytics", "budget", "report", "memory", "general"}
    for intent, agent in AGENTS_BY_INTENT.items():
        assert agent.name == intent


def test_route_by_intent_dispatches_to_the_matching_agent_name():
    for intent in AGENTS_BY_INTENT:
        assert _route_by_intent({"intent": intent}) == intent


def test_route_by_intent_defaults_to_general_when_missing():
    assert _route_by_intent({}) == "general"


async def test_build_graph_compiles_and_has_every_expected_node():
    client = AsyncMongoMockClient()
    database = client["expensedb_test"]

    compiled = build_graph(database)

    node_names = set(compiled.get_graph().nodes)
    for expected in ("load_memories", "detect_intent", *AGENTS_BY_INTENT, "generative_ui"):
        assert expected in node_names
