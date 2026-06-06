#!/usr/bin/env python3
"""
Analyze full_profiles.jsonl for data quality.
"""

import json

# Expected sections in details object
EXPECTED_SECTIONS = [
    "tasks",
    "skills",
    "knowledge",
    "abilities",
    "work_activities",
    "work_styles",
    "education",
    "job_zone",
]
# Sections that should have items with ratings
SECTIONS_WITH_RATINGS = ["tasks", "skills", "knowledge", "abilities", "work_activities", "work_styles"]


def analyze_profile(profile):
    """Analyze a single profile."""
    results = {
        "code": profile.get("code"),
        "title": profile.get("title"),
        "completeness": {},
        "ratings": {},
        "issues": [],
    }

    details = profile.get("details", {})

    # 1. Completeness check
    for section in EXPECTED_SECTIONS:
        if section in details:
            section_data = details[section]
            if isinstance(section_data, list):
                present = len(section_data) > 0
                count = len(section_data)
            elif isinstance(section_data, dict):
                present = len(section_data) > 0
                count = len(section_data)
            else:
                present = section_data is not None and section_data != ""
                count = 1 if present else 0

            results["completeness"][section] = {"present": present, "count": count}
        else:
            results["completeness"][section] = {"present": False, "count": 0}

    # 2. Check for ratings in list items
    for section in SECTIONS_WITH_RATINGS:
        if section in details:
            section_data = details[section]
            if isinstance(section_data, list) and len(section_data) > 0:
                first_item = section_data[0]
                if isinstance(first_item, dict):
                    # Check for common rating fields
                    has_rating = any(
                        key in first_item for key in ["importance", "level", "percentage", "value", "rating"]
                    )
                    results["ratings"][section] = {
                        "has_rating": has_rating,
                        "keys": list(first_item.keys()) if first_item else [],
                    }
                    if not has_rating:
                        results["issues"].append(
                            f"  • {section}: No rating field (importance/level/percentage) found in first item"
                        )
                else:
                    results["ratings"][section] = {"has_rating": False, "keys": []}

    # 3. Data consistency checks
    # Check for missing or empty education
    if "education" not in details or not details["education"]:
        results["issues"].append("  • education: Missing or empty")

    # Check for missing or empty job_zone
    if "job_zone" not in details or not details["job_zone"]:
        results["issues"].append("  • job_zone: Missing or empty")

    # Check for null values in specific fields
    for key in ["in_demand_skills", "software_skills", "technology_skills"]:
        if key in details and details[key] is None:
            results["issues"].append(f"  • {key}: Set to null")

    # Check for zero-item sections that should have data
    for section in ["skills", "knowledge", "abilities", "work_activities"]:
        if section in details:
            if isinstance(details[section], list) and len(details[section]) == 0:
                results["issues"].append(f"  • {section}: Empty list (expected to have items)")

    return results


def main():
    profiles = []
    with open("/workspaces/onet_role_dna/full_profiles.jsonl") as f:
        for line in f:
            if line.strip():
                profiles.append(json.loads(line))

    all_results = []
    for profile in profiles:
        result = analyze_profile(profile)
        all_results.append(result)

    # Print detailed analysis
    for result in all_results:
        for section in EXPECTED_SECTIONS:
            info = result["completeness"][section]
            "✓ Present" if info["present"] else "✗ Missing/Empty"
            if info["present"]:
                pass
            else:
                pass

        if result["ratings"]:
            for _section, rating_info in result["ratings"].items():
                "✓ Has rating" if rating_info["has_rating"] else "✗ No rating"
        else:
            pass

        if result["issues"]:
            for _issue in result["issues"]:
                pass
        else:
            pass

    # Summary and Recommendations

    # Check what's universally missing
    sections_missing_count = {section: 0 for section in EXPECTED_SECTIONS}
    ratings_missing_count = {section: 0 for section in SECTIONS_WITH_RATINGS}

    for result in all_results:
        for section in EXPECTED_SECTIONS:
            if not result["completeness"][section]["present"]:
                sections_missing_count[section] += 1
        for section in SECTIONS_WITH_RATINGS:
            if section in result["ratings"] and not result["ratings"][section]["has_rating"]:
                ratings_missing_count[section] += 1

    missing_sections = [s for s, count in sections_missing_count.items() if count > 0]
    if missing_sections:
        for _section in missing_sections:
            pass
    else:
        pass

    missing_ratings = [s for s, count in ratings_missing_count.items() if count > 0]
    if missing_ratings:
        for _section in missing_ratings:
            pass
    else:
        pass

    total_issues = sum(len(r["issues"]) for r in all_results)

    if total_issues == 0 and not missing_sections and not missing_ratings:
        pass
    else:
        if missing_sections or missing_ratings:
            pass
        if total_issues > 0:
            pass


if __name__ == "__main__":
    main()
