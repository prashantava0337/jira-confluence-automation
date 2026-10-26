# Specification Review: Gaps, Contradictions and Unclear Requirements

**Reviewed**: [constitution.md](./constitution.md) (v1.1.0) and [specification.md](./specification.md) (Draft, updated 2026-10-26)
**Reviewer role**: Senior developer, pre-planning review
**Date**: 2026-10-26
**Purpose**: Find what must be decided before `plan` and `tasks`. Nothing here changes the spec yet; each item ends with what is needed to close it.

## How to read this document

- **Blocker**: planning or implementation of a core flow cannot start without a decision.
- **Major**: the area can be started, but the gap will cause rework or a security or data-integrity problem.
- **Minor**: should be settled, low risk of rework.
- IDs: **C** = contradiction (two statements disagree), **G** = gap (missing), **U** = unclear (present but ambiguous or untestable).
- "Spec" means `specification.md`; "Const." means `constitution.md`.

## Summary

| Type | Blocker | Major | Minor | Total |
|---|---|---|---|---|
| Contradictions (C) | 2 | 7 | 7 | 16 |
| Gaps (G) | 2 | 16 | 7 | 25 |
| Unclear requirements (U) | 0 | 5 | 6 | 11 |
| **Total** | **4** | **28** | **20** | **52** |

The two `[NEEDS CLARIFICATION]` markers already in the spec are included as Q-01 and Q-02 below.

**Must resolve first (blockers):**
1. **C-01**: Sign-in is a requirement, but no endpoint, column, or user-management flow exists for it.
2. **C-02**: "Synchronous jobs" contradicts `queued`, `cancelled`, "fetch a running job", and the schedule and webhook triggers.
3. **G-01**: No permission matrix, and any maintainer can bind an automation to any integration's credentials.
4. **G-02**: Triggers, conditions, actions, and input mapping have no schema, so an automation cannot be implemented.

---

## 1. Contradictions

**C-01 · Blocker · Sign-in is required but nothing defines it**
- Where: Spec US5, FR-021 to FR-023 vs Appendix A (API) and Appendix B (data model).
- Problem: Key Entities say a User has a role, but the `users` table has no `role` and no password hash. Appendix A has no login, logout, or user endpoints. US5 AC1 says "valid credentials" without saying what they are. The scaffolded migration copies these omissions.
- Needed: Define the credential type, the auth endpoints, the `users` columns (role, password hash, active flag), and how users are created. See G-09 and Q-02.

**C-02 · Blocker · Synchronous execution vs the job lifecycle**
- Where: FR-013 and Const. VII ("jobs run synchronously") vs FR-012 (`queued`, `cancelled`), US3 AC5 ("fetch a running job"), FR-007 (schedule, webhook).
- Problem: If `POST /jobs` blocks until the job finishes, nobody can fetch it while `running`, and `queued` and `cancelled` can never occur. Cancellation has no endpoint. A schedule trigger needs a background scheduler, and a webhook trigger needs an inbound endpoint. Neither fits a purely synchronous model. A long job also holds an HTTP request open.
- Needed: Decide between (a) truly synchronous and drop `queued`, `cancelled`, and the "running" scenario, or (b) accept the request, return the job id immediately, and run it in-process behind a runner interface. Option (b) keeps the Phase 1 "no external queue" rule. See Q-04.

**C-03 · Major · Atlassian authentication is undecided but required**
- Where: Spec Assumptions ("settled in the first RFC"), FR-003, FR-005, Const. III and scope (OAuth2 or API tokens).
- Problem: The spec requires both methods yet defers the choice. For Jira Cloud, API-token auth also needs the account email, but the example integration carries only `{ token }`. Scopes are an OAuth 2.0 concept; for a classic API token the spec never says how least privilege is achieved. OAuth2 needs redirect URIs, a consent flow, and token refresh, none of which are specified.
- Needed: Pick the Phase 1 method and the credential shape per method. See Q-03.

**C-04 · Major · Credential storage options vs the data model**
- Where: Const. III and FR-003 ("encrypted at rest, or a reference to a secrets manager") vs Appendix B (`credentials_encrypted BYTEA` only) and the request example.
- Problem: The data model cannot hold a secrets-manager reference. The request nests secrets inside `config`, while `config` is described as non-sensitive metadata. Nothing says the server must strip `config.credentials` before persisting `config`, so an implementation could store secrets in plain JSONB.
- Needed: One storage mode for Phase 1, a column (or table) for it, and an explicit rule that secrets are extracted from `config` and never persisted there.

**C-05 · Major · `triggered_by` is client-supplied and not stored**
- Where: Appendix A (`POST /jobs` body) vs Appendix B (`jobs` has no `triggered_by` column), FR-011.
- Problem: Letting the caller state who triggered a job allows spoofing and corrupts the audit actor. The value is also never persisted.
- Needed: Derive the actor from the authenticated token, remove it from the request body, and add a column (nullable for schedule and webhook).

**C-06 · Major · "Immutable" and "100%" audit vs the data model and failure modes**
- Where: Const. VI, FR-018, FR-019, SC-002 vs Appendix B.
- Problem:
  - Const. VI says each entry records status, but `audit_logs` has no status column.
  - `actor` is free text while users have UUIDs.
  - Immutability is not enforced anywhere (no revoked UPDATE and DELETE, no trigger).
  - `job_id` must be nullable for non-job events (see G-13) but is not declared so.
  - If the database is down after a remote action succeeds, the 100% target is impossible (listed as an edge case, but without behavior).
- Needed: Define the columns, enforce append-only at the database level, and choose a write order (record intent before the action and the result after). See Q-12.

**C-07 · Major · Idempotency promises cannot be met as written**
- Where: FR-015, SC-004, Const. VI, Appendix B (`idempotency_key UNIQUE`).
- Problem: Jira has no idempotency keys, so "0 duplicate external resources" cannot be guaranteed when a create call times out after succeeding. The key is globally unique, so two users using the same key collide. Same key with a different body is listed as an edge case with no rule. There is no key lifetime.
- Needed: Scope keys per user, set a retention window, return 409 on a body mismatch, and reword SC-004 to what is achievable (for example, no duplicate jobs, and at-least-once semantics for ambiguous remote failures). See Q-11.

**C-08 · Minor · `PUT` used for partial updates**
- Where: Appendix A (`PUT /integrations/:id`: "partial update or credential rotation").
- Problem: `PUT` means full replacement. Partial semantics need `PATCH`, or the endpoint must require the whole object.
- Needed: Choose `PATCH` for partial updates, or state that `PUT` replaces.

**C-09 · Major · Mock Jira: tests only, or a runtime feature**
- Where: Assumptions ("simulated in tests") vs SC-001 ("first run against a mock Jira using only the UI") and the Phase 1 goal of running a job against a mock.
- Problem: A UI user can only run against a mock if one ships with the product or dev stack. The spec does not say it does.
- Needed: Decide whether a mock Atlassian server is part of `/infra` for local and demo use, and how an integration is pointed at it.

**C-10 · Major · Milestones omit required work**
- Where: Appendix D vs US5, FR-021 to FR-023, FR-031.
- Problem: No milestone includes authentication, user management, or the jobs and audit UI pages (M2 lists only integrations and automations pages). Yet FR-031 requires all four pages and US5 is P2.
- Needed: Add the missing work to a milestone and confirm the priorities.

**C-11 · Minor · Two OpenAPI locations**
- Where: Const. V and FR-026 (`/spec/openapi.yaml`) vs the skeleton's `server/docs/swagger.yaml`.
- Problem: Two files for one contract, both currently empty placeholders; no rule for which is authoritative or how it is generated.
- Needed: One source of truth, and whether it is hand-written or generated from code.

**C-12 · Minor · Where dev tooling lives**
- Where: Const. layout (`/infra` holds "docker-compose and local development tooling") and FR-030 vs the skeleton (`/scripts/dev-db.sh`, `migrate.sh`, `seed.sh`; `/infra` holds only compose).
- Needed: Put the scripts in one place and update the layout.

**C-13 · Minor · "Test-First" principle allows tests after the code**
- Where: Const. IV: the principle is "Test-First", but the rule says tests are written "before or together with" the code.
- Needed: Pick one rule, or rename the principle.

**C-14 · Minor · `/metrics` is unconditional in one place and optional in another**
- Where: Const. VI ("exposes /metrics") vs FR-027 ("when enabled") and `PROMETHEUS_ENABLED`.
- Problem: When disabled, does it return 404 or an empty body? Is it authenticated? Exposing it publicly is a leak risk (see G-19).
- Needed: Define the disabled behavior and who may read it.

**C-15 · Minor · 429 listed with no inbound rate limit**
- Where: FR-025 and Const. V list 429; FR-017 only limits calls out to Atlassian.
- Problem: Nothing defines when the platform itself returns 429 to its own clients.
- Needed: State whether inbound rate limiting exists (and on which routes), or remove 429 from the platform's own errors and add 502/503/504 for upstream problems (see G-12).

**C-16 · Minor · Client language not stated, skeleton mixes both**
- Where: Const. stack table ("React 18 + Vite") vs the skeleton (`client/tsconfig.json` alongside `.jsx` and `.js` files).
- Needed: Decide JavaScript or TypeScript for client and server, and make the linting and test setup match.

---

## 2. Gaps

**G-01 · Blocker · No authorization matrix, and a privilege-escalation path**
- Where: FR-022, Const. III; US1 (admin creates integrations), US2 (maintainer creates automations), FR-009.
- Problem: Roles are named but no table says who may read, create, change, delete, or run what. Can a `user` run an automation they do not own? Who can see audit logs? More serious: if a maintainer can add an action that targets any integration, the job runs with that integration's stored credentials, so a maintainer gains the admin's Jira access indirectly.
- Needed: A role-by-operation matrix; a rule for which integrations a user may bind; and a statement that jobs run with the integration's authority, with the triggering user recorded. See Q-06 and Q-07.

**G-02 · Blocker · No schema for triggers, conditions, actions, or input mapping**
- Where: FR-006 to FR-008, US2, Appendix A.
- Problem: The central object of the product is "declarative" but undefined. Missing: the JSON shape for each trigger type; what a condition is and how it is evaluated (see U-02); the parameters of each action type (for example fields of `create_issue`: project, issue type, summary, fields); how run `input` feeds action parameters (the example `issue_summary` has no stated binding); the shape of `result` and of per-action results. The FR-008 check ("integration exists") is the only validation rule.
- Needed: A versioned JSON Schema per trigger and action type, a templating rule for input, and a stated validator. See Q-08.

**G-03 · Major · Which Atlassian products and API versions**
- Where: Appendix A examples (`example.atlassian.net`), no other statement.
- Problem: Cloud is implied, never stated. Cloud and Data Center/Server differ in auth, endpoints, and rate limits. Jira Cloud comments and Confluence pages use structured content formats, and Confluence has more than one API generation. `update_page` is also ambiguous: replace the page, a section, or append?
- Needed: State the supported products and API versions, content format handling, and exact `update_page` semantics. See Q-10.

**G-04 · Major · Multi-action execution semantics**
- Where: US3 AC1 to AC3, Edge Cases.
- Problem: Not defined: what happens when action 2 of 3 fails (stop or continue); whether earlier actions are compensated; whether the job is `failed` or has a partial state; per-action and per-job timeouts; maximum job duration; concurrency limits; a cancellation mechanism; a cap on honoring `Retry-After` (an hour-long value must not hold a request or a worker); which errors are retryable (429, 5xx, network) and the danger of retrying a non-idempotent create after a timeout (see C-07).
- Needed: A failure policy (see Q-05), timeouts, retry classification, and per-action result recording.

**G-05 · Major · Schedule and webhook triggers**
- Where: FR-007.
- Problem: Required by a MUST but no behavior: cron syntax and timezone, what component runs schedules and survives restarts or multiple instances, how missed runs are handled, the inbound webhook URL, how it is authenticated (it cannot use the user JWT), signature verification and replay protection, and who the actor is for audit. None is in the API contract.
- Needed: Define them, or defer both to Phase 2 and amend FR-007 to "manual only in Phase 1". See Q-09.

**G-06 · Major · Outbound request security (SSRF)**
- Where: Const. III ("validate and sanitize"), Appendix A (`baseUrl` supplied by a user).
- Problem: The server makes HTTP calls to a user-supplied URL. Without rules, a user can aim it at internal addresses or cloud metadata endpoints. Not specified: HTTPS-only, host allow-list or domain pattern, blocking private and link-local ranges, redirect handling, response size, and timeouts.
- Needed: An outbound-call policy and tests for it.

**G-07 · Major · Job snapshot and deletion semantics**
- Where: FR-020 ("reconstruct and re-run"), Edge Cases, US1 AC4 (Q-01), Appendix B.
- Problem: `jobs` stores only `automation_id`, so editing or deleting an automation erases what a past job ran, and a running job may pick up changes mid-flight. `ON DELETE` behavior is unspecified for `jobs.automation_id`, `audit_logs.job_id`, and `automation_configs.owner_id`. Hard or soft delete is not stated. "Re-run" is mentioned but no re-run feature exists.
- Needed: Snapshot the automation definition on the job, define delete behavior (soft delete recommended), and either define re-run or remove the phrase.

**G-08 · Major · Session and login security**
- Where: FR-021, Appendix C (`JWT_SECRET`, `JWT_ALGO`).
- Problem: Missing: token lifetime, refresh, revocation or logout, where the browser stores the token (XSS and CSRF trade-off), CORS policy, password hashing algorithm and policy, login rate limiting and lockout. RS256 is permitted but Appendix C defines no key variables. The seed script creates an admin user: it must never run, or have a known password, in production.
- Needed: A session design and a rule that seeds are non-production only.

**G-09 · Major · No user management**
- Where: Appendix A, Key Entities.
- Problem: There is no way to create a maintainer, change a role, or deactivate a user. Only a seeded admin exists. The skeleton already has placeholder `auth` and `users` routes that the spec does not cover.
- Needed: User and role endpoints, or an explicit statement that users are managed outside the app in Phase 1.

**G-10 · Major · Credential rotation and connection testing have no endpoint**
- Where: FR-004 ("rotate credentials and re-test").
- Problem: Only `PUT` exists. No "test connection" operation, no result shape, and no integration health or last-verified state shown in the UI.
- Needed: A test endpoint (for example `POST /integrations/:id/test`), its response, and whether create tests the connection first.

**G-11 · Major · List endpoint conventions**
- Where: Appendix A.
- Problem: Only `/audit` has `limit` and `since`. Integrations, automations, and jobs have no pagination or sorting. For audit: is `since` inclusive; what is the maximum `limit`; with "newest first" plus `since`, how does a client page forward; how are ties on the same timestamp handled.
- Needed: One pagination convention (cursor recommended) applied to every list.

**G-12 · Major · Error model details**
- Where: FR-025, Const. V.
- Problem: Only five status codes are listed. Missing: 409 (conflicts, deletion blocked, idempotency mismatch), 422 or a rule for validation, 502, 503, and 504 for upstream and readiness failures. No catalogue of `code` values, no shape for `details` on validation errors, and no rule that errors never echo secrets.
- Needed: An error code catalogue and the `details` shape.

**G-13 · Major · Audit covers only job actions**
- Where: FR-018, Const. VI ("every automation action").
- Problem: Security-relevant events are not audited: sign-in and failures, integration create, update, rotate, and delete, role changes, and automation edits and deletes. FR-018 ties each entry to a job, but these have none.
- Needed: Define the audited event set and make `job_id` optional (see C-06).

**G-14 · Major · Retention, privacy, and redaction**
- Where: FR-020, Const. Persistence, Const. backups.
- Problem: No retention period for jobs and audit rows, no rule on what Jira or Confluence content may be stored in `result` or `details` (it can contain personal data), no redaction rules for logs and audit, and no way to reconcile "immutable" with a deletion request or the 30-day backup window.
- Needed: Retention periods, a redaction list, and a stated stance on erasure.

**G-15 · Major · Concurrency control**
- Where: Edge Cases ("two users update the same automation").
- Problem: Listed but no requirement. Without versioning, the last write silently wins.
- Needed: Optimistic locking (a version column or ETag with `If-Match`), and the error returned on conflict (409).

**G-16 · Major · Key management**
- Where: Appendix C (`ENCRYPTION_KEY`, `JWT_SECRET`), Const. III.
- Problem: One environment variable holds the encryption key. Not specified: the algorithm and mode, key identifier stored with each ciphertext, how keys are rotated and old data re-encrypted, and what happens when a key is lost or an entry cannot be decrypted (an edge case with no behavior).
- Needed: An encryption design and a rotation procedure.

**G-17 · Major · Performance and recovery targets**
- Where: FR-013, SC-006, SC-007, Const. non-functional targets.
- Problem: "Hundreds of runs per day" is volume, not a requirement. No latency target (for example API p95), no maximum concurrent jobs, no request or payload size limits. 99.5% availability has no measurement method (the earlier text said "measured at service endpoints") and no maintenance-window rule. Daily backups imply up to 24 hours of lost audit data, but no recovery point objective is stated.
- Needed: Concrete targets, how each is measured, and an RPO.

**G-18 · Major · Environments and deployment**
- Where: Const. CD and Docker; Spec Assumptions.
- Problem: The deployment target is not named (the earlier text mentioned Kubernetes or simple container hosts). Missing: which registry, how staging and production get secrets and which secrets manager, when migrations run during a deploy, rollback and down-migration policy, zero-downtime expectations, and a ban on running seeds in production. The compose file runs the app as an opt-in profile only because the server Dockerfile is a placeholder.
- Needed: A deployment target and a migration and rollback policy.

**G-19 · Minor · Observability details**
- Where: FR-027, FR-028, Const. VI.
- Problem: Correlation id source and propagation to Atlassian calls are unspecified. No log redaction rule. No metric label set or cardinality guidance. Tracing was dropped when the spec was restructured. No alerting or SLO definitions. Whether `/health`, `/ready`, and `/metrics` are authenticated is not stated.
- Needed: Decide each, especially the exposure of `/metrics`.

**G-20 · Minor · UI requirements**
- Where: FR-031, SC-001.
- Problem: Only page names are given. Missing: the login and logout screens, how a user edits triggers and actions (raw JSON or structured forms), the manual-run input form, loading, empty, and error states, accessibility level, supported browsers, and the routing structure. SC-001 ("10 minutes using only the UI") depends on these.
- Needed: UI scenarios and an accessibility target.

**G-21 · Minor · Field validation rules**
- Where: Appendix A and B.
- Problem: No lengths, formats, or uniqueness rules (integration and automation names, user email). Unspecified whether a malformed id returns 400 or 404. No named validation library or JSON Schema approach.
- Needed: A constraints table.

**G-22 · Minor · Time handling**
- Where: FR-024.
- Problem: RFC 3339 is required, but storage in UTC, the timezone of schedules, and clock-skew handling are not stated.
- Needed: UTC everywhere in storage, and an explicit timezone field for schedules.

**G-23 · Minor · Governance and referenced documents**
- Where: Const. Governance, Const. layout.
- Problem: "Project leads" and the owner are not named (the earlier version listed an owner; the restructured one dropped it). No RFC template, numbering, or status flow, and no RFC exists yet, including the first one the spec says is needed (authentication). `/spec/README.md`, `integrations.md`, `recovery.md`, and `openapi.yaml` are referenced as required but are empty.
- Needed: Name the owners, add an RFC template, and fill or remove the referenced documents.

**G-24 · Minor · CI/CD details**
- Where: Const. Workflow.
- Problem: Pre-commit tooling, the severity that fails the dependency scan, coverage enforcement in CI, Node version matrix, image tagging and scanning, and branch-protection settings are all unstated. The CI workflow file is an empty placeholder.
- Needed: Choices for each, recorded in the plan.

**G-25 · Minor · Tooling choices left open**
- Where: Spec Appendix F ("recommended").
- Problem: Not decided: ORM or query layer and migration tool (knex, node-pg-migrate, or Prisma), the server test runner (jest or vitest), HTTP client, logger. The skeleton's `migrate.js` and the SQL migration make assumptions that depend on these.
- Needed: An RFC or plan decision before scaffolding code.

---

## 3. Unclear requirements

**U-01 · Minor · Open-ended action list.** FR-007 says action types "including" three examples. Is the list closed in Phase 1? Adding types later needs a versioning rule (see G-02).

**U-02 · Major · "Conditions".** Present in FR-006 and the data model, never defined: what they evaluate (job input, previous action results, remote data), the expression format, and whether Phase 1 supports them at all.

**U-03 · Major · "Minimum scopes".** FR-005 and Const. III require least privilege, but nothing maps each action type to the scopes or permissions it needs, or says who decides.

**U-04 · Major · Per-integration rate limiting.** FR-017 gives no rate, burst, or window, and no behavior when exceeded (wait, fail, or queue). An in-memory limiter resets on restart and does not work across more than one server instance; Phase 1 single-instance is implied but not stated.

**U-05 · Minor · "Only when audit requires".** FR-020 allows storing full external payloads when audit requires it. Who decides, and what is the rule? (See G-14.)

**U-06 · Minor · "Must not prevent" a later queue.** FR-013 cannot be tested. Rephrase as a design constraint, such as a runner interface with an in-process implementation.

**U-07 · Minor · What "ready" means.** FR-027 says `/ready` includes database connectivity. Does it also require applied migrations or reachability of Atlassian? Atlassian outages should usually not make the service unready.

**U-08 · Minor · Ownership.** The owner of an automation can change or be deactivated. Is transfer possible, and who may transfer? Is `owner_id` required? The table allows null, FR-009 implies it is always set.

**U-09 · Major · Edge cases with no behavior.** All eight edge cases are only listed. Each needs a stated outcome or a requirement: edit or delete during a run; remote outage or malformed response; same key with a different body; concurrent edits; revoked credential mid-job; oversized `limit` or invalid `since`; undecryptable credential; database down when an audit entry is due.

**U-10 · Major · Success criteria that cannot be measured as written.**
- SC-001 (10 minutes using only the UI) and SC-005 (a working stack in under 15 minutes) name no method or test subject.
- SC-006 restates a volume, not a pass or fail test.
- SC-003 ("0 credentials ... in any committed file") needs a named scanning tool in CI.
- Needed: Who measures, how, and what tool.

**U-11 · Minor · Audit "outcome".** US4 says entries show the outcome, but the data model has no outcome or status field (see C-06). Is it a column or inside `details`?

---

## 4. Impact on the current scaffold

These items are already reflected in files committed under `module08-skeleton/`:
- [001_init.sql](../server/migrations/001_init.sql) has no `users.role`, password hash, `jobs.triggered_by`, automation snapshot, audit `status`, or soft-delete columns (C-01, C-05, C-06, G-07).
- The jobs controller reads the `Idempotency-Key` header and passes the whole request body, including any client-supplied actor, to the service (C-05, C-07).
- Only `/health` is wired in the server routes; `/ready` and `/metrics` do not exist (FR-027).
- `spec/openapi.yaml`, `spec/README.md`, `spec/integrations.md`, `spec/recovery.md`, `.github/workflows/ci.yml`, and the lint config files are empty placeholders (C-11, G-23, G-24).
- The server `Dockerfile` is a placeholder, so the compose `server` service is behind an opt-in profile (G-18).

Resolve the blockers before building further on the migration and the routes.

## 5. Questions to answer

Each question has a recommended default so it can be accepted quickly. These are proposals for the owners to approve, not decisions.

| # | Question | Recommended default | Closes |
|---|---|---|---|
| Q-01 | Deleting an integration that automations use: block or cascade? | Block with 409; list the dependent automations in `details` | US1 AC4, G-07 |
| Q-02 | Users: local accounts or linked to Jira? | Local accounts with email and a hashed password; SSO in Phase 2 | FR-023, C-01, G-09 |
| Q-03 | Atlassian auth in Phase 1? | API token (email plus token) for Cloud; OAuth2 in Phase 2 via an RFC | C-03 |
| Q-04 | Job execution model? | `POST /jobs` returns the job id immediately; run in-process behind a runner interface; statuses `queued`, `running`, terminal | C-02, U-06 |
| Q-05 | Failure policy across actions? | Stop at the first failed action; mark the job `failed`; record each action's result; no automatic rollback | G-04 |
| Q-06 | Role permissions? | `admin`: everything. `maintainer`: manage own automations, run any enabled automation, read integrations without secrets. `user`: read and run enabled automations, read audit | G-01 |
| Q-07 | Who may bind which integration? | Integrations are shared org-wide and admin-managed; maintainers may bind them; the risk is documented and every job records its actor | G-01 |
| Q-08 | Phase 1 action catalogue and input mapping? | `create_issue`, `add_comment`, `update_page` only; JSON Schema per type; `{{input.key}}` templating; no conditions | G-02, U-01, U-02 |
| Q-09 | Triggers in Phase 1? | Manual only; schedule and webhook deferred, and FR-007 amended | G-05 |
| Q-10 | Which Atlassian products? | Jira Cloud and Confluence Cloud only | G-03 |
| Q-11 | Idempotency rules? | Key unique per user, 24-hour retention, 409 on body mismatch; reword SC-004 to "no duplicate jobs" | C-07 |
| Q-12 | Audit write order? | Write an intent entry before each action and a result entry after; if the intent write fails, skip the action; make the table append-only by database permission | C-06, G-13 |
| Q-13 | Session design? | HS256, 60-minute access token held in memory, no refresh in Phase 1; seeds never run in production | G-08 |
| Q-14 | Mock Atlassian server? | Ship a small mock under `/infra` for development and tests | C-09 |
| Q-15 | Client and server language? | Pick one of JavaScript or TypeScript for both and align tooling | C-16 |
| Q-16 | Migrations, data access, tests? | node-pg-migrate, `pg`, vitest | G-25 |

## 6. Closing this review

1. Answer or amend Q-01 to Q-16 (the owners decide; the defaults above are only suggestions).
2. Record the answers in a `## Clarifications` section in `specification.md`, dated, and update the affected requirements, data model, and milestones.
3. Remove the two `[NEEDS CLARIFICATION]` markers once Q-01 and Q-02 are answered.
4. Fix the scaffolded migration and controllers to match, then proceed to the plan and tasks.
