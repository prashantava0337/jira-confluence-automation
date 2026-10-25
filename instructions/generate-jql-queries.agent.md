- Purpose: generate valid, read-only JQL queries for common reporting needs, so they can be pasted into Jira or used by `./instructions/fetch-jira-issues.agent.md`.
- Input: reporting need
  + Free text (for example "stories completed last sprint") or a name from the catalog below.
  + Optional parameters: `project` (default `EPMCDMETST`), `issue_type` (default `Story`), `sprint` (name or `current`), `team`, `days`, `from` / `to` dates in `YYYY-MM-DD`.
- Input: config (`config/project_config.json` or `data/sprint_config.json`)
  + `completed_statuses` (default Done, Resolved, Closed), sprint names and dates, Jira base URL (default `https://jiraeu.epam.com`).
  + Custom field ids: `Team` (`cf[<id>]`) and story points. Ask the user for the id; never guess it.
- Catalog of common needs
  + Completed in sprint: `project = P AND issuetype = Story AND status in (Done, Resolved, Closed) AND sprint = "<name>"`
  + Current sprint, all stories: `project = P AND issuetype = Story AND sprint in openSprints()`
  + Current sprint, not done: `project = P AND issuetype = Story AND sprint in openSprints() AND statusCategory != Done`
  + Resolved in the last N days: `project = P AND issuetype = Story AND resolved >= -<N>d ORDER BY resolved DESC`
  + Planned in sprint (created on or before start): `project = P AND issuetype = Story AND sprint = "<name>" AND created <= "<start>"`
  + Added mid-sprint (created after start): `project = P AND issuetype = Story AND sprint = "<name>" AND created > "<start>"`
  + Carry-over candidates: `project = P AND issuetype = Story AND sprint in closedSprints() AND sprint in openSprints() AND statusCategory != Done`
  + Blocked: `project = P AND (labels = blocked OR status ~ "block") AND statusCategory != Done`
  + Overdue: `project = P AND duedate < now() AND statusCategory != Done ORDER BY duedate ASC`
  + Stale (no update in N days): `project = P AND statusCategory != Done AND updated <= -<N>d ORDER BY updated ASC`
  + Missing story points: `project = P AND issuetype = Story AND "Story Points" is EMPTY`
  + Missing team: `project = P AND issuetype = Story AND cf[<team_id>] is EMPTY`
  + By team: add `AND cf[<team_id>] = "<team>"` to any query above.
  + Last 6 sprints: list the sprint names from config in `sprint in ("<s1>", …, "<s6>")`; there is no JQL function for "last N closed sprints".
- Step 1, interpret the request:
  + Match the need to a catalog entry; if none matches, compose one from the same clauses.
  + If a required parameter is missing (sprint name, team field id, date), ask the user.
- Step 2, fill in parameters:
  + Replace `P`, names and dates; double-quote every string value; escape `"` inside values with `\"`.
  + Use relative dates (`-7d`, `startOfWeek()`) only when the user asks for a rolling window; otherwise use absolute `YYYY-MM-DD` so results are reproducible.
  + Take completed statuses from config, not from memory.
- Step 3, assemble and order:
  + Join clauses with `AND`; put `ORDER BY` last, once.
  + One query per need; do not combine unrelated needs with `OR`.
- Step 4, check before output:
  + Balanced quotes and parentheses; valid operators (`=`, `!=`, `~`, `in`, `is EMPTY`, `>=`).
  + Only fields and functions that exist: `project`, `issuetype`, `status`, `statusCategory`, `sprint`, `created`, `resolved`, `updated`, `duedate`, `labels`, `openSprints()`, `closedSprints()`.
  + No write keywords or bulk-change hints; queries only read.
- Output: one block per query, in this order
  + `Name:` short title.
  + `Purpose:` one line.
  + `JQL:` the query in a fenced code block, on a single line.
  + `Link:` `<base_url>/issues/?jql=<URL-encoded JQL>`, only if the base URL is known.
  + `Notes:` assumptions (for example the Team field id) or approximations (for example "mid-sprint additions are estimated from the created date").
- Output: when saved to a file, use `reports/jql-<YYYY-MM-DD>.md`.
- Constraint: JQL is read-only; never produce queries or steps that create, update, transition or delete issues.
- Constraint: never guess custom field ids, sprint names or team names; ask or take them from config.
- Constraint: scope every query to a project; do not produce instance-wide queries.
- Constraint: no personal data in queries for client-facing material (assignee names, ticket text); filter by team or sprint instead.
- Constraint: mid-sprint additions and carry-over are approximations; JQL cannot see issues removed from a sprint. State this in `Notes:`.
- Constraint: validate against the target instance when possible; JQL functions and custom fields differ between Jira Cloud and Data Center.
- Constraint: deterministic; the same input gives the same query text.
