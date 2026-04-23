from __future__ import annotations

from datetime import date

import streamlit as st

from pawpal_ai.agent import PawPalAgent
from pawpal_ai.logging_utils import configure_logging
from pawpal_ai.models import Owner, Pet, Task
from pawpal_ai.rag import KnowledgeBaseRetriever
from pawpal_ai.scheduler import Scheduler

DATA_FILE = "assets/demo_owner.json"
KNOWLEDGE_FILE = "assets/knowledge_base.json"

configure_logging()
st.set_page_config(page_title="PawPal+ AI", layout="wide")
st.title("PawPal+ AI Planner")
st.caption("Starter project expanded with integrated RAG and agentic plan-act-check workflow.")

if "owner" not in st.session_state:
    st.session_state.owner = Owner.load_from_json(DATA_FILE)
    for pet in st.session_state.owner.pets:
        for task in pet.tasks:
            task.due_date = date.today()

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)
retriever = KnowledgeBaseRetriever(KNOWLEDGE_FILE)
agent = PawPalAgent(scheduler=scheduler, retriever=retriever)

st.subheader("Owner and Pets")
owner_name = st.text_input("Owner name", value=owner.name)
owner.name = owner_name

pet_col1, pet_col2, pet_col3, pet_col4 = st.columns(4)
with pet_col1:
    pet_name = st.text_input("Pet name", key="pet_name")
with pet_col2:
    pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="pet_species")
with pet_col3:
    pet_age = st.number_input("Age", min_value=0, max_value=40, value=2, key="pet_age")
with pet_col4:
    if st.button("Add pet"):
        try:
            owner.add_pet(Pet(name=pet_name.strip(), species=pet_species, age=int(pet_age)))
            owner.save_to_json(DATA_FILE)
            st.success("Pet added")
        except ValueError as exc:
            st.warning(str(exc))

if owner.pets:
    st.dataframe(
        [
            {
                "name": pet.name,
                "species": pet.species,
                "age": pet.age,
                "task_count": pet.task_count(),
            }
            for pet in owner.pets
        ],
        use_container_width=True,
    )
else:
    st.info("Add at least one pet to continue.")

st.subheader("Tasks")
if owner.pets:
    task_col1, task_col2, task_col3, task_col4, task_col5 = st.columns(5)
    with task_col1:
        task_title = st.text_input("Task", value="Morning walk")
    with task_col2:
        task_time = st.text_input("Time HH:MM", value="08:30")
    with task_col3:
        task_duration = st.number_input("Duration", min_value=5, max_value=240, value=20)
    with task_col4:
        task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with task_col5:
        task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=0)

    pet_for_task = st.selectbox("Assign task to", [pet.name for pet in owner.pets])

    if st.button("Add task"):
        if not task_title.strip():
            st.warning("Task name is required")
        else:
            owner.add_task_to_pet(
                pet_for_task,
                Task(
                    description=task_title.strip(),
                    time=task_time.strip(),
                    duration_minutes=int(task_duration),
                    priority=task_priority,
                    frequency=task_frequency,
                    due_date=date.today(),
                ),
            )
            owner.save_to_json(DATA_FILE)
            st.success("Task added")

all_tasks = scheduler.sort_by_priority_then_time(scheduler.get_all_tasks(include_completed=True))
if all_tasks:
    st.dataframe(
        [
            {
                "time": t.time,
                "pet": t.pet_name,
                "description": t.description,
                "priority": t.priority,
                "duration_minutes": t.duration_minutes,
                "completed": t.completed,
            }
            for t in all_tasks
        ],
        use_container_width=True,
    )

st.subheader("AI Assistant")
user_query = st.text_area(
    "Ask for a schedule or explanation",
    value="Plan today with medication first and explain tradeoffs.",
)

if st.button("Run AI workflow"):
    response = agent.run(user_query)

    st.markdown("### Output")
    st.write(response.answer)

    st.markdown("### Retrieval Citations")
    if response.citations:
        for cid in response.citations:
            st.write(f"- {cid}")
    else:
        st.write("- none")

    st.markdown("### Reliability Checks")
    for check in response.checks:
        st.write(f"- {check}")

st.subheader("Current Daily Priority Plan")
plan = scheduler.build_priority_plan(date.today())
if not plan:
    st.info("No tasks currently planned for today.")
else:
    st.table(
        [
            {
                "time": task.time,
                "pet": task.pet_name,
                "task": task.description,
                "priority": task.priority,
                "duration": task.duration_minutes,
            }
            for task in plan
        ]
    )

warnings = scheduler.detect_conflicts(plan)
for warning in warnings:
    st.warning(warning)

if st.button("Save data"):
    owner.save_to_json(DATA_FILE)
    st.success("Saved owner data")
