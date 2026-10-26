# Feature Specification: Jira / Confluence Automation Platform

**Feature Branch**: `001-jira-confluence-automation`
**Created**: 2026-09-14
**Updated**: 2026-10-26
**Status**: Draft
**Constitution**: [constitution.md](./constitution.md) (v1.1.0)
**Input**: Build an automation platform that integrates with Atlassian Jira and Confluence. It exposes a secure REST API and a React UI so users can define automations, manage integrations, run jobs, and review audit logs.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Jira and Confluence integrations (Priority: P1)

An administrator registers a connection to a Jira or Confluence instance (name, provider, base URL, authentication type, credentials, scopes), reviews existing connections, updates them, rotates credentials, and removes them.

**Why this priority**: Every automation acts through an integration. Nothing else works without at least one.

**Independent Test**: Create a Jira integration through the UI or API, list it, update its name, rotate its token, then delete it. Confirm the credentials are never returned in any response.

**Acceptance Scenarios**:

1. **Given** no integrations exist, **When** an admin creates a Jira integration with a base URL and an API token, **Then** the system returns the new integration without the token and the integration appears in the list.
2. **Given** an integration exists, **When** an admin lists integrations filtered by provider `confluence`, **Then** only Confluence integrations are returned.
3. **Given** an integration exists, **When** an admin submits new credentials for it, **Then** the stored credentials are replaced and the old ones are no longer used.
4. **Given** an integration is referenced by an automation, **When** an admin deletes it, **Then** [NEEDS CLARIFICATION: block the deletion, or delete and disable the dependent automations?].
5. **Given** a non-admin user, **When** they try to create or delete an integration, **Then** the system rejects the request with a 403 error.

---

### User Story 2 - Define automations (Priority: P1)

A maintainer creates an automation: a named, declarative definition with a trigger (manual, schedule, or webhook), optional conditions, and one or more actions (for example create a Jira issue, add a comment, update a Confluence page), each pointing at an integration. They can enable, disable, edit, and delete it.

**Why this priority**: Automations are the core product. Without them there is nothing to run.

**Independent Test**: Create an automation with a manual trigger and one action targeting an existing integration, fetch it, disable it, then delete it.

**Acceptance Scenarios**:

1. **Given** an existing integration, **When** a maintainer creates an automation with a manual trigger and a `create_issue` action, **Then** the system stores it, records the maintainer as owner, and returns its id.
2. **Given** an automation owned by user A, **When** user B (not an admin) tries to modify it, **Then** the system rejects the request with a 403 error.
3. **Given** an automation whose action references an integration that does not exist, **When** it is submitted, **Then** the system rejects it with a 400 validation error that names the invalid field.
4. **Given** a disabled automation, **When** someone tries to run it, **Then** the system refuses to start a job.

---

### User Story 3 - Run an automation and track the job (Priority: P1)

A user starts an automation manually, optionally passing input. The system creates a job, performs the actions against Jira or Confluence using the stored credentials, records the outcome, and lets the user check the job's status and result at any time.

**Why this priority**: This is the end-to-end value of the platform and the Phase 1 success criterion.

**Independent Test**: Against a mock Jira, run an automation that creates an issue. Confirm a job reaches `success`, the mock received the request, and audit log entries exist for the run.

**Acceptance Scenarios**:

1. **Given** an enabled automation with a valid integration, **When** a user starts a job, **Then** the system creates a job, runs each action in order, sets the job to `success`, and stores the result.
2. **Given** an action fails permanently, **When** the job runs, **Then** the job ends as `failed` with an error summary and an audit entry for the failure.
3. **Given** the remote API returns a rate-limit response with a `Retry-After` value, **When** the job runs, **Then** the system waits at least that long before retrying, up to the retry limit.
4. **Given** a client sends the same start request twice with the same `Idempotency-Key`, **When** the second request arrives, **Then** no second job is created and the original job is returned.
5. **Given** a running job, **When** a user fetches it, **Then** the response shows its current status, timestamps, and any result so far.
6. **Given** a list of jobs, **When** a user filters by automation or status, **Then** only matching jobs are returned.

---

### User Story 4 - Review the audit trail (Priority: P2)

A user or auditor browses an immutable history of what the platform did: which job, which action, who triggered it, the target, the time, and the outcome.

**Why this priority**: Required for trust and compliance, but only useful once jobs exist.

**Independent Test**: Run a job, then list audit entries and confirm one entry per action with correct actor, target, and timestamp. Confirm no endpoint can edit or delete an entry.

**Acceptance Scenarios**:

1. **Given** completed jobs, **When** a user requests the latest 50 audit entries, **Then** they are returned newest first.
2. **Given** a timestamp, **When** a user requests entries since that time, **Then** only newer entries are returned.
3. **Given** any audit entry, **When** anyone attempts to change or delete it through the API, **Then** the system offers no such operation.

---

### User Story 5 - Sign in and access by role (Priority: P2)

Users authenticate to use the UI and API. Their role (admin, maintainer, user) limits what they can do.

**Why this priority**: Required before the platform handles real credentials, but the core flows can be built against a seeded user first.

**Independent Test**: Sign in as each role and confirm that allowed actions succeed and disallowed ones return 401 or 403.

**Acceptance Scenarios**:

1. **Given** valid credentials, **When** a user signs in, **Then** the system returns a session token.
2. **Given** a missing, expired, or invalid token, **When** a protected endpoint is called, **Then** the system returns 401.
3. **Given** a signed-in user lacking the needed role, **When** they call a restricted endpoint, **Then** the system returns 403.

---

### User Story 6 - Operate and monitor the service (Priority: P3)

An operator checks service health, readiness, and metrics, and can trace any request through the logs.

**Why this priority**: Important for running in production, but not needed to demonstrate the main flows.

**Independent Test**: Call `/health`, `/ready`, and `/metrics`; stop the database and confirm `/ready` reports not ready while `/health` still responds.

**Acceptance Scenarios**:

1. **Given** the service and database are up, **When** an operator calls `/ready`, **Then** it reports ready.
2. **Given** the database is unreachable, **When** an operator calls `/ready`, **Then** it reports not ready.
3. **Given** metrics are enabled, **When** an operator calls `/metrics`, **Then** job counts, job durations, external call counts, and error counts are exposed in Prometheus format.
4. **Given** any request, **When** it is logged, **Then** the log entry is structured JSON containing a correlation id.

---

### Edge Cases

- A job is started for an automation that was edited or deleted while the job was running.
- The remote Jira or Confluence service is unreachable, slow, or returns malformed data.
- A start request is repeated with the same idempotency key but a different body.
- Two users update the same automation at the same time.
- A credential is expired or revoked on the remote side mid-job.
- A list endpoint is called with a very large `limit` or an invalid `since` value.
- A stored credential cannot be decrypted (key rotated or data corrupted).
- The database is down when an audit entry should be written for an action that already happened remotely.

---

## Requirements *(mandatory)*

### Functional Requirements

**Integrations**
- **FR-001**: The system MUST let authorized users create, read, update, list, and delete integrations for the providers `jira` and `confluence`.
- **FR-002**: The system MUST support filtering integrations by provider.
- **FR-003**: The system MUST accept credentials (API token, or OAuth2 client id and secret) on create and update, store them encrypted or as a reference to an external secrets manager, and never return them in any response or log.
- **FR-004**: The system MUST support rotating an integration's credentials and re-testing the connection.
- **FR-005**: The system MUST record the scopes requested for each integration and request only the minimum needed.

**Automations**
- **FR-006**: The system MUST let authorized users create, read, update, list, and delete automations made of a trigger, optional conditions, and one or more actions.
- **FR-007**: The system MUST support trigger types `manual`, `schedule`, and `webhook`, and action types including `create_issue`, `comment`, and `update_page`.
- **FR-008**: The system MUST validate that every action references an existing integration and reject invalid definitions with a descriptive 400 error.
- **FR-009**: The system MUST record the owner of each automation and allow only the owner or an admin to modify or delete it.
- **FR-010**: The system MUST allow an automation to be enabled or disabled, and MUST NOT run a disabled automation.

**Jobs**
- **FR-011**: The system MUST let authorized users start a job for an automation with optional input, and return the job id.
- **FR-012**: The system MUST track each job through the statuses `queued`, `running`, `success`, `failed`, and `cancelled`, with start and finish times and a result.
- **FR-013**: In Phase 1 the system MUST execute jobs synchronously within the API process; the design MUST NOT prevent moving to a queue and worker later.
- **FR-014**: The system MUST let users fetch a single job and list jobs filtered by automation and status.
- **FR-015**: The system MUST honor an `Idempotency-Key` header so repeated start requests do not create duplicate jobs or duplicate external resources.
- **FR-016**: The system MUST retry transient failures of external calls with exponential backoff and jitter (default maximum 3 retries) and MUST honor `Retry-After`.
- **FR-017**: The system MUST apply per-integration rate limiting so the platform stays within Atlassian quotas.

**Audit**
- **FR-018**: The system MUST write an immutable audit entry for every automation action, recording job, action, actor, target, details, and timestamp.
- **FR-019**: The system MUST let users list audit entries with a `limit` and a `since` filter, newest first, and MUST NOT offer any way to edit or delete entries.
- **FR-020**: The system MUST store only the minimum metadata needed to reconstruct and re-run an operation; full external payloads are stored only when audit requires them.

**Authentication and authorization**
- **FR-021**: The system MUST authenticate UI and API users with signed session tokens (JWT) and return 401 for missing, expired, or invalid tokens.
- **FR-022**: The system MUST enforce the roles `admin`, `maintainer`, and `user` in middleware and return 403 when the role is insufficient.
- **FR-023**: [NEEDS CLARIFICATION: Are users local accounts created in the platform, or linked to Jira accounts? Phase 1 SSO is out of scope.]

**API conventions**
- **FR-024**: All endpoints MUST be under `/api/v1`, use JSON, and use RFC 3339 timestamps.
- **FR-025**: All errors MUST use the format `{ code, message, details? }` with the correct HTTP status (400, 401, 403, 404, 429, 500).
- **FR-026**: The system MUST publish an OpenAPI v3 document that matches the implemented routes.

**Operations**
- **FR-027**: The system MUST expose `/health`, `/ready` (including database connectivity), and `/metrics` (Prometheus format when enabled).
- **FR-028**: The system MUST emit structured JSON logs with timestamp, level, correlation id, and user id when known.
- **FR-029**: The system MUST apply database schema changes only through version-controlled migrations and provide a seed script for local development.
- **FR-030**: The system MUST run locally with PostgreSQL 15 in Docker and provide scripts to start the database, migrate, and seed.

**User interface**
- **FR-031**: The UI MUST provide pages to list and manage integrations and automations, to trigger a job manually and watch its status, and to browse audit logs.

### Key Entities

- **User**: a person using the platform. Has a username, display name, email, and role. Owns automations.
- **Integration**: a connection to one Jira or Confluence instance. Has a name, provider, non-sensitive configuration (such as base URL and auth type), encrypted credentials, and scopes.
- **Automation Config**: a declarative definition with a name, description, trigger, conditions, actions, enabled flag, and owner. Each action references an Integration.
- **Job**: one execution of an Automation Config. Has a status, input, result, idempotency key, and start and finish times.
- **Audit Log**: an immutable record of one action taken during a Job. Has an action, actor, target, details, and timestamp.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can create an integration and an automation and complete a first successful run against a mock Jira in under 10 minutes using only the UI.
- **SC-002**: 100% of automation actions executed produce a matching audit entry.
- **SC-003**: 0 credentials appear in any API response, log line, or committed file.
- **SC-004**: Repeating a start request with the same idempotency key creates 0 additional jobs and 0 duplicate external resources.
- **SC-005**: A fresh PostgreSQL 15 database reaches the full schema with a single migration command, and a developer has a working local stack in under 15 minutes.
- **SC-006**: The service handles hundreds of automation runs per day with no special scaling.
- **SC-007**: Service availability is at least 99.5%, recovery time after failure is at most 1 hour, and daily backups are kept for 30 days.
- **SC-008**: The CI pipeline passes on every merged change with lint, unit tests, integration tests, and the client build, and service-layer coverage is at least 80%.

---

## Assumptions

- Phase 1 supports the providers Jira and Confluence only, using API tokens or OAuth2 (the choice between them is to be settled in the first RFC).
- Jira and Confluence behavior in tests is simulated with mock servers or recorded fixtures; live tenants are not used in CI.
- Phase 1 volume is moderate (hundreds of operations per day), so Redis, queues, and distributed rate limiting are deferred to Phase 2.
- Production uses a managed PostgreSQL; local development and CI use PostgreSQL 15 in Docker.
- The integration request carries credentials inside `config.credentials`, and `triggered_by` is a user id or null. Earlier examples that showed top-level `credentials` or a value like `user:alice` are superseded by this specification.
- The system serves one organization; multi-tenancy is out of scope for Phase 1.
- Enterprise SSO and large-scale event-driven automation are deferred.

---

## Appendix A: API Contract (summary)

All paths are prefixed with `/api/v1`. Authentication is a bearer token. Full detail belongs in `/spec/openapi.yaml`.

| Resource | Method and path | Notes |
|---|---|---|
| Integrations | `GET /integrations` | Query `?provider=jira\|confluence`; returns id, name, provider, timestamps, metadata |
| | `GET /integrations/:id` | |
| | `POST /integrations` | Body: name, provider, config (baseUrl, authType, credentials), scopes; returns 201 |
| | `PUT /integrations/:id` | Partial update or credential rotation |
| | `DELETE /integrations/:id` | 204 |
| Automations | `GET /automations`, `GET /automations/:id` | |
| | `POST /automations` | Body: name, description, trigger, conditions, actions, enabled; returns 201 |
| | `PUT /automations/:id`, `DELETE /automations/:id` | 204 on delete |
| Jobs | `POST /jobs` | Body: automation_id, triggered_by, input; `Idempotency-Key` header; returns 201 |
| | `GET /jobs/:id` | Status, timestamps, result, audit log ids |
| | `GET /jobs?automation_id=&status=` | |
| Audit | `GET /audit?limit=50&since=` | Newest first |
| Ops | `GET /health`, `GET /ready`, `GET /metrics` | Outside the `/api/v1` prefix |

Example job request:

```json
{
  "automation_id": "<uuid>",
  "triggered_by": "<user-uuid>",
  "input": { "issue_summary": "Automated issue from SpecKit" }
}
```

Example integration request:

```json
{
  "name": "Jira Dev",
  "provider": "jira",
  "config": {
    "baseUrl": "https://example.atlassian.net",
    "authType": "token",
    "credentials": { "token": "<REDACTED>" }
  },
  "scopes": ["read:jira-work", "write:jira-work"]
}
```

## Appendix B: Data Model (PostgreSQL 15)

Conventions: `snake_case` tables, UUID primary keys, `pgcrypto` for UUID generation, timestamps with time zone.

| Table | Columns |
|---|---|
| `users` | id, username (unique), display_name, email, created_at |
| `integrations` | id, name, provider (`jira`\|`confluence`), config (JSONB), credentials_encrypted (BYTEA), scopes (TEXT[]), created_at, updated_at |
| `automation_configs` | id, name, description, trigger (JSONB), conditions (JSONB), actions (JSONB), enabled (default true), owner_id → users, created_at, updated_at |
| `jobs` | id, automation_id → automation_configs, status (`queued`\|`running`\|`success`\|`failed`\|`cancelled`), idempotency_key (unique), input (JSONB), result (JSONB), started_at, finished_at, created_at |
| `audit_logs` | id, job_id → jobs, action, actor, target (JSONB), details (JSONB), timestamp (default now) |

Indexes: `jobs(automation_id)`, `jobs(status)`, `jobs(created_at)`, `audit_logs(job_id)`, `audit_logs(timestamp)`.

Seed data: an admin user, a sample integration with a mocked token, a sample manual automation, and a few job and audit rows for UI development.

## Appendix C: Configuration

| Variable | Purpose |
|---|---|
| `PORT` | Server port (default 4000) |
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET`, `JWT_ALGO` | Token signing secret and algorithm (`HS256`, or `RS256` with keys) |
| `NODE_ENV` | Runtime environment |
| `ENCRYPTION_KEY` | 32-byte base64 key for encrypting integration credentials when no external secrets manager is used |
| `SENTRY_DSN`, `PROMETHEUS_ENABLED` | Optional error reporting and metrics toggle |

Local development copies `.env.example` to `.env`. Real values are never committed.

## Appendix D: Delivery Milestones

| Milestone | Weeks | Scope |
|---|---|---|
| M1 Project setup | 0-2 | Monorepo and skeleton, workspaces, root CI, migration tooling, Postgres in Docker |
| M2 Core API and database | 2-4 | Integrations and automations CRUD, jobs skeleton, migrations and seed, basic React pages for integrations and automations |
| M3 Execution and audit | 4-6 | Synchronous job runner, persistent audit logs, retry and backoff, idempotency, tests and instrumentation |
| M4 Hardening and CI/CD | 6-8 | Full CI pipeline, Docker images pushed to a registry, metrics and logs, documentation |

## Appendix E: Verification Checklist

- [ ] OpenAPI spec exists and matches the implemented routes
- [ ] Migrations apply cleanly to a fresh PostgreSQL 15 instance
- [ ] Server unit and integration tests pass in CI
- [ ] Client builds with `vite build` in CI
- [ ] A sample automation run creates a job and audit log entries locally
- [ ] No secrets are present in any committed file

## Appendix F: Recommended Tooling

- **Backend:** express, pino (logging), pg, knex or node-pg-migrate or Prisma (migrations and data access), axios, jose or jsonwebtoken, supertest
- **Frontend:** react, react-router, vite, vitest, an axios or fetch wrapper
- **Delivery:** Docker, docker-compose, GitHub Actions, testcontainers (optional)
