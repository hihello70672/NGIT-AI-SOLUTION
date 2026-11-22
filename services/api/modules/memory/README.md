# Private memory and knowledge services

The memory module persists conversations, ordered messages, and typed user memories using the existing `ngit.conversations`, `ngit.messages`, and `ngit.memory_records` schema. Every operation takes the authenticated server-derived user UUID and uses `Database.connection(user_id)`, setting transaction-local `ngit.user_id` for RLS. SQL predicates and composite foreign keys further constrain ownership. Client bodies do not set the owner.

`RetrievalService` ranks records deterministically using local lexical scoring. An optional vector adapter can be injected into the service; vector hits are intersected against that user's authorized records before merging. `EmbeddingVectorSearch` in `vector.py` is an optional cosine-similarity adapter: supply an embedding callable and a candidate loader that returns the caller's authorized records including embeddings. No provider, vector database, or external AI API is required by default; the current schema has no embedding column, so embeddings remain an integration boundary rather than being persisted by this module.

Knowledge ingestion normalizes caller-supplied text into bounded chunks and records source, chunk index, and a verification marker in memory metadata. `ingest_verified` requires an explicit server-configured source allowlist. URL entries match exact scheme, hostname, and effective port; identifiers match exactly. The service never fetches URLs and does not independently prove the content's truth. Configure `NGIT_KNOWLEDGE_SOURCE_ALLOWLIST` as comma-separated approved source identifiers/URLs; empty means ingestion is disabled.

All memory routes are mounted under the configured API prefix and require the existing bearer authentication. API tests: `pytest services/api/tests/test_memory.py` from repository root. Database RLS integration tests are separately documented in `services/api/db/tests/README.md` and require disposable PostgreSQL.

Tests were not run as part of authoring this module update; no passing status is claimed.
