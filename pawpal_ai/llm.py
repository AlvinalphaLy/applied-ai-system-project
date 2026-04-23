from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class LanguageModel(Protocol):
    def generate(self, prompt: str) -> str:
        ...


@dataclass
class RuleBasedModel:
    """Deterministic fallback so the project runs without API keys."""

    def generate(self, prompt: str) -> str:
        if "STEP-BY-STEP PLAN" in prompt:
            return (
                "1. Review today's tasks sorted by priority and time.\n"
                "2. Allocate tasks that fit the daily time budget.\n"
                "3. Insert medication and feeding tasks first.\n"
                "4. Add enrichment tasks in remaining open slots.\n"
                "5. Return a concise schedule and explain why each task appears."
            )
        return "The response could not be generated."


class OpenAIChatModel:
    def __init__(self, model_name: str = "gpt-4o-mini") -> None:
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed.") from exc

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=self.model_name,
            input=prompt,
            temperature=0.2,
        )
        return response.output_text.strip()


def load_model() -> LanguageModel:
    provider = os.getenv("PAWPAL_MODEL_PROVIDER", "rule-based").lower()
    if provider == "openai":
        return OpenAIChatModel(model_name=os.getenv("PAWPAL_OPENAI_MODEL", "gpt-4o-mini"))
    return RuleBasedModel()
