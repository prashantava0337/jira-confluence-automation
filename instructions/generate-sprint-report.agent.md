- Purpose: turn a Jira CSV export into a self-contained HTML report with sprint metrics and a delivery forecast, in `client` or `internal` mode.
- Spec and build plan: `./project-jira-automation/project_spec.md`, `./project-jira-automation/backlog.md`. Run from `./project-jira-automation/` with `python3 -m sprint_report`.
- Input: CSV export (default `data/export.csv`)
  + One row per issue; read **every** repeated `Sprint` column, in order.
  + Required columns: issue key, issue type, status, Created, Resolved, Sprint (repeated), Team (`Team` or `Custom field (Team)`), story points.
  + Use only issue type `Story`.
- Input: config file (default `config/project_config.json`)
  + Keys: project name, sprints (name, start, end), `contract_deadline`, `total_scope`, `column_map`, `completed_statuses`, `date_formats`, `velocity_method`, `at_risk_warning_sprints`, `client_sprint_labels`.
- Input: arguments
  + `--mode client|internal` (default `client`).
  + `--today YYYY-MM-DD` (optional, for reproducible runs).
- Step 1, load and validate config:
  + Stop with an error naming the offending key if a key is missing, a date is invalid, sprints overlap or are out of order, or scope is not positive.
- Step 2, load the CSV:
  + Map headers, filter to Stories, normalise status against `completed_statuses` (case-insensitive).
  + Parse dates and points; blank points become `None`.
  + Collect data warnings for bad rows instead of failing.
  + Fail only if a required column is missing or the file is unreadable.
- Step 3, compute metrics per sprint:
  + Completed: count each Done story once, in the last sprint listed for it.
  + Planned: created on or before the sprint start. Added: created after the start.
  + Completed vs planned: completed ÷ (planned + added); guard against empty sprints.
  + Carry-over: a story in sprint N that also appears in a later sprint.
  + Story points completed; warn about stories without points.
  + Flag the current sprint as "in progress" using `today`.
- Step 4, compute the forecast:
  + Velocity: last 6 completed sprints (current sprint excluded), or per `velocity_method`.
  + Remaining = `total_scope` − all completed stories.
  + Sprints needed = ceil(remaining ÷ velocity); projected finish = end of current sprint + sprints needed × 14 days.
  + Status: On track if projected finish ≤ `contract_deadline`, otherwise At risk; apply the `at_risk_warning_sprints` band.
  + Velocity 0 or too little history: At risk plus a warning.
- Step 5, write the history snapshot:
  + Write `data/history/<date>.json`; overwrite any same-day file.
  + Build the trend series from existing snapshots; skip gaps.
  + Report figures must never depend on history.
- Step 6, check freshness:
  + Use the CSV modification time as "Data as of".
  + Add a stale warning per the defined weekday and weekend rule.
- Step 7, build the view model for the chosen mode:
  + In `client` mode, exclude team names, individual names and ticket text at the data level, not only in the template.
- Step 8, render the HTML:
  + Escape all text.
  + Write to `reports/sprint_report_<mode>_<date>.html`; create the directory if needed.
- Output: one self-contained HTML file (inline CSS and SVG, no external resources), sections in this order:
  + Header: project, generation date, "Data as of", mode.
  + Forecast banner: status, projected finish, contract date.
  + Per-sprint table: completed, planned, added, completed vs planned, carry-over, story points, "in progress" label.
  + SVG bar chart of completed stories per sprint; current sprint visually distinct.
  + Forecast trend, only if snapshots exist.
  + Per-team breakdown, `internal` mode only.
  + Notes: all warnings.
- Output: console
  + On success, print the output path.
  + On failure, print to stderr and exit non-zero.
- Constraint: Python 3, standard library only.
- Constraint: deterministic; the same CSV, config and `--today` produce byte-identical HTML.
- Constraint: `client` reports contain no team names, individual names, ticket keys or summaries, including in warnings.
- Constraint: real exports, history and reports stay git-ignored; no credentials are used.
- Constraint: data problems always appear as warnings in the report; never silently change figures.
- Constraint: mid-sprint additions are estimated from creation dates and removals cannot be detected; state this in the documentation.
- Constraint: the forecast is only as good as the manually entered `total_scope`.
