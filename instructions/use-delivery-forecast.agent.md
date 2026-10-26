- Purpose: forecast whether the remaining scope will be finished by the deadline with `./tools/delivery-forecast.py`, and produce the banner status and reason.
- When to use:
  + The user asks if the project is on track or at risk, when the scope will finish, or how many sprints remain.
  + Sprint figures come from `./instructions/use-metric-calc.agent.md` (`tools/sprint-metrics.py`); this tool does not read the CSV.
  + Do not use for per-sprint metrics or the HTML report (`./instructions/generate-sprint-report.agent.md`).
- Input: values to collect before running
  + Completed counts per closed sprint, oldest first: the `Completed` column of every `Closed` row from `sprint-metrics.py`.
  + Current sprint completed so far: the `Completed` value of the `In progress` row (default 0).
  + Total scope: positive number of stories, entered by the user or in the config (`total_scope`); never guess it.
  + Current sprint end date: `YYYY-MM-DD`, from the sprint config.
  + Deadline: `YYYY-MM-DD`, from the user or the config; never guess it.
  + Optional: velocity method, warning margin in sprints, sprint length in days.
- Step 1, get the completed counts:
  + Run `python3 tools/sprint-metrics.py ... --last 100 --format json` so that **all** closed sprints are returned; the default `--last 6` hides older sprints and would overstate remaining.
  + Use `--mode client`; the forecast needs no team data.
  + Read `completed` per sprint from the JSON `sprints` list; closed sprints go to `--completed`, the `In progress` one to `--current-completed`.
- Step 2, run from the workspace root:
  + `python3 tools/delivery-forecast.py --completed <n1> <n2> ... --scope <N> --sprint-end <date> --deadline <date> [--current-completed <n>] [--velocity-method average_last_6|worst_of_last_3] [--warning-sprints <n>] [--sprint-days <n>] [--format text|json]`
  + Example: `python3 tools/delivery-forecast.py --completed 10 12 9 11 10 8 --current-completed 4 --scope 150 --sprint-end 2026-10-30 --deadline 2027-02-27 --warning-sprints 1`
  + `--completed` accepts spaces or commas (`10,12,9`); omit it only if there is no closed sprint.
  + `--velocity-method`: `average_last_6` (default) or the cautious `worst_of_last_3`; use another method only if the user or config asks.
  + `--warning-sprints`: default `0` = late date only; `1` adds the "At risk – tight" band for a finish within one sprint length (14 days) before the deadline.
  + `--sprint-days`: default `14`.
- Step 3, handle errors:
  + Exit code `1` with `error: ...`: invalid values (negative counts, scope not positive, sprint length not positive); fix the input or ask the user, then rerun.
  + Exit code `2`: invalid arguments such as a bad date or a non-numeric count.
  + Do not calculate the forecast by hand if the tool fails.
- Rules the tool applies (do not restate different ones):
  + Velocity: mean of the last 6 closed sprints, or the lowest of the last 3; with less history all available sprints are used plus a warning.
  + Remaining = scope − all closed completed − current sprint completed.
  + Sprints needed = remaining ÷ velocity rounded up, in exact fractions (no float rounding); projected finish = sprint end + sprints needed × sprint length.
  + On track: finish is on or before the deadline minus the warning margin. Otherwise At risk; "tight" means the finish is within the margin but not after the deadline.
  + Remaining ≤ 0: On track, 0 sprints needed. Velocity 0 or no history: At risk, no finish date, with a warning.
- Output (text): `Status`, `Reason`, `Velocity`, `Remaining`, `Sprints needed`, `Projected finish`, `Deadline`, then one `Warning:` line per warning.
  + JSON adds `label`, `tight`, `velocity_exact` (e.g. `13/3`); `velocity` is rounded to 2 decimals for display only.
- Present results:
  + Lead with the status label (`On track`, `At risk`, `At risk – tight`) and the one-sentence reason, unchanged; it is written for the banner.
  + Then list velocity, remaining, sprints needed, projected finish and deadline.
  + Always show the warnings, especially short history (under 6 sprints) and velocity 0; they change how far the result can be trusted.
  + With no finish date (velocity 0 or no history), say the date cannot be projected; do not invent one.
  + State the inputs used (scope, method, margin) so the assumptions are visible.
- Constraint: the forecast is only as good as the manually entered scope and the history; say so when presenting it.
- Constraint: the forecast uses story counts, not story points.
- Constraint: the tool is read-only and deterministic; the same inputs give the same output.
