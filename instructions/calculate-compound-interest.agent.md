- Purpose: calculate compound interest with `./tools/compound_interest.py` and report the final amount and interest earned.
- When to use:
  + The user asks for compound interest, future value of a deposit/investment, or interest earned over time with a fixed rate.
  + Do not use for simple interest, recurring contributions, variable rates, taxes or inflation; say the tool does not cover them.
- Input: four positional arguments, in this order
  + `principal`: initial amount, number `>= 0`.
  + `rate`: annual rate in **percent** (`5` means 5%, not `0.05`), number `>= 0`.
  + `compounds`: compounding periods per year, integer `> 0` (1 annual, 2 semi-annual, 4 quarterly, 12 monthly, 365 daily).
  + `years`: total duration in years, number `>= 0`; decimals allowed (`0.5` = 6 months).
- Step 1, collect inputs:
  + Ask the user for any missing value; never guess the rate or compounding frequency.
  + Convert units before calling: months to years (`months / 12`), rate given as a fraction to percent.
  + Strip currency symbols and thousands separators from numbers.
- Step 2, run:
  + Command: `python3 tools/compound_interest.py <principal> <rate> <compounds> <years>`
  + Example: `python3 tools/compound_interest.py 1000 5 12 10`
  + Run from the workspace root; Python 3.9+, standard library only.
- Step 3, handle errors:
  + Exit code `2` means invalid arguments (negative value, `compounds` of 0, non-numeric input); fix the input or ask the user, then rerun.
  + Do not compute the result by hand if the tool fails.
- Output of the tool, two lines, rounded to 2 decimals with thousands separators:
  + `Final amount:    1,647.01`
  + `Interest earned: 647.01`
- Present results:
  + Start with the answer: final amount and interest earned.
  + Restate the inputs used (principal, rate, compounding frequency, years) so assumptions are visible.
  + Use the currency the user gave; if none, show plain numbers.
  + Keep the tool's 2-decimal rounding; do not re-round or recompute.
  + For several scenarios, use a table with one row per scenario: principal, rate, compounds/year, years, final amount, interest earned.
  + Example: "Investing 1,000 at 5% compounded monthly for 10 years grows to 1,647.01, earning 647.01 in interest."
- Constraint: formula is `A = P * (1 + r/n) ** (n * t)`; interest earned is `A - P`.
- Constraint: the output is an estimate; do not present it as financial advice.
