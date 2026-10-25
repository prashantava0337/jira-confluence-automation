import csv
import json
from pathlib import Path


def csv_to_json(csv_path, json_path=None, indent=2):
    """Read a CSV file and return its rows as a JSON string.

    Each row becomes an object keyed by the CSV header. If json_path is given,
    the JSON is also written to that file.
    """
    with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    json_text = json.dumps(rows, indent=indent, ensure_ascii=False)

    if json_path is not None:
        Path(json_path).write_text(json_text, encoding="utf-8")

    return json_text


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.exit("Usage: python csv_to_json.py <input.csv> [output.json]")

    result = csv_to_json(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    if len(sys.argv) < 3:
        print(result)
