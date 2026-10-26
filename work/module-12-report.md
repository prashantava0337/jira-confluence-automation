# Module 12 Completion Report

## Instruction File
- Filename: use-delivery-forecast.agent.md

~~~markdown
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
~~~

## Script File
- Filename: delivery-forecast.py
- Language: Python

~~~python
#!/usr/bin/env python3
"""Delivery forecast: will the remaining scope be finished by the deadline?

Inputs: stories completed per closed sprint (oldest first), total scope, the end
date of the current sprint and the deadline.

Rules:
- Velocity: `average_last_6` (mean of the last 6 closed sprints, default) or
  `worst_of_last_3` (lowest of the last 3). With less history, all available
  sprints are used and a warning is added.
- Remaining = scope - all completed stories (closed sprints + current sprint).
- Sprints needed = ceil(remaining / velocity), projected finish = sprint end +
  sprints needed * sprint length (default 14 days).
- On track: finish is on or before the deadline minus the warning margin
  (`warning_sprints` * sprint length). At risk: finish is later than that.
  "Tight" At risk: finish is within the margin but not after the deadline.
- Velocity 0 or no history: At risk, no finish date. Remaining <= 0: On track.

All arithmetic uses `fractions.Fraction`, so an exact 6.0 sprints never becomes
7 through float error.
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from fractions import Fraction

METHODS = ("average_last_6", "worst_of_last_3")
FULL_HISTORY = 6
ON_TRACK = "On track"
AT_RISK = "At risk"


@dataclass
class Forecast:
    status: str
    tight: bool
    reason: str
    velocity: Fraction | None
    remaining: int
    sprints_needed: int | None
    projected_finish: date | None
    deadline: date
    warnings: list[str] = field(default_factory=list)

    @property
    def label(self):
        return f"{self.status} \u2013 tight" if self.tight else self.status

    def to_dict(self):
        return {
            "status": self.status,
            "tight": self.tight,
            "label": self.label,
            "reason": self.reason,
            "velocity": None if self.velocity is None else float(round(self.velocity, 2)),
            "velocity_exact": None if self.velocity is None else str(self.velocity),
            "remaining": self.remaining,
            "sprints_needed": self.sprints_needed,
            "projected_finish": None if self.projected_finish is None else self.projected_finish.isoformat(),
            "deadline": self.deadline.isoformat(),
            "warnings": self.warnings,
        }


def velocity_from(completed, method):
    """Exact velocity as a Fraction, or None when there is no history."""
    if method not in METHODS:
        raise ValueError(f"velocity method must be one of {', '.join(METHODS)}.")
    if not completed:
        return None
    if method == "average_last_6":
        window = completed[-6:]
        return Fraction(sum(window), len(window))
    return Fraction(min(completed[-3:]))


def fmt_fraction(value, places=2):
    """Decimal text rounded half up with exact arithmetic, trailing zeros trimmed."""
    scaled = value * 10**places
    rounded = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    text = f"{rounded // 10**places}.{rounded % 10**places:0{places}d}".rstrip("0").rstrip(".")
    return text


def plural(count, singular, many=None):
    return f"{count} {singular if count == 1 else (many or singular + 's')}"


def forecast(completed, scope, sprint_end, deadline, *, current_completed=0,
             method="average_last_6", warning_sprints=0, sprint_days=14):
    """Return a Forecast. `completed` = closed sprints' counts, oldest first."""
    completed = list(completed)
    if any(c < 0 for c in completed) or current_completed < 0:
        raise ValueError("completed counts must not be negative.")
    if scope <= 0:
        raise ValueError("scope must be a positive number of stories.")
    if warning_sprints < 0:
        raise ValueError("warning sprints must not be negative.")
    if sprint_days <= 0:
        raise ValueError("sprint length must be a positive number of days.")

    velocity = velocity_from(completed, method)
    remaining = scope - sum(completed) - current_completed
    warnings = []
    if completed and len(completed) < FULL_HISTORY:
        warnings.append(
            f"Only {plural(len(completed), 'closed sprint')} of history "
            f"({FULL_HISTORY} expected); the forecast is less reliable."
        )

    def result(status, reason, tight=False, needed=None, finish=None):
        return Forecast(status, tight, reason, velocity, remaining, needed, finish, deadline, warnings)

    if remaining <= 0:
        return result(
            ON_TRACK,
            f"On track: all {plural(scope, 'story', 'stories')} in scope are already complete.",
            needed=0,
            finish=sprint_end,
        )
    if velocity is None:
        warnings.append("No closed sprints, so velocity cannot be calculated.")
        return result(
            AT_RISK,
            f"At risk: there is no sprint history to measure velocity, "
            f"so {plural(remaining, 'remaining story', 'remaining stories')} cannot be forecast.",
        )
    if velocity == 0:
        warnings.append("Velocity is 0, so no finish date can be projected.")
        return result(
            AT_RISK,
            f"At risk: velocity is 0 stories per sprint, so "
            f"{plural(remaining, 'remaining story', 'remaining stories')} cannot be forecast to finish.",
        )

    needed = math.ceil(Fraction(remaining) / velocity)
    finish = sprint_end + timedelta(days=needed * sprint_days)
    slack = (deadline - finish).days
    margin = warning_sprints * sprint_days
    basis = (
        f"{plural(remaining, 'story', 'stories')} remaining at {fmt_fraction(velocity)} per sprint "
        f"needs {plural(needed, 'sprint')}, finishing {finish.isoformat()}"
    )

    if slack < 0:
        return result(
            AT_RISK,
            f"At risk: {basis}, {plural(-slack, 'day')} after the deadline of {deadline.isoformat()}.",
            needed=needed, finish=finish,
        )
    if slack < margin:
        when = "on the deadline date" if slack == 0 else f"only {plural(slack, 'day')} before the deadline"
        return result(
            AT_RISK,
            f"At risk: {basis}, {when} of {deadline.isoformat()}, "
            f"inside the {plural(warning_sprints, 'sprint')} warning margin.",
            tight=True, needed=needed, finish=finish,
        )
    return result(
        ON_TRACK,
        f"On track: {basis}, {plural(slack, 'day')} before the deadline of {deadline.isoformat()}.",
        needed=needed, finish=finish,
    )


def iso_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid YYYY-MM-DD date") from None


def count_list(values):
    """Accept `12 15 9` or `12,15,9` (or a mix)."""
    counts = []
    for value in values:
        for part in value.split(","):
            if part.strip():
                try:
                    counts.append(int(part))
                except ValueError:
                    raise argparse.ArgumentTypeError(f"'{part}' is not a whole number") from None
    return counts


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Forecast whether the remaining scope meets the deadline.")
    parser.add_argument("--completed", nargs="*", default=[], metavar="N",
                        help="stories completed per closed sprint, oldest first (space or comma separated)")
    parser.add_argument("--current-completed", type=int, default=0,
                        help="stories already completed in the current sprint (default: %(default)s)")
    parser.add_argument("--scope", type=int, required=True, help="total stories in scope")
    parser.add_argument("--sprint-end", type=iso_date, required=True, help="end date of the current sprint, YYYY-MM-DD")
    parser.add_argument("--deadline", type=iso_date, required=True, help="contract deadline, YYYY-MM-DD")
    parser.add_argument("--velocity-method", choices=METHODS, default="average_last_6",
                        help="default: %(default)s")
    parser.add_argument("--warning-sprints", type=int, default=0,
                        help="sprints of margin before the deadline that count as 'tight' (default: %(default)s)")
    parser.add_argument("--sprint-days", type=int, default=14, help="sprint length in days (default: %(default)s)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="default: %(default)s")
    args = parser.parse_args(argv)
    try:
        args.completed = count_list(args.completed)
    except argparse.ArgumentTypeError as error:
        parser.error(str(error))
    return args


def render_text(result):
    velocity = "n/a" if result.velocity is None else f"{fmt_fraction(result.velocity)} stories per sprint"
    needed = "n/a" if result.sprints_needed is None else str(result.sprints_needed)
    finish = "n/a" if result.projected_finish is None else result.projected_finish.isoformat()
    lines = [
        f"Status: {result.label}",
        f"Reason: {result.reason}",
        f"Velocity: {velocity}",
        f"Remaining: {result.remaining}",
        f"Sprints needed: {needed}",
        f"Projected finish: {finish}",
        f"Deadline: {result.deadline.isoformat()}",
    ]
    lines += [f"Warning: {w}" for w in result.warnings]
    return "\n".join(lines) + "\n"


def main(argv=None):
    args = parse_args(argv)
    try:
        result = forecast(
            args.completed, args.scope, args.sprint_end, args.deadline,
            current_completed=args.current_completed, method=args.velocity_method,
            warning_sprints=args.warning_sprints, sprint_days=args.sprint_days,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if args.format == "json":
        sys.stdout.write(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
~~~

## Script Execution Output
Command: `python3 tools/delivery-forecast.py --help`

~~~text
usage: delivery-forecast.py [-h] [--completed [N ...]]
                            [--current-completed CURRENT_COMPLETED] --scope
                            SCOPE --sprint-end SPRINT_END --deadline DEADLINE
                            [--velocity-method {average_last_6,worst_of_last_3}]
                            [--warning-sprints WARNING_SPRINTS]
                            [--sprint-days SPRINT_DAYS] [--format {text,json}]

Forecast whether the remaining scope meets the deadline.

options:
  -h, --help            show this help message and exit
  --completed [N ...]   stories completed per closed sprint, oldest first
                        (space or comma separated)
  --current-completed CURRENT_COMPLETED
                        stories already completed in the current sprint
                        (default: 0)
  --scope SCOPE         total stories in scope
  --sprint-end SPRINT_END
                        end date of the current sprint, YYYY-MM-DD
  --deadline DEADLINE   contract deadline, YYYY-MM-DD
  --velocity-method {average_last_6,worst_of_last_3}
                        default: average_last_6
  --warning-sprints WARNING_SPRINTS
                        sprints of margin before the deadline that count as
                        'tight' (default: 0)
  --sprint-days SPRINT_DAYS
                        sprint length in days (default: 14)
  --format {text,json}  default: text
~~~
