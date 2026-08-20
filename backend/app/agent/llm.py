"""The agent's LLM client.

Wraps `ChatGroq` behind `get_llm()` so every node asks for a model the same
way regardless of whether a real Groq key is configured. Nodes should not
import `langchain_groq` directly — this keeps the "does Groq run or not"
decision in exactly one place, matching `settings.groq_enabled`.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_groq import ChatGroq

from app.core.config import settings


@lru_cache
def get_llm() -> ChatGroq:
    """Return a configured ChatGroq client.

    Callers must check `settings.groq_enabled` first — nodes that need
    structured/tool-calling output fall back to a deterministic stub
    implementation when it's False, rather than calling this and failing.
    """
    return ChatGroq(
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        max_retries=settings.groq_max_retries,
        timeout=settings.groq_timeout_seconds,
        api_key=settings.groq_api_key,
    )
