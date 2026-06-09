"""
Script to save the five target O*NET-SOC codes to a dynamically dated JSON file
conforming to PEP-8 and strict workspace standards.
"""

import datetime
import json
import pathlib


def main() -> None:
    # Exactly five O*NET-SOC codes
    soc_codes = [
        "13-2072.00",
        "11-3031.00",
        "11-1021.00",
        "15-2031.00",
        "41-3091.00",
    ]

    # Generate today's date in YYYY-MM-DD format
    today_str = datetime.date.today().isoformat()
    filename = f"step1_codes_{today_str}.json"
    target_path = pathlib.Path(filename)

    # Write the list as a JSON array
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(soc_codes, f, indent=2)

    # Print confirmation message
    print(f"Saved codes to {filename}")


if __name__ == "__main__":
    main()
