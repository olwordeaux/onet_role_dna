"""
O*NET Career DNA Trajectory Builder (Step 7).
Parses a chronological career timeline, ensures all O*NET dependencies
are normalized, and compiles a completely un-truncated portfolio report.
"""

import datetime
import json
import logging
import pathlib
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("OnetTrajectory")

BASE_URL = "https://api-v2.onetcenter.org/"
API_KEY = "jD5Xi-hGSyq-gVapp-QiCbI"

# Decoupled Career Timeline Data (Fully Mapped)
TIMELINE = [
    {"seq": 1, "code": "41-3091.00", "company": "Parson's Technology", "from": "1/1/98", "to": "10/9/01"},
    {"seq": 2, "code": "13-2072.00", "company": "First Choice Mortgage", "from": "10/10/01", "to": "2/14/03"},
    {"seq": 3, "code": "11-3031.00", "company": "Specialty Lending", "from": "2/16/03", "to": "7/19/04"},
    {"seq": 4, "code": "13-2072.00", "company": "Family Lending", "from": "7/20/04", "to": "10/13/07"},
    {"seq": 5, "code": "11-3031.00", "company": "Global State Mortgage", "from": "10/13/07", "to": "3/12/09"},
    {"seq": 6, "code": "11-1021.00", "company": "O.N.E. Consulting", "from": "3/20/09", "to": "11/18/18"},
    {"seq": 7, "code": "15-2031.00", "company": "Wells Fargo", "from": "10/18/18", "to": "12/15/24"},
]


def parse_date(date_str: str) -> datetime.date:
    """Parses M/D/YY or M/D/YYYY string into a datetime.date object."""
    parts = date_str.split("/")
    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
    if year < 100:
        year += 1900 if year >= 80 else 2000
    return datetime.date(year, month, day)


def calculate_duration(from_str: str, to_str: str) -> tuple[int, int, float]:
    """Calculates duration in years, months, and decimal years."""
    d1, d2 = parse_date(from_str), parse_date(to_str)
    decimal_years = (d2 - d1).days / 365.25
    total_months = round(decimal_years * 12.0)
    return total_months // 12, total_months % 12, round(decimal_years, 2)


def make_bar(val: float) -> str:
    """Generates a text-based progress bar for [0, 1] values."""
    filled = round(val * 10)
    return f"`{'█' * filled}{'░' * (10 - filled)}` {val * 100.0:.1f}%"


def ensure_onet_code_is_normalized(code: str) -> None:
    """Self-healing compilation hook to ensure dataset completeness."""
    norm_path = pathlib.Path("data") / f"step4_normal_{code}.json"
    if norm_path.exists():
        return

    logger.info("Self-healing Hook: Pulling and normalizing missing code: %s", code)
    headers = {"X-API-Key": API_KEY}
    try:
        from scripts.clean_raw_data import clean_occupation_profile
        from scripts.fetch_raw_data import ENDPOINTS, extract_payload, make_request_with_retry
        from scripts.normalize_data import normalize_profile

        base_res = make_request_with_retry(f"{BASE_URL}online/occupations/{code}/", headers=headers)
        if base_res.status_code != 200:
            raise Exception(f"HTTP {base_res.status_code} for {code}")

        raw_data = base_res.json()
        raw_data["code"] = code
        raw_data["title"] = raw_data.get("title", "Unknown")

        for domain, endpoint_name in ENDPOINTS.items():
            detail_url = f"{BASE_URL}online/occupations/{code}/details/{endpoint_name}"
            detail_res = make_request_with_retry(detail_url, headers=headers)
            raw_data[domain] = extract_payload(detail_res.json(), domain) if detail_res.status_code == 200 else []
            time.sleep(0.5)

        clean_data = clean_occupation_profile(raw_data)
        normalized_data = normalize_profile(clean_data)
        norm_path.write_text(json.dumps(normalized_data, indent=2, sort_keys=True, ensure_ascii=False))
        logger.info("Successfully processed and normalized %s.", code)
    except Exception as e:
        logger.error("Failed self-healing pull for %s: %s", code, e)
        sys.exit(1)


def generate_trajectory_markdown(timeline_nodes: list[dict]) -> str:
    """Compiles a complete chronological career trajectory markdown report."""
    md = []
    md.append("# 🏆 Professional Career DNA Trajectory Portfolio")
    md.append(
        "\n*An advanced chronological audit mapping complete, "
        "un-truncated O*NET Occupational Role DNA against 26 years of career history (1998-2024).*"
    )
    md.append("\n---\n")

    total_duration_years = 0.0

    for node in timeline_nodes:
        seq = node["seq"]
        code = node["code"]
        company = node["company"]
        from_date = node["from"]
        to_date = node["to"]

        years, months, decimal_years = calculate_duration(from_date, to_date)
        total_duration_years += decimal_years

        duration_str = f"{years} years" if years > 0 else ""
        if months > 0:
            duration_str += f" {months} months" if duration_str else f"{months} months"
        if not duration_str:
            duration_str = "0 months"

        # Safe O*NET code check
        if not isinstance(code, str):
            continue

        filepath = pathlib.Path("data") / f"step4_normal_{code}.json"
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        title = data.get("title", "Unknown")

        md.append(f"## 📌 Sequence {seq}: {title} ({code})")
        md.append(f"* **Company:** {company}")
        md.append(f"* **Tenure:** {from_date} — {to_date} ({duration_str} | {decimal_years} years)")

        jz_val = data.get("job_zone", {}).get("job_zone", 0.0)
        raw_zone = round(jz_val * 4.0 + 1.0)
        md.append(f"* **Job Zone Preparation:** Zone {raw_zone} ({make_bar(jz_val)})")
        md.append("\n")

        # 1. Complete Tasks performed (No limits)
        tasks = data.get("tasks", [])
        md.append("### 📝 Core Tasks Performed")
        if tasks:
            for t in tasks:
                md.append(f"- {t.get('task')}")
        else:
            md.append("*No core task definitions are available for this incomplete profile.*")
        md.append("\n")

        # 2. Complete Technology Skills utilized (No limits)
        tech = data.get("technology_skills", [])
        md.append("### 💻 Technology & Software Skills Utilized")
        if tech:
            seen = set()
            for t in tech:
                name = t.get("workplace_example", "N/A")
                if name in seen or name == "N/A":
                    continue
                seen.add(name)
                tags = [
                    tag
                    for cond, tag in [
                        (t.get("hot_technology"), "🔥 Hot"),
                        (t.get("in_demand"), "⭐ In Demand"),
                    ]
                    if cond
                ]
                tag_str = f" ({', '.join(tags)})" if tags else ""
                md.append(f"- **{name}**{tag_str}")
        else:
            md.append("*No software requirements are available for this profile.*")
        md.append("\n")

        # 3. Complete Competency Strengths across all domains (No limits)
        md.append("### 📊 Complete Competency Strengths Profile")
        domains = {
            "Abilities": "abilities",
            "Skills": "skills",
            "Knowledge": "knowledge",
            "Work Activities": "work_activities",
            "Work Context": "work_context",
            "Work Styles": "work_styles",
            "Interests (Holland Codes)": "interests",
            "Education Requirements": "education",
        }
        for label, key in domains.items():
            items = data.get(key, [])
            md.append(f"#### {label}")
            if items:
                for item in items:
                    name = item.get("element_name", item.get("title", "N/A"))
                    val = item.get("data_value", 0.0)
                    el_id = item.get("element_id")
                    id_str = f" [{el_id}]" if el_id else ""
                    md.append(f"- **{name}**{id_str}: {make_bar(val)}")
            else:
                md.append("*[No data available for this domain]*")
            md.append("")
        md.append("\n---\n")

    md.append("## 📈 Accumulated Trajectory Summary")
    md.append(f"* **Total Career Tenure:** {total_duration_years:.2f} years")
    md.append(f"* **Total Career Sequences:** {len(timeline_nodes)} employment milestones")

    return "\n".join(md)


def main() -> None:
    logger.info("Initializing Career Trajectory compilation...")
    for node in TIMELINE:
        code = node.get("code")
        if isinstance(code, str):
            ensure_onet_code_is_normalized(code)

    logger.info("Generating complete, un-truncated Career DNA Trajectory Markdown Portfolio...")
    report = generate_trajectory_markdown(TIMELINE)

    out_path = pathlib.Path("data") / "career_dna_trajectory.md"
    out_path.write_text(report, encoding="utf-8")
    logger.info("SUCCESS: Complete Career DNA Trajectory report saved to: %s", out_path)


if __name__ == "__main__":
    main()
