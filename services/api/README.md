# NGIT API

FastAPI identity API and modular services. Configure PostgreSQL with the values in the root `.env.example`; the database role must be a constrained application role and not a superuser/table owner to exercise RLS.

## Brain runtime
The optional Brain service supports the `/api/v1/brain/models` and `/api/v1/brain/generate` endpoints and local/self-hosted OpenAI-compatible endpoints. See `.env.example` and `docs/interfaces/BRAIN.md`. External AI is optional.

## Private memory and knowledge
Authenticated routes under `/api/v1`: create/list conversations, append/list conversation messages, create/list memory records, search memories, and ingest verified source text. See `docs/interfaces/MEMORY.md` for contracts and privacy requirements. Records use the existing `conversations`, `messages`, and `memory_records` schema. Each operation gets its owner exclusively from bearer authentication, applies user transaction context for RLS, and keeps explicit `user_id` SQL predicates. Knowledge source allowlists are configured in the application; no source is trusted by default. Ingestion accepts supplied text and does not crawl URLs. Search has deterministic lexical retrieval; an optional vector adapter is accepted by the router/service API and is constrained to the authenticated user's corpus. No vector extension or embedding service is required.

## Tests
Install `services/api/requirements.txt`, then run `PYTHONPATH=. pytest services/api/tests` from the repository root. Run SQL/RLS checks against disposable PostgreSQL with `services/api/db/tests/run.sh`. Tests are not claimed as passing unless executed in the target environment.
