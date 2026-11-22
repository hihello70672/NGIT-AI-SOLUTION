# NGIT API

FastAPI identity API and modular services. Configure PostgreSQL using the values in the root `.env.example`; the database role must be a constrained application role and not a superuser/table owner to exercise RLS.

## Brain runtime
The optional Brain service supports `/api/v1/brain/models` and `/api/v1/brain/generate` with local/self-hosted OpenAI-compatible endpoints. See `.env.example` and `docs/interfaces/BRAIN.md`. External AI is optional.

## Private memory and knowledge
Authenticated routes under `/api/v1` provide conversation/message and memory operations, retrieval, and allowlist-verified supplied-text ingestion. See `docs/interfaces/MEMORY.md` for privacy and source constraints.

## Personal Agent
The approval-gated Personal Agent contracts and safety boundaries are documented in `docs/interfaces/AGENT.md`. Agent API wiring requires an explicitly configured isolated workspace and the existing shared `RestrictedActionManager` and `ApprovalEngine`; no host computer or shell access is enabled by default. In-process task history is not durable. Browser/computer adapters remain optional.

## Tests
Install `services/api/requirements.txt`, then run `PYTHONPATH=. python -m unittest discover -s services/api/tests` from the repository root. Run SQL/RLS checks against disposable PostgreSQL with `services/api/db/tests/run.sh`. Tests are not claimed as passing unless executed in the target environment.
