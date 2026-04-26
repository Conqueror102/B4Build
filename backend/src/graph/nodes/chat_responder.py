"""Chat responder node - replies to 'chat' and 'challenge' intents without modifying the plan."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from ...llm.client import get_llm_client
from ...logging_config import get_logger
from ...settings import get_settings
from ..state import AdvisorState

logger = get_logger(__name__)


class ChatResponse(BaseModel):
    response: str = Field(description="The conversational response to the user.")


def _extract_relevant_context(plan_dict: dict, user_message: str) -> str:
    """Extract relevant parts of the plan based on what the user is asking about."""
    message_lower = user_message.lower()
    
    # Map keywords to plan sections
    phase_keywords = {
        "pressure": ["pressure_test"],
        "viable": ["pressure_test"],
        "problem": ["problem_model_fit"],
        "model": ["problem_model_fit"],
        "architecture": ["architecture"],
        "arch": ["architecture"],
        "component": ["architecture"],
        "build": ["build_buy_train"],
        "buy": ["build_buy_train"],
        "train": ["build_buy_train"],
        "vendor": ["build_buy_train"],
        "github": ["build_buy_train"],
        "oss": ["build_buy_train"],
        "tools": ["build_buy_train"],
        "infrastructure": ["infrastructure"],
        "infra": ["infrastructure"],
        "hosting": ["infrastructure"],
        "deploy": ["infrastructure"],
        "cost": ["cost_model"],
        "price": ["cost_model"],
        "budget": ["cost_model"],
        "security": ["security"],
        "auth": ["security"],
        "pii": ["security"],
        "observability": ["observability"],
        "monitoring": ["observability"],
        "metrics": ["observability"],
        "logging": ["observability"],
        "scaling": ["scaling"],
        "scale": ["scaling"],
        "bottleneck": ["scaling"],
        "red team": ["red_team"],
        "critique": ["red_team"],
        "risk": ["red_team"],
    }
    
    # Find which sections are relevant
    relevant_sections = set()
    for keyword, sections in phase_keywords.items():
        if keyword in message_lower:
            relevant_sections.update(sections)
    
    # If no specific section found, include executive summary and a few key sections
    if not relevant_sections:
        relevant_sections = {"executive_summary", "next_steps", "idea"}
    
    # Build context from relevant sections
    context_parts = []
    for section in relevant_sections:
        if section in plan_dict and plan_dict[section]:
            context_parts.append(f"## {section.replace('_', ' ').title()}\n{json.dumps(plan_dict[section], default=str, indent=2)}")
    
    # Add metadata
    if "plan_id" in plan_dict:
        context_parts.insert(0, f"Plan ID: {plan_dict['plan_id']}")
    if "idea" in plan_dict and "idea" not in relevant_sections:
        context_parts.insert(1, f"Original Idea: {plan_dict['idea']}")
    
    return "\n\n".join(context_parts)


async def chat_responder_node(state: AdvisorState) -> dict[str, Any]:
    """Generate a conversational reply based on the plan and user message."""
    request_id = state.get("metadata", {}).get("request_id", "unknown")
    settings = get_settings()
    client = get_llm_client()

    user_msgs = [m for m in state.get("messages", []) if m.get("role") == "user"]
    latest_msg = user_msgs[-1]["content"] if user_msgs else state.get("idea")

    intent_metadata = state.get("metadata", {}).get("intent_classification", {})
    intent_str = intent_metadata.get("intent", "chat")
    target_phase = intent_metadata.get("target_phase")

    system_msg = (
        "You are the AI Build Advisor. You have already generated a comprehensive architecture plan for the user.\n"
        f"The user has sent a follow-up message with the intent: '{intent_str}'.\n\n"
    )

    if state.get("final_plan"):
        plan_dict = state["final_plan"].model_dump(mode="json") if hasattr(state["final_plan"], "model_dump") else state["final_plan"]
        
        # Extract relevant context based on what the user is asking about
        relevant_context = _extract_relevant_context(plan_dict, latest_msg)
        
        system_msg += f"Here is the relevant context from the plan:\n\n{relevant_context}\n\n"

    if intent_str == "deep_dive":
        system_msg += (
            "The user wants a deeper explanation of a specific part of the plan. "
            "Provide detailed reasoning, trade-offs, and implementation considerations. "
            "Reference specific details from the plan context above."
        )
    elif intent_str == "challenge":
        system_msg += (
            "The user is challenging or questioning a recommendation in the plan. "
            "Explain your reasoning clearly, acknowledge valid concerns, and discuss trade-offs. "
            "Be specific and reference the plan details."
        )
    else:
        system_msg += (
            "Reply directly and conversationally to the user. Answer their question using the specific "
            "context from the plan above. Be helpful and specific, not generic."
        )

    try:
        reply = await client.complete_structured(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": latest_msg}
            ],
            schema=ChatResponse,
            request_id=request_id,
            phase="chat_responder",
            model=settings.openai_default_model,
            temperature=0.4,
        )
    except Exception as exc:
        logger.error("chat_responder.failed", request_id=request_id, error=str(exc))
        return {"errors": [f"chat_responder: {exc}"], "current_phase": None}

    logger.info("chat_responder.complete", request_id=request_id, intent=intent_str)

    # Add the assistant's reply to the message history so the frontend gets it
    # We also mark the intent as handled so coordinator knows we are done.
    metadata = dict(state.get("metadata", {}))
    if "intent_classification" in metadata:
        metadata["intent_classification"]["handled"] = True

    return {
        "metadata": metadata,
        "messages": [{"role": "assistant", "content": reply.response}],
        "current_phase": None,
    }
