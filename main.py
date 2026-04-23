from __future__ import annotations

from datetime import date

from pawpal_ai.agent import PawPalAgent
from pawpal_ai.logging_utils import configure_logging
from pawpal_ai.models import Owner
from pawpal_ai.rag import KnowledgeBaseRetriever
from pawpal_ai.scheduler import Scheduler


def load_default_owner() -> Owner:
    owner = Owner.load_from_json("assets/demo_owner.json")
    for pet in owner.pets:
        for task in pet.tasks:
            task.due_date = date.today()
    return owner


def print_schedule(scheduler: Scheduler) -> None:
    print("\nPriority Plan")
    print("-" * 40)
    schedule = scheduler.build_priority_plan()
    if not schedule:
        print("No tasks for today.")
        return

    for task in schedule:
        print(
            f"{task.time} | {task.pet_name:<8} | {task.description:<20} "
            f"| {task.priority:<6} | {task.duration_minutes} min"
        )


def main() -> None:
    configure_logging()
    owner = load_default_owner()
    scheduler = Scheduler(owner)
    retriever = KnowledgeBaseRetriever("assets/knowledge_base.json")
    agent = PawPalAgent(scheduler=scheduler, retriever=retriever)

    print_schedule(scheduler)

    query = (
        "Build a safe schedule for today, prioritize medication, "
        "and explain why this ordering works."
    )
    response = agent.run(query)

    print("\nAssistant Output")
    print("-" * 40)
    print(response.answer)
    print("\nCitations:", ", ".join(response.citations) if response.citations else "none")
    print("Checks:", ", ".join(response.checks) if response.checks else "none")


if __name__ == "__main__":
    main()
