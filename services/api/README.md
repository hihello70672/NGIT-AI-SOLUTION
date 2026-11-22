# API service

This path is reserved for the planned modular FastAPI backend. The service structure, persistence tooling, authentication approach, and migration tool are not yet implemented or selected. Add runnable application code and tests with the relevant approved tooling decisions rather than presenting placeholders as working services.

The target service follows `docs/ARCHITECTURE.md` and `docs/interfaces/SHARED_PROTOCOLS.md`: versioned `/api/v1`, thin route handlers, typed domain services, explicit user context, PostgreSQL ownership boundaries, consistent safe errors, and optional external adapters.
