- Purpose: calculate per-sprint delivery metrics from a Jira CSV export with `./tools/sprint-metrics.py`.
- When to use:
  + The user asks for planned vs added, completed vs planned, carry-over, story points or a per-team split per sprint.
  + The user needs a sprint summary table from a Jira CSV export.
  + Do not use for the delivery forecast (`./tools/delivery-forecast.py`) or the HTML report (`./instructions/generate-sprint-report.agent.md`).
- Input: CSV export
  + One row per issue; Jira repeats the `Sprint` column once per sprint; the tool reads all of them.
  + Required columns: issue key, status, `Sprint`, `Created`. Optional: `Issue Type`, `Team`, story points.
  + Only issue type `Story` is used.
  + Default path `data/export.csv`; real exports stay git-ignored.
- Input: config file (JSON)
  + Required: `sprints`, an ordered, non-overlapping list of `{"name", "start", "end"}` with `YYYY-MM-DD` dates; the CSV has no sprint dates.
  + Optional: `completed_statuses` (default Done, Resolved, Closed), `date_formats`, `columns` (header-name overrides).
  + Default path `config/project_config.json`; `project-jira-automation/data/sprint_config.json` has a different shape and does not work.
  + If no suitable config exists, ask the user for the sprint names and dates; never guess them.
- Step 1, choose the mode:
  + `client` (default): no team names, ticket keys or team warnings; use for anything shared outside the delivery team.
  + `internal`: adds a per-team table (with `Unassigned`) and ticket keys in warnings.
  + If unsure who reads the output, use `client`.
- Step 2, run from the workspace root:
  + `python3 tools/sprint-metrics.py --csv <csv> --config <config> [--mode client|internal] [--today YYYY-MM-DD] [--last N] [--format markdown|json] [--output <path>]`
  + Example: `python3 tools/sprint-metrics.py --csv data/export.csv --config config/project_config.json --mode client`
  + `--today`: reference date, default system date; pass it for reproducible output.
  + `--last N`: closed sprints to show, default 6, plus the current sprint; future sprints are not shown.
  + `--output`: write to a file and print its path; default is stdout. Suggested name `reports/sprint-summary-<mode>-<YYYY-MM-DD>.md`.
- Step 3, handle errors:
  + Exit code `1` with `error: ...` on stderr: unreadable CSV or config, missing required column, invalid sprint list, unrecognised date format; fix the named input or ask the user, then rerun.
  + Exit code `2`: invalid arguments.
  + Do not calculate the figures by hand if the tool fails.
- Calculation rules (do not restate different ones):
  + Completed: status in `completed_statuses`, counted once, in the last configured sprint listed for the story.
  + Planned: created on or before the sprint start date. Added: created after it.
  + Completed vs planned: completed ÷ (planned + added), whole percent; `n/a` for an empty sprint.
  + Carry-over: in the sprint and also in a later sprint.
  + Points: sum for completed stories; stories without points count as 0 and raise a warning.
  + `Total` row: sums of the rows shown; percentage recomputed from the totals.
- Present results:
  + Show the tool's table unchanged; do not re-round or recompute.
  + Keep the estimate note and the `Notes` warnings; do not drop them.
  + Mention the state (`Closed`, `In progress`) when discussing the current sprint, since its numbers change daily.
  + A story that spans several sprints appears in each of them, so row sums can exceed the number of distinct stories.
  + Use `--format json` when another tool consumes the output (sorted keys; `completed_vs_planned` is `null` for an empty sprint).
- Constraint: in `client` output never add team names, individual names, ticket keys or summaries, including in your own commentary.
- Constraint: the tool is read-only; it does not modify the CSV or the config.
- Constraint: mid-sprint additions are estimated from `Created` dates and removals from a sprint cannot be detected; say so when presenting added counts.
