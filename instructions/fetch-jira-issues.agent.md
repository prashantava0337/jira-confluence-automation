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
