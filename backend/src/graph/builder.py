"""Compile the LangGraph state machine.

Wiring:

  START
    -> coordinator
         -> conversation_handler -> END        (clarify branch)
         -> phase_worker -> coordinator        (loop until all 9 phases done)
         -> red_team -> synthesizer -> END     (final assembly)

The conditional edge after ``coordinator`` uses ``coordinator_route`` which
inspects ``state.current_phase``:

- "clarify"  -> conversation_handler
- None       -> red_team    (all phases complete)
- "phase_X"  -> phase_worker
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..services.checkpointing import get_checkpointer
from .nodes.chat_responder import chat_responder_node
from .nodes.conversation_handler import conversation_handler_node
from .nodes.coordinator import coordinator_node, coordinator_route
from .nodes.phase_worker import phase_worker_node
from .nodes.red_team import red_team_node
from .nodes.researcher import researcher_node
from .nodes.synthesizer import synthesizer_node
from .state import AdvisorState


def _conversation_handler_route(state: AdvisorState) -> str:
    """Stop after asking clarifying questions.

    The clarify path is meant to be one-shot: ask questions, stream them to the client,
    then END so the user can answer. Without this, the coordinator will re-enter
    clarify and loop.
    """
    meta = state.get("metadata", {}) or {}
    if meta.get("clarifying_questions") and not (state.get("clarifying_answers") or {}):
        return END
    return "coordinator"


def build_graph():
    """Return a compiled LangGraph ready for ``ainvoke`` / ``astream``."""
    checkpointer = get_checkpointer()
    graph = StateGraph(AdvisorState)

    graph.add_node("coordinator", coordinator_node)
    graph.add_node("conversation_handler", conversation_handler_node)
    graph.add_node("phase_worker", phase_worker_node)
    graph.add_node("red_team", red_team_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("chat_responder", chat_responder_node)
    graph.add_node("researcher", researcher_node)

    graph.add_edge(START, "coordinator")

    graph.add_conditional_edges(
        "coordinator",
        coordinator_route,
        {
            "conversation_handler": "conversation_handler",
            "phase_worker": "phase_worker",
            "red_team": "red_team",
            "synthesizer": "synthesizer",
            "chat_responder": "chat_responder",
            "researcher": "researcher",
        },
    )

    graph.add_edge("phase_worker", "coordinator")
    graph.add_edge("researcher", "coordinator")
    graph.add_conditional_edges(
        "conversation_handler",
        _conversation_handler_route,
        {
            "coordinator": "coordinator",
            END: END,
        },
    )
    graph.add_edge("chat_responder", END)
    graph.add_edge("red_team", "synthesizer")
    graph.add_edge("synthesizer", END)

    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()
