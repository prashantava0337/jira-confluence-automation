# Implementation Tasks: Jira / Confluence Automation Platform

**Source plan**: [plan.md](./plan.md)  
**Specification**: [specification.md](./specification.md)  
**Constitution**: [constitution.md](./constitution.md) v1.1.0  
**Status**: Proposed; implementation tasks are gated by the decisions below.

## Task conventions

- Each task has a stable ID, dependencies, and verifiable acceptance criteria.
- A dependency is a prerequisite, not merely an earlier task in this list.
- Tasks depending on unresolved decisions must not begin until the decision is
  recorded in `specification.md` (and in an RFC where required).
- Scope changes require updating the specification and this task list before
  implementation.

## Phase 0 — Clarify and baseline (Gate G0)

### T001 — Resolve product and architecture questions

**Depends on**: None  
**Scope**: Obtain owner decisions for the open questions in
[`clarify.md`](./clarify.md), including identity, Atlassian authentication,
authorization, integration sharing/deletion, job execution, failure handling,
idempotency, audit, triggers/actions, mock services, language/tooling, and
deployment assumptions.

**Acceptance criteria**
- [ ] Every blocker and every question that affects Phase 1 behavior, API
  contracts, permissions, or schema has an explicit owner-approved answer or
  an explicit deferral.
- [ ] Deferred requirements are removed from or marked out of scope in
  `specification.md`; they are not merely omitted from implementation tasks.
- [ ] The decisions are recorded in a dated `Clarifications` section in
  `specification.md`.
- [ ] Constitutional or architectural changes have an approved RFC.
- [ ] The two existing `[NEEDS CLARIFICATION]` markers are resolved or replaced
  with explicit out-of-scope decisions.

### T002 — Reconcile the specification and API contract

**Depends on**: T001  
**Scope**: Update requirements, examples, API behavior, role matrix, status
codes, pagination, authentication routes, trigger/action schemas, and error
contracts to agree with approved decisions.

**Acceptance criteria**
- [ ] Every in-scope operation states method, path, request, response, status
  codes, authentication, and authorization.
- [ ] The actor is derived from the authenticated identity for user-triggered
  requests; non-user triggers have explicitly defined actor values.
- [ ] Job lifecycle, triggers, idempotency, audit, deletion, and error behavior
  have no conflicting statements.
- [ ] Validation, conflict, and upstream error behavior is represented in the
  specification.
- [ ] The API contract and all examples use the same field names and payload
  shapes.

### T003 — Reconcile the data model and lifecycle rules

**Depends on**: T001, T002  
**Scope**: Finalize entities, constraints, indexes, secret-storage boundary,
job snapshots, actor references, audit fields, retention, and delete behavior.

**Acceptance criteria**
- [ ] All entities and fields required by approved user stories and API
  contracts are represented, including user roles and authentication data if
  local accounts are selected.
- [ ] Foreign-key delete behavior and soft/hard deletion rules are explicit.
- [ ] Job records preserve enough information to explain completed executions
  after an automation changes.
- [ ] Secrets cannot be persisted in non-sensitive JSON configuration.
- [ ] Audit actor, status/outcome, immutability, retention, and failure behavior
  are defined.
- [ ] The model specifies UUID and timestamp conventions, uniqueness,
  nullability, and query indexes.

### T004 — Approve Phase 1 scope and measurable targets

**Depends on**: T001, T002, T003  
**Scope**: Confirm Phase 1 included/deferred features and make non-functional
  criteria measurable.

**Acceptance criteria**
- [ ] Every deferred MUST requirement has an approved scope change recorded in
  `specification.md`.
- [ ] Throughput, latency, concurrency, availability measurement window, RPO,
  and RTO have measurable values or are explicitly scheduled for a later phase.
- [ ] Security, privacy, retention, and performance requirements have an
  observable verification method.
- [ ] Product owner and technical lead approve the baseline.

**Gate G0 exit**: T001–T004 accepted. No implementation task that fixes
authentication, database schema, permissions, or job execution may start before
this gate passes.

## Phase 1 — Foundation (Milestone M1)

### T005 — Establish workspace and runtime conventions

**Depends on**: T004  
**Acceptance criteria**
- [ ] Root npm workspaces include the approved client and server packages.
- [ ] Root, client, and server scripts are documented and use the same approved
  Node LTS version.
- [ ] A clean dependency install succeeds without relying on globally
  installed project packages.
- [ ] Lockfile and `.nvmrc` values are committed and consistent.

### T006 — Configure linting and formatting

**Depends on**: T005  
**Acceptance criteria**
- [ ] Root ESLint and Prettier configuration matches the approved language and
  file types.
- [ ] `lint` and `format:check` commands run from the repository root.
- [ ] A deliberately malformed/lint-violating fixture causes the relevant
  check to fail.
- [ ] Existing source files pass the configured checks or have documented
  baseline exceptions.

### T007 — Finalize local PostgreSQL 15 infrastructure

**Depends on**: T004  
**Acceptance criteria**
- [ ] `infra/docker-compose.yml` starts PostgreSQL 15 with a persistent named
  volume and health check.
- [ ] Service credentials are configurable without committing secrets.
- [ ] `docker compose config` succeeds.
- [ ] The database becomes healthy and accepts a connection using the
  documented local configuration.

### T008 — Implement database connection and migration runner

**Depends on**: T003, T005, T007  
**Acceptance criteria**
- [ ] The server reads the database URL from configuration and fails
  explicitly when connection setup fails.
- [ ] Migrations run in deterministic order from a clean PostgreSQL 15 database.
- [ ] Migration failures return a non-zero exit status and preserve useful
  diagnostics without exposing credentials.
- [ ] Running migrations a second time does not duplicate schema changes.
- [ ] The chosen rollback or recovery policy is documented.

### T009 — Implement and verify the initial database schema

**Depends on**: T003, T008  
**Acceptance criteria**
- [ ] A fresh database creates all approved tables, constraints, foreign keys,
  indexes, and extensions.
- [ ] Schema definitions match the approved data model in `specification.md`.
- [ ] Migration tests verify important uniqueness, nullability, and foreign-key
  constraints.
- [ ] Schema changes are made only through version-controlled migrations.

### T010 — Implement safe development seed tooling

**Depends on**: T003, T008, T009  
**Acceptance criteria**
- [ ] A seed command creates only the approved local/test sample records.
- [ ] The seed command is repeatable or fails clearly on duplicate data.
- [ ] The seed command refuses to run in production.
- [ ] No real or reusable credentials are embedded in seed data.
- [ ] Seed behavior and sample account access are documented safely.

### T011 — Bootstrap the Express server

**Depends on**: T005, T008  
**Acceptance criteria**
- [ ] The server starts on the configured port and shuts down cleanly.
- [ ] Middleware order includes parsing, request correlation, logging, routers,
  not-found handling, and the final error handler.
- [ ] Unhandled errors use the approved error envelope and do not leak stack
  traces or secrets to clients.
- [ ] A smoke test can start the app and call its initial health route.

### T012 — Bootstrap the Vite client and local developer workflow

**Depends on**: T005, T007, T011  
**Acceptance criteria**
- [ ] The React 18 + Vite client starts and produces a production build.
- [ ] The documented local workflow starts PostgreSQL, applies migrations,
  starts the API, and starts the client.
- [ ] Client-to-server API base URL is configurable for local development.
- [ ] A clean checkout can follow the workflow without undocumented manual
  setup.

### T013 — Establish OpenAPI as the API contract source

**Depends on**: T002, T004  
**Acceptance criteria**
- [ ] Exactly one OpenAPI v3 document is authoritative and its path is recorded
  in `specification.md`.
- [ ] The document defines common timestamps, error schema, authentication
  scheme, and agreed health endpoints.
- [ ] A validation command checks the OpenAPI document in CI.
- [ ] Duplicate API descriptions are removed or clearly marked as generated.

### T014 — Add continuous integration quality gates

**Depends on**: T006, T008, T009, T011, T012, T013  
**Acceptance criteria**
- [ ] CI runs dependency install, lint, format check, unit tests, PostgreSQL
  integration tests, client build, migration verification, and agreed security
  scans.
- [ ] Service/core-logic coverage is measured against the constitution's 80%
  target.
- [ ] CI fails when a required check fails and provides useful logs.
- [ ] The scan's blocking severity and exception policy are documented.

**Milestone M1 exit**: T005–T014 pass on a clean checkout; documented bootstrap
time meets the approved SC-005 target.

## Phase 2 — Identity and core configuration (Milestone M2)

### T015 — Implement user schema and authentication

**Depends on**: T003, T009, T013  
**Acceptance criteria**
- [ ] User fields and credential handling match the approved identity model.
- [ ] Login/session endpoints implement the approved token/session lifecycle.
- [ ] Missing, invalid, expired, and inactive credentials return the approved
  401 response.
- [ ] Credential storage uses the approved password-hashing method if local
  passwords are selected.
- [ ] Authentication tests cover success and failure paths.

### T016 — Implement authorization and ownership middleware

**Depends on**: T015, T001  
**Acceptance criteria**
- [ ] Middleware enforces the approved role/operation matrix on every protected
  route.
- [ ] Automation ownership and integration-binding policies are enforced
  server-side.
- [ ] Forbidden operations return the approved 403 error envelope.
- [ ] Tests cover each role, owner/non-owner, and integration access boundary.
- [ ] No authorization decision trusts a role or actor supplied in the request
  body.

### T017 — Implement integration persistence and secret handling

**Depends on**: T003, T009, T015, T016  
**Acceptance criteria**
- [ ] Integration CRUD persistence follows the approved schema and deletion
  policy.
- [ ] Credentials are encrypted or referenced through the approved secrets
  manager.
- [ ] Secret data is removed before non-sensitive config is persisted.
- [ ] Responses, logs, and errors never contain credentials.
- [ ] Unit and integration tests verify encryption/storage boundary and
  redaction.

### T018 — Implement integration REST API

**Depends on**: T013, T016, T017  
**Acceptance criteria**
- [ ] Create, list/filter, detail, update/rotation, connection-test, and delete
  operations match the approved OpenAPI contract.
- [ ] Validation, not-found, conflict, and permission failures return specified
  status codes and error shapes.
- [ ] In-use integration deletion follows the approved behavior.
- [ ] API integration tests verify filtering, authorization, secret omission,
  updates, and deletion.

### T019 — Implement automation schema, validation, and persistence

**Depends on**: T003, T009, T016  
**Acceptance criteria**
- [ ] Database representation matches approved trigger, condition, and action
  schemas.
- [ ] Every action's integration reference is validated.
- [ ] Invalid structures and fields receive descriptive validation errors.
- [ ] Ownership, enable/disable, update concurrency, and deletion behavior
  follow the approved specification.
- [ ] Unit and database integration tests cover valid and invalid definitions.

### T020 — Implement automation REST API

**Depends on**: T013, T016, T019  
**Acceptance criteria**
- [ ] Create, list, detail, update, enable/disable, and delete routes match
  OpenAPI.
- [ ] Non-owner and insufficient-role requests are denied as specified.
- [ ] Pagination and sorting follow the shared list convention.
- [ ] API tests cover integration reference validation and concurrent update
  conflicts if selected.

### T021 — Implement sign-in and session UI

**Depends on**: T012, T015, T016  
**Acceptance criteria**
- [ ] Users can sign in and sign out using the approved session mechanism.
- [ ] Client token/session storage and CSRF/CORS behavior follow the approved
  security design.
- [ ] Expired or invalid sessions lead to the specified re-authentication flow.
- [ ] UI displays authentication failures without exposing server internals.

### T022 — Implement integration management UI

**Depends on**: T018, T021  
**Acceptance criteria**
- [ ] Authorized users can list/filter integrations and create, edit, test, and
  delete them according to role policy.
- [ ] Credential entry is write-only after submission; saved credentials are
  never rendered back into the UI.
- [ ] Loading, empty, validation, success, conflict, and error states are
  covered.
- [ ] Component tests verify role-based control visibility and API error
  handling.

### T023 — Implement automation management UI

**Depends on**: T020, T021  
**Acceptance criteria**
- [ ] Authorized users can create, view, edit, enable/disable, and delete
  automations.
- [ ] Forms represent the approved trigger/action schemas and validation rules.
- [ ] Integration selection respects the approved integration-binding policy.
- [ ] Loading, empty, validation, conflict, and error states are covered by
  component tests.

### T024 — Complete M2 contract and feature verification

**Depends on**: T018, T020, T022, T023  
**Acceptance criteria**
- [ ] OpenAPI covers all implemented auth, integration, and automation routes.
- [ ] Integration and automation independent tests in the specification pass.
- [ ] All M2 routes have auth and authorization tests.
- [ ] Client production build and relevant coverage gates pass.
- [ ] The data model and examples remain consistent with implementation.

**Milestone M2 exit**: T015–T024 pass; no integration or automation path can
expose secrets or bypass the approved permissions.

## Phase 3 — Execution and audit (Milestone M3)

### T025 — Implement job persistence and state transitions

**Depends on**: T003, T009, T016, T019  
**Acceptance criteria**
- [ ] Job fields include the approved actor, automation snapshot/version,
  idempotency metadata, result, and timestamps.
- [ ] Only permitted state transitions are accepted and persisted.
- [ ] Job creation captures a stable automation definition for the run.
- [ ] Unit and database tests cover each valid and invalid transition.

### T026 — Implement idempotent job API and listing

**Depends on**: T013, T016, T025  
**Acceptance criteria**
- [ ] Job start, detail, and filtered list endpoints match OpenAPI.
- [ ] Repeating the same idempotency key and same request follows the approved
  response behavior without creating another job.
- [ ] Reusing a key with a different request follows the approved conflict
  behavior.
- [ ] Key scope and expiration are enforced and tested under concurrent
  requests.
- [ ] User-supplied actor identity is ignored or rejected according to the
  approved contract.

### T027 — Implement Atlassian adapters and outbound URL safeguards

**Depends on**: T001, T017, T019  
**Acceptance criteria**
- [ ] Supported Jira/Confluence products and API versions match the approved
  decision.
- [ ] Credentials are applied server-side and never returned or logged.
- [ ] Base URL validation, DNS/IP restrictions, HTTPS policy, redirects,
  response-size limits, and network timeouts match the approved SSRF policy.
- [ ] Tests cover permitted hosts and blocked internal, link-local, and
  disallowed destinations.
- [ ] Adapter contract tests use mocks or fixtures, not live tenants.

### T028 — Implement the in-process action runner

**Depends on**: T019, T025, T027  
**Acceptance criteria**
- [ ] Runner executes only approved action types using the approved input
  mapping and validation rules.
- [ ] Actions execute in the specified order and use a stable job snapshot.
- [ ] Per-action and per-job timeout and concurrency limits are enforced.
- [ ] Failure/continuation behavior matches the approved policy and is covered
  by tests.
- [ ] The runner interface permits a future queue implementation without
  changing action business logic.

### T029 — Implement retry and per-integration rate limiting

**Depends on**: T027, T028  
**Acceptance criteria**
- [ ] Transient failure classification matches the approved retry policy.
- [ ] Exponential backoff and jitter use the approved retry count and bounds.
- [ ] `Retry-After` is honored only up to the approved maximum wait.
- [ ] Per-integration rate and burst limits have deterministic behavior and are
  observable in tests.
- [ ] Non-idempotent remote operations are not blindly retried after ambiguous
  outcomes.

### T030 — Implement append-only audit persistence

**Depends on**: T003, T009, T025  
**Acceptance criteria**
- [ ] Audit records contain the approved actor, action, target, outcome/status,
  timestamp, job association, and redacted details.
- [ ] The approved intent/result write ordering is implemented.
- [ ] Database permissions or equivalent enforcement prevent update/delete of
  audit rows through normal application credentials.
- [ ] Behavior is tested for audit-write failure before and after a remote side
  effect.
- [ ] Retention and privacy rules are enforced or explicitly scheduled.

### T031 — Implement job execution orchestration

**Depends on**: T026, T028, T029, T030  
**Acceptance criteria**
- [ ] Starting a job follows the approved acceptance/execution model.
- [ ] Job state and per-action results are persisted through success and
  failure.
- [ ] Every action receives the required audit entries.
- [ ] Remote failures, timeouts, and persistence failures produce the approved
  terminal state and safe error summary.
- [ ] Tests cover successful runs, permanent failure, transient retry,
  rate-limit response, and partial multi-action failure.

### T032 — Implement job and audit REST API

**Depends on**: T013, T026, T030, T031  
**Acceptance criteria**
- [ ] Job detail/list responses expose approved statuses, timestamps, results,
  and audit references without secret or sensitive payload leakage.
- [ ] Audit list supports the approved pagination, time filter, and ordering.
- [ ] No audit update or delete endpoint exists.
- [ ] API integration tests cover status visibility, authorization, filters,
  error behavior, and redaction.

### T033 — Implement job and audit UI

**Depends on**: T021, T032  
**Acceptance criteria**
- [ ] A user can manually start an enabled automation with validated input.
- [ ] The UI presents job status, safe result/error details, and job history.
- [ ] Users can browse and filter audit entries using the approved list
  contract.
- [ ] Loading, empty, partial, success, and failure states are tested.
- [ ] User-visible data is consistent with API authorization rules.

### T034 — Add mock-based end-to-end workflow

**Depends on**: T022, T023, T031, T032, T033  
**Acceptance criteria**
- [ ] The local/test environment can provide the approved mock Jira/Confluence
  behavior.
- [ ] An automated test configures an integration, creates an automation,
  starts a job, and exercises a mock external effect through the UI/API.
- [ ] The test asserts final job state and the expected audit records.
- [ ] The test uses no live Atlassian credentials or tenant.
- [ ] The SC-001 flow can be timed using the approved measurement procedure.

**Milestone M3 exit**: T025–T034 pass; the end-to-end critical path, audit
guarantees, retry rules, and idempotency behavior are verified.

## Phase 4 — Hardening and release readiness (Milestone M4)

### T035 — Implement health, readiness, metrics, and structured observability

**Depends on**: T011, T031  
**Acceptance criteria**
- [ ] `/health`, `/ready`, and `/metrics` behavior matches the approved
  availability and authentication policy.
- [ ] `/ready` reports database readiness as specified and distinguishes
  dependency failures from liveness.
- [ ] Logs include timestamp, level, correlation id, and user id when known.
- [ ] Correlation ids propagate through external requests where supported.
- [ ] Secret redaction and metric cardinality rules are tested.

### T036 — Complete security and privacy hardening

**Depends on**: T015–T035  
**Acceptance criteria**
- [ ] Security review verifies authentication, authorization, credential
  encryption/key rotation, SSRF defenses, CORS/CSRF, validation, rate limits,
  and error redaction.
- [ ] Secret scanning finds no committed credentials.
- [ ] Dependency/security scans meet the approved blocking policy.
- [ ] Data retention, deletion, redaction, and privacy behavior have automated
  tests or documented operational controls.
- [ ] Blocking security findings are fixed or formally accepted by the
  designated owner.

### T037 — Verify performance and reliability targets

**Depends on**: T004, T031, T035  
**Acceptance criteria**
- [ ] Load test represents the approved throughput, latency, concurrency, and
  payload-size targets.
- [ ] Results are recorded with reproducible environment and commands.
- [ ] Timeout, graceful shutdown, retry, rate-limit, and database pool behavior
  pass their criteria under load/failure tests.
- [ ] Availability measurement follows the approved window and data source.

### T038 — Implement and test backups and recovery

**Depends on**: T003, T009, T036  
**Acceptance criteria**
- [ ] PostgreSQL backups run on the approved schedule and retain 30 days.
- [ ] A restore exercise recovers jobs and audit records from a backup.
- [ ] Measured RPO and RTO meet approved values.
- [ ] Credential encryption-key recovery/rotation procedures are documented
  and tested where feasible.
- [ ] Recovery steps are recorded in `spec/recovery.md`.

### T039 — Finalize production containers and deployment pipeline

**Depends on**: T014, T035, T036, T037, T038  
**Acceptance criteria**
- [ ] Client and server production images build reproducibly and pass image
  scanning.
- [ ] Staging deployment uses the approved registry and deployment target.
- [ ] Secrets are injected by the approved secrets mechanism, not baked into
  images.
- [ ] Migration ordering, rollback procedure, immutable tags, and production
  seed prohibition are documented and tested.
- [ ] Production promotion is manual and uses an approved semantic-version
  release process.

### T040 — Complete release documentation and verification

**Depends on**: T013, T034–T039  
**Acceptance criteria**
- [ ] Quickstart, integrations, recovery, and API documentation are complete
  and consistent with the running system.
- [ ] Every specification verification-checklist item has a passing test or
  recorded evidence.
- [ ] All measurable success criteria are either met or have an explicitly
  approved exception.
- [ ] Full CI passes, including PostgreSQL integration tests, coverage,
  client build, and security/dependency scans.
- [ ] Required code review and QA/release approvals are recorded.

**Milestone M4 exit**: T035–T040 pass and the approved staging-to-production
release process is ready.

## Dependency summary

```text
T001 -> T002 -> T003 -> T004 (Gate G0)
T004 -> T005 -> T006
T004 -> T007
T003 + T005 + T007 -> T008 -> T009 -> T010
T005 + T008 -> T011 -> T012
T002 + T004 -> T013
T006 + T008 + T009 + T011 + T012 + T013 -> T014 (M1)
T003 + T009 + T013 -> T015 -> T016
T003 + T009 + T015 + T016 -> T017 -> T018
T003 + T009 + T016 -> T019 -> T020
T012 + T015 + T016 -> T021
T018 + T021 -> T022
T020 + T021 -> T023
T018 + T020 + T022 + T023 -> T024 (M2)
T003 + T009 + T016 + T019 -> T025 -> T026
T017 + T019 + T001 -> T027 -> T028 -> T029
T003 + T009 + T025 -> T030
T026 + T028 + T029 + T030 -> T031 -> T032 -> T033
T022 + T023 + T031 + T032 + T033 -> T034 (M3)
T011 + T031 -> T035
T015..T035 -> T036
T004 + T031 + T035 -> T037
T003 + T009 + T036 -> T038
T014 + T035..T038 -> T039 -> T040 (M4)
```

The range notation in the final dependency entries means all applicable tasks
in that range must be complete; it does not imply unrelated work can be
skipped.
