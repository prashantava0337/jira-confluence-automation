# Module 08 Completion Report

## Tracked Files
```text
.env.example
.gitignore
PROJECT_IDEAS.md
README.md
SPRINT_DASHBOARD_REQUIREMENTS.md
data/notes.md
data/sample_sprint.csv
data/sprint_config.json
project_spec.md
scripts/build_dashboard.py
scripts/generate_report.py
```

## Spec Commit History
```text
e5287e5 Add Jira automation scripts, sprint dashboard and project specification
```

## project_spec.md Contents
````markdown
# Technical Specification: Sprint Delivery Report

## 1. Overview
A command-line tool that reads a Jira CSV export and produces an HTML report on the number of stories each sprint completed. It also forecasts whether the contractual delivery date will be met.

- **User:** Delivery Manager of a 35-person team on a fixed-price project.
- **Primary question:** how many stories did we complete per sprint, and will we finish on time?
- **Readers:** the Delivery Manager, plus the client and senior management.

## 2. Confirmed requirements

| Area | Decision |
|---|---|
| Jira instance | `https://jiraeu.epam.com` (self-hosted) |
| Project | `EPMCDMETST` |
| Teams | Several teams share one board; a story's team comes from the Jira **Team** field |
| Story | Issue type **Story** only |
| Completed | Status is **Done**, **Resolved** or **Closed** |
| Sprint length | 2 weeks |
| History | Last 6 sprints plus the current sprint |
| Sprint attribution | A completed story is counted in the **last sprint it belongs to** |
| Data source | CSV export from Jira (API tokens are not available) |
| Data refresh | **Daily**, see section 5 |
| Form | Python command-line tool producing a static HTML report |
| Forecast unit | Story count |
| Contract deadline | 2027-02-27 |
| Remaining scope | Total story count typed into a config file |
| Forecast result | Whether the contract date will be met: on track or at risk |

### Metrics
1. **Stories completed** per sprint, as a total and by team.
2. **Story points completed** per sprint.
3. **Planned vs completed** per sprint.
4. **Carry-over stories:** stories in a sprint that were not done and moved to the next sprint.
5. **Stories added mid-sprint.**
6. **Delivery forecast:** on track or at risk against the contract date.

## 3. Report modes
The answers contain two requirements that appear to conflict:
- You asked for a **breakdown by team**.
- You asked that a client-facing report show **totals only, with no team names**.

The tool therefore produces two outputs from the same data. Please confirm this is what you intend.

| Mode | Content | Intended reader |
|---|---|---|
| `internal` | Totals plus a breakdown by team | Delivery Manager |
| `client` | Totals only; no team names, individual names or ticket text | Client, senior management |

The default is `client`, so the safe output is produced unless `--mode internal` is requested.

## 4. Inputs

### 4.1 Jira CSV export
Export with a filter such as `project = EPMCDMETST AND issuetype = Story`, with all required columns included.

| Field | Default column name(s) | Used for |
|---|---|---|
| Key | `Issue key` | Identity |
| Issue type | `Issue Type` | Filter to Story |
| Status | `Status` | Completed or not |
| Team | `Custom field (Team)`, `Team` | Team breakdown |
| Sprint | `Sprint` (several columns) | Sprint attribution and carry-over |
| Story points | `Custom field (Story point estimate)` | Points metric |
| Created | `Created` | Mid-sprint additions |
| Resolved | `Resolved` | Dates for reconciliation |

Jira repeats the `Sprint` column once per sprint a story has belonged to. The parser must read every one of them.

### 4.2 Config file (`config/project_config.json`)
- Sprint list: name, start date and end date for the last 6 sprints and the current one. The CSV has no sprint dates.
- Contract deadline: `2027-02-27`.
- Total scope: total story count for the contract.
- Column name mapping, completed-status list and date formats.

## 5. Data refresh

**Frequency: daily.** The report must reflect the previous working day's Jira data at the start of each working day.

### 5.1 Workflow
1. Export the CSV from Jira once per working day, saved to a fixed path: `data/export.csv`.
2. Run the report command. It regenerates the HTML from the latest CSV.
3. Share the new report, replacing the previous day's.

Because API tokens are not allowed, step 1 stays manual. The CSV export is the only part of the refresh that needs a person.

### 5.2 Requirements
- **Freshness check:** the report shows the CSV's last-modified date as "Data as of". A warning appears if the file is older than 1 day, or older than 3 days over a weekend.
- **Repeatable runs:** running the command again with the same CSV gives the same report. Reports are named by date, so one run per day never overwrites an earlier day's report.
- **Current sprint:** the in-progress sprint is labelled as in progress, and its numbers change daily until the sprint ends.
- **Missed days:** if a daily export is skipped, the next run still produces a correct report from the newer CSV. The report never depends on earlier runs; the history snapshots in 5.3 are for trend viewing only.
- **Optional scheduling:** a scheduled job, such as cron or launchd, can run the report command each morning against `data/export.csv`. It still depends on a fresh CSV being placed there, so the freshness warning matters.

### 5.3 Daily history
Each run saves a small snapshot of the key numbers to `data/history/<date>.json`: stories completed, planned, added, carried over and the forecast result. This lets the manager see how the forecast changed day to day. It also makes mid-sprint additions more accurate for sprints observed from the day they start onwards.

## 6. Calculation rules

- **Sprint completed:** each story in a Done status is counted once, in the **last** sprint listed for it.
- **Carry-over:** a story that appears in sprint N and also in a later sprint was carried over from sprint N. The count is per sprint it left.
- **Planned:** stories in the sprint that were created on or before its start date.
- **Added mid-sprint:** stories in the sprint that were created after its start date.
- **Completed vs planned:** completed stories divided by planned plus added stories, shown separately so the sprint's scope change is visible.
- **Forecast, with these assumptions that need confirming:**
  - Velocity is the average stories completed per sprint over the last 6 completed sprints.
  - Remaining = total scope in the config − all stories completed to date.
  - Sprints needed = remaining ÷ velocity, rounded up.
  - Projected finish = end of the current sprint + (sprints needed × 14 days).
  - Status is **On track** if the projected finish is on or before `2027-02-27`, otherwise **At risk**.

## 7. Output

### 7.1 HTML report
A single self-contained file, with inline CSS and SVG and no external resources. It contains:
- A header with the project, generation date, a "Data as of" date and the report mode.
- A forecast banner showing On track or At risk, with the projected finish date and the contract date.
- A table of stories completed per sprint, covering the last 6 sprints plus the current one.
- A bar chart of stories completed per sprint.
- Planned vs completed, carry-over and mid-sprint additions per sprint.
- A story points completed column.
- In `internal` mode only, a per-team breakdown.
- A notes section listing data warnings, such as unrecognised sprints or stories with no points.

### 7.2 Output location
`reports/sprint_report_<mode>_<date>.html`

## 8. Command-line interface
```bash
python3 -m sprint_report --csv data/export.csv --mode client
python3 -m sprint_report --csv data/export.csv --mode internal --config config/project_config.json
```
The CSV and config paths have defaults. Errors are written to stderr with a non-zero exit code.

## 9. Technical design
- **Language:** Python 3, standard library only.
- **Modules:** `csv_loader` (parsing and column mapping), `metrics` (calculations), `forecast`, `history` (daily snapshots), `render_html`, `cli`.
- **Existing code:** reuse the CSV parsing and date handling in [`scripts/build_dashboard.py`](scripts/build_dashboard.py), moved into a shared module.
- **Security:** the exported CSV holds ticket content, so it must be ignored by Git. All text is HTML-escaped in the report. No credentials are used.
- **Testing:** unit tests for the calculation rules, using a small anonymised CSV fixture that covers carry-over, mid-sprint additions, repeated Sprint columns and an empty sprint.

## 10. Acceptance criteria
You said success means "the report is ready and you can use it." I have made that measurable, so please confirm:
1. One command produces the HTML report from a real Jira export.
2. For at least one past sprint, stories completed match the count in Jira's own sprint report.
3. The `client` report contains no team names, individual names or ticket text.
4. The forecast banner clearly shows On track or At risk.
5. Data problems appear as warnings in the report rather than being silently ignored.
6. Running the command on consecutive days produces a new dated report each time. The report shows a "Data as of" date and warns when the CSV is stale.

## 11. Limitations
- A CSV has no change history, so **mid-sprint additions** are estimated from creation dates. A story moved into a sprint later cannot be detected.
- **Stories removed from a sprint** are not detectable.
- Forecast accuracy depends on the total scope figure in the config, which is maintained by hand.
- Results are only as current as the last export. With a daily refresh, the daily CSV export is a manual step that someone has to remember.

## 12. Open questions
1. How many teams are there, and do any stories have no Team value?
2. Should the forecast be more cautious by using a lower velocity, such as the worst of the last 3 sprints?
3. Is "At risk" only a late projected date, or should there be a warning band, such as within one sprint?
4. What are the real CSV column names and date format? An export header row would settle this.
5. Does the client report need the sprint names, or only sprint numbers?
6. Should the sprint list in the config be replaced by reading sprint dates automatically once API access is available?

## 13. Future work
- Replace the CSV with a live Jira API loader once Personal Access Tokens are allowed. The loader interface should make this a drop-in change.
- Fully automatic daily refresh without a manual CSV export, once API access is available.
- Export to Excel or PDF.
````
