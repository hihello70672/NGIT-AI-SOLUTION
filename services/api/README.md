# API service

NGIT's modular FastAPI backend exposes versioned REST endpoints at `/api/v1`. Route handlers remain thin; identity and authorization logic is owned by existing services and shared security infrastructure. PostgreSQL access is mediated by `database.py`.

## Local startup

1. Copy `.env.example` to `.env`, set `AUTH_TOKEN_PEPPER` to a unique random value of at least 32 bytes, and optionally set `DATABASE_URL` or the `POSTGRES_*` values. Configure `PASSWORD_PEPPER` before creating accounts if using it.
2. Start PostgreSQL from the repository root with `docker compose up -d postgres`.
3. Apply `services/api/db/migrations/0001_initial_schema.sql` and `0002_seed_reference_data.sql` using the documented database test runner or `psql`.
4. Install `services/api/requirements.txt` and run `PYTHONPATH=. uvicorn services.api.app:app --reload` from the repository root.
5. Browse `/docs` for generated OpenAPI documentation. `/health` reports process liveness, not database readiness.

## Brain model configuration

The Brain has no mandatory third-party AI service. Set `NGIT_LOCAL_MODEL_BASE_URL` to an OpenAI-compatible chat-completions API base URL, such as a local Ollama-compatible `http://localhost:11434/v1`, and set `NGIT_LOCAL_MODEL_NAME` to the served model name. The optional `NGIT_SELF_HOSTED_MODEL_BASE_URL` configures a secondary self-hosted runtime used only when `allow_fallback` is true and primary candidates fail. API keys are optional and loaded only by the server from environment variables; never send provider credentials from a browser. With no model configured, `/api/v1/brain/models` returns an empty registry and generation safely returns `model_unavailable`.

`GET /api/v1/brain/models` lists configured enabled chat models. `POST /api/v1/brain/generate` accepts text, optional model selection, temperature, token limit, confidence threshold, and fallback policy; it returns generated text with intent, confidence, selected model ID, and fallback indicator. The baseline intent classifier is deterministic and replaceable through the service interface. Registry state is currently process-local; durable model administration is not implemented in this phase.

The model endpoint is trusted server configuration. Configure only an endpoint you control or explicitly trust. The current adapter supports OpenAI-compatible JSON chat completions and applies request timeouts.

## Tests

From repository root after installing API requirements, run `PYTHONPATH=. pytest services/api/tests`. Brain tests use deterministic fake runtimes and do not make network calls or require external model credentials. The database-backed API lifespan may require PostgreSQL for tests that do not replace the database boundary.

## Security limitation

Token and approval state in the existing security interface is process-local. Production multi-worker persistence/revocation needs a separately approved shared-store decision. Model endpoints and their credentials are server-side only.
