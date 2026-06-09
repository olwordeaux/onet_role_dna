"""
O*NET Cleaned Data Auditor.
Loads step3_clean_*.json files and prints clean structural summaries.
"""

import json
import pathlib


def main():
    for code in ["11-1021.00", "41-3091.00"]:
        try:
            filepath = f"data/step3_clean_{code}.json"
            path = pathlib.Path(filepath)
            if not path.exists():
                print(f"File not found: {filepath}")
                continue

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            print(f"=== Cleaned Profile: {data.get('title')} ({code}) ===")
            print(f"  * JSON Keys Present: {list(data.keys())}")
            print(f"  * Job Zone Metadata: {data.get('job_zone')}")

            # Audit a few fields to confirm filtering and flat variable mapping
            for key in ["abilities", "work_context", "work_styles", "tasks", "technology_skills"]:
                val = data.get(key)
                if isinstance(val, list):
                    count = len(val)
                    sample = val[0] if count > 0 else "Empty List (Missing Domain)"
                    print(f"  * {key.upper()} (Total Records: {count}):")
                    print(f"    - Sample Record: {sample}")
            print()
        except Exception as e:
            print(f"Error auditing {code}: {e}\n")


if __name__ == "__main__":
    main()
