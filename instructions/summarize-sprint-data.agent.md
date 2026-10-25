- Purpose: turn normalised sprint issue data into one summary table, one row per sprint, with the agreed delivery metrics.
- Scope: only the sprint table; fetching is in `./instructions/fetch-jira-issues.agent.md`, the forecast and HTML report are in `./instructions/generate-sprint-report.agent.md`. Reuse `compute_metrics` in `./project-jira-automation/scripts/build_dashboard.py` where it fits.
- Input: issue records
  + Output of `./instructions/fetch-jira-issues.agent.md`: `key`, `issue_type`, `status`, `group`, `team`, `created`, `resolved`, `points`, `sprints` (ordered list).
  + Only issue type `Story` is used.
- Input: sprint config
  + Sprints with `name`, `start`, `end` (`YYYY-MM-DD`, ordered, not overlapping), `completed_statuses` (default Done, Resolved, Closed).
- Input: arguments
  + `--today YYYY-MM-DD` (default: system date), `--mode client|internal` (default `client`), `--last N` sprints (default 6 plus the current one), `--format markdown|json` (default `markdown`).
- Step 1, validate the input:
  + Stop with an error naming the key if a sprint is missing `name`, `start` or `end`, dates are invalid, sprints overlap or are unordered.
  + Warn, do not fail, about issue sprint names that are not in the config; exclude them from the table.
- Step 2, assign stories to sprints:
  + A story belongs to every configured sprint in its `sprints` list.
  + A completed story (status in `completed_statuses`, case-insensitive) is counted as completed once, in the last sprint listed for it.
- Step 3, compute per sprint:
  + Planned: stories in the sprint with `created` on or before the sprint start.
  + Added: stories in the sprint with `created` after the sprint start.
  + Completed: as in Step 2.
  + Completed vs planned: completed ÷ (planned + added), as a percentage rounded to the nearest whole number; `n/a` if the divisor is 0.
  + Carry-over: stories in the sprint that also appear in a later sprint.
  + Story points completed: sum of `points` of the completed stories; stories with no points add 0 and raise a warning.
  + State: `Closed` if `end` < today, `In progress` if `start` <= today <= `end`, otherwise `Planned`.
- Step 4, total and order:
  + Order rows by sprint start date, oldest first; keep the last `--last` closed sprints and the current sprint.
  + Add a `Total` row: sums for planned, added, completed, carry-over and points; completed vs planned recomputed from the totals, not averaged.
  + `internal` mode only: add a per-team table with the same columns, plus an `Unassigned` row for missing teams.
- Step 5, collect warnings:
  + Unrecognised sprint names, missing story points, missing team (`internal` only), empty sprints.
- Output: Markdown (default)
  + Header: `| Sprint | Dates | State | Planned | Added | Completed | Completed vs planned | Carry-over | Points |`.
  + One row per sprint, then the `Total` row; dates as `YYYY-MM-DD to YYYY-MM-DD`; integers without decimals.
  + Below the table, a `Notes` bullet list with all warnings; omit it if there are none.
  + Save to `reports/sprint-summary-<mode>-<YYYY-MM-DD>.md` when a file is requested.
- Output: JSON
  + `{"generated": "<date>", "mode": "...", "sprints": [{"name", "start", "end", "state", "planned", "added", "completed", "completed_vs_planned", "carry_over", "points"}], "total": {...}, "warnings": [...]}` with sorted keys.
  + `internal` mode adds a `teams` object keyed by team name.
- Constraint: Python 3, standard library only.
- Constraint: deterministic; the same records, config and `--today` give identical output.
- Constraint: inject `today`; never call the system clock inside the calculation functions.
- Constraint: never divide by zero; an empty sprint shows 0 counts and `n/a`.
- Constraint: `client` output contains no team names, individual names, ticket keys or summaries, including in `Notes`.
- Constraint: report counts as the data gives them; do not round, estimate or fill gaps silently, and show every data problem as a warning.
- Constraint: mid-sprint additions are estimated from `created` dates, and stories removed from a sprint cannot be detected; state this under the table.
- Constraint: do not modify the input data or config files.
