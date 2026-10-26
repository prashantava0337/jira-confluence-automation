#!/usr/bin/env python3
"""Calculate compound interest: A = P * (1 + r/n) ** (n * t)."""

import argparse


def compound_interest(principal: float, rate: float, compounds: int, years: float) -> tuple[float, float]:
    """Return (final_amount, interest_earned). `rate` is a percentage (e.g. 5 for 5%)."""
    amount = principal * (1 + rate / 100 / compounds) ** (compounds * years)
    return amount, amount - principal


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must not be negative")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate compound interest.")
    parser.add_argument("principal", type=non_negative_float, help="initial amount invested")
    parser.add_argument("rate", type=non_negative_float, help="annual interest rate in percent (e.g. 5 for 5%%)")
    parser.add_argument("compounds", type=positive_int, help="number of times interest compounds per year")
    parser.add_argument("years", type=non_negative_float, help="total number of years")
    args = parser.parse_args()

    amount, interest = compound_interest(args.principal, args.rate, args.compounds, args.years)
    print(f"Final amount:    {amount:,.2f}")
    print(f"Interest earned: {interest:,.2f}")


if __name__ == "__main__":
    main()
