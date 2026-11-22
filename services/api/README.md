# NGIT API

FastAPI identity API and modular services. Configure PostgreSQL using the values in root `.env.example`; the database role must be a constrained application role and not a superuser/table owner to exercise RLS.

## Brain runtime
The optional Brain service supports `/api/v1/brain/models` and `/api/v1/brain/generate` with local/self-hosted OpenAI-compatible endpoints. See `.env.example` and `docs/interfaces/BRAIN.md`. External AI is optional.

## Private memory and knowledge
Authenticated routes under `/api/v1` provide conversation/message and memory operations, retrieval, and allowlist-verified supplied-text ingestion. See `docs/interfaces/MEMORY.md` for privacy and source constraints.

## Personal Agent
The approval-gated agent API is documented in `docs/interfaces/AGENT.md`. Routes are mounted only when `NGIT_AGENT_WORKSPACE` explicitly sets a sandbox path. Sensitive tool policies are registered with the shared `RestrictedActionManager`; reviewers use the shared one-time approval workflow. Browser and computer adapters remain optional, shell/host control is not enabled, and task history is process-local rather than durable.

## Tests
Install `services/api/requirements.txt`, then run `PYTHONPATH=. python -m unittest discover -s services/api/tests` from the repository root. Run SQL/RLS checks against disposable PostgreSQL with `services/api/db/tests/run.sh`. Tests are not claimed as passing unless executed in the target environment.
