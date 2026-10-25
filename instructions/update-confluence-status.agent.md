- Purpose: publish a project status report to an existing Confluence page by replacing only the status section, never the whole page.
- Source report: produced by `./instructions/create-status-report.agent.md` (for example `reports/status-<YYYY-MM-DD>.md`). Do not invent or edit its content.
- Input: status report
  + Markdown file: title `# Weekly Status Report: <range>`, then `## Accomplishments`, `## Blockers`, `## Next Week`, each with bullets only.
  + Path from `--report`; default is the newest `reports/status-*.md`.
- Input: target page
  + `CONFLUENCE_BASE_URL`, `CONFLUENCE_PAGE_ID` and auth: `CONFLUENCE_EMAIL` + `CONFLUENCE_API_TOKEN` (Basic) or `CONFLUENCE_PAT` (Bearer). Read from environment variables or `.env`.
  + Optional `CONFLUENCE_SECTION_HEADING`, default `Project Status`; the section is the content under this heading up to the next heading of the same or higher level.
- Input: arguments
  + `--dry-run` (default) prints the new page body and the diff; `--apply` performs the update.
- Step 1, validate the input:
  + Fail with a clear error if the report is missing, empty, has a section other than the three above, or a placeholder such as `<...>` remains.
  + Fail if a required variable is missing; name the variable, never print its value.
- Step 2, fetch the page:
  + `GET <base_url>/rest/api/content/<page_id>?expand=body.storage,version`.
  + Keep `title`, `version.number` and `body.storage.value`.
  + Save the current body to `data/confluence_backup/<page_id>-v<version>.html` before any change.
- Step 3, convert the report to Confluence storage format (XHTML):
  + Title line becomes a paragraph in bold: `<p><strong>…</strong></p>`.
  + Each `##` section becomes `<h3>…</h3>` followed by `<ul><li>…</li></ul>`.
  + Escape `&`, `<`, `>` and quotes in all text.
  + Add a line `Last updated: <YYYY-MM-DD>` using the report date, not the system clock.
- Step 4, replace the section:
  + Find the heading from `CONFLUENCE_SECTION_HEADING` in the page body.
  + Replace its content with the converted report; leave the heading and everything outside the section byte-identical.
  + If the heading is missing, stop with an error; do not append or guess.
  + If the new body equals the current body, report "no changes" and stop.
- Step 5, update the page (only with `--apply`):
  + `PUT <base_url>/rest/api/content/<page_id>` with `id`, `type: page`, `title` (unchanged), `version.number` = current + 1, `body.storage` with `representation: storage`.
  + On HTTP 409 (version conflict), re-fetch once and retry; if it fails again, stop and report.
  + Set a 30 second timeout per request.
- Step 6, verify:
  + Re-fetch the page and confirm the version increased by 1 and the section contains the report text.
- Output: console
  + Dry run: the proposed section as text and a unified diff against the current section.
  + Apply: page title, old and new version numbers, the page URL (`<base_url>/pages/viewpage.action?pageId=<page_id>`) and the backup path.
  + Failure: message to stderr, non-zero exit code, no partial update.
- Output: Confluence page
  + Updated section content in storage format as defined in Step 3; all other content unchanged.
- Constraint: Python 3, standard library only (`urllib`, `json`, `difflib`, `html`).
- Constraint: dry run is the default; never update the page without `--apply`.
- Constraint: update one page and one section only; do not create, delete, move or restore pages, and do not change title, labels or permissions.
- Constraint: never print, log or commit the token, PAT or `Authorization` header; keep `.env` and `data/confluence_backup/` out of git.
- Constraint: do not publish internal-only data (individual names, ticket text) to a client-visible page; ask the user if the page audience is unknown.
- Constraint: the endpoint and authentication method depend on whether the instance is Confluence Cloud or Data Center; verify against the actual instance before the first `--apply`.
- Constraint: deterministic; the same report and page body give the same new body.
