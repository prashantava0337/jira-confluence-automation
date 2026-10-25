# SpecKit Constitution — Jira / Confluence Automation Project

Version: 1.0
Date: 2026-09-14
Owner: Project Team / Automation Squad

## 1. Purpose
This Constitution defines the scope, architecture, standards, and governance for the Jira/Confluence Automation project (the Project), whose goal is to build a maintainable automation platform that integrates with Atlassian Jira and Confluence to automate common workflows, templates, and documentation tasks.

The Project uses a modern web stack:
- Frontend: React 18 + Vite
- Backend: Node.js (LTS) + Express
- Database: PostgreSQL 15 (containerized via Docker)

This document is written as a SpecKit-style constitution to guide implementing teams, reviewers, and future maintainers.

## 2. Scope
In scope:
- Build a secure REST API that performs actions against Jira and Confluence using OAuth2 or API tokens.
- Provide a web UI for configuration, monitoring, and manual triggers of automations.
- Persist configuration, audit logs, and small reference data in PostgreSQL 15.
- Containerize the backend and database for local dev and CI using Docker and docker-compose (or similar).
- Provide CI/CD pipelines for tests, linting, build, and deployment.

Out of scope (initial):
- Implementing full enterprise SSO integration (deferred to Phase 2).
- Large-scale event-driven automation at massive scale (deferred; initial target is moderate throughput).

## 3. Non-functional Requirements
- Security: secrets must be stored encrypted (Vault or environment-managed secrets in CI). Minimally, do not commit API tokens.
- Observability: logs, metrics, and basic tracing for the backend (structured JSON logs and Prometheus metrics where feasible).
- Reliability: automated retries for external API calls with exponential backoff and idempotency where necessary.
- Performance: the system should handle typical org automation load (hundreds of ops/day) without special scaling in Phase 1.
- Maintainability: clear modular separation (routes → controllers → services → models) and tests for services and key integrations.

## 4. High-level Architecture
- Client (React 18 + Vite): Single Page App for configuration, audit views, and manual/preview flows. Communicates with backend via secure REST API.
- API (Node.js + Express): Implements API endpoints for UI and automation workers; encapsulates Jira/Confluence integration logic in service modules.
- PostgreSQL 15: stores accounts, configuration, audit logs, job metadata, and lightweight state.
- Docker: local dev and CI will run PostgreSQL in a Docker container. Production deployment may use managed Postgres.

Suggested repo layout (monorepo):
- /client — React + Vite app
- /server — Node/Express API
- /spec — design and SpecKit docs
- /infra — docker-compose and local dev tooling

## 5. Data Model (High level)
- users: local application users (if needed), references to Jira accounts
- integrations: per-tenant integration records (credentials, scopes, metadata)
- automation_configs: definitions of triggers, conditions, and actions
- jobs: execution history, status, result payloads
- audit_logs: immutable records of automation actions and source

Design note: store only the minimal set of metadata required to reconstruct and re-run operations. Avoid persisting complete external payloads unless required for audit.

## 6. Security and Secrets
- API tokens and OAuth client secrets MUST NOT be committed to source control.
- For local dev, use .env files listed in .env.example; never commit .env.
- In CI/CD and production, prefer a secrets manager (HashiCorp Vault, AWS Secrets Manager, or equivalent) or the host platform's secrets feature.
- Use HTTPS for all external callbacks and redirect URIs.
- Follow least-privilege: request only required scopes from Jira/Confluence for each integration.

## 7. API Contract Guidelines
- RESTful, versioned endpoints (/api/v1/...), JSON request/response.
- Use consistent error format: { code, message, details? }
- Provide openapi/swagger spec in /spec for key endpoints. Keep the spec up to date as part of PR review.

## 8. Local Development and Docker
- docker-compose.yml (in /infra) will define:
  - postgres: image postgres:15
  - server: optional local build referencing server source
  - (optional) a lightweight reverse proxy for routing
- Provide a script to bootstrap local DB schema (migrations) and seed minimal test data.
- Keep docker images small (alpine-based production builds where appropriate) but prefer correctness and stability.

## 9. Testing Strategy
- Unit tests for services and utility functions (Node: jest or vitest for frontend).
- Integration tests for API endpoints using a test database (Postgres in Docker) and test doubles for Jira/Confluence where possible (recorded fixtures or mock server).
- End-to-end tests for high-level workflows as time permits; start with a small critical-path E2E suite.

## 10. CI/CD
- CI pipelines must run: lint, unit tests, build (client), and server unit tests.
- For merging to main, require passing CI and at least one approving review.
- CD: container images pushed to registry and deployed to staging. Production promotion via PR and release tagging.

## 11. Observability and Logging
- Backend logs: structured JSON with timestamps, correlation IDs, and log-levels.
- Expose a /health and /metrics endpoints on the server for readiness and monitoring.
- Capture audit logs for each automation action (who/what/when/status).

## 12. Backup and Recovery
- Database backups: scheduled snapshots (if using managed DB) or pg_dump-based backups for self-hosted.
- Ensure that audit and job records are included in backups and that recovery procedures are documented in /spec/recovery.md.

## 13. Coding Standards and Conventions
- JavaScript/TypeScript style: eslint + prettier configuration in root. Enforce via pre-commit hooks and CI.
- Project structure: keep controllers thin; business logic belongs in services. Models should be ORMs or lightweight query modules.
- Commit messages: follow Conventional Commits for clarity and automation.

## 14. Branching and Release Policy
- Main branch: protected, always deployable.
- Development branches: feature/*, fix/*, chore/*.
- PRs require code review, passing CI, and an optional QA sign-off for larger changes.
- Releases: tag with semantic versioning and attach changelog entries.

## 15. Governance and Change Control
- This Constitution is the authoritative project design guide. Changes to architecture or major decisions must be recorded as RFCs in /spec/rfcs and approved by the project owners.
- Minor changes to coding standards may be approved via PRs; major changes require an RFC and an approval by project leads.

## 16. Onboarding and Documentation
- Keep this constitution and a short QuickStart in /spec/README.md.
- Document how to obtain Jira/Confluence developer credentials and recommended scopes in /spec/integrations.md.
- Provide examples for local dev, migration, and seeding in /infra and /spec.

## 17. Risk Register (top items)
- Credential leakage — mitigate with secrets management and peer review.
- API rate limits from Atlassian — mitigate via caching, retries, and backoff.
- Schema drift between environments — mitigate with migrations + CI checks.

## 18. Appendix
- Tech stack: React 18 (Vite), Node.js (LTS) + Express, PostgreSQL 15 via Docker.
- Recommended Node version: match .nvmrc (LTS, e.g., 24.x).
- Spec location: /spec in repository; RFCs live in /spec/rfcs.

---

This constitution can be updated by submitting an RFC and approval. For immediate next steps, draft an initial RFC that details: authentication choices (OAuth2 vs API tokens), required Jira/Confluence scopes, and a minimal data model for automations and audit logs.
