"""
O*NET Combined Profiles Builder.
Loads all Step 4 normalized JSON profiles and compiles them into a single
unified master JSON database file.
"""

import json
import logging
import pathlib
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("OnetCombiner")


def main() -> None:
    data_dir = pathlib.Path("data")
    normal_files = sorted(list(data_dir.glob("step4_normal_*.json")))

    # Filter out any pre-existing combined file to avoid self-combining loops
    normal_files = [f for f in normal_files if "combined" not in f.name]

    if not normal_files:
        logger.error("No Step 4 normalized files found in data/ directory! Aborting.")
        sys.exit(1)

    logger.info("Combining %d normalized profiles...", len(normal_files))

    combined_profiles = []
    for filepath in normal_files:
        logger.info("Reading profile: %s", filepath.name)
        try:
            with open(filepath, encoding="utf-8") as f:
                profile_data = json.load(f)
            combined_profiles.append(profile_data)
        except Exception as e:
            logger.error("  [ERROR] Failed to read %s: %s", filepath.name, e)
            sys.exit(1)

    # Save the combined list as step4_normal_combined.json
    out_filename = "step4_normal_combined.json"
    out_path = data_dir / out_filename

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(combined_profiles, f, indent=2, sort_keys=True, ensure_ascii=False)
        logger.info("Successfully saved combined database to: %s", out_path)
    except Exception as e:
        logger.error("Failed to write combined JSON: %s", e)
        sys.exit(1)

    print("\n==========================================================")
    print("O*NET Dynamic Profile Combination Summary")
    print("==========================================================")
    print(f"Total Occupations Combined: {len(combined_profiles)}")
    print(f"Combined Database saved to: {out_path}")
    print("==========================================================")


if __name__ == "__main__":
    main()
