# Memory and knowledge interface

## Privacy contract
All methods receive the authenticated server-derived `user_id`, validate it as UUID, and open database transactions with `Database.connection(user_id)`, which applies transaction-local `ngit.user_id` for PostgreSQL RLS. Client-supplied owner values are never accepted in request bodies. SQL also scopes reads and writes by owner; conversation-message writes require a matching active owned conversation. Composite database foreign keys and RLS remain authoritative.

## Service API
`MemoryService` creates/lists conversations, persists ordered messages, and stores/list memories using existing `conversations`, `messages`, and `memory_records` tables. Supported persisted memory types are the schema's profile, preference, fact, and summary. `RetrievalService.search` performs deterministic lexical retrieval and can accept an optional vector adapter implementing `search(user_id, query, limit, memory_type)`. Vector hits are constrained to IDs from the authenticated user's memory corpus before returning results. Embeddings and the vector index are deliberately external/optional because the current schema has no vector column or extension.

`KnowledgeService.ingest_text` normalizes and chunks caller-provided text into summary memory records, preserving source, chunk index, and verification marker in metadata. `ingest_verified` rejects unallowlisted sources. URL verification compares exact scheme, hostname, and effective port; identifiers require exact match. Ingestion does not fetch URLs or assert that content is true: callers must provide source text and a configured allowlist.

## REST
Mounted beneath the configured API prefix: `POST/GET /conversations`, `GET/POST /conversations/{id}/messages`, `POST/GET /memories`, `POST /memories/search`, and `POST /knowledge/ingest`. All endpoints require existing bearer authentication. Search can operate without external AI or vector services. Knowledge ingestion is disabled for all sources unless the application configures an explicit allowlist.

## Validation
`services/api/tests/test_memory.py` covers owner-scoped SQL/RLS setup, foreign conversation rejection, input validation, vector hit filtering, lexical retrieval, exact source validation, and chunk metadata. Execute using the existing API pytest instructions with dependencies installed. Database integration should additionally run `services/api/db/tests/run.sh` against disposable PostgreSQL to validate actual schema constraints and RLS.
