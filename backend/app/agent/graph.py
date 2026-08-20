"""Builds the LangGraph recovery graph.

    ingest -> triage -> enrich -> score -> route ---> plan_retries -----------> compose -> guardrail -> execute -> END
                                             |------> plan_action_required -->/
                                             `------> escalate -----------------------------------------------> END

Each node that touches the database takes `session` as a second argument; the
graph is built fresh per invocation via `build_graph(session)`, binding that
session into every node with `functools.partial` so LangGraph's node
signature (state -> partial state) stays uniform.

Checkpointed with `AsyncSqliteSaver` keyed on `thread_id = case_id`, so a
case's run can be streamed, resumed, or re-invoked (e.g. after an outcome
webhook) without losing prior state.
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.nodes.compose import compose
from app.agent.nodes.enrich import enrich
from app.agent.nodes.escalate import escalate
from app.agent.nodes.execute import execute
from app.agent.nodes.guardrail import guardrail
from app.agent.nodes.ingest import ingest
from app.agent.nodes.plan_action_required import plan_action_required
from app.agent.nodes.plan_retries import plan_retries
from app.agent.nodes.route import route
from app.agent.nodes.score import score
from app.agent.nodes.triage import triage
from app.agent.state import RecoveryState


def build_graph(session: AsyncSession) -> StateGraph:
    """Wire nodes into a StateGraph bound to `session` for this invocation."""
    graph = StateGraph(RecoveryState)

    graph.add_node("ingest", partial(ingest, session=session))
    graph.add_node("triage", triage)
    graph.add_node("enrich", partial(enrich, session=session))
    graph.add_node("score", score)
    graph.add_node("plan_retries", partial(plan_retries, session=session))
    graph.add_node("plan_action_required", partial(plan_action_required, session=session))
    graph.add_node("compose", compose)
    graph.add_node("guardrail", guardrail)
    graph.add_node("execute", partial(execute, session=session))
    graph.add_node("escalate", partial(escalate, session=session))

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "triage")
    graph.add_edge("triage", "enrich")
    graph.add_edge("enrich", "score")
    graph.add_conditional_edges(
        "score",
        route,
        {
            "plan_retries": "plan_retries",
            "compose_action_required": "plan_action_required",
            "escalate": "escalate",
        },
    )
    graph.add_edge("plan_retries", "compose")
    graph.add_edge("plan_action_required", "compose")
    graph.add_edge("compose", "guardrail")
    graph.add_edge("guardrail", "execute")
    graph.add_edge("execute", END)
    graph.add_edge("escalate", END)

    return graph
