"""
O*NET Data Cleaning and Processing Script.
Loads raw Step 2 JSON files, applies strict importance/frequency filtering rules,
flattens nested variables, and outputs minimal structured schemas.
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
logger = logging.getLogger("OnetCleaner")


def filter_and_map_elements(raw_items: list[dict[str, Any]], expected_scale: str) -> list[dict[str, Any]]:
    """
    Filters core rating elements by scale, suppression, and relevance flags.
    Maps results to: element_id, element_name, data_value.
    """
    cleaned = []
    for item in raw_items:
        # 1. Extract scale and suppression properties (defensive defaults for Web Services)
        scale_id = item.get("scale_id", expected_scale)
        suppress = item.get("recommend_suppress", "N")
        not_relevant = item.get("not_relevant", "N")

        # 2. Apply strict filter checks
        if scale_id != expected_scale:
            continue
        if suppress == "Y":
            continue
        if not_relevant == "Y":
            continue

        # Determine dynamic O*NET value key (importance, context/frequency, or interest)
        data_value = item.get("importance")
        if data_value is None:
            data_value = item.get("context")
        if data_value is None:
            data_value = item.get("occupational_interest")
        if data_value is None:
            data_value = item.get("data_value", 0)

        cleaned.append(
            {
                "element_id": item.get("id", item.get("element_id", "N/A")),
                "element_name": item.get("name", item.get("element_name", "N/A")),
                "data_value": data_value,
            }
        )
    return cleaned


def clean_occupation_profile(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Applies strict data cleaning, category filtering, and variable flattening
    to assemble a highly minimal, compliant Step 3 JSON object.
    """
    code = raw_data.get("code", "Unknown")
    title = raw_data.get("title", "Unknown")

    cleaned = {
        "code": code,
        "title": title,
    }

    # 1. abilities, skills, knowledge, work_activities, work_styles (Expect 'IM')
    for domain in ["abilities", "skills", "knowledge", "work_activities", "work_styles"]:
        cleaned[domain] = filter_and_map_elements(raw_data.get(domain, []), "IM")

    # 2. work_context (Expect 'FR')
    cleaned["work_context"] = filter_and_map_elements(raw_data.get("work_context", []), "FR")

    # 3. interests (Expect 'RI')
    cleaned["interests"] = filter_and_map_elements(raw_data.get("interests", []), "RI")

    # 4. education (Extract: element_name, data_value)
    education_cleaned = []
    for item in raw_data.get("education", []):
        education_cleaned.append(
            {
                "element_name": item.get("title", item.get("element_name", "N/A")),
                "data_value": item.get("percentage_of_respondents", item.get("data_value", 0)),
            }
        )
    cleaned["education"] = education_cleaned

    # 5. job_zone (Extract: job_zone integer)
    job_zone_raw = raw_data.get("job_zone", {})
    job_zone_code = job_zone_raw.get("code", 0) if isinstance(job_zone_raw, dict) else 0
    cleaned["job_zone"] = {"job_zone": int(job_zone_code)}

    # 6. tasks (Extract: task text)
    tasks_cleaned = []
    for item in raw_data.get("tasks", []):
        tasks_cleaned.append(
            {
                "task": item.get("title", item.get("task", "N/A")),
            }
        )
    cleaned["tasks"] = tasks_cleaned

    # 7. technology_skills (Extract: workplace_example, hot_technology, in_demand)
    tech_cleaned = []
    for category in raw_data.get("technology_skills", []):
        # We parse both 'example' and 'example_more' lists inside the nested categories
        examples = category.get("example", [])
        if not isinstance(examples, list):
            examples = []
        examples_more = category.get("example_more", [])
        if not isinstance(examples_more, list):
            examples_more = []

        all_examples = examples + examples_more
        for ex in all_examples:
            tech_cleaned.append(
                {
                    "workplace_example": ex.get("title", "N/A"),
                    "hot_technology": ex.get("hot_technology", False),
                    "in_demand": ex.get("in_demand", False),
                }
            )
    cleaned["technology_skills"] = tech_cleaned

    return cleaned


def main() -> None:
    data_dir = pathlib.Path("data")
    raw_files = sorted(list(data_dir.glob("step2_raw_*.json")))

    if not raw_files:
        logger.error("No Step 2 raw files (step2_raw_*.json) found in data directory! Aborting.")
        sys.exit(1)

    logger.info("Starting raw dataset cleaning for %d occupations...", len(raw_files))

    success_count = 0
    for file_path in raw_files:
        logger.info("Cleaning file: %s", file_path.name)
        try:
            with open(file_path, encoding="utf-8") as f:
                raw_data = json.load(f)

            cleaned_profile = clean_occupation_profile(raw_data)

            # Save the clean object as step3_clean_{code}.json
            code = raw_data.get("code")
            out_filename = f"step3_clean_{code}.json"
            out_path = data_dir / out_filename

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_profile, f, indent=2, sort_keys=True, ensure_ascii=False)

            logger.info("  Cleaned data saved to: %s", out_path)
            success_count += 1
        except Exception as e:
            logger.error("  [ERROR] Failed to clean data for %s: %s", file_path.name, e)

    print("\n==========================================================")
    print("O*NET Step 3 Data Cleaning Summary")
    print("==========================================================")
    print(f"Successfully Processed: {success_count}/{len(raw_files)} files.")
    print("==========================================================")

    if success_count != len(raw_files):
        sys.exit(1)

    print("Step 3 complete. Cleaned data saved in data/step3_clean_*.json")


if __name__ == "__main__":
    main()
