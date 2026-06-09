"""
O*NET Data Normalization Script.
Loads Step 3 Clean JSON files, scales numeric attributes to a uniform [0, 1] range,
and outputs standardized tabular schemas for downstream modeling.
"""

import json
import logging
import pathlib
import sys
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("OnetNormalizer")


def normalize_profile(clean_data: dict[str, Any]) -> dict[str, Any]:
    """
    Applies strict min-max scaling to numeric ratings, converting 0-100 domains
    and 1-5 Job Zones into a uniform 0-1 float range.
    """
    code = clean_data.get("code", "Unknown")
    title = clean_data.get("title", "Unknown")

    normalized = {
        "code": code,
        "title": title,
    }

    # 1. Normalize 0-100 domains: normalized = data_value / 100.0
    domains_100 = [
        "abilities",
        "skills",
        "knowledge",
        "work_activities",
        "work_context",
        "work_styles",
        "interests",
        "education",
    ]

    for domain in domains_100:
        norm_items = []
        for item in clean_data.get(domain, []):
            norm_item = item.copy()
            raw_value = item.get("data_value", 0)
            # Safe float scaling rounded to 4 decimal places
            norm_item["data_value"] = round(float(raw_value) / 100.0, 4)
            norm_items.append(norm_item)
        normalized[domain] = norm_items

    # 2. Normalize 1-5 Job Zone: normalized = (job_zone - 1.0) / 4.0
    jz_raw = clean_data.get("job_zone", {})
    raw_zone = jz_raw.get("job_zone", 0)

    if raw_zone > 0:
        norm_zone = round((float(raw_zone) - 1.0) / 4.0, 4)
    else:
        norm_zone = 0.0

    normalized["job_zone"] = {"job_zone": norm_zone}

    # 3. Maintain non-numeric domains completely unchanged
    normalized["tasks"] = clean_data.get("tasks", [])
    normalized["technology_skills"] = clean_data.get("technology_skills", [])

    return normalized


def main() -> None:
    data_dir = pathlib.Path("data")
    clean_files = sorted(list(data_dir.glob("step3_clean_*.json")))

    if not clean_files:
        logger.error("No Step 3 clean files (step3_clean_*.json) found in data directory! Aborting.")
        sys.exit(1)

    logger.info("Starting dataset normalization for %d occupations...", len(clean_files))

    success_count = 0
    for file_path in clean_files:
        logger.info("Normalizing file: %s", file_path.name)
        try:
            with open(file_path, encoding="utf-8") as f:
                clean_data = json.load(f)

            normalized_profile = normalize_profile(clean_data)

            # Save the normalized object as step4_normal_{code}.json
            code = clean_data.get("code")
            out_filename = f"step4_normal_{code}.json"
            out_path = data_dir / out_filename

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(normalized_profile, f, indent=2, sort_keys=True, ensure_ascii=False)

            logger.info("  Normalized data saved to: %s", out_path)
            success_count += 1
        except Exception as e:
            logger.error("  [ERROR] Failed to normalize data for %s: %s", file_path.name, e)

    print("\n==========================================================")
    print("O*NET Step 4 Data Normalization Summary")
    print("==========================================================")
    print(f"Successfully Processed: {success_count}/{len(clean_files)} files.")
    print("==========================================================")

    if success_count != len(clean_files):
        sys.exit(1)

    print("Step 4 complete. Normalized data saved in data/step4_normal_*.json")


if __name__ == "__main__":
    main()
