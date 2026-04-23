from datetime import date

from pawpal_ai.agent import PawPalAgent
from pawpal_ai.llm import LanguageModel
from pawpal_ai.models import Owner, Pet, Task
from pawpal_ai.rag import KnowledgeBaseRetriever
from pawpal_ai.scheduler import Scheduler


class FakeModel(LanguageModel):
    def generate(self, prompt: str) -> str:
        return (
            "Start with Medication, then Morning walk. "
            "Medication timing supports safety and conflict management."
        )


def test_retriever_returns_relevant_chunks() -> None:
    retriever = KnowledgeBaseRetriever("assets/knowledge_base.json")
    hits = retriever.retrieve("How should I schedule medication and conflicts?", top_k=2)

    assert hits
    assert hits[0].chunk.chunk_id in {"kb-001", "kb-004"}


def test_agent_pipeline_returns_citations_and_checks() -> None:
    owner = Owner("Jordan", available_minutes_per_day=60)
    pet = Pet("Pixel", "cat")
    owner.add_pet(pet)
    owner.add_task_to_pet(
        "Pixel",
        Task(
            description="Medication",
            time="08:00",
            priority="high",
            duration_minutes=10,
            due_date=date.today(),
        ),
    )

    scheduler = Scheduler(owner)
    retriever = KnowledgeBaseRetriever("assets/knowledge_base.json")
    agent = PawPalAgent(scheduler=scheduler, retriever=retriever, model=FakeModel())

    response = agent.run("Plan medication first and explain why")

    assert "Medication" in response.answer
    assert response.citations
    assert any(check.startswith("quality:") for check in response.checks)
