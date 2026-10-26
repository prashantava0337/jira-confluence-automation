# Module 10 Completion Report

## Instruction Files
~~~
instructions/create-status-report.agent.md
instructions/creating-instructions.agent.md
instructions/fetch-jira-issues.agent.md
instructions/generate-jql-queries.agent.md
instructions/generate-sprint-report.agent.md
instructions/main.agent.md
instructions/summarize-sprint-data.agent.md
instructions/update-confluence-status.agent.md
~~~

## main.agent.md Contents
~~~markdown
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

- [`./instructions/create-status-report.agent.md`](./create-status-report.agent.md) — generate a concise weekly status report (accomplishments, blockers, next week).
  + Keywords: status report, weekly status, weekly report, team update, accomplishments, blockers
  + Target: `reports/*.md`
  + Exceptions: save the report as `reports/status-<YYYY-MM-DD>.md`.
~~~

## Sample Instruction
- File: fetch-jira-issues.agent.md
- Contents:
~~~markdown
- Purpose: fetch Jira issue data from a CSV export or the Jira REST API and format it into one normalised list of issue records for downstream reports.
- Source choice:
  + CSV is the default; API tokens are not available for `https://jiraeu.epam.com` (see `./project-jira-automation/project_spec.md`).
  + Use the API only when `JIRA_BASE_URL`, `JIRA_EMAIL` and `JIRA_API_TOKEN` are set; otherwise use the CSV.
  + Reuse the existing code: `fetch_jira_issues` in `./project-jira-automation/scripts/generate_report.py`, `read_issues` in `./project-jira-automation/scripts/build_dashboard.py`.
- Input: CSV file
  + Path from `--csv` (default `data/export.csv`); one row per issue, first row is the header.
  + Encoding `utf-8-sig`; skip fully empty rows.
  + Map columns by header name, case-insensitive, using the `columns` mapping in config. Accepted alternatives: `Custom field (Team)` / `Team`; `Custom field (Story point estimate)` / `Custom field (Story Points)` / `Story Points`.
  + Read **every** repeated `Sprint` column, in order.
  + Required: issue key, status. Optional: summary, issue type, assignee, team, Created, Resolved, story points, Sprint.
- Input: Jira API
  + Credentials and project from environment variables or `.env` (`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT`); see `.env.example`.
  + Query by JQL, for example `project = <JIRA_PROJECT> AND (updated >= -<days>d OR statusCategory != Done) ORDER BY updated DESC`.
  + Request only the needed fields (`summary`, `status`, `assignee`, `priority`, `duedate`, `labels`, `resolutiondate`, plus sprint, team and story points fields).
- Input: config
  + `columns`, `status_groups`, `date_formats`, `completed_statuses`; defaults live in `build_dashboard.py`.
- Step 1, validate the input:
  + CSV: fail with a clear error if the file is empty or unreadable, or a required column is missing; list the columns found and name the config key to adjust.
  + API: fail with a clear error if a credential variable is missing or the request fails (HTTP status, no token in the message).
- Step 2, fetch:
  + CSV: read all rows with `csv.reader`.
  + API: send a `POST` to `<base_url>/rest/api/3/search/jql` with Basic auth, `maxResults: 100`, and follow `nextPageToken` until it is absent.
  + API: stop at 1000 issues and add a warning that results are truncated.
  + API: set a 30 second timeout per request.
- Step 3, normalise each issue:
  + Trim all text; blank `Assignee` becomes `Unassigned`, blank `Team` becomes `Unassigned`.
  + Parse Created and Resolved using the `date_formats` list in order; an unparseable value raises an error naming the value and the config key `date_formats`.
  + Parse story points to a number; blank becomes `None`.
  + Map status to a group: `done` (Done, Closed, Resolved, case-insensitive), `in_progress`, otherwise `todo`. For the API, `statusCategory` may be used as a fallback.
  + Keep sprint names as an ordered list.
- Step 4, filter:
  + Keep only the requested issue type (default `Story`) and, if `sprint_name` is set, only issues in that sprint.
  + Fail if a requested sprint name matches no issues.
- Step 5, collect warnings, do not fail:
  + Missing optional column, missing story points, missing Team, unrecognised sprint name, truncated API results.
- Output: list of issue records, the same shape for CSV and API
  + Fields: `key`, `summary`, `issue_type`, `status`, `group`, `assignee`, `team`, `created`, `resolved`, `due`, `labels`, `points`, `sprints`, `url`.
  + Dates are `datetime.date` in memory and `YYYY-MM-DD` when written out.
  + `url` is `<JIRA_BASE_URL>/browse/<key>` when the base URL is known, otherwise empty.
  + Plus a list of warning strings.
  + Optional file output: JSON with sorted keys at `data/issues.json`; keep it out of git.
- Constraint: Python 3, standard library only (`csv`, `json`, `urllib`, `datetime`).
- Constraint: never print, log or write the API token or the `Authorization` header; never commit `.env`, real CSV exports or `data/issues.json`.
- Constraint: treat `summary`, `assignee` and `team` as internal data; they must not reach a client-facing report.
- Constraint: deterministic; the same input gives the same records in the same order (preserve the source order).
- Constraint: the API request is read-only; do not create, update or transition issues.
- Constraint: the existing API call targets the Jira Cloud v3 endpoint; verify the endpoint and authentication against the self-hosted instance before relying on it.
- Constraint: a bad row never silently changes figures; report it as a warning or fail with an error.
~~~


Create a Python script at tools/ sprint-metrics.py that reads the Jira CSV, including the repeated Sprint columns, and calculates the per-sprint figures. Those are completed (counted once, in the last sprint listed), planned versus added (a story created on the start date counts as planned), completed vs planned, carry-over, story points and the per-team split. Client mode leaves out team names, ticket keys and team-related warnings.  Accept [parameters] as command-line arguments.”