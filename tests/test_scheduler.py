from datetime import date, timedelta

from pawpal_ai.models import Owner, Pet, Task
from pawpal_ai.scheduler import Scheduler


def test_priority_sorting_orders_high_first() -> None:
    owner = Owner("Jordan")
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    owner.add_task_to_pet("Mochi", Task(description="low", time="09:00", priority="low"))
    owner.add_task_to_pet("Mochi", Task(description="high", time="10:00", priority="high"))

    scheduler = Scheduler(owner)
    ordered = scheduler.sort_by_priority_then_time()
    assert [task.description for task in ordered] == ["high", "low"]


def test_daily_recurrence_creates_followup() -> None:
    owner = Owner("Jordan")
    pet = Pet("Pixel", "cat")
    owner.add_pet(pet)

    base_date = date.today()
    task = Task(description="meds", time="08:00", frequency="daily", due_date=base_date)
    owner.add_task_to_pet("Pixel", task)
    scheduler = Scheduler(owner)

    next_task = scheduler.mark_task_complete(task)
    assert next_task is not None
    assert next_task.due_date == base_date + timedelta(days=1)


def test_detect_conflicts() -> None:
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog")
    cat = Pet("Pixel", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    owner.add_task_to_pet("Mochi", Task(description="walk", time="08:00"))
    owner.add_task_to_pet("Pixel", Task(description="meds", time="08:00"))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(scheduler.generate_daily_schedule())
    assert warnings
    assert "Conflict at 08:00" in warnings[0]
