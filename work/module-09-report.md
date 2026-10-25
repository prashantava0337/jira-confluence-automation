# Module 09 Completion Report

## Tracked Files
```
.env.example
.gitignore
PROJECT_IDEAS.md
README.md
SPRINT_DASHBOARD_REQUIREMENTS.md
backlog.md
data/notes.md
data/sample_sprint.csv
data/sprint_config.json
project_spec.md
scripts/build_dashboard.py
scripts/generate_report.py
```

## Backlog Commit History
```
6067433 Add implementation backlog for Sprint Delivery Report
```

## backlog.md Contents
```markdown
# Implementation Backlog: Sprint Delivery Report

Source: [project_spec.md](./project_spec.md). Python 3, standard library only.

**MVP (first usable milestone):** Phases 1–3 deliver both `client` and `internal` modes with metrics and the forecast. Phase 4 hardens and verifies; Phase 5 documents.

**Priority order (earliest first):** forecast banner → planned vs completed / carry-over / mid-sprint additions → daily history snapshots → internal per-team breakdown → story points. Privacy and freshness are acceptance criteria, so they are scheduled where they are needed, not deferred.

---

## Phase 1: Setup

### 1.1 Decisions (spec §12 open questions; implement as configurable defaults)
- [ ] D1. Team count and missing Team values: default to an `Unassigned` bucket in `internal` mode and add a data warning.
- [ ] D2. Velocity: config key `velocity_method` (`average_last_6` default; `worst_of_last_3` option).
- [ ] D3. At-risk definition: config key `at_risk_warning_sprints` (default `0` = late date only; `1` adds an "At risk – tight" band).
- [ ] D4. Real CSV column names and date format: get an export header row from the user and update the config mapping defaults.
- [ ] D5. Client report sprint labels: config key `client_sprint_labels` (`names` default | `numbers`).
- [ ] D6. Confirm the two-mode intent (§3) and the acceptance criteria (§10) with the user.
- [ ] D7. Record the sprint-list-from-API item as future work only (§13); no implementation.

### 1.2 Project skeleton
- [ ] Review the existing [scripts/build_dashboard.py](./scripts/build_dashboard.py) and [scripts/generate_report.py](./scripts/generate_report.py); list reusable CSV parsing and date handling.
- [ ] Create the `sprint_report/` package with `__init__.py` and `__main__.py`.
- [ ] Create stub modules: `csv_loader`, `metrics`, `forecast`, `history`, `render_html`, `cli`.
- [ ] Create the directories `config/`, `data/history/`, `reports/`, `tests/fixtures/`.
- [ ] Update [.gitignore](./.gitignore): `data/export.csv`, `data/history/`, `reports/`, and any real exports. Keep the anonymised fixtures tracked.
- [ ] Update [.env.example](./.env.example) or remove it if no credentials are used.

### 1.3 Config
- [ ] Define the schema for `config/project_config.json`: project, sprints (name, start, end), `contract_deadline`, `total_scope`, `column_map`, `completed_statuses`, `date_formats`, plus the D2/D3/D5 keys.
- [ ] Add `config/project_config.example.json` with the 6 past sprints plus the current one, deadline `2027-02-27`, and the default completed statuses (Done, Resolved, Closed).
- [ ] Implement the config loader with validation: missing keys, bad dates, overlapping or unordered sprints, non-positive scope. Errors name the offending key.
- [ ] Add the shared date-parsing helper (multiple formats), moved from `build_dashboard.py`.

### 1.4 Test scaffolding
- [ ] Set up `unittest` discovery (`python3 -m unittest`).
- [ ] Create the anonymised fixture `tests/fixtures/export_small.csv`: repeated `Sprint` columns, carry-over, mid-sprint additions, an empty sprint, multiple teams, a missing Team, a missing story-point value, and a non-Story issue type.

---

## Phase 2: Core Features

### 2.1 CSV loader (`csv_loader`)
- [ ] Parse the CSV with header-name mapping, including alternative column names (`Custom field (Team)` / `Team`).
- [ ] Read **every** repeated `Sprint` column per row and preserve order.
- [ ] Filter to issue type `Story`.
- [ ] Normalise status against `completed_statuses`, case-insensitively.
- [ ] Parse Created and Resolved dates; parse story points (blank → `None`).
- [ ] Return a `Story` record (key, team, status, sprints, points, created, resolved) plus a list of data warnings.
- [ ] Fail with a clear error if a required column is missing or the file is unreadable (stderr, non-zero exit).

### 2.2 Metrics (`metrics`), in priority order
- [ ] Map sprint names from the CSV to configured sprints; warn about unrecognised sprints.
- [ ] **Completed per sprint:** count each Done story once, in the last sprint listed for it. Total, and by team.
- [ ] **Planned:** stories in the sprint created on or before the start date.
- [ ] **Added mid-sprint:** stories in the sprint created after the start date.
- [ ] **Completed vs planned:** completed ÷ (planned + added), with planned and added shown separately. Guard against divide-by-zero for empty sprints.
- [ ] **Carry-over:** a story in sprint N that also appears in a later sprint counts as carried over from N.
- [ ] **Story points completed** per sprint; warn about stories with no points.
- [ ] Mark the current sprint as "in progress" based on today's date versus the config dates.
- [ ] Allow `today` to be injected so metrics are deterministic and testable.

### 2.3 Forecast (`forecast`)
- [ ] Velocity: average stories completed over the last 6 completed sprints (the current sprint is excluded). Support the D2 option.
- [ ] Remaining = `total_scope` − all completed stories to date.
- [ ] Sprints needed = ceil(remaining ÷ velocity). Handle velocity 0 or fewer than 6 sprints of history: At risk with a warning.
- [ ] Projected finish = end of current sprint + sprints needed × 14 days.
- [ ] Status: On track if the projected finish ≤ `2027-02-27`, otherwise At risk. Apply the D3 warning band.
- [ ] Return a structured result: status, velocity, remaining, sprints needed, projected finish, deadline, and a short reason.

### 2.4 Daily history (`history`)
- [ ] Write `data/history/<date>.json` with completed, planned, added, carried over and the forecast result.
- [ ] A re-run on the same day overwrites that day's snapshot (idempotent).
- [ ] Read previous snapshots to produce a forecast-trend series; skip missing days gracefully.
- [ ] Ensure the report calculations never depend on history (§5.2 "Missed days").

### 2.5 Freshness
- [ ] Read the CSV mtime as "Data as of".
- [ ] Stale warning when older than 1 day, or older than 3 days when the weekend rule applies. Define the weekend rule explicitly (e.g. a Monday run with a Friday file is fine).

---

## Phase 3: Integration

### 3.1 HTML renderer (`render_html`)
- [ ] Build a single self-contained HTML file with inline CSS and SVG, no external resources.
- [ ] Header: project, generation date, "Data as of", mode.
- [ ] Forecast banner: On track / At risk, projected finish, contract date.
- [ ] Per-sprint table: completed, planned, added, completed vs planned, carry-over, story points, "in progress" label for the current sprint.
- [ ] SVG bar chart of stories completed per sprint (current sprint visually distinct).
- [ ] History trend section (forecast over time) when snapshots exist.
- [ ] `internal` mode only: per-team breakdown table.
- [ ] Notes section listing all warnings (unrecognised sprints, missing points, missing Team, stale data).
- [ ] HTML-escape all text.

### 3.2 Client-mode privacy
- [ ] Make the `client` view model structurally exclude team names, individual names and ticket text (don't just hide them in the template).
- [ ] Apply the D5 sprint label option in `client` mode.
- [ ] Ensure warnings in client mode contain no team names or ticket keys/summaries.

### 3.3 CLI (`cli`)
- [ ] Arguments: `--csv` (default `data/export.csv`), `--config` (default `config/project_config.json`), `--mode` (`client` default | `internal`), plus an optional `--today` for reproducible runs.
- [ ] Wire the pipeline: load config → load CSV → metrics → forecast → history → render.
- [ ] Write to `reports/sprint_report_<mode>_<date>.html`, creating the directory if needed.
- [ ] Errors go to stderr with a non-zero exit code; success prints the output path.
- [ ] Support `python3 -m sprint_report`.

### 3.4 Existing code
- [ ] Move the reusable parsing and date helpers from `scripts/build_dashboard.py` into the shared module.
- [ ] Update `build_dashboard.py` and `generate_report.py` to import from it, or mark them deprecated. Confirm that the old behaviour still works.

### 3.5 Optional scheduling
- [ ] Provide an example cron entry and a launchd plist in the docs. No code dependency.

---

## Phase 4: Testing

### 4.1 Unit tests (fixture-based)
- [ ] `csv_loader`: repeated Sprint columns, alternative column names, non-Story filtering, bad dates, missing columns.
- [ ] `metrics`: last-sprint attribution, planned vs added boundary (created on the start date), carry-over, empty sprint, points, current-sprint flag, by-team totals.
- [ ] `forecast`: on track, at risk, velocity 0, fewer than 6 sprints, remaining ≤ 0, the D2 and D3 options.
- [ ] `history`: write, overwrite on the same day, read with gaps.
- [ ] Freshness: weekday, weekend and boundary cases.
- [ ] Config validation errors.

### 4.2 Integration and security tests
- [ ] End-to-end CLI test on the fixture in both modes, comparing key figures in the output.
- [ ] Determinism: the same CSV and `--today` give byte-identical HTML.
- [ ] Client report scan: assert that no team names, individual names or ticket text appear.
- [ ] Escaping test: HTML/JS in a field value is escaped.
- [ ] Self-contained check: no `http(s)://` resource references in the HTML.
- [ ] CLI error paths: missing file, bad config, bad mode → stderr and non-zero exit.

### 4.3 Acceptance verification (§10)
- [ ] Run against a real Jira export (needs D4 and the sprint dates from the user).
- [ ] Compare completed counts for at least one past sprint with Jira's own sprint report.
- [ ] Review the `client` report manually for leaked team or individual names.
- [ ] Confirm the forecast banner is clear to a non-technical reader.
- [ ] Run on two consecutive days (or with `--today`) and confirm separate dated reports and updated "Data as of" and stale warnings.
- [ ] Confirm that data problems appear as warnings in the report.

---

## Phase 5: Documentation

- [ ] Update [README.md](./README.md): purpose, requirements, quick start, and the two commands.
- [ ] Document the daily workflow: export the CSV to `data/export.csv`, run, share the report.
- [ ] Jira export guide: filter, required columns, repeated Sprint columns.
- [ ] Config reference: every key, with an example.
- [ ] Calculation rules and forecast assumptions, in plain language for the client audience.
- [ ] Limitations (§11): mid-sprint additions estimated, removals undetectable, scope entered by hand, manual export.
- [ ] Security notes: the CSV is git-ignored, no credentials, how to share the `client` report.
- [ ] Optional scheduling instructions (cron / launchd).
- [ ] Future work (§13): API loader interface, automatic refresh, Excel/PDF.
- [ ] Reconcile or archive the overlapping [SPRINT_DASHBOARD_REQUIREMENTS.md](./SPRINT_DASHBOARD_REQUIREMENTS.md) and [PROJECT_IDEAS.md](./PROJECT_IDEAS.md).
```
