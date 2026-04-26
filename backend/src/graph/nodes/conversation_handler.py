"""Conversation handler - asks the user clarifying questions or classifies their intent.

Phase 1/4:
- If we are in phase "clarify", we use ClarifyingQuestions to get more context.
- If we are in phase "iterate", we use IntentClassification to figure out what the user wants to do with their plan.
"""

from __future__ import annotations

from typing import Any

from ...llm.client import get_llm_client
from ...logging_config import get_logger
from ...prompts.coordinator import ClarifyingQuestions
from ...prompts.coordinator import build_prompt as build_coordinator_prompt
from ...prompts.intent import IntentClassification
from ...settings import get_settings
from ..state import AdvisorState

logger = get_logger(__name__)


async def conversation_handler_node(state: AdvisorState) -> dict[str, Any]:
    """Generate clarifying questions OR classify intent based on current_phase."""
    request_id = state.get("metadata", {}).get("request_id", "unknown")
    settings = get_settings()
    client = get_llm_client()

    current_phase = state.get("current_phase")

    if current_phase == "clarify":
        messages = build_coordinator_prompt(dict(state))
        try:
            questions = await client.complete_structured(
                messages=messages,
                schema=ClarifyingQuestions,
                request_id=request_id,
                phase="clarify",
                model=settings.openai_default_model,
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as exc:
            logger.error("clarify.failed", request_id=request_id, error=str(exc))
            return {
                "errors": [f"clarify: {exc}"],
                "current_phase": None,
            }

        logger.info(
            "clarify.complete",
            request_id=request_id,
            question_count=len(questions.questions),
        )

        metadata = dict(state.get("metadata", {}))
        metadata["clarifying_questions"] = [q.model_dump() for q in questions.questions]
        return {"metadata": metadata, "current_phase": None}

    # If it's an iteration (e.g. current_phase == "iterate")
    if current_phase == "iterate":
        # Extract the last user message from the state transcript
        user_msgs = [m for m in state.get("messages", []) if m.get("role") == "user"]
        latest_msg = user_msgs[-1]["content"] if user_msgs else state.get("idea")

        # Get plan context to help with classification
        plan_context = ""
        if state.get("final_plan"):
            plan_dict = state["final_plan"].model_dump(mode="json") if hasattr(state["final_plan"], "model_dump") else state["final_plan"]
            plan_context = f"\nThe plan includes these phases: {', '.join([k for k in plan_dict.keys() if k not in ['plan_id', 'created_at', 'total_cost_usd']])}"

        system_msg = (
            "You are an intent classifier for the AI Build Advisor. The user just sent a message about their existing plan.\n"
            "Classify their intent based on the message. The plan has already been generated.\n\n"
            "Valid intents:\n"
            "- 'edit': User wants to change/modify a specific part of the plan (e.g., 'change the database to MongoDB')\n"
            "- 'what_if': User wants to explore an alternative scenario (e.g., 'what if we used AWS instead?')\n"
            "- 'deep_dive': User wants MORE detail/explanation about a specific phase (e.g., 'explain the infrastructure', 'I don't understand the architecture')\n"
            "- 'challenge': User is questioning or disagreeing with a recommendation (e.g., 'why did you choose X?', 'I disagree with Y')\n"
            "- 'chat': General conversation, acknowledgment, or questions not about the plan specifics\n\n"
            "IMPORTANT: If the user says they 'don't understand' or asks 'explain' or 'tell me more about' a specific phase, "
            "classify it as 'deep_dive', NOT 'chat'.\n"
            f"{plan_context}"
        )

        try:
            intent = await client.complete_structured(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": latest_msg}
                ],
                schema=IntentClassification,
                request_id=request_id,
                phase="classify_intent",
                model=settings.openai_default_model,
                temperature=0.0,
            )
        except Exception as exc:
            logger.error("classify.failed", request_id=request_id, error=str(exc))
            return {"errors": [f"classify: {exc}"], "current_phase": None}

        logger.info("classify.complete", request_id=request_id, intent=intent.intent, target_phase=intent.target_phase)

        # Now we route based on the intent. For now, we will just return the intent
        # in the metadata so the coordinator/builder can route it.
        metadata = dict(state.get("metadata", {}))
        metadata["intent_classification"] = intent.model_dump()

        # Mark dirty phases if edit/what_if
        dirty = []
        if intent.intent in ("edit", "what_if") and intent.affected_phases:
            dirty = intent.affected_phases

        return {
            "metadata": metadata,
            # Hand control back to the coordinator. It routes based on
            # metadata.intent_classification + dirty_phases.
            "current_phase": None,
            "dirty_phases": dirty,
        }

    return {"current_phase": None}
