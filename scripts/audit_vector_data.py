"""
O*NET Vector Data Auditor.
Loads step5_vector_*.json files and prints clean structural summaries with dense vector validation.
"""

import json
import pathlib


def main():
    for code in ["11-1021.00", "41-3091.00"]:
        try:
            filepath = f"data/step5_vector_{code}.json"
            path = pathlib.Path(filepath)
            if not path.exists():
                print(f"File not found: {filepath}")
                continue

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            vector = data.get("vector", [])
            feature_names = data.get("feature_names", [])

            print(f"=== Vector Profile: {data.get('title')} ({code}) ===")
            print(f"  * Dense Vector Length:     {len(vector)} features")
            print(f"  * Master Schema Length:    {len(feature_names)} features")

            # Check that both lists match in size
            assert len(vector) == len(feature_names), "Length mismatch between vector and features!"

            # Identify non-zero indices and values (PEP 618 explicit strict length matching)
            non_zero_elements = [(feat, val) for feat, val in zip(feature_names, vector, strict=True) if val > 0.0]
            print(f"  * Non-Zero Dimensions Count: {len(non_zero_elements)} / {len(vector)}")

            print("  * Sample Non-Zero Vector Dimensions:")
            for feat, val in non_zero_elements[:5]:
                print(f"    - {feat}: {val}")

            # Audit the last element (which should be job_zone)
            print(f"  * Final Dimension check: {feature_names[-1]} = {vector[-1]}")
            print()
        except Exception as e:
            print(f"Error auditing {code}: {e}\n")


if __name__ == "__main__":
    main()
