# Memory and knowledge interface

This contract defines the Memory boundary; it is not evidence every capability is runtime-validated. Inspect `services/api/modules/memory/` and [shared protocols](SHARED_PROTOCOLS.md) before changes. Shared-contract changes require Chief Architect review.

## Responsibility and ownership

Memory owns user/conversation memory, persistence, retrieval, knowledge ingestion, provenance and preference memory. PostgreSQL is authoritative for persisted records. The module owns its persistence/migrations; consumers use public contracts, not direct table access.

## Contract requirements

- Authenticated operations receive server-derived caller context. Bind reads/writes to that owner in service queries; ignore client owner IDs as authority.
- Validate conversation/memory identifiers and verify ownership before use. Return safe typed failures without disclosing another user's existence or content.
- Restrict lexical/vector retrieval candidates to the authenticated user's corpus and requested types before return/use.
- Bound query, document, chunk, result and resource sizes. Imported/retrieved content is untrusted. Preserve source/provenance metadata where available; an allowed URL origin does not prove content authentic or safe, and fetching requires separate network protections.
- Embedding generation/persistence is optional until approved storage/privacy contracts are selected. Do not imply vector persistence where absent.
- Fail safely on invalid input, foreign IDs, unavailable persistence and adapter failures. Logs/responses must not expose secrets, prompts, traces or other users' content.

## Isolation and verification

Validate service and database isolation with cross-user checks; where RLS applies, use a non-owner, non-superuser role without `BYPASSRLS`. RLS is defense in depth. Status records say Memory/database/runtime checks were not run for the update; checked-in tests do not demonstrate execution or passing results.
