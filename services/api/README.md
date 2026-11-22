# NGIT API

FastAPI identity API and modular services. Configure PostgreSQL using root `.env.example`; use a constrained application role to exercise RLS.

## Brain
Optional local/self-hosted OpenAI-compatible runtime at `/api/v1/brain`; see `docs/interfaces/BRAIN.md`. External AI is optional.

## Memory and knowledge
Authenticated owner-scoped conversation, memory, retrieval, and allowlist-verified supplied-text ingestion routes under `/api/v1`. See `docs/interfaces/MEMORY.md`.

## Personal Agent
Agent contracts and safety boundaries are in `docs/interfaces/AGENT.md`. Routes mount only when `NGIT_AGENT_WORKSPACE` explicitly configures an isolated sandbox. Side-effecting tool policies are registered in the shared security engine and require a distinct reviewer’s one-time approval. No shell or implicit desktop access is enabled. Browser/computer adapters are optional, and task history is process-local.

## Tests
Install `services/api/requirements.txt` and run `PYTHONPATH=. python -m unittest discover -s services/api/tests` from the repository root. SQL/RLS checks require disposable PostgreSQL and `services/api/db/tests/run.sh`. No test is claimed as passed unless run in its target environment.
