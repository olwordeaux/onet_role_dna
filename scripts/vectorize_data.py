"""
O*NET Data Vectorization Script.
Gathers all O*NET numeric dimensions across domains, establishes a uniform
global schema, and compiles dense fixed-order feature vectors for machine learning.
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
logger = logging.getLogger("OnetVectorizer")


def build_master_feature_schema(profiles: list[dict[str, Any]]) -> list[str]:
    """
    Builds a unique, lexicographically sorted list of feature identifiers
    representing the union of all dimensions across all profiles.
    """
    all_features = set()
    domains_with_id = [
        "abilities",
        "skills",
        "knowledge",
        "work_activities",
        "work_context",
        "work_styles",
        "interests",
    ]

    for p in profiles:
        # A. Elements with static IDs
        for domain in domains_with_id:
            for item in p.get(domain, []):
                element_id = item.get("element_id")
                if element_id:
                    all_features.add(f"{domain}:{element_id}")

        # B. Education categories (using element_name)
        for item in p.get("education", []):
            el_name = item.get("element_name")
            if el_name:
                all_features.add(f"education:{el_name}")

    # Lexicographically sort all accumulated dimensions
    sorted_features = sorted(list(all_features))

    # Append job_zone to the very end of the feature matrix
    sorted_features.append("job_zone")

    return sorted_features


def vectorize_profile(profile: dict[str, Any], schema: list[str]) -> list[float]:
    """
    Converts a single occupation profile into a dense, fixed-order numeric vector
    representing its complete normalized O*NET taxonomy footprint.
    """
    vector = []

    for feat in schema:
        if feat == "job_zone":
            # Extract job zone rating value
            jz_raw = profile.get("job_zone", {})
            vector.append(float(jz_raw.get("job_zone", 0.0)))
            continue

        domain, el_key = feat.split(":", 1)

        # Handle education dimension lookups
        if domain == "education":
            matched_value = 0.0
            for item in profile.get("education", []):
                if item.get("element_name") == el_key:
                    matched_value = float(item.get("data_value", 0.0))
                    break
            vector.append(matched_value)
            continue

        # Handle standard domain lookup
        matched_value = 0.0
        for item in profile.get(domain, []):
            if item.get("element_id") == el_key:
                matched_value = float(item.get("data_value", 0.0))
                break
        vector.append(matched_value)

    return vector


def main() -> None:
    data_dir = pathlib.Path("data")
    normal_files = sorted(list(data_dir.glob("step4_normal_*.json")))

    if not normal_files:
        logger.error("No Step 4 normalized files found in data/ directory! Aborting.")
        sys.exit(1)

    # 1. Load all normalized profiles into memory
    profiles = []
    for filepath in normal_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                profiles.append(json.load(f))
        except Exception as e:
            logger.error("Failed to read %s: %s", filepath.name, e)
            sys.exit(1)

    # 2. Build the unified dynamic schema
    master_schema = build_master_feature_schema(profiles)
    logger.info(
        "Successfully compiled global feature schema. Total Dimensions: %d",
        len(master_schema),
    )

    # 3. Vectorize and save each profile
    success_count = 0
    for profile in profiles:
        code = profile.get("code")
        title = profile.get("title")
        logger.info("Vectorizing profile: %s (%s)", title, code)

        try:
            dense_vector = vectorize_profile(profile, master_schema)

            output_payload = {
                "code": code,
                "title": title,
                "vector": dense_vector,
                "feature_names": master_schema,
            }

            out_filename = f"step5_vector_{code}.json"
            out_path = data_dir / out_filename

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output_payload, f, indent=2, sort_keys=True, ensure_ascii=False)

            logger.info("  Vector saved to: %s", out_path)
            success_count += 1
        except Exception as e:
            logger.error("  [ERROR] Failed to vectorize profile for %s: %s", code, e)

    print("\n==========================================================")
    print("O*NET Step 5 Dense Vectorization Summary")
    print("==========================================================")
    print(f"Successfully Vectorized: {success_count}/{len(profiles)} profiles.")
    print(f"Feature Dimensions:     {len(master_schema)}")
    print("==========================================================")

    if success_count != len(profiles):
        sys.exit(1)

    print("Step 5 complete. Vector data saved in data/step5_vector_*.json")


if __name__ == "__main__":
    main()
