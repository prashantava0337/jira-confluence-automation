#!/usr/bin/env python3
"""Per-sprint delivery metrics from a Jira CSV export.

Metrics per sprint: planned, added, completed, completed vs planned, carry-over
and story points completed. `internal` mode adds a per-team split; `client` mode
never reads team names or ticket keys, so they cannot reach the output.

Rules:
- Only issue type Story is used. A story belongs to every configured sprint in
  its repeated Sprint columns.
- Completed: status in `completed_statuses`, counted once, in the last
  configured sprint listed for the story.
- Planned: created on or before the sprint start date. Added: created after it.
- Completed vs planned: completed / (planned + added), whole percent.
- Carry-over: story is in the sprint and also in a later configured sprint.

Config (JSON): {"sprints": [{"name", "start", "end"}, ...]} with YYYY-MM-DD
dates, ordered and not overlapping. Optional keys: `completed_statuses`,
`date_formats`, `columns` (header-name overrides).
"""

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_COLUMNS = {
    "key": ["Issue key", "Key"],
    "type": ["Issue Type"],
    "status": ["Status"],
    "created": ["Created"],
    "sprint": ["Sprint"],
    "team": ["Custom field (Team)", "Team"],
    "points": ["Custom field (Story point estimate)", "Custom field (Story Points)", "Story Points"],
}
DEFAULT_COMPLETED = ["Done", "Resolved", "Closed"]
DEFAULT_DATE_FORMATS = [
    "%d/%b/%y %I:%M %p",
    "%d/%b/%Y %I:%M %p",
    "%d/%b/%y",
    "%d/%b/%Y",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
]
REQUIRED_COLUMNS = ("key", "status", "sprint", "created")
UNASSIGNED = "Unassigned"
NOTE_ESTIMATE = (
    "Mid-sprint additions are estimated from creation dates; stories removed from a sprint "
    "cannot be detected. A story that spans several sprints is counted in each of them."
)


class DataError(Exception):
    pass


def parse_iso(value, label):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        raise DataError(f"{label}: '{value}' is not a valid YYYY-MM-DD date.") from None


def load_config(path):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise DataError(f"Cannot read config {path}: {error.strerror}.") from None
    except json.JSONDecodeError as error:
        raise DataError(f"Config {path} is not valid JSON: {error}.") from None

    sprints = []
    for index, item in enumerate(raw.get("sprints") or []):
        label = f"config 'sprints[{index}]'"
        for key in ("name", "start", "end"):
            if not str(item.get(key, "")).strip():
                raise DataError(f"{label} is missing '{key}'.")
        start = parse_iso(item["start"], f"{label}.start")
        end = parse_iso(item["end"], f"{label}.end")
        if end < start:
            raise DataError(f"{label}: end is before start.")
        if sprints and start <= sprints[-1]["end"]:
            raise DataError(f"{label}: sprints must be ordered and must not overlap.")
        sprints.append({"name": item["name"].strip(), "start": start, "end": end})
    if not sprints:
        raise DataError("Config key 'sprints' is missing or empty.")
    names = [s["name"].lower() for s in sprints]
    if len(set(names)) != len(names):
        raise DataError("Config key 'sprints' contains duplicate sprint names.")

    columns = {**DEFAULT_COLUMNS, **raw.get("columns", {})}
    return {
        "sprints": sprints,
        "columns": {k: [v] if isinstance(v, str) else list(v) for k, v in columns.items()},
        "completed": {s.strip().lower() for s in raw.get("completed_statuses", DEFAULT_COMPLETED)},
        "date_formats": raw.get("date_formats", DEFAULT_DATE_FORMATS),
    }


def parse_date(value, formats, row_number):
    value = value.strip()
    if not value:
        return None
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise DataError(f"Row {row_number}: unrecognised date '{value}'. Add its format to 'date_formats' in the config.")


def parse_points(value):
    try:
        return float(value)
    except ValueError:
        return None


def read_stories(csv_path, config, internal):
    """Return (stories, warnings). Keys and teams are kept only in internal mode."""
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    except OSError as error:
        raise DataError(f"Cannot read CSV {csv_path}: {error.strerror}.") from None
    if not rows:
        raise DataError(f"{csv_path} is empty.")

    header, data = rows[0], rows[1:]
    columns = {}
    for name, candidates in config["columns"].items():
        wanted = {c.strip().lower() for c in candidates}
        columns[name] = [i for i, h in enumerate(header) if h.strip().lower() in wanted]
    missing = [name for name in REQUIRED_COLUMNS if not columns[name]]
    if missing:
        raise DataError(
            f"Required column(s) {missing} not found. Columns in the CSV: {header}. "
            "Adjust 'columns' in the config."
        )

    warnings = []
    if not columns["type"]:
        warnings.append("No Issue Type column found; every row is treated as a Story.")
    if not columns["points"]:
        warnings.append("No story points column found; points are reported as 0.")
    if internal and not columns["team"]:
        warnings.append(f"No Team column found; all stories are assigned to '{UNASSIGNED}'.")

    def cell(row, name):
        index = columns[name][0] if columns[name] else None
        return row[index].strip() if index is not None and index < len(row) else ""

    sprint_order = {s["name"].lower(): i for i, s in enumerate(config["sprints"])}
    stories, unknown_sprints, no_created = [], set(), 0
    for number, row in enumerate(data, start=2):
        if not any(value.strip() for value in row):
            continue
        if columns["type"] and cell(row, "type").lower() != "story":
            continue
        listed = []
        for i in columns["sprint"]:
            name = row[i].strip() if i < len(row) else ""
            if not name:
                continue
            if name.lower() in sprint_order:
                if sprint_order[name.lower()] not in listed:
                    listed.append(sprint_order[name.lower()])
            else:
                unknown_sprints.add(name)
        created = parse_date(cell(row, "created"), config["date_formats"], number)
        if created is None:
            no_created += 1
        story = {
            "sprints": listed,
            "created": created,
            "done": cell(row, "status").lower() in config["completed"],
            "points": parse_points(cell(row, "points")),
            "key": cell(row, "key") if internal else None,
            "team": (cell(row, "team") or UNASSIGNED) if internal else None,
        }
        stories.append(story)

    if unknown_sprints:
        warnings.append(
            "Sprint names not in the config were ignored: " + ", ".join(sorted(unknown_sprints)) + "."
        )
    if no_created:
        warnings.append(f"Stories with no Created date (counted as planned): {no_created}.")
    if internal:
        no_team = sum(1 for s in stories if s["team"] == UNASSIGNED)
        if no_team and columns["team"]:
            warnings.append(f"Stories with no Team (listed as '{UNASSIGNED}'): {no_team}.")
    return stories, warnings


def percent(completed, scope):
    if scope == 0:
        return None
    return (200 * completed + scope) // (2 * scope)


def sprint_state(sprint, today):
    if sprint["end"] < today:
        return "Closed"
    if sprint["start"] <= today:
        return "In progress"
    return "Planned"


def compute_sprint(stories, index, sprint):
    """Metrics for one sprint; `index` is its position in the config order."""
    planned = added = completed = carry_over = 0
    points = 0.0
    unestimated = 0
    for story in stories:
        if index not in story["sprints"]:
            continue
        if story["created"] is None or story["created"] <= sprint["start"]:
            planned += 1
        else:
            added += 1
        if max(story["sprints"]) > index:
            carry_over += 1
        if story["done"] and story["sprints"][-1] == index:
            completed += 1
            if story["points"] is None:
                unestimated += 1
            else:
                points += story["points"]
    return {
        "planned": planned,
        "added": added,
        "completed": completed,
        "completed_vs_planned": percent(completed, planned + added),
        "carry_over": carry_over,
        "points": points,
        "unestimated": unestimated,
    }


def total_of(rows):
    total = {key: sum(r[key] for r in rows) for key in ("planned", "added", "completed", "carry_over", "points", "unestimated")}
    total["completed_vs_planned"] = percent(total["completed"], total["planned"] + total["added"])
    return total


def select_sprints(sprints, today, last):
    closed = [i for i, s in enumerate(sprints) if s["end"] < today]
    current = [i for i, s in enumerate(sprints) if s["start"] <= today <= s["end"]]
    return (closed[-last:] if last else []) + current


def build_report(stories, config, today, last, internal, warnings):
    sprints = config["sprints"]
    chosen = select_sprints(sprints, today, last)
    rows = []
    for index in chosen:
        sprint = sprints[index]
        rows.append({
            "name": sprint["name"],
            "start": sprint["start"],
            "end": sprint["end"],
            "state": sprint_state(sprint, today),
            **compute_sprint(stories, index, sprint),
        })

    warnings = list(warnings)
    if not rows:
        warnings.append("No closed or in-progress sprints found for the given date.")
    empty = [r["name"] for r in rows if r["planned"] + r["added"] == 0]
    if empty:
        warnings.append("Sprints with no stories: " + ", ".join(empty) + ".")
    total = total_of(rows)
    if total["unestimated"]:
        message = f"Completed stories with no story points (counted as 0): {total['unestimated']}."
        if internal:
            keys = sorted(
                s["key"] for s in stories
                if s["done"] and s["points"] is None and s["sprints"] and s["sprints"][-1] in chosen
            )
            message += " Keys: " + ", ".join(keys) + "."
        warnings.append(message)

    report = {"rows": rows, "total": total, "warnings": warnings, "teams": None}
    if internal:
        teams = {}
        for team in sorted({s["team"] for s in stories}, key=lambda t: (t == UNASSIGNED, t.lower())):
            subset = [s for s in stories if s["team"] == team]
            team_rows = [compute_sprint(subset, i, sprints[i]) for i in chosen]
            teams[team] = {
                "sprints": {sprints[i]["name"]: r for i, r in zip(chosen, team_rows)},
                "total": total_of(team_rows),
            }
        report["teams"] = teams
    return report


def fmt_number(value):
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def fmt_percent(value):
    return "n/a" if value is None else f"{value}%"


def cell_text(text):
    return str(text).replace("|", "\\|")


def render_markdown(report, mode, today):
    lines = [f"# Sprint metrics ({mode}, {today.isoformat()})", ""]
    lines += [
        "| Sprint | Dates | State | Planned | Added | Completed | Completed vs planned | Carry-over | Points |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    def metrics_cells(m):
        return [m["planned"], m["added"], m["completed"], fmt_percent(m["completed_vs_planned"]),
                m["carry_over"], fmt_number(m["points"])]

    for r in report["rows"]:
        cells = [cell_text(r["name"]), f"{r['start']} to {r['end']}", r["state"], *metrics_cells(r)]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    cells = ["**Total**", "", "", *metrics_cells(report["total"])]
    lines.append("| " + " | ".join(str(c) for c in cells) + " |")

    if report["teams"] is not None:
        lines += ["", "## By team", "",
                  "| Team | Planned | Added | Completed | Completed vs planned | Carry-over | Points |",
                  "|---|---|---|---|---|---|---|"]
        for team, data in report["teams"].items():
            cells = [cell_text(team), *metrics_cells(data["total"])]
            lines.append("| " + " | ".join(str(c) for c in cells) + " |")

    lines += ["", NOTE_ESTIMATE]
    if report["warnings"]:
        lines += ["", "## Notes", ""] + [f"- {w}" for w in report["warnings"]]
    return "\n".join(lines) + "\n"


def render_json(report, mode, today):
    def clean(metrics):
        return {k: (int(v) if k == "points" and float(v).is_integer() else v)
                for k, v in metrics.items() if k != "unestimated"}

    payload = {
        "generated": today.isoformat(),
        "mode": mode,
        "sprints": [
            {**clean(r), "name": r["name"], "start": r["start"].isoformat(),
             "end": r["end"].isoformat(), "state": r["state"]}
            for r in report["rows"]
        ],
        "total": clean(report["total"]),
        "note": NOTE_ESTIMATE,
        "warnings": report["warnings"],
    }
    if report["teams"] is not None:
        payload["teams"] = {
            team: {"sprints": {n: clean(m) for n, m in data["sprints"].items()}, "total": clean(data["total"])}
            for team, data in report["teams"].items()
        }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def iso_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid YYYY-MM-DD date") from None


def non_negative_int(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must not be negative")
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Calculate per-sprint metrics from a Jira CSV export.")
    parser.add_argument("--csv", default="data/export.csv", help="Jira CSV export (default: %(default)s)")
    parser.add_argument("--config", default="config/project_config.json",
                        help="JSON config with the sprint list (default: %(default)s)")
    parser.add_argument("--mode", choices=("client", "internal"), default="client",
                        help="client hides team names, ticket keys and team warnings (default: %(default)s)")
    parser.add_argument("--today", type=iso_date, help="reference date YYYY-MM-DD (default: system date)")
    parser.add_argument("--last", type=non_negative_int, default=6,
                        help="number of closed sprints to show, plus the current one (default: %(default)s)")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown",
                        help="output format (default: %(default)s)")
    parser.add_argument("--output", help="write to this file instead of stdout")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    today = args.today or date.today()
    internal = args.mode == "internal"
    try:
        config = load_config(args.config)
        stories, warnings = read_stories(args.csv, config, internal)
        report = build_report(stories, config, today, args.last, internal, warnings)
    except DataError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    render = render_json if args.format == "json" else render_markdown
    output = render(report, args.mode, today)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        print(path)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
