# Memory and knowledge interface

## Privacy and ownership contract

All user-scoped methods receive authenticated server-derived `user_id`, validate it as UUID, and open database transactions with `Database.connection(user_id)`, which sets transaction-local `ngit.user_id` for PostgreSQL RLS. Request-body owner values are never accepted as authority. Queries scope reads and writes by owner; conversation-message writes require a matching active owned conversation. Composite foreign keys and RLS provide database enforcement. Validate RLS using a non-owner, non-superuser application role.

## Service API

`MemoryService` creates/lists conversations, persists ordered messages, and stores/lists memory records using existing `conversations`, `messages`, and `memory_records` tables. Persisted kinds follow schema-supported profile, preference, fact, and summary values.

`RetrievalService.search` performs deterministic lexical retrieval and can accept an optional vector adapter implementing `search(user_id, query, limit, memory_type)`. Vector hits are intersected with IDs from the authenticated user’s database corpus before results are returned. Embeddings/indexing are optional external adapters because the current schema has no embedding column or vector extension.

`KnowledgeService.ingest_text` normalizes and chunks caller-provided text into summary memory records while retaining source, chunk index, and verification marker in metadata. `ingest_verified` rejects unallowlisted sources. URL-origin verification compares exact scheme, hostname, and effective port; it does not fetch URLs or establish truth. Callers provide the source text and configured allowlist.

## REST and trust boundaries

Mounted under the configured API prefix: conversation create/list; message create/list under a conversation; memory create/list/search; and `POST /knowledge/ingest`. Every route requires existing bearer authentication. Search works without external AI/vector services. Knowledge ingestion is disabled for all sources unless an explicit source allowlist is configured. Imported text and provenance are untrusted; retain source metadata and do not imply verification beyond the implemented marker.

## Validation

The status records `services/api/tests/test_memory.py` coverage for owner-scoped SQL/RLS setup, foreign conversation rejection, input validation, vector-hit filtering, lexical retrieval, exact source verification, and chunk metadata. It has not been run for this update. API tests use the documented API test command; database integration should also use `services/api/db/tests/run.sh` against disposable PostgreSQL to check actual constraints and RLS.
