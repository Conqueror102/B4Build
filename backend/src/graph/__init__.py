"""LangGraph state machine that runs the 9-phase advisor.

The shape of this package:
- ``state.py``   - ``AdvisorState`` TypedDict (graph-wide shared state)
- ``builder.py`` - ``build_graph()`` returns a compiled ``CompiledStateGraph``
- ``nodes/``     - the five node implementations (coordinator, phase_worker,
                   conversation_handler, red_team, synthesizer)
"""

from .builder import build_graph
from .state import AdvisorState, new_state

__all__ = ["AdvisorState", "build_graph", "new_state"]
