# SpecKit Specification — Jira / Confluence Automation Project

Version: 1.0
Date: 2026-09-14
Authors: Automation Squad

This specification expands the constitution into concrete design decisions, API contracts, data models, development and deployment patterns, and verification guidance. It is written in the SpecKit style (clear sections, requirements, examples, and an actionable implementation checklist).

CONTENTS
- Overview
- Goals & Success Criteria
- Glossary
- System Architecture (components & interactions)
- API Specification (paths, methods, payloads)
- Data Model (DDL-like schema + notes)
- Authentication & Authorization
- Local Development & Infra (docker-compose + commands)
- Environment Variables (.env.example)
- Database Migrations and Seed
- Error Handling, Retries, Rate Limiting, Idempotency
- Observability & Monitoring
- Testing Strategy (unit, integration, e2e)
- CI/CD
- Security Considerations
- Non-functional Requirements and SLAs
- Implementation Plan & Milestones

---

## 1. Overview
This project builds an automation platform that integrates with Atlassian Jira and Confluence. The platform exposes a secure REST API and a React UI, allowing users to define automations, manage integrations, and review audit logs.

Primary technologies:
- Frontend: React 18 + Vite
- Backend: Node.js (LTS) + Express
- DB: PostgreSQL 15
- Containerization: Docker (docker-compose for local dev)

Deployment target: container-based environments (Kubernetes or simple container hosts) with managed Postgres recommended for production.

## 2. Goals & Success Criteria
- Implement stable REST API for automations and integrations with clear OpenAPI documentation.
- Provide a minimal React UI to configure integrations and display audit logs.
- Persist configuration and audit logs to PostgreSQL with migrations under source control.
- Local development via docker-compose with Postgres 15.
- CI pipeline that runs lint, tests, and builds client and server.

Success criteria (Phase 1):
- API implements CRUD for integrations and automation configs and a /jobs endpoint to track runs.
- Postgres schema and DB seeded for local dev.
- Integration with a mock Jira/Confluence allows running an automation job and recording audit logs.
- CI passing on PR with tests and lint configured.

## 3. Glossary
- Integration: credentials/configuration for a Jira or Confluence connection.
- Automation Config: a declarative object describing trigger, conditions, and actions.
- Job: a run/execution instance of an automation config; contains status and result.
- Audit Log: immutable record of actions performed by the platform.

## 4. System Architecture
Components:
- Client (SPA): communicates with API over HTTPS, authenticates via session/JWT.
- API Server: Express app; routes -> controllers -> services -> models.
- Worker (optional): same codebase may run scheduled or queued jobs; for Phase 1 jobs are executed synchronously via API.
- PostgreSQL: persistent storage for configuration and audit logs.
- (Optional) Redis: for caching and rate-limiting (Phase 2).

Sequence (example: run automation manually):
1. UI issues POST /api/v1/jobs with automation_id and parameters.
2. API validates, records a Job with status=queued, then executes the automation via service modules.
3. Service calls Jira/Confluence APIs (using stored integration credentials) and records results.
4. Job status updated to success/failure and audit log entry created.

## 5. API Specification
All endpoints prefixed with /api/v1
Responses are JSON. Timestamp format: RFC3339 (ISO 8601). Error format: { code, message, details? }

Authentication: Bearer JWT for API calls from UI or external clients (see auth section).

5.1 Integrations
- GET /api/v1/integrations
  - Query: ?provider= jira|confluence
  - Response: 200 [ { id, name, provider, created_at, updated_at, metadata } ]

- GET /api/v1/integrations/:id
  - Response: 200 { id, name, provider, metadata }

- POST /api/v1/integrations
  - Body: { name: string, provider: "jira"|"confluence", config: { baseUrl:string, authType: "token"|"oauth2", credentials: { token? , clientId?, clientSecret? } }, scopes?: [string] }
  - Response: 201 { id, name, provider, created_at }
  - Notes: credentials.token or oauth2 client id/secret are accepted but stored encrypted (see security)

- PUT /api/v1/integrations/:id
  - Body: partial allowed; update metadata or rotate credentials.
  - Response: 200 updated object

- DELETE /api/v1/integrations/:id
  - Response: 204

5.2 Automation Configs
- GET /api/v1/automations
  - Response: 200 [ { id, name, trigger, actions[], enabled, owner } ]

- GET /api/v1/automations/:id
  - Response: 200 { automation object }

- POST /api/v1/automations
  - Body: { name, description?, trigger: { type: 'manual'|'schedule'|'webhook', config: {} }, conditions?: [], actions: [ { type: 'create_issue'|'comment'|'update_page'|..., target_integration_id, params: {} } ], enabled: boolean }
  - Response: 201 { id }

- PUT /api/v1/automations/:id
  - Response: 200 updated

- DELETE /api/v1/automations/:id
  - Response: 204

5.3 Jobs (executions)
- POST /api/v1/jobs
  - Body: { automation_id, triggered_by: user_id|null, input?: {} }
  - Behavior: create Job row with status=running (or queued), execute actions, record results
  - Response: 201 { job_id }

- GET /api/v1/jobs/:id
  - Response: 200 { id, automation_id, status, started_at, finished_at, result, audit_log_ids }

- GET /api/v1/jobs?automation_id=&status=
  - Response: 200 [jobs]

5.4 Audit Logs
- GET /api/v1/audit?limit=50&since=
  - Response: 200 [ { id, job_id, action, actor, target, timestamp, details } ]

5.5 Health & Metrics
- GET /health
  - Response: 200 { status: 'ok', db: 'ok', queue: 'ok' }

- GET /metrics
  - Prometheus plaintext metrics (if enabled)

5.6 OpenAPI
- Provide an OpenAPI v3 spec file at /spec/openapi.yaml and a docs UI accessible in dev (optional).

## 6. Data Model (Postgres)
Use snake_case table names and UUIDs for primary keys (uuid_generate_v4()). Example minimal schema definitions.

6.1 Extensions
- Enable: "pgcrypto" or "uuid-ossp" to generate UUIDs.

6.2 Tables

users
- id UUID PRIMARY KEY
- username TEXT UNIQUE
- display_name TEXT
- email TEXT
- created_at TIMESTAMP WITH TIME ZONE

integrations
- id UUID PRIMARY KEY
- name TEXT
- provider TEXT -- 'jira' or 'confluence'
- config JSONB -- non-sensitive metadata
- credentials_encrypted BYTEA -- encrypted blob for secrets (or store reference to secret manager)
- scopes TEXT[]
- created_at TIMESTAMP WITH TIME ZONE
- updated_at TIMESTAMP WITH TIME ZONE

automation_configs
- id UUID PRIMARY KEY
- name TEXT
- description TEXT
- trigger JSONB
- conditions JSONB
- actions JSONB
- enabled BOOLEAN DEFAULT TRUE
- owner_id UUID REFERENCES users(id)
- created_at TIMESTAMP
- updated_at TIMESTAMP

jobs
- id UUID PRIMARY KEY
- automation_id UUID REFERENCES automation_configs(id)
- status TEXT -- enum 'queued'|'running'|'success'|'failed'|'cancelled'
- input JSONB
- result JSONB
- started_at TIMESTAMP
- finished_at TIMESTAMP
- created_at TIMESTAMP

audit_logs
- id UUID PRIMARY KEY
- job_id UUID REFERENCES jobs(id)
- action TEXT
- actor TEXT
- target JSONB
- details JSONB
- timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()

indexes: create indexes on frequently queried columns (automation_id, status, created_at)

## 7. Authentication & Authorization
7.1 Authentication
- JWT-based session tokens for UI-authenticated users (stateless). For API-to-API calls (workers, webhooks), use signed JWTs or client credentials.
- JWT signing: use RS256 (asymmetric) or HS256 with strong secret rotated regularly.

7.2 Authorization
- Role-based (basic) roles: admin, maintainer, user. Enforce via middleware.
- Ownership checks on automations: only owners or admins can modify.

7.3 Integration Credentials
- Sensitive credentials stored encrypted in DB (SERVER-side encryption) or better: store in an external secrets manager and keep only a reference in DB.
- Rotate credentials: expose an endpoint to rotate integration credentials and re-test.

## 8. Local Development & Infra
8.1 docker-compose (infra/docker-compose.yml)
A minimal docker-compose file (example):

services:
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: automations_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  server:
    build: ./server
    environment:
      DATABASE_URL: postgres://postgres:postgres@postgres:5432/automations_dev
      NODE_ENV: development
    ports:
      - "4000:4000"
    depends_on:
      - postgres

volumes:
  pgdata:

8.2 Local start scripts (makefile or scripts/)
- scripts/dev-db.sh — start docker-compose, wait for DB
- scripts/migrate.sh — run migrations against DATABASE_URL
- scripts/seed.sh — seed demo data

8.3 Developer workflow
- Copy .env.example to .env and update local overrides
- npm install at repo root (workspaces) OR cd into server/client and npm install
- Start Postgres and server: docker-compose up --build
- Start client: cd client; npm run dev

## 9. Environment Variables (.env.example)

# Server
PORT=4000
DATABASE_URL=postgres://postgres:postgres@localhost:5432/automations_dev
JWT_SECRET=replace_with_strong_secret
JWT_ALGO=HS256
NODE_ENV=development
ENCRYPTION_KEY=replace_with_32_byte_base64_key

# Optional
SENTRY_DSN=
PROMETHEUS_ENABLED=false

Notes:
- Do not commit local .env files. Provide .env.example with placeholders.
- ENCRYPTION_KEY used to encrypt integration credentials when not using external secret manager.

## 10. Database Migrations and Seed
- Use a migration tool (recommended: node-pg-migrate, Knex migrations, or Prisma Migrate).
- Store migrations under /server/migrations.
- Example commands:
  - npm run migrate:dev -> runs migrations against $DATABASE_URL
  - npm run migrate:up all
  - npm run migrate:down last

Seed content:
- Create an admin user, a sample integration (mocked token), a sample automation (manual trigger) and a few job/audit rows for UI development.

## 11. Error Handling, Retries, Rate Limiting, Idempotency
11.1 Error format
- Standard error response: { code: "ErrCode", message: "Human readable", details: { ... } }
- HTTP codes: 400 for validation, 401 unauthorized, 403 forbidden, 404 not found, 429 rate limited, 500 server error

11.2 Retries and backoff
- External HTTP calls (Jira/Confluence): implement exponential backoff with jitter, max retries = 3 by default.
- Respect Retry-After headers when returned by remote APIs.

11.3 Idempotency
- For actions that create external resources (create issue) support idempotency keys on Jobs: accept Idempotency-Key header; store key with job and ensure duplicate requests do not create duplicates.

11.4 Rate limiting
- Implement per-integration rate limiting to avoid hitting Atlassian quotas. Initially simple token-bucket in-memory; Phase 2 move to Redis for distributed rate limiting.

## 12. Observability & Monitoring
- Structured JSON logs (use pino or bunyan), include request id/correlation id and user id when available.
- Expose /metrics in Prometheus format. Track metrics: job_count_total{status=}, job_duration_seconds, external_api_calls_total{provider}, error_count_total.
- Health endpoints: /health (simple), /ready (readiness checks including DB connectivity).
- Tracing: add simple request timing and optional OpenTelemetry instrumentation.

## 13. Testing Strategy
13.1 Unit tests
- Test services, utilities, and controllers in isolation (mock external API clients).
- Coverage target: 80% minimum for services and core business logic.

13.2 Integration tests
- Run against a Postgres test DB in Docker. Use docker-compose-test or testcontainers to spin up Postgres for CI runs.
- Integration tests exercise API endpoints (supertest) and assert DB state changes.

13.3 End-to-end (E2E)
- Minimal end-to-end tests that run the client and server (or call API directly) to run one full automation path against mocked external APIs.

13.4 Contract tests
- If possible, add contract tests for Jira/Confluence interactions (mock servers or recorded fixtures) to detect breaking changes.

## 14. CI/CD
14.1 CI pipeline (example GitHub Actions)
- On PR: install (root workspaces), lint, run unit tests (server + client), build client (vite build), run integration tests (with Postgres service), upload coverage, run security scans (npm audit or Snyk).
- On merge to main: run full pipeline and build Docker images, push to registry with tag, trigger deployment to staging.

14.2 CD
- Staging: auto-deploy images from main branch builds.
- Production: manual promotion with release tag and changelog.

## 15. Security Considerations
- Secrets must never be committed. Use .env.example and secret manager in CI.
- Encrypt sensitive fields at rest or use external secret stores.
- Use HTTPS in all environments; require TLS for callbacks and webhooks.
- Validate and sanitize all inputs before calling external APIs.
- Rate-limit and throttle to protect downstream services.
- Regular dependency scanning and CVE monitoring.

## 16. Non-functional Requirements and SLAs
- Availability: target 99.5% in Phase 1 (measured at service endpoints)
- Recovery time objective (RTO): 1 hour for service restore
- Backup retention: daily backups retained for 30 days (configurable)

## 17. Implementation Plan & Milestones
M1 (Week 0-2): Project setup
- Create monorepo and skeleton (done)
- Configure workspaces and root CI
- Add migration tooling and basic Postgres Docker compose

M2 (Week 2-4): Core API & DB
- Implement integrations CRUD, automations CRUD, jobs execution skeleton
- Add migrations and seed scripts
- Add basic React pages for listing integrations and automations

M3 (Week 4-6): Execution & Audit
- Implement job runner (sync) and persistent audit logs
- Add retry/backoff and idempotency support
- Add tests and instrumentation

M4 (Week 6-8): Hardening & CI/CD
- Complete CI pipeline, build Docker images, push to registry
- Add observability (metrics, logs) and docs

## 18. Verification Checklist
- [ ] OpenAPI spec exists and matches implemented routes
- [ ] Database migrations apply cleanly to a fresh Postgres 15 instance
- [ ] Server passes unit + integration tests in CI
- [ ] Client builds with `vite build` (production) in CI
- [ ] Sample automation run creates a job and audit log when executed locally
- [ ] Secrets are not present in any committed files

## 19. Appendix
19.1 Example Job request

POST /api/v1/jobs
Headers: Authorization: Bearer <token>
Body:
{
  "automation_id": "<uuid>",
  "triggered_by": "user:alice",
  "input": { "issue_summary": "Automated issue from SpecKit" }
}

19.2 Example Integration create

POST /api/v1/integrations
Body:
{
  "name": "Jira Dev",
  "provider": "jira",
  "config": { "baseUrl": "https://example.atlassian.net", "authType": "token" },
  "credentials": { "token": "<REDACTED>" }
}

19.3 Recommended libraries & tools
- Node: express, pino (logging), node-postgres (pg), knex or prisma (migrations/ORM), axios (HTTP client), jose/jsonwebtoken (JWT)
- Frontend: vite, react, react-router, axios or fetch wrapper, vitest
- Dev: docker, docker-compose, GitHub Actions (or other CI), testcontainers (optional)

---

For the next step: I can generate the OpenAPI spec skeleton (/spec/openapi.yaml), create infra/docker-compose.yml, or scaffold the server migration files. Which would you like me to do next?