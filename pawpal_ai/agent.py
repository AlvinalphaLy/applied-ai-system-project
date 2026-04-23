from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import List

from .guardrails import validate_user_query
from .llm import LanguageModel, load_model
from .rag import KnowledgeBaseRetriever, RetrievalHit
from .scheduler import Scheduler

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    answer: str
    citations: List[str]
    checks: List[str]


class PawPalAgent:
    """Plan -> retrieve -> act -> evaluate workflow."""

    def __init__(self, scheduler: Scheduler, retriever: KnowledgeBaseRetriever, model: LanguageModel | None = None) -> None:
        self.scheduler = scheduler
        self.retriever = retriever
        self.model = model or load_model()

    def run(self, user_query: str, target_date: date | None = None) -> AgentResponse:
        guardrail = validate_user_query(user_query)
        if not guardrail.allowed:
            logger.warning("Guardrail blocked request: %s", guardrail.reason)
            return AgentResponse(
                answer=f"Request blocked: {guardrail.reason}",
                citations=[],
                checks=["guardrail:blocked"],
            )

        day = target_date or date.today()
        todays_plan = self.scheduler.build_priority_plan(day)
        retrieved = self.retriever.retrieve(user_query, top_k=3)
        context = self.retriever.format_context(retrieved)
        schedule_text = self._format_schedule(todays_plan)

        prompt = (
            "You are PawPal+, a pet-care planning assistant.\n"
            "Use retrieved evidence and the schedule to answer the user.\n"
            "Return concise recommendations and explain tradeoffs.\n\n"
            f"USER QUESTION:\n{user_query}\n\n"
            "STEP-BY-STEP PLAN:\n"
            "1) prioritize safety and required tasks\n"
            "2) fit tasks into time budget\n"
            "3) explain with evidence\n\n"
            f"SCHEDULE CANDIDATES:\n{schedule_text}\n\n"
            f"RETRIEVED KNOWLEDGE:\n{context}\n"
        )

        answer = self.model.generate(prompt)
        if todays_plan:
            top_task = todays_plan[0]
            answer = (
                f"{answer}\n\n"
                f"Grounded top task: {top_task.description} for {top_task.pet_name} at {top_task.time}."
            )
        checks = self._evaluate(answer, todays_plan, retrieved)
        citations = [hit.chunk.chunk_id for hit in retrieved]

        return AgentResponse(answer=answer, citations=citations, checks=checks)

    def _format_schedule(self, tasks) -> str:
        if not tasks:
            return "No tasks available for this date."
        lines = []
        for task in tasks:
            lines.append(
                f"- {task.time} | {task.pet_name} | {task.description} | "
                f"{task.priority} | {task.duration_minutes} min"
            )
        return "\n".join(lines)

    def _evaluate(self, answer: str, tasks, hits: List[RetrievalHit]) -> List[str]:
        results: List[str] = []
        if len(answer.strip()) >= 40:
            results.append("quality:length_ok")
        else:
            results.append("quality:too_short")

        if tasks:
            first_task = tasks[0].description.lower()
            if first_task in answer.lower():
                results.append("grounding:mentions_top_task")
            else:
                results.append("grounding:missed_top_task")

        if hits:
            evidence_word = hits[0].chunk.title.split()[0].lower()
            if evidence_word in answer.lower():
                results.append("grounding:mentions_retrieval")
            else:
                results.append("grounding:no_retrieval_reference")

        return results
