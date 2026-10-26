# Implementation Plan: Jira / Confluence Automation Platform

**Source**: [specification.md](./specification.md) (Draft, updated 2026-10-26)  
**Governing principles**: [constitution.md](./constitution.md) v1.1.0  
**Review inputs**: [clarify.md](./clarify.md)  
**Status**: Proposed; implementation is gated on the decisions listed below.

## 1. Planning assumptions and gates

The specification and review contain unresolved requirements. The defaults in
`clarify.md` are recommendations, not approved decisions. This plan does not
silently adopt them.

### Gate A — Resolve before implementation of affected areas

Before creating database migrations or implementing authentication, automation
execution, or authorization, the product owner must resolve the blocker
questions in `clarify.md`:

- **Q-02 / C-01**: local accounts or linked Jira accounts; define credential and
  user provisioning model.
- **Q-04 / C-02**: synchronous request execution or immediate job acceptance
  with an in-process runner; reconcile job statuses and lifecycle.
- **Q-06 and Q-07 / G-01**: role permissions and which integrations users may
  bind to automations.
- **Q-08 / G-02**: schemas and Phase 1 support for triggers, conditions,
  actions, and mapping run input into actions.

Other decisions that materially affect data or API contracts must also be
resolved before the corresponding milestone: Q-01, Q-03, Q-05, Q-09, Q-11,
Q-12, Q-13, Q-14, Q-15, and Q-16. Record accepted answers in a dated
`Clarifications` section in `specification.md`; update the constitution or add
an RFC where required. Do not treat this plan as approval of any proposed
default.

### Provisional sequencing only

The milestones below preserve the specification's M1–M4 sequence while
expanding it to cover the required authentication, UI, operational, and
delivery work. The specification's week ranges (0–8) are indicative only;
re-estimate after Gate A and technical spikes. Phase 1 scope remains the
specification's intended scope until owners explicitly defer or change a
requirement.

## 2. Phase overview

| Phase | Milestone | Goal | Dependencies |
|---|---|---|---|
| 0. Clarify and baseline | G0 | Close architecture and product blockers; make one authoritative API and data contract | None |
| 1. Foundation | M1 | Establish a reproducible monorepo, database, migration, and CI workflow | G0 decisions for tooling and schema |
| 2. Identity and core configuration | M2 | Implement auth, role checks, integrations and automation configuration | M1; decisions Q-01–Q-03, Q-06–Q-08, Q-13 |
| 3. Execution and audit | M3 | Run jobs against Jira/Confluence, record reliable audit history, provide job and audit UX | M2; decisions Q-04–Q-05, Q-09–Q-12, Q-14 |
| 4. Hardening and release | M4 | Validate security, operations, performance, backup/recovery, CI/CD and release readiness | M3; deployment and NFR decisions |

## 3. Phase 0 — Clarify and baseline (Gate G0)

### Work

1. Answer the four blocker groups in Gate A and all related `NEEDS
   CLARIFICATION` items.
2. Decide supported Atlassian products and authentication, credential
   boundaries, outbound URL policy, action and trigger schemas, job failure and
   retry behavior, idempotency scope, audit write semantics, data retention,
   user/session lifecycle, and permission matrix.
3. Confirm which features are Phase 1 versus deferred. Any deferral must update
   the MUST requirements and success criteria, not only the milestone table.
4. Decide server/client language, database access and migration tooling, test
   runner, HTTP client, logger, and OpenAPI source of truth.
5. Reconcile the API contract, entity model, milestones, and examples. In
   particular, make `triggered_by` server-derived, define `jobs` snapshot and
   delete behavior, and document how audit status and actor are represented.
6. Record decisions in `specification.md`; write RFCs for constitutional or
   architectural changes. Update `clarify.md` to mark resolved items and retain
   only genuinely open questions.

### Exit criteria

- No unresolved blocker remains for the approved Phase 1 scope.
- Every in-scope API operation has a request, response, authorization rule, and
  error behavior.
- Trigger/action schemas and the database model support the approved behavior.
- OpenAPI location and source of truth are decided.
- The product owner and technical lead approve the baseline.

**Gate**: Do not start implementation that would lock in an unresolved data
model, auth, execution, or permissions decision.

## 4. Phase 1 — Foundation (Milestone M1)

**Goal**: A new contributor can install dependencies, start PostgreSQL 15,
apply migrations, run the client and server, and receive CI feedback.

### Work packages

1. **Repository and runtime**
   - Confirm npm workspace boundaries, `.nvmrc` and package scripts.
   - Pin compatible dependencies after the language/tooling decisions.
   - Configure root ESLint and Prettier, ignore rules, and any approved
     pre-commit checks.
2. **Database and local infrastructure**
   - Finalize `infra/docker-compose.yml` and health checks for PostgreSQL 15.
   - Implement repeatable migration and seed commands.
   - Add a migration runner and database connection configuration.
   - Keep the seed safe for development and tests; prohibit production seed
     execution.
3. **Service bootstrap**
   - Replace the placeholder server entry point and Dockerfile.
   - Mount middleware in a defined order: request parsing, correlation id,
     logging, routers, not-found handling, then error handling.
   - Establish client and server development/build/test commands.
4. **CI baseline**
   - Add CI for dependency installation, lint, client build, unit tests, and
     PostgreSQL-backed integration tests.
   - Add coverage enforcement for the constitution's 80% service/core-logic
     target and a dependency/security scan with an agreed failure policy.
5. **Contract skeleton**
   - Make the chosen OpenAPI document the single source of truth.
   - Define common error envelope, timestamp convention, and health endpoints.

### Deliverables

- Working root workspace scripts and pinned runtime.
- PostgreSQL 15 compose service that becomes healthy before dependent tasks.
- Initial reviewed migration and a non-production seed process.
- Running Express and Vite development servers.
- Non-empty CI, lint, format, server/client test, and OpenAPI scaffolding.

### Exit criteria

- A clean checkout can bootstrap locally within the SC-005 target of 15
  minutes, measured using a documented procedure.
- A fresh PostgreSQL 15 database migrates successfully; migration failure is
  visible and non-zero.
- CI passes on a clean checkout and fails on lint, test, build, or migration
  errors.
- No secrets are required in source control; `.env` remains ignored.

**Spec traceability**: FR-024–FR-030; SC-005, SC-008; Constitution principles
IV, V, VII.

## 5. Phase 2 — Identity and core configuration (Milestone M2)

**Goal**: Authorized users can sign in, manage integrations, and create and
maintain validated automation definitions.

### Work packages

1. **Schema and data access**
   - Implement users, integrations, and automation-config persistence according
     to the decisions from G0.
   - Include required ownership, role, credential-reference/encryption,
     timestamps, versioning, and delete semantics.
   - Add migration rollback/forward verification and repository-level tests.
2. **Authentication and authorization**
   - Implement the approved login/session mechanism and middleware.
   - Enforce the approved role/operation matrix and ownership checks.
   - Derive the actor from the verified identity, never from a client-supplied
     actor field.
   - Add tests for unauthenticated, forbidden, owner, admin, and inactive-user
     cases.
3. **Integration management**
   - Implement create, list/filter, detail, update/rotation, and delete
     behavior.
   - Encrypt credentials or store an approved secrets-manager reference.
   - Ensure credentials never appear in response objects, logs, errors, or
     persisted non-secret config.
   - Implement the approved connection test and in-use deletion behavior.
4. **Automation configuration**
   - Implement create, list, detail, update, enable/disable, and delete.
   - Validate the approved trigger/action JSON schemas, referenced integrations,
     role access, and ownership.
   - Add optimistic concurrency handling if selected at G0.
5. **Initial React UI**
   - Implement sign-in/session handling and integration and automation list,
     detail, create, and edit flows.
   - Include loading, empty, validation, and error states.
   - Use the shared API client; never send stored secrets back to the browser
     unless the user is actively entering replacement credentials.
6. **Contract and tests**
   - Complete the OpenAPI definitions for auth, integrations, and automations.
   - Add service unit tests, API integration tests, and client component tests.

### Exit criteria

- Integration and automation independent tests in the specification pass.
- Every endpoint enforces the approved permission matrix.
- Secrets are demonstrably absent from API responses and logs.
- The UI supports the approved management flows and all documented states.
- Migrations work from an empty database and from the prior release schema.

**Spec traceability**: US1, US2, US5; FR-001–FR-010, FR-021–FR-026,
FR-031; SC-003, SC-005, SC-008.

## 6. Phase 3 — Execution and audit (Milestone M3)

**Goal**: A user can submit a valid automation run, observe its job lifecycle,
and inspect an accurate audit trail.

### Work packages

1. **Job lifecycle**
   - Implement the approved request-acceptance model and state transitions.
   - Persist the automation definition/version snapshot selected at start.
   - Add job creation, detail, and filtered-list operations.
   - Implement idempotency scope, request-body matching, conflict handling, and
     expiration/retention.
2. **Action runner**
   - Implement a runner boundary and Phase 1 execution strategy.
   - Implement only the approved action types and integration adapters.
   - Apply input mapping and schema validation before external calls.
   - Enforce per-action/job timeouts, concurrency limits, and the approved
     stop/continue behavior on action failure.
3. **Atlassian clients and resilience**
   - Implement the approved Atlassian Cloud or other supported API clients.
   - Enforce HTTPS/host and redirect policy for configured base URLs.
   - Add least-privilege credentials, rate limiting, retry classification,
     exponential backoff/jitter, `Retry-After` caps, and safe handling of
     ambiguous remote outcomes.
   - Test against mocks/fixtures only; never use live credentials in CI.
4. **Audit trail**
   - Implement the agreed write-before/write-after semantics and ensure an
     action is not performed if its required audit intent cannot be persisted.
   - Record action, actor, target, outcome/status, timestamp, and redacted
     details; enforce append-only behavior at the database boundary.
   - Define and test behavior when an action succeeds remotely but result
     persistence fails.
5. **Job and audit UI**
   - Add manual-run form, job detail/status display, filtered job history, and
     audit browsing.
   - Display partial action results and safe error summaries without exposing
     credentials or sensitive payloads.
6. **End-to-end verification**
   - Complete the critical path against the local mock: configure integration,
     create automation, run job, assert remote mock effect, verify status and
     audit entries.

### Exit criteria

- Successful and failed jobs transition to defined terminal states and return
  stable result shapes.
- Repeated idempotent requests follow the approved policy.
- Every attempted automation action has the defined audit records.
- The mock-based end-to-end flow passes from UI through API, database, runner,
  and audit.
- Retry, rate-limit, timeout, failure, duplicate, and partial-failure tests pass.

**Spec traceability**: US3, US4; FR-011–FR-020, FR-031; SC-001, SC-002,
SC-004, SC-008; Constitution principles IV and VI.

## 7. Phase 4 — Hardening and release readiness (Milestone M4)

**Goal**: Demonstrate that the service is safe to operate, observable, and
deployable against the approved Phase 1 targets.

### Work packages

1. **Operational endpoints and observability**
   - Implement `/health`, `/ready`, and optional `/metrics` with the approved
     authentication/exposure policy.
   - Add structured JSON logs, request correlation propagation, safe redaction,
     and metrics with bounded label cardinality.
   - Add alerts/runbook guidance for the approved service-level objectives.
2. **Security and privacy**
   - Review auth/session, authorization, credential encryption/key rotation,
     SSRF protections, validation, CORS, rate limiting, and secret redaction.
   - Run dependency and secret scans; resolve release-blocking findings.
   - Apply retention, deletion, backup, and data-minimization decisions.
3. **Performance and reliability**
   - Add load tests against agreed throughput, latency, and concurrency targets.
   - Verify API timeouts, rate limits, graceful shutdown, and database pool
     behavior.
   - Measure availability against a stated window and monitoring source.
4. **Backup and recovery**
   - Implement PostgreSQL backup schedule and 30-day retention.
   - Perform a restore exercise and measure RPO/RTO against approved targets.
   - Document recovery and credential-key recovery procedures.
5. **Containers and delivery**
   - Finalize production client/server images and local compose setup.
   - Select registry and deployment target; configure staging deployment,
     image scanning, immutable tags, and production promotion.
   - Define migration ordering, rollback policy, and production seed prohibition.
6. **Documentation and release**
   - Complete README/quickstart, integrations, recovery, and OpenAPI documents.
   - Verify all examples against the implementation.
   - Run the full verification checklist and obtain required review/QA approval.

### Exit criteria

- All SC-001–SC-008 have a repeatable measurement or test, and the approved
  thresholds pass.
- Full CI passes, including service coverage at or above 80%, integration tests
  on PostgreSQL 15, client production build, and security/dependency checks.
- Backup restore and deployment rollback have been exercised.
- OpenAPI matches the running endpoints; no secrets are committed or emitted.
- Staging deployment succeeds and production promotion has an approved manual
  release procedure.

**Spec traceability**: US6; FR-024–FR-030; SC-001, SC-003, SC-005–SC-008;
Constitution principles III–VI.

## 8. Cross-cutting work and quality gates

Apply these across all phases:

- Update specification, OpenAPI, migrations, tests, and user-facing
  documentation in the same change when behavior or contract changes.
- Keep routes, controllers, services, and models separated as required by the
  constitution.
- For each feature, write or update tests before or with implementation.
- Do not use live Jira/Confluence credentials or tenants in CI.
- Review secret redaction and authorization in both success and error paths.
- Keep schema evolution additive where possible; every migration must be
  reversible or have a documented recovery strategy.
- Use Conventional Commits, feature/fix/chore branches, protected `main`, and
  pull requests with CI and at least one approval.

## 9. Dependency and risk register

| Risk / dependency | Impact | Mitigation / gate |
|---|---|---|
| Unresolved identity, roles, and integration-sharing policy | Security flaw or rework to schema and UI | Resolve Q-02, Q-06, Q-07 before M2 |
| Unresolved job execution and trigger scope | Lifecycle/API redesign; impossible status behavior | Resolve Q-04 and Q-09 before M3 |
| Unspecified action schemas and input mapping | Cannot validate or safely execute automations | Resolve Q-08 before M2 automation persistence |
| Credential handling and user-supplied base URLs | Credential exposure or SSRF | Resolve Q-03 and G-06 controls before integration calls |
| Idempotency cannot guarantee remote exactly-once behavior | Duplicate external work after timeouts | Resolve Q-11; document delivery semantics and test ambiguous outcomes |
| Audit requirement conflicts with database outage | Missing audit record for an external side effect | Resolve Q-12 and define failure policy before execution |
| Empty/placeholder scaffold files and Dockerfile | False confidence that CI, OpenAPI, and deployment already exist | Treat placeholders as unfinished; M1/M4 exit checks require working files |
| Moderate-volume target lacks latency/concurrency definition | Cannot validate performance claim | Agree measurable thresholds before M4 load testing |

## 10. Recommended task-generation order

After Gate G0 approval, generate implementation tasks in this dependency order:

1. Workspace, runtime, lint/test scripts, server bootstrap, Docker Compose,
   database connection, migration runner, initial schema, CI.
2. Authentication/user schema and authorization middleware.
3. Integration schema/service/API/UI and secret-handling tests.
4. Automation schema/service/API/UI and definition-validation tests.
5. Job schema/API/state machine/idempotency.
6. Atlassian adapters, runner, retry/rate limit, and audit persistence.
7. Job/audit UI and mock-based end-to-end flow.
8. Health/readiness/metrics, security/performance, backups/recovery, images,
   staging deployment, and release documentation.

Do not parallelize tasks that modify the same API or schema until their
contracts have been approved. UI work may proceed against the approved OpenAPI
contract and mocked responses once the corresponding API shape is stable.
