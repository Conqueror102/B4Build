"""LangGraph node implementations.

The graph is intentionally small (5 nodes) and lets the polymorphic
``phase_worker`` handle the 9 advisor phases by looking each one up in
``src.prompts.PHASE_REGISTRY``.
"""

from . import conversation_handler, coordinator, phase_worker, red_team, synthesizer

__all__ = [
    "conversation_handler",
    "coordinator",
    "phase_worker",
    "red_team",
    "synthesizer",
]
