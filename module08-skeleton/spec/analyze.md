# Task Analysis: Jira / Confluence Automation Platform

**Inputs**: [tasks.md](./tasks.md), [plan.md](./plan.md), [specification.md](./specification.md), [clarify.md](./clarify.md), and [constitution.md](./constitution.md)  
**Date**: 2026-10-26  
**Status**: Assessment only; proposed defaults are not approvals.

## Executive summary

The 40 tasks cover the major product and delivery areas, and the G0 gate is a
good safeguard against locking in unresolved identity, authorization, data, and
execution choices. However, the plan and task graph do not yet enforce all
milestone gates, and several spec requirements have no explicit implementation
task unless they are formally deferred. In particular, schedule/webhook
triggers, user provisioning, a runnable mock Atlassian service, and cancellation
are not assigned complete implementation work.

The specification remains Draft and still contains two `[NEEDS CLARIFICATION]`
markers. All 16 questions in `clarify.md` remain proposals rather than
owner-approved decisions. Do not treat this analysis, the plan, or task
acceptance criteria as approval to implement those choices.

Complexity estimates reflect scope, integration count, and verification
burden—not elapsed time. Dependencies below reproduce the task list; identified
missing gate dependencies and artifacts are called out in the findings.

## Per-task assessment

| ID | Task | Complexity | Key risks | Dependencies |
|---|---|---|---|---|
| T001 | Resolve product and architecture questions | High | Owner decisions may stall; broad decision scope risks partial or contradictory answers; RFC approvals may take longer than implementation work. | None |
| T002 | Reconcile specification and API contract | High | Many cross-cutting payload, error, permission, and lifecycle changes; examples can drift from the final contract. | T001 |
| T003 | Reconcile data model and lifecycle rules | High | Changes affect migrations, historical records, secrets, retention, and delete behavior; an incomplete model causes expensive schema rework. | T001, T002 |
| T004 | Approve Phase 1 scope and measurable targets | Medium | NFRs may remain subjective or conflict with Phase 1 scope; product and technical approval are required. | T001, T002, T003 |
| T005 | Establish workspace and runtime conventions | Medium | Workspace boundaries, language, runtime, and package choices constrain all later work; clean-install compatibility is a risk. | T004 |
| T006 | Configure linting and formatting | Low | Overly broad rules or mismatched JS/TS configuration can create noise and slow adoption. | T005 |
| T007 | Finalize local PostgreSQL 15 infrastructure | Medium | Secrets, persistent-volume lifecycle, health-check behavior, and developer-specific Docker setup can make local startup unreliable. | T004 |
| T008 | Implement database connection and migration runner | High | Migration ordering, partial failure, locking, retries, and recovery policy can cause schema drift or data loss. | T003, T005, T007 |
| T009 | Implement and verify initial database schema | High | Depends on settled identity, ownership, snapshots, audit, and retention; late decisions require migration redesign. | T003, T008 |
| T010 | Implement safe development seed tooling | Low | Seeded credentials or an unsafe environment check could expose a reusable admin account in production. | T003, T008, T009 |
| T011 | Bootstrap the Express server | Medium | Middleware ordering and error handling can leak secrets or produce inconsistent errors; health semantics need alignment. | T005, T008 |
| T012 | Bootstrap the Vite client and local workflow | Medium | Local setup depends on stable API configuration and usable clean-checkout documentation. | T005, T007, T011 |
| T013 | Establish OpenAPI as the API contract source | Medium | Existing locations conflict; contract-first versus generated workflow and validation tooling are undecided. | T002, T004 |
| T014 | Add continuous integration quality gates | High | CI is coupled to test, database, coverage, and scan decisions; enforcing the full 80% target before meaningful service logic exists may be misleading. | T006, T008, T009, T011, T012, T013 |
| T015 | Implement user schema and authentication | High | Account model, password/session lifecycle, key management, and provisioning remain unresolved; auth errors affect every protected route. | T003, T009, T013 |
| T016 | Implement authorization and ownership middleware | High | Incorrect role or integration-binding rules can expose privileged Atlassian credentials; tests must cover all role/resource combinations. | T015, T001 |
| T017 | Implement integration persistence and secret handling | High | Encryption, secret extraction, redaction, rotation, and deletion behavior are security-critical and depend on approved storage/key policy. | T003, T009, T015, T016 |
| T018 | Implement integration REST API | Medium | API behavior depends on connection-test, pagination, conflict, and in-use deletion contracts; secrets must be omitted on every path. | T013, T016, T017 |
| T019 | Implement automation schema, validation, and persistence | High | Trigger/action schemas and integration access rules are unresolved; weak validation may permit privilege escalation or unsafe execution. | T003, T009, T016 |
| T020 | Implement automation REST API | Medium | Route behavior and concurrent updates depend on a stable OpenAPI and authorization contract. | T013, T016, T019 |
| T021 | Implement sign-in and session UI | Medium | Browser storage, CSRF/CORS, token expiry, and re-authentication behavior are security-sensitive and must match the selected session design. | T012, T015, T016 |
| T022 | Implement integration management UI | Medium | Credential entry must remain write-only; role-based controls and API error states need end-to-end consistency. | T018, T021 |
| T023 | Implement automation management UI | High | Trigger/action editors can become complex; supported schemas, mapping, conditions, and integration visibility must be fixed first. | T020, T021 |
| T024 | Complete M2 contract and feature verification | Medium | Its listed dependencies do not include all M2 tasks directly, and the specification’s independent tests may be too vague to serve as release evidence. | T018, T020, T022, T023 |
| T025 | Implement job persistence and state transitions | High | Snapshot semantics, actor, idempotency, cancellation, and terminal states depend on unresolved execution decisions. | T003, T009, T016, T019 |
| T026 | Implement idempotent job API and listing | High | Concurrent duplicate requests, key scope/expiry, body mismatch, and synchronous-versus-accepted execution must be specified precisely. | T013, T016, T025 |
| T027 | Implement Atlassian adapters and outbound URL safeguards | High | SSRF defenses, DNS rebinding, redirect behavior, credential formats, API versions, and safe error handling are security-critical. | T001, T017, T019 |
| T028 | Implement the in-process action runner | High | Action semantics, input mapping, timeouts, concurrency, and partial failure can cause duplicate or inconsistent external effects. | T019, T025, T027 |
| T029 | Implement retry and per-integration rate limiting | High | Retries after ambiguous non-idempotent calls may duplicate external changes; `Retry-After` can exceed acceptable request/job duration. | T027, T028 |
| T030 | Implement append-only audit persistence | High | Write ordering, DB outage behavior, redaction, retention, and append-only database permissions must be agreed and tested. | T003, T009, T025 |
| T031 | Implement job execution orchestration | High | Combines state transitions, external effects, retry, audit, and persistence; failure windows between remote success and DB writes are difficult to recover. | T026, T028, T029, T030 |
| T032 | Implement job and audit REST API | Medium | Authorization, pagination, status visibility, and sensitive-result redaction must agree with the final contract. | T013, T026, T030, T031 |
| T033 | Implement job and audit UI | Medium | Polling/status refresh and partial-result handling depend on the selected job acceptance model and stable response shapes. | T021, T032 |
| T034 | Add mock-based end-to-end workflow | High | A test-only mock may not satisfy the UI demonstration criterion; test data, environment startup, and timing methodology are not assigned explicitly. | T022, T023, T031, T032, T033 |
| T035 | Implement health, readiness, metrics, and observability | Medium | Exposure/auth policy, readiness semantics, correlation propagation, and metric cardinality must be explicit to avoid leaks and operational noise. | T011, T031 |
| T036 | Complete security and privacy hardening | High | Broad scope risks becoming a checklist without evidence or independent review; unresolved retention and key-management decisions block sign-off. | T015–T035 |
| T037 | Verify performance and reliability targets | High | Cannot produce meaningful pass/fail results without approved throughput, latency, concurrency, payload, and measurement-window targets. | T004, T031, T035 |
| T038 | Implement and test backups and recovery | High | Managed-database capabilities, key recovery, retention, and restore testing must match deployment reality and approved RPO/RTO. | T003, T009, T036 |
| T039 | Finalize production containers and deployment pipeline | High | Registry, deployment target, secret injection, migration ordering, rollback, and release controls are not yet selected; scope is large for one task. | T014, T035, T036, T037, T038 |
| T040 | Complete release documentation and verification | Medium | Broad completion criteria can miss an unverified requirement; acceptance depends on traceability and prior milestone gates. | T013, T034–T039 |

## Cross-document gaps, contradictions, and missing artifacts

### High priority: resolve before implementation

1. **The decision gate is not a complete, enforceable baseline.**
   - `specification.md` is still Draft and contains unresolved markers for
     integration deletion and account identity. The 16 questions in
     `clarify.md` have recommendations, not decisions.
   - `plan.md` names Q-02, Q-04, Q-06, Q-07, and Q-08 as primary blockers, but
     its explicit list of other questions omits **Q-10** (supported Atlassian
     products). The plan's Phase 0 work mentions deciding products, but Gate A
     should list it consistently.
   - Deployment target, registry, and production secret mechanism are noted as
     open in the risk register and deferred to T039, but are not an explicit
     owner decision in the Q-01–Q-16 table or a clearly testable T001 decision.
   - **Recommendation**: Make T001's decision register exhaustive, include
     Q-10 and the deployment decisions, assign decision owners, and record
     approved answers or explicit deferrals before passing G0.

2. **The task graph does not enforce the plan's milestone sequencing.**
   - The plan says M2 depends on M1 and M3 on M2. However, T015 does not depend
     on T014/M1 exit, and T025/T027 (and their downstream M3 work) do not depend
     on T024/M2 exit. Work can therefore be marked ready across phase
     boundaries before the prior milestone's exit criteria pass.
   - T040 does not depend on T024, so the final release task can complete
     without the explicit M2 contract-verification task being accepted.
   - **Recommendation**: Add explicit milestone-gate dependencies (or named
     gate tasks) so the dependency graph and phase overview express the same
     sequencing. Make T040 depend on all required milestone verification
     tasks, including T024.

3. **Schedule/webhook triggers are required in the spec but have no complete
   runtime implementation task.**
   - FR-007 includes `schedule` and `webhook`; the task list covers schemas,
     forms, manual runs, and a runner, but no scheduler, inbound webhook
     endpoint, webhook authentication/replay protection, or restart/missed-run
     behavior.
   - Q-09 proposes deferring these triggers, but that proposal is not approved.
   - **Recommendation**: If retained, add scoped implementation and test tasks
     for each trigger type. If deferred, amend FR-007 and related acceptance
     criteria, success criteria, and UI scope in the specification.

4. **User provisioning and role lifecycle are not assigned.**
   - T015 covers user schema and authentication but its acceptance criteria
     focus on sign-in/session endpoints. No task implements user creation,
     role changes, deactivation, or an explicit external provisioning model.
   - **Recommendation**: Add a task for the approved provisioning/administration
     flow, or explicitly document that Phase 1 users and roles are managed
     outside the application.

5. **Mock service and demo environment are not concretely deliverable.**
   - SC-001 requires a successful mock-Jira run using only the UI. T034 says the
     local/test environment can provide mock behavior, but no task creates or
     configures the mock service. Q-14 recommends a mock under `/infra`, but
     remains unapproved.
   - **Recommendation**: Add an explicit mock service/fixture task and make
     T034 depend on it, or redefine SC-001 as a test-only/API criterion.

6. **Job cancellation is represented without an operation.**
   - The specification's job statuses include `cancelled`, while the API
     summary and task list do not define a cancel route, authorization rule, or
     cancellation behavior for in-progress actions.
   - **Recommendation**: Either define and task cancellation end-to-end, or
     remove `cancelled` from the Phase 1 lifecycle and related acceptance
     criteria.

### Medium priority: align contracts, artifacts, and verification

7. **Referenced specification artifacts exist but are empty.**
   - `spec/README.md`, `spec/openapi.yaml`, `spec/recovery.md`, and
     `spec/integrations.md` are each 0 bytes. `spec/rfcs/` contains only
     `.gitkeep`.
   - T013 and T040 eventually require OpenAPI and documentation, while T038
     requires recovery content. T001 requires RFCs when needed, but no task
     explicitly owns creating and approving those RFCs.
   - **Recommendation**: Assign explicit deliverables and owners: initial
     authoritative OpenAPI in T013, user/integration docs in M2/M4, recovery
     runbook in T038, and an RFC template plus decision RFCs where approved.

8. **API contract work is not explicit at every milestone.**
   - T013 establishes the contract and T024 checks auth/integration/automation
     routes. T032 does not explicitly require OpenAPI coverage for job/audit
     routes, despite the constitution and plan requiring the document to match
     every endpoint.
   - **Recommendation**: Add OpenAPI synchronization and validation criteria
     to T026/T032 and require the final document to cover operational and
     authentication endpoints as well as product routes.

9. **Requirement-to-task traceability is incomplete.**
   - `plan.md` maps broad FR/SC ranges to milestones, but `tasks.md` has no
     per-task traceability to user stories, functional requirements, success
     criteria, or verification checklist items.
   - T040 says every checklist item must have evidence, but does not provide a
     trace matrix or evidence location.
   - **Recommendation**: Add a compact task-to-requirement/evidence matrix so
     omitted requirements and unverified acceptance criteria can be detected.

10. **Some acceptance criteria are blocked by unresolved or unspecified
    decisions.**
    - Many criteria correctly refer to the “approved” contract, but the plan
      does not yet name an owner or artifact for some decisions (deployment,
      provisioning, mock setup, and retained trigger types).
    - T014 measures the 80% service/core-logic coverage target in M1, before
      substantial service code is expected. The measured source set and whether
      the threshold ramps with implementation are unspecified.
    - **Recommendation**: Define the owner and evidence for each decision;
      specify the coverage denominator and enforce the final 80% threshold once
      the applicable service code exists (without weakening the constitution's
      final target).

11. **Several large tasks combine independently verifiable work.**
    - T001, T003, T014, T036, T039, and T040 span multiple decisions or
      deliverables. Their broad acceptance criteria make progress and blockers
      hard to report.
    - **Recommendation**: Keep stable task IDs where possible, but split work
      into independently reviewable subtasks (especially security/privacy
      review versus remediation, and image build versus deployment pipeline)
      if parallel ownership or estimates are needed.

12. **Versioning and compatibility behavior needs explicit verification.**
    - T019/T023 depend on approved trigger/action schemas, but the spec does not
      yet define schema versioning or how existing automation definitions are
      handled when a schema changes.
    - **Recommendation**: Record schema versions in stored automation/job
      snapshots and define migration or compatibility behavior before T019 and
      T025 implementation.

## Recommended sequencing changes

1. Close T001–T004 only after all decision questions, including Q-10 and
   deployment/provisioning choices, are recorded and approved.
2. Make M1 exit (T014) a prerequisite for M2 implementation, and make M2 exit
   (T024) a prerequisite for M3 implementation.
3. Add or explicitly defer tasks for user provisioning, non-manual triggers,
   mock service delivery, and cancellation.
4. Publish the authoritative OpenAPI document early and keep it updated in
   each API task; record evidence against requirements as tasks complete.
5. Re-estimate high-complexity tasks after G0, when schemas, deployment,
   security, and operational targets are known.

## Overall assessment

The plan is directionally complete and its clarification-first approach is
sound, but the current task list is not yet a fully closed, phase-gated delivery
backlog. The most important changes are to make the decision register
exhaustive, encode milestone prerequisites in the dependency graph, and either
add or explicitly defer the unassigned product capabilities above. The empty
referenced artifacts should be treated as missing deliverables, not as existing
documentation.
