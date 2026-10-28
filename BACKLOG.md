# Implementation Backlog: Sprint Delivery Report

Source: [project_spec.md](./project_spec.md). Python 3, standard library only.

**MVP (first usable milestone):** Phases 1–3 deliver both `client` and `internal` modes with metrics and the forecast. Phase 4 hardens and verifies; Phase 5 documents.

**Priority order (earliest first):** forecast banner → planned vs completed / carry-over / mid-sprint additions → daily history snapshots → internal per-team breakdown → story points. Privacy and freshness are acceptance criteria, so they are scheduled where they are needed, not deferred.

---

## Phase 1: Setup

### 1.1 Decisions (spec §12 open questions; implement as configurable defaults)
- [ ] D1. Team count and missing Team values: default to an `Unassigned` bucket in `internal` mode and add a data warning. ([#1](https://github.com/prashantava0337/jira-confluence-automation/issues/1))
- [ ] D2. Velocity: config key `velocity_method` (`average_last_6` default; `worst_of_last_3` option). ([#2](https://github.com/prashantava0337/jira-confluence-automation/issues/2))
- [ ] D3. At-risk definition: config key `at_risk_warning_sprints` (default `0` = late date only; `1` adds an "At risk – tight" band). ([#3](https://github.com/prashantava0337/jira-confluence-automation/issues/3))
- [ ] D4. Real CSV column names and date format: get an export header row from the user and update the config mapping defaults. ([#4](https://github.com/prashantava0337/jira-confluence-automation/issues/4))
- [ ] D5. Client report sprint labels: config key `client_sprint_labels` (`names` default | `numbers`). ([#5](https://github.com/prashantava0337/jira-confluence-automation/issues/5))
- [ ] D6. Confirm the two-mode intent (§3) and the acceptance criteria (§10) with the user. ([#6](https://github.com/prashantava0337/jira-confluence-automation/issues/6))
- [ ] D7. Record the sprint-list-from-API item as future work only (§13); no implementation. ([#7](https://github.com/prashantava0337/jira-confluence-automation/issues/7))

### 1.2 Project skeleton
- [ ] Review the existing [scripts/build_dashboard.py](./scripts/build_dashboard.py) and [scripts/generate_report.py](./scripts/generate_report.py); list reusable CSV parsing and date handling. ([#8](https://github.com/prashantava0337/jira-confluence-automation/issues/8))
- [ ] Create the `sprint_report/` package with `__init__.py` and `__main__.py`. ([#9](https://github.com/prashantava0337/jira-confluence-automation/issues/9))
- [ ] Create stub modules: `csv_loader`, `metrics`, `forecast`, `history`, `render_html`, `cli`. ([#10](https://github.com/prashantava0337/jira-confluence-automation/issues/10))
- [ ] Create the directories `config/`, `data/history/`, `reports/`, `tests/fixtures/`. ([#11](https://github.com/prashantava0337/jira-confluence-automation/issues/11))
- [ ] Update [.gitignore](./.gitignore): `data/export.csv`, `data/history/`, `reports/`, and any real exports. Keep the anonymised fixtures tracked. ([#12](https://github.com/prashantava0337/jira-confluence-automation/issues/12))
- [ ] Update [.env.example](./.env.example) or remove it if no credentials are used. ([#13](https://github.com/prashantava0337/jira-confluence-automation/issues/13))

### 1.3 Config
- [ ] Define the schema for `config/project_config.json`: project, sprints (name, start, end), `contract_deadline`, `total_scope`, `column_map`, `completed_statuses`, `date_formats`, plus the D2/D3/D5 keys. ([#14](https://github.com/prashantava0337/jira-confluence-automation/issues/14))
- [ ] Add `config/project_config.example.json` with the 6 past sprints plus the current one, deadline `2027-02-27`, and the default completed statuses (Done, Resolved, Closed). ([#15](https://github.com/prashantava0337/jira-confluence-automation/issues/15))
- [ ] Implement the config loader with validation: missing keys, bad dates, overlapping or unordered sprints, non-positive scope. Errors name the offending key. ([#16](https://github.com/prashantava0337/jira-confluence-automation/issues/16))
- [ ] Add the shared date-parsing helper (multiple formats), moved from `build_dashboard.py`. ([#17](https://github.com/prashantava0337/jira-confluence-automation/issues/17))

### 1.4 Test scaffolding
- [ ] Set up `unittest` discovery (`python3 -m unittest`). ([#18](https://github.com/prashantava0337/jira-confluence-automation/issues/18))
- [ ] Create the anonymised fixture `tests/fixtures/export_small.csv`: repeated `Sprint` columns, carry-over, mid-sprint additions, an empty sprint, multiple teams, a missing Team, a missing story-point value, and a non-Story issue type. ([#19](https://github.com/prashantava0337/jira-confluence-automation/issues/19))

---

## Phase 2: Core Features

### 2.1 CSV loader (`csv_loader`)
- [ ] Parse the CSV with header-name mapping, including alternative column names (`Custom field (Team)` / `Team`). ([#20](https://github.com/prashantava0337/jira-confluence-automation/issues/20))
- [ ] Read **every** repeated `Sprint` column per row and preserve order. ([#21](https://github.com/prashantava0337/jira-confluence-automation/issues/21))
- [ ] Filter to issue type `Story`. ([#22](https://github.com/prashantava0337/jira-confluence-automation/issues/22))
- [ ] Normalise status against `completed_statuses`, case-insensitively. ([#23](https://github.com/prashantava0337/jira-confluence-automation/issues/23))
- [ ] Parse Created and Resolved dates; parse story points (blank → `None`). ([#24](https://github.com/prashantava0337/jira-confluence-automation/issues/24))
- [ ] Return a `Story` record (key, team, status, sprints, points, created, resolved) plus a list of data warnings. ([#25](https://github.com/prashantava0337/jira-confluence-automation/issues/25))
- [ ] Fail with a clear error if a required column is missing or the file is unreadable (stderr, non-zero exit). ([#26](https://github.com/prashantava0337/jira-confluence-automation/issues/26))

### 2.2 Metrics (`metrics`), in priority order
- [ ] Map sprint names from the CSV to configured sprints; warn about unrecognised sprints. ([#27](https://github.com/prashantava0337/jira-confluence-automation/issues/27))
- [ ] **Completed per sprint:** count each Done story once, in the last sprint listed for it. Total, and by team. ([#28](https://github.com/prashantava0337/jira-confluence-automation/issues/28))
- [ ] **Planned:** stories in the sprint created on or before the start date. ([#29](https://github.com/prashantava0337/jira-confluence-automation/issues/29))
- [ ] **Added mid-sprint:** stories in the sprint created after the start date. ([#30](https://github.com/prashantava0337/jira-confluence-automation/issues/30))
- [ ] **Completed vs planned:** completed ÷ (planned + added), with planned and added shown separately. Guard against divide-by-zero for empty sprints. ([#31](https://github.com/prashantava0337/jira-confluence-automation/issues/31))
- [ ] **Carry-over:** a story in sprint N that also appears in a later sprint counts as carried over from N. ([#32](https://github.com/prashantava0337/jira-confluence-automation/issues/32))
- [ ] **Story points completed** per sprint; warn about stories with no points. ([#33](https://github.com/prashantava0337/jira-confluence-automation/issues/33))
- [ ] Mark the current sprint as "in progress" based on today's date versus the config dates. ([#34](https://github.com/prashantava0337/jira-confluence-automation/issues/34))
- [ ] Allow `today` to be injected so metrics are deterministic and testable. ([#35](https://github.com/prashantava0337/jira-confluence-automation/issues/35))

### 2.3 Forecast (`forecast`)
- [ ] Velocity: average stories completed over the last 6 completed sprints (the current sprint is excluded). Support the D2 option. ([#36](https://github.com/prashantava0337/jira-confluence-automation/issues/36))
- [ ] Remaining = `total_scope` − all completed stories to date. ([#37](https://github.com/prashantava0337/jira-confluence-automation/issues/37))
- [ ] Sprints needed = ceil(remaining ÷ velocity). Handle velocity 0 or fewer than 6 sprints of history: At risk with a warning. ([#38](https://github.com/prashantava0337/jira-confluence-automation/issues/38))
- [ ] Projected finish = end of current sprint + sprints needed × 14 days. ([#39](https://github.com/prashantava0337/jira-confluence-automation/issues/39))
- [ ] Status: On track if the projected finish ≤ `2027-02-27`, otherwise At risk. Apply the D3 warning band. ([#40](https://github.com/prashantava0337/jira-confluence-automation/issues/40))
- [ ] Return a structured result: status, velocity, remaining, sprints needed, projected finish, deadline, and a short reason. ([#41](https://github.com/prashantava0337/jira-confluence-automation/issues/41))

### 2.4 Daily history (`history`)
- [ ] Write `data/history/<date>.json` with completed, planned, added, carried over and the forecast result. ([#42](https://github.com/prashantava0337/jira-confluence-automation/issues/42))
- [ ] A re-run on the same day overwrites that day's snapshot (idempotent). ([#43](https://github.com/prashantava0337/jira-confluence-automation/issues/43))
- [ ] Read previous snapshots to produce a forecast-trend series; skip missing days gracefully. ([#44](https://github.com/prashantava0337/jira-confluence-automation/issues/44))
- [ ] Ensure the report calculations never depend on history (§5.2 "Missed days"). ([#45](https://github.com/prashantava0337/jira-confluence-automation/issues/45))

### 2.5 Freshness
- [ ] Read the CSV mtime as "Data as of". ([#46](https://github.com/prashantava0337/jira-confluence-automation/issues/46))
- [ ] Stale warning when older than 1 day, or older than 3 days when the weekend rule applies. Define the weekend rule explicitly (e.g. a Monday run with a Friday file is fine). ([#47](https://github.com/prashantava0337/jira-confluence-automation/issues/47))

---

## Phase 3: Integration

### 3.1 HTML renderer (`render_html`)
- [ ] Build a single self-contained HTML file with inline CSS and SVG, no external resources. ([#48](https://github.com/prashantava0337/jira-confluence-automation/issues/48))
- [ ] Header: project, generation date, "Data as of", mode. ([#49](https://github.com/prashantava0337/jira-confluence-automation/issues/49))
- [ ] Forecast banner: On track / At risk, projected finish, contract date. ([#50](https://github.com/prashantava0337/jira-confluence-automation/issues/50))
- [ ] Per-sprint table: completed, planned, added, completed vs planned, carry-over, story points, "in progress" label for the current sprint. ([#51](https://github.com/prashantava0337/jira-confluence-automation/issues/51))
- [ ] SVG bar chart of stories completed per sprint (current sprint visually distinct). ([#52](https://github.com/prashantava0337/jira-confluence-automation/issues/52))
- [ ] History trend section (forecast over time) when snapshots exist. ([#53](https://github.com/prashantava0337/jira-confluence-automation/issues/53))
- [ ] `internal` mode only: per-team breakdown table. ([#54](https://github.com/prashantava0337/jira-confluence-automation/issues/54))
- [ ] Notes section listing all warnings (unrecognised sprints, missing points, missing Team, stale data). ([#55](https://github.com/prashantava0337/jira-confluence-automation/issues/55))
- [ ] HTML-escape all text. ([#56](https://github.com/prashantava0337/jira-confluence-automation/issues/56))

### 3.2 Client-mode privacy
- [ ] Make the `client` view model structurally exclude team names, individual names and ticket text (don't just hide them in the template). ([#57](https://github.com/prashantava0337/jira-confluence-automation/issues/57))
- [ ] Apply the D5 sprint label option in `client` mode. ([#58](https://github.com/prashantava0337/jira-confluence-automation/issues/58))
- [ ] Ensure warnings in client mode contain no team names or ticket keys/summaries. ([#59](https://github.com/prashantava0337/jira-confluence-automation/issues/59))

### 3.3 CLI (`cli`)
- [ ] Arguments: `--csv` (default `data/export.csv`), `--config` (default `config/project_config.json`), `--mode` (`client` default | `internal`), plus an optional `--today` for reproducible runs. ([#60](https://github.com/prashantava0337/jira-confluence-automation/issues/60))
- [ ] Wire the pipeline: load config → load CSV → metrics → forecast → history → render. ([#61](https://github.com/prashantava0337/jira-confluence-automation/issues/61))
- [ ] Write to `reports/sprint_report_<mode>_<date>.html`, creating the directory if needed. ([#62](https://github.com/prashantava0337/jira-confluence-automation/issues/62))
- [ ] Errors go to stderr with a non-zero exit code; success prints the output path. ([#63](https://github.com/prashantava0337/jira-confluence-automation/issues/63))
- [ ] Support `python3 -m sprint_report`. ([#64](https://github.com/prashantava0337/jira-confluence-automation/issues/64))

### 3.4 Existing code
- [ ] Move the reusable parsing and date helpers from `scripts/build_dashboard.py` into the shared module. ([#65](https://github.com/prashantava0337/jira-confluence-automation/issues/65))
- [ ] Update `build_dashboard.py` and `generate_report.py` to import from it, or mark them deprecated. Confirm that the old behaviour still works. ([#66](https://github.com/prashantava0337/jira-confluence-automation/issues/66))

### 3.5 Optional scheduling
- [ ] Provide an example cron entry and a launchd plist in the docs. No code dependency. ([#67](https://github.com/prashantava0337/jira-confluence-automation/issues/67))

---

## Phase 4: Testing

### 4.1 Unit tests (fixture-based)
- [ ] `csv_loader`: repeated Sprint columns, alternative column names, non-Story filtering, bad dates, missing columns. ([#68](https://github.com/prashantava0337/jira-confluence-automation/issues/68))
- [ ] `metrics`: last-sprint attribution, planned vs added boundary (created on the start date), carry-over, empty sprint, points, current-sprint flag, by-team totals. ([#69](https://github.com/prashantava0337/jira-confluence-automation/issues/69))
- [ ] `forecast`: on track, at risk, velocity 0, fewer than 6 sprints, remaining ≤ 0, the D2 and D3 options. ([#70](https://github.com/prashantava0337/jira-confluence-automation/issues/70))
- [ ] `history`: write, overwrite on the same day, read with gaps. ([#71](https://github.com/prashantava0337/jira-confluence-automation/issues/71))
- [ ] Freshness: weekday, weekend and boundary cases. ([#72](https://github.com/prashantava0337/jira-confluence-automation/issues/72))
- [ ] Config validation errors. ([#73](https://github.com/prashantava0337/jira-confluence-automation/issues/73))

### 4.2 Integration and security tests
- [ ] End-to-end CLI test on the fixture in both modes, comparing key figures in the output. ([#74](https://github.com/prashantava0337/jira-confluence-automation/issues/74))
- [ ] Determinism: the same CSV and `--today` give byte-identical HTML. ([#75](https://github.com/prashantava0337/jira-confluence-automation/issues/75))
- [ ] Client report scan: assert that no team names, individual names or ticket text appear. ([#76](https://github.com/prashantava0337/jira-confluence-automation/issues/76))
- [ ] Escaping test: HTML/JS in a field value is escaped. ([#77](https://github.com/prashantava0337/jira-confluence-automation/issues/77))
- [ ] Self-contained check: no `http(s)://` resource references in the HTML. ([#78](https://github.com/prashantava0337/jira-confluence-automation/issues/78))
- [ ] CLI error paths: missing file, bad config, bad mode → stderr and non-zero exit. ([#79](https://github.com/prashantava0337/jira-confluence-automation/issues/79))

### 4.3 Acceptance verification (§10)
- [ ] Run against a real Jira export (needs D4 and the sprint dates from the user). ([#80](https://github.com/prashantava0337/jira-confluence-automation/issues/80))
- [ ] Compare completed counts for at least one past sprint with Jira's own sprint report. ([#81](https://github.com/prashantava0337/jira-confluence-automation/issues/81))
- [ ] Review the `client` report manually for leaked team or individual names. ([#82](https://github.com/prashantava0337/jira-confluence-automation/issues/82))
- [ ] Confirm the forecast banner is clear to a non-technical reader. ([#83](https://github.com/prashantava0337/jira-confluence-automation/issues/83))
- [ ] Run on two consecutive days (or with `--today`) and confirm separate dated reports and updated "Data as of" and stale warnings. ([#84](https://github.com/prashantava0337/jira-confluence-automation/issues/84))
- [ ] Confirm that data problems appear as warnings in the report. ([#85](https://github.com/prashantava0337/jira-confluence-automation/issues/85))

---

## Phase 5: Documentation
- [ ] Update [README.md](./README.md): purpose, requirements, quick start, and the two commands. ([#86](https://github.com/prashantava0337/jira-confluence-automation/issues/86))
- [ ] Document the daily workflow: export the CSV to `data/export.csv`, run, share the report. ([#87](https://github.com/prashantava0337/jira-confluence-automation/issues/87))
- [ ] Jira export guide: filter, required columns, repeated Sprint columns. ([#88](https://github.com/prashantava0337/jira-confluence-automation/issues/88))
- [ ] Config reference: every key, with an example. ([#89](https://github.com/prashantava0337/jira-confluence-automation/issues/89))
- [ ] Calculation rules and forecast assumptions, in plain language for the client audience. ([#90](https://github.com/prashantava0337/jira-confluence-automation/issues/90))
- [ ] Limitations (§11): mid-sprint additions estimated, removals undetectable, scope entered by hand, manual export. ([#91](https://github.com/prashantava0337/jira-confluence-automation/issues/91))
- [ ] Security notes: the CSV is git-ignored, no credentials, how to share the `client` report. ([#92](https://github.com/prashantava0337/jira-confluence-automation/issues/92))
- [ ] Optional scheduling instructions (cron / launchd). ([#93](https://github.com/prashantava0337/jira-confluence-automation/issues/93))
- [ ] Future work (§13): API loader interface, automatic refresh, Excel/PDF. ([#94](https://github.com/prashantava0337/jira-confluence-automation/issues/94))
- [ ] Reconcile or archive the overlapping [SPRINT_DASHBOARD_REQUIREMENTS.md](./SPRINT_DASHBOARD_REQUIREMENTS.md) and [PROJECT_IDEAS.md](./PROJECT_IDEAS.md). ([#95](https://github.com/prashantava0337/jira-confluence-automation/issues/95))
