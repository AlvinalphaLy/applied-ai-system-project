# Model Card: PawPal+ AI Reliability Planner

## 1. Model and System Scope

- System name: PawPal+ AI Reliability Planner
- Base project: PawPal+ (Module 2 Project)
- Primary use case: pet-care schedule planning with evidence-grounded explanations
- Core AI features: Retrieval-Augmented Generation (RAG), agentic workflow, reliability checks

This system combines deterministic scheduling logic with retrieval-guided generation to produce transparent daily care recommendations. It is designed for educational and portfolio use, not medical or veterinary diagnosis.

## 2. Intended Users and Environment

- Intended users: learners, instructors, and portfolio reviewers
- Deployment environment: local execution via Python CLI and Streamlit app
- Interaction modes: direct user prompt input, schedule viewing, citation review, reliability-check review

## 3. Data and Knowledge Sources

- Scheduling data: owner/pet/task records from assets/demo_owner.json
- Retrieval data: local curated chunks in assets/knowledge_base.json
- External model (optional): OpenAI chat model when environment variables are configured

Known data constraints:

- Retrieval corpus is small and manually curated.
- Guidance may not cover edge-case care situations.
- No dynamic web retrieval is used in this implementation.

## 4. Reliability and Evaluation

Implemented reliability methods:

- Automated tests:
  - Scheduler ordering and recurrence behavior
  - Conflict detection behavior
  - Retriever relevance behavior
  - Agent pipeline output/citation behavior
- Runtime reliability checks in agent output:
  - quality:length_ok / quality:too_short
  - grounding:mentions_top_task / grounding:missed_top_task
  - grounding:mentions_retrieval / grounding:no_retrieval_reference
- Logging and guardrails:
  - Input validation and unsafe-query blocking
  - Logged guardrail actions and runtime errors
- Human evaluation:
  - User reviews output quality, citations, and checks in Streamlit

Latest summary metrics:

- Automated tests: 5/5 passed
- Demo-query reliability checks: 3/3 passed after grounding fix
- Observed weakness: lexical retrieval can miss semantically similar phrasing without token overlap

## 5. Limitations and Biases

- Lexical retrieval bias:
  - The retriever favors exact or near-exact token overlap and can underrepresent semantically similar phrasing.
- Small static corpus bias:
  - Recommendations are limited to authored chunks and may reflect narrow assumptions.
- Generation style bias:
  - Rule-based fallback is intentionally structured and may appear repetitive or overly rigid.

## 6. Misuse Risks and Mitigations

Potential misuse:

- Harmful or unsafe pet-care requests
- Over-reliance on AI output as professional medical guidance

Current mitigations:

- Guardrails reject unsafe/invalid input
- Responses include evidence citations for transparency
- README and documentation frame system as educational, not clinical advice

Recommended future mitigations:

- Expand unsafe query taxonomy
- Add escalation message directing users to licensed veterinary professionals for health-critical scenarios
- Add stricter policy checks before final response generation

## 7. Reflection on AI Collaboration

Helpful AI suggestion:

- AI suggested using a modular plan -> retrieve -> act -> evaluate architecture, which improved maintainability and made testing clearer.

Flawed or incorrect AI suggestion:

- An earlier AI-generated response path produced fluent output that occasionally failed grounding checks by omitting the top scheduled task. The implementation was corrected to append explicit grounded task context.

What surprised us during reliability testing:

- Coherent answers can still be weakly grounded. Explicit reliability tags made this visible and drove a targeted fix.

## 8. Ethical Position

This system prioritizes transparency over fluency by exposing citations and reliability checks to users. It does not claim clinical authority and should not replace professional veterinary guidance. Responsible use requires human review, especially for safety-sensitive decisions.
