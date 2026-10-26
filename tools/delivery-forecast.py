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
