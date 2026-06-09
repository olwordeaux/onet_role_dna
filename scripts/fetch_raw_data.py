"""
O*NET Raw Data Fetcher.
Sequentially downloads all requested details domains for the 5 target codes,
handles retries/backoffs and 404/422s, and compiles raw JSON datasets.
"""

import json
import logging
import os
import pathlib
import sys
import time
from typing import Any

import requests

# Configure logging to output both progress and warning levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("OnetRawFetcher")

BASE_URL = "https://api-v2.onetcenter.org/"

# Target endpoint domain mapping
ENDPOINTS = {
    "abilities": "abilities",
    "skills": "skills",
    "knowledge": "knowledge",
    "work_activities": "work_activities",
    "work_context": "work_context",
    "work_styles": "work_styles",
    "interests": "interests",
    "education": "education",
    "job_zone": "job_zone",
    "tasks": "task_statements",
    "technology_skills": "software_skills",
}


def make_request_with_retry(url: str, headers: dict[str, str], max_retries: int = 3) -> requests.Response:
    """
    Sends a GET request with exponential backoff retries for non-404/422 errors.
    """
    backoff = 1.0
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response
            elif response.status_code in (404, 422):
                # Do not retry on 404 or 422 (they represent structural missing data)
                return response
            else:
                logger.warning(
                    "Request to %s failed with status %d. Attempt %d/%d.",
                    url,
                    response.status_code,
                    attempt + 1,
                    max_retries + 1,
                )
        except requests.RequestException as e:
            logger.warning(
                "Request exception for %s: %s. Attempt %d/%d.",
                url,
                e,
                attempt + 1,
                max_retries + 1,
            )

        if attempt < max_retries:
            time.sleep(backoff)
            backoff *= 2.0

    raise Exception(f"Failed to fetch {url} after {max_retries} retries.")


def extract_payload(res_json: dict[str, Any], domain: str) -> Any:
    """
    Safely extracts the standard list/dictionary payload from raw API JSON response structures.
    """
    # Standard array fields in O*NET responses
    for list_key in ["element", "task", "response", "category", "skills_matched", "example", "example_title"]:
        if list_key in res_json and isinstance(res_json[list_key], list):
            return res_json[list_key]

    # Return raw dict if it represents a structured single object like job_zone
    if domain == "job_zone" and isinstance(res_json, dict):
        return res_json

    return [] if domain != "job_zone" else {}


def main() -> None:
    # 1. Read API key from environment variable
    api_key = os.environ.get("ONET_API_KEY")
    if not api_key:
        logger.error("ONET_API_KEY environment variable not found. Exiting.")
        sys.exit(1)

    headers = {"X-API-Key": api_key}

    soc_codes = [
        "13-2072.00",
        "11-3031.00",
        "11-1021.00",
        "15-2031.00",
        "41-3091.00",
    ]

    data_dir = pathlib.Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    success_codes = []
    failure_codes = []

    logger.info("Beginning raw data pull for %d occupations...", len(soc_codes))

    for code in soc_codes:
        logger.info("Processing occupation: %s", code)
        try:
            # Step A: Fetch base occupation data to get the official title
            base_url = f"{BASE_URL}online/occupations/{code}/"
            base_res = make_request_with_retry(base_url, headers=headers)
            if base_res.status_code in (404, 422):
                logger.error("Occupation %s not found on API (HTTP %d). Skipping.", code, base_res.status_code)
                failure_codes.append(code)
                continue

            base_json = base_res.json()
            title = base_json.get("title", "Unknown Title")
            logger.info("  Official Title: %s", title)

            # Initialize target raw payload object
            combined_object = {
                "code": code,
                "title": title,
            }

            # Step B: Fetch each detail domain sequentially
            for domain, endpoint_name in ENDPOINTS.items():
                detail_url = f"{BASE_URL}online/occupations/{code}/details/{endpoint_name}"
                logger.info("    Fetching domain [%s] from endpoints/%s...", domain, endpoint_name)

                detail_res = make_request_with_retry(detail_url, headers=headers)

                if detail_res.status_code == 200:
                    payload = extract_payload(detail_res.json(), domain)
                    combined_object[domain] = payload
                elif detail_res.status_code in (404, 422):
                    logger.warning(
                        "    [%d MISSING] Domain %s missing for %s. Treating as missing.",
                        detail_res.status_code,
                        domain,
                        code,
                    )
                    combined_object[domain] = [] if domain != "job_zone" else {}
                else:
                    raise Exception(f"Unresolved HTTP status {detail_res.status_code} for {domain}")

                # Enforce the strict 0.5-second rate limit pause rule
                time.sleep(0.5)

            # Step C: Save combined object as step2_raw_{code}.json
            file_name = f"step2_raw_{code}.json"
            target_path = data_dir / file_name
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(combined_object, f, indent=2, sort_keys=True, ensure_ascii=False)

            logger.info("  Successfully compiled and saved raw data to: %s", target_path)
            success_codes.append(code)

        except Exception as e:
            logger.error("  [ERROR] Failed to compile raw data for %s: %s", code, e)
            failure_codes.append(code)

    # Step D: Print audit summary
    print("\n==========================================================")
    print("O*NET Step 2 Fetch Audit Summary")
    print("==========================================================")
    print(f"Total Successes: {len(success_codes)} {success_codes}")
    print(f"Total Failures:  {len(failure_codes)} {failure_codes}")
    print("==========================================================")

    if failure_codes:
        sys.exit(1)

    print("Step 2 complete. Raw data saved in data/step2_raw_*.json")


if __name__ == "__main__":
    main()
