---
description: Entry point that lists the available instruction files and when to use each.
---

# Main Agent Instructions

Use the instruction file that matches the user's request, and follow it exactly.

Each entry below is an instruction file with a one-line description. Optional sub-fields after `+`:
- **Keywords** — trigger words/phrases: if the user's request matches, load this instruction.
- **Target** — file glob pattern: if the current file or context matches, consider this instruction relevant.
- **Exceptions** — edge cases or clarifications that don't fit in the one-liner.

---

- [`./instructions/creating-instructions.agent.md`](./creating-instructions.agent.md) — create, update and wire up instructions, skills and IDE wrappers.
  + Keywords: create instruction, update instruction, new instruction, add skill, instruction catalog, prompt file, wrapper
  + Target: `instructions/**`, `.github/prompts/*.prompt.md`

- [`./instructions/fetch-jira-issues.agent.md`](./fetch-jira-issues.agent.md) — fetch Jira issues from a CSV export or the REST API and format them into normalised issue records.
  + Keywords: fetch issues, Jira API, Jira CSV, export, parse CSV, issue data, normalise issues, JQL
  + Target: `project-jira-automation/scripts/*.py`, `project-jira-automation/data/*.csv`
  + Exceptions: CSV is the default source; the API is used only when credentials are configured.

- [`./instructions/update-confluence-status.agent.md`](./update-confluence-status.agent.md) — publish a weekly status report to a Confluence page by replacing its status section (dry run by default).
  + Keywords: Confluence, update page, publish status, wiki, status page, project status
  + Target: `reports/status-*.md`
  + Exceptions: requires a report from `create-status-report.agent.md`; no Confluence code exists yet.

- [`./instructions/generate-jql-queries.agent.md`](./generate-jql-queries.agent.md) — generate read-only JQL queries for common reporting needs (completed, planned, carry-over, blocked, overdue, by team).
  + Keywords: JQL, Jira query, filter, search issues, completed stories, overdue, blocked, carry-over
  + Target: `project-jira-automation/**`
  + Exceptions: custom field ids (Team, story points) are never guessed; ask the user.

- [`./instructions/summarize-sprint-data.agent.md`](./summarize-sprint-data.agent.md) — process sprint issue data into a per-sprint summary table (planned, added, completed, carry-over, points).
  + Keywords: sprint summary, summary table, sprint metrics, completed vs planned, carry-over, velocity table
  + Target: `reports/sprint-summary-*.md`
  + Exceptions: table only; forecast and HTML output are in `generate-sprint-report.agent.md`.

- [`./instructions/generate-sprint-report.agent.md`](./generate-sprint-report.agent.md) — turn a Jira CSV export into an HTML sprint delivery report with metrics and a forecast (`client` or `internal` mode).
  + Keywords: sprint report, sprint delivery report, Jira CSV, velocity, forecast, carry-over, client report, internal report
  + Target: `project-jira-automation/**`, `reports/sprint_report_*.html`
  + Exceptions: the `sprint_report` tool is not built yet; see `project-jira-automation/backlog.md`.

- [`./instructions/calculate-compound-interest.agent.md`](./calculate-compound-interest.agent.md) — calculate compound interest (final amount and interest earned) with `tools/compound_interest.py` and present the result.
  + Keywords: compound interest, interest earned, future value, investment growth, compounding, principal, annual rate
  + Target: `tools/compound_interest.py`
  + Exceptions: no simple interest, recurring contributions or variable rates.

- [`./instructions/use-metric-calc.agent.md`](./use-metric-calc.agent.md) — run `tools/sprint-metrics.py` to calculate per-sprint metrics (completed, planned vs added, carry-over, points, per-team split) from a Jira CSV.
  + Keywords: sprint metrics, planned vs added, completed vs planned, carry-over, story points, per-team split, sprint table
  + Target: `tools/sprint-metrics.py`, `data/export.csv`
  + Exceptions: needs a config with the sprint list; no forecast (`tools/delivery-forecast.py`) or HTML output.

- [`./instructions/use-delivery-forecast.agent.md`](./use-delivery-forecast.agent.md) — run `tools/delivery-forecast.py` to forecast velocity, sprints needed, projected finish and an On track / At risk status with a banner reason.
  + Keywords: forecast, on track, at risk, velocity, projected finish, deadline, sprints needed, remaining scope
  + Target: `tools/delivery-forecast.py`
  + Exceptions: needs total scope and deadline from the user or config; completed counts come from `use-metric-calc.agent.md`.

- [`./instructions/create-status-report.agent.md`](./create-status-report.agent.md) — generate a concise weekly status report (accomplishments, blockers, next week).
  + Keywords: status report, weekly status, weekly report, team update, accomplishments, blockers
  + Target: `reports/*.md`
  + Exceptions: save the report as `reports/status-<YYYY-MM-DD>.md`.
