---
description: Generate a concise weekly status report in Markdown with accomplishments, blockers and next week's plan.
---

# Create Weekly Status Report

Generate a weekly status report from the work details the user provides. Do not invent facts; if information for a section is missing, write `- None reported`.

## Format
- Output Markdown only.
- Use a title line: `# Weekly Status Report: <week or date range>`.
- Use exactly three `##` sections, in this order:
  1. `## Accomplishments`
  2. `## Blockers`
  3. `## Next Week`
- Under each section, use bullet points only. No paragraphs, tables or numbered lists.

## Section content
- **Accomplishments:** completed work with concrete outcomes, deliverables or metrics.
- **Blockers:** open issues, dependencies or risks. State the impact and the owner or required action.
- **Next Week:** planned priorities, with deadlines and dependencies where known.

## Constraints
- Maximum 20 lines in total, counting the title, headings and bullets (blank lines excluded).
- One idea per bullet, one line per bullet.
- Professional tone, written in the third person or as neutral statements.
- No fluff: omit filler, hedging and promotional words such as "very", "really", "great", "exciting", "just", "hopefully", "significant progress".
- Prefer specifics (names, numbers, dates) over general statements.

## Example
```markdown
# Weekly Status Report: 20–24 Oct

## Accomplishments
- Delivered CSV loader; 14 unit tests passing.
- Merged forecast module; velocity calculation verified against sprint data.

## Blockers
- Jira export header row not provided; blocks column mapping. Owner: Delivery Manager.

## Next Week
- Implement HTML renderer and client-mode privacy checks by 30 Oct.
- Run acceptance check against a real Jira export.
```
