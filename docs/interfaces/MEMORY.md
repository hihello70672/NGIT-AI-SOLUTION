# Memory and knowledge interface

This document describes the Memory module boundary; it is not evidence that every capability is runtime-validated. See [project status](../STATUS.md). Inspect current Memory code and [shared protocols](SHARED_PROTOCOLS.md) before changes. Shared-contract changes require Chief Architect review.

## Responsibility and ownership

Memory owns user/conversation memory, persistence, retrieval, knowledge ingestion, provenance, and preference memory. PostgreSQL is authoritative for persisted records. The module owns its persistence and migrations; consumers use published contracts rather than accessing its tables directly.

## Contract requirements

- Authenticated operations receive server-derived caller context. Bind reads/writes to that owner in service queries; ignore client-provided owner IDs as authority.
- Conversation and memory identifiers are validated and checked against the caller's ownership before use. Return safe failures without exposing another user's existence or data.
- Retrieval candidates, including optional vector-search results, are constrained to the authenticated owner's corpus and requested types before returning or using them.
- Bound query, document, chunk, result, and resource sizes. Treat imported text and retrieved content as untrusted input.
- Preserve provenance/source metadata where available. URL-origin allowlisting is not proof that remote content is authentic or safe; fetching requires separate network protections.
- Embedding generation and persistence are optional/open until supported by approved storage and privacy contracts.

## Failure behavior and isolation

Invalid input, inaccessible/foreign identifiers, unavailable persistence, or adapter errors fail safely with typed errors. Logs and responses must not contain secrets, prompts, internal traces, or other users' content. Validate isolation with cross-user service/database tests and, where RLS is configured, a non-owner, non-superuser database role without `BYPASSRLS`.

## Current operational caveat

The status record says memory/database tests and runtime checks have not been run for this update. Checked-in tests are source coverage, not passing-test evidence.
