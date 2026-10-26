# Jira / Confluence Automation Constitution

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)
Every feature starts as a specification, then a plan, then tasks, then code.
- The specification (`/spec/specification.md`) and this constitution are the source of truth; code follows them, not the reverse.
- Changes to behavior, API contracts, or the data model update the spec in the same pull request.
- Architectural decisions and amendments to this constitution are recorded as RFCs in `/spec/rfcs`.

### II. Layered Architecture
The backend is strictly layered: **routes → controllers → services → models**.
- Routes only map HTTP paths to controllers. Controllers are thin: parse input, call a service, shape the response.
- All business logic and all Jira/Confluence integration logic live in services.
- Models are ORM entities or lightweight query modules; no business rules.
- The React client talks to the backend only through the REST API, using a single API client module.

### III. Security and Secrets First (NON-NEGOTIABLE)
- API tokens, OAuth client secrets, JWT secrets, and encryption keys are never committed. Only `.env.example` with placeholders is tracked; `.env` is git-ignored.
- Integration credentials are stored encrypted at rest, or as references to an external secrets manager. They are never returned by the API or written to logs.
- Request only the minimum Jira/Confluence scopes each integration needs (least privilege).
- All external callbacks and redirect URIs use HTTPS. All inputs are validated and sanitized before use or before being forwarded to external APIs.
- Authorization is role-based (admin, maintainer, user) and enforced in middleware; only owners or admins may modify an automation.

### IV. Test-First Quality
- Services and core business logic require unit tests, with a minimum of **80% coverage**. External API clients are mocked.
- API endpoints require integration tests (supertest) against a real PostgreSQL 15 instance running in Docker.
- Jira/Confluence interactions are tested against mock servers or recorded fixtures, never live tenants in CI.
- At least one end-to-end test covers the critical path: run an automation, record a job, write audit logs.
- Tests are written before or together with the code they cover; a pull request that adds behavior without tests is not mergeable.

### V. API Contract Discipline
- The REST API is versioned (`/api/v1/...`), JSON-only, with RFC 3339 timestamps.
- Errors use one format everywhere: `{ code, message, details? }`, with correct HTTP status codes (400, 401, 403, 404, 429, 500).
- An OpenAPI v3 document (`/spec/openapi.yaml`) describes every endpoint and is updated in the same pull request as any route change.
- Breaking changes require a new API version and an RFC.

### VI. Reliability and Observability
- Calls to Jira/Confluence use exponential backoff with jitter (default max 3 retries) and honor `Retry-After`.
- Actions that create external resources support idempotency keys (`Idempotency-Key` header) so duplicate requests do not create duplicates.
- Per-integration rate limiting protects Atlassian quotas.
- Logs are structured JSON with timestamp, level, correlation ID, and user ID when known.
- The server exposes `/health`, `/ready` (including database connectivity), and `/metrics` (Prometheus format).
- Every automation action produces an immutable audit log entry (who, what, when, status).

### VII. Simplicity and Maintainability
- Prefer the simplest design that meets the spec; add abstraction only when a second use case exists.
- Phase 1 runs jobs synchronously through the API; queues, workers, and Redis are deferred until needed.
- Database schema changes are made only through version-controlled migrations, never by hand.

## Technology Stack and Constraints

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, single-page app |
| Backend | Node.js (LTS) + Express; the Node version matches `.nvmrc` |
| Database | PostgreSQL 15, run in Docker for local development and CI |
| Containers | Docker and docker-compose (`/infra/docker-compose.yml`) |
| Authentication | JWT-based sessions with RS256, or HS256 with a strong, rotated secret |

Repository layout (monorepo, npm workspaces):
- `/client` — React + Vite app
- `/server` — Node/Express API, including `/server/migrations`
- `/spec` — this constitution, the specification, RFCs, OpenAPI, and recovery docs
- `/infra` — docker-compose and local development tooling

Data and persistence:
- Primary keys are UUIDs; table names are `snake_case`.
- Core tables: `users`, `integrations`, `automation_configs`, `jobs`, `audit_logs`.
- Persist only the minimum metadata needed to reconstruct and re-run an operation. Do not store full external payloads unless audit requires it.

Scope:
- In scope: a secure REST API acting on Jira and Confluence (OAuth2 or API tokens), a web UI for configuration, monitoring, and manual triggers, persisted configuration and audit logs, containerized dev and CI, and CI/CD pipelines.
- Out of scope for Phase 1: enterprise SSO (Phase 2) and large-scale event-driven automation.

Non-functional targets (Phase 1):
- Handle typical organizational load (hundreds of operations per day) without special scaling.
- Availability 99.5%; recovery time objective 1 hour; daily backups retained 30 days, including audit and job records.

## Development Workflow and Quality Gates

- **Code style:** ESLint and Prettier configured at the repository root, enforced by pre-commit hooks and CI.
- **Commits:** Conventional Commits.
- **Branches:** `main` is protected and always deployable. Work happens on `feature/*`, `fix/*`, and `chore/*` branches.
- **Pull requests:** require passing CI and at least one approving review. Larger changes may also need QA sign-off.
- **CI must run:** lint, client and server unit tests, integration tests with a PostgreSQL service, client production build (`vite build`), and a dependency security scan.
- **CD:** images built from `main` are pushed to the registry and auto-deployed to staging. Production promotion is a manual step using a semantic-version release tag and changelog.
- **Local development:** copy `.env.example` to `.env`; start PostgreSQL with docker-compose; run migrations and seed scripts; the client runs with the Vite dev server.
- **Docker images:** small (Alpine-based for production) but correctness and stability come first.

## Governance

- This constitution supersedes other practices and guides. Reviewers verify compliance in every pull request.
- Any complexity that departs from a principle must be justified in the pull request.
- Amendments require an RFC in `/spec/rfcs`, approval from the project leads, and a version bump below. Minor coding-standard adjustments may be approved through a regular pull request.
- Versioning follows semantic versioning: MAJOR for removed or redefined principles, MINOR for added principles or sections, PATCH for clarifications.
- Top risks tracked against these principles: credential leakage (Principle III), Atlassian API rate limits (Principle VI), and schema drift between environments (Principle VII, migrations checked in CI).

**Version**: 1.1.0 | **Ratified**: 2026-09-14 | **Last Amended**: 2026-10-26
