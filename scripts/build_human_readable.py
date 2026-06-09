"""O*NET Human-Readable Profile Builder (Step 6)."""

import json
import pathlib
import sys


def make_bar(val: float) -> str:
    filled = round(val * 10)
    return f"`{'█' * filled}{'░' * (10 - filled)}` {val * 100.0:.1f}%"


def generate_markdown(data: dict) -> str:
    title, code = data.get("title", "Unknown"), data.get("code", "Unknown")
    md = [f"# O*NET Occupational Profile: {title} ({code})\n\n---\n"]

    # 1. Job Zone
    jz_val = data.get("job_zone", {}).get("job_zone", 0.0)
    raw_zone = round(jz_val * 4.0 + 1.0)
    md.append(
        f"## 🏢 Job Zone Preparation\n"
        f"* **Normalized Preparation Score:** {make_bar(jz_val)}\n"
        f"* **O*NET Job Zone Classification:** Zone {raw_zone}\n\n---\n"
    )

    # 2. Tasks
    tasks = data.get("tasks", [])
    md.append("## 📝 Core Tasks")
    if tasks:
        md.extend([f"- {t.get('task', 'N/A')}" for t in tasks])
    else:
        md.append("*No core task definitions are available.*")
    md.append("\n---\n")

    # 3. Technology Skills
    tech = data.get("technology_skills", [])
    md.append("## 💻 Technology & Software Skills")
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
        md.append("*No software requirements are available.*")
    md.append("\n---\n")

    # 4. Numeric Domains
    domains = {
        "Abilities": "abilities",
        "Skills": "skills",
        "Knowledge": "knowledge",
        "Work Activities": "work_activities",
        "Work Context": "work_context",
        "Work Styles": "work_styles",
        "Interests": "interests",
        "Education": "education",
    }
    for label, key in domains.items():
        md.append(f"## 📊 {label}")
        items = data.get(key, [])
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
    return "\n".join(md)


def main():
    data_dir = pathlib.Path("data")
    files = sorted(list(data_dir.glob("step4_normal_*.json")))
    if not files:
        print("ERROR: No Step 4 normalized files found!", file=sys.stderr)
        sys.exit(1)
    print(f"Building profiles for {len(files)} occupations...")
    for fpath in files:
        code = fpath.name.replace("step4_normal_", "").replace(".json", "")
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            md_content = generate_markdown(data)
            out_path = data_dir / f"step6_profile_{code}.md"
            out_path.write_text(md_content, encoding="utf-8")
            print(f"  * Saved: {out_path.name}")
        except Exception as e:
            print(f"  [ERROR] Failed for {code}: {e}", file=sys.stderr)
    print("\nStep 6 complete. Human-readable profiles saved in data/step6_profile_*.md")


if __name__ == "__main__":
    main()
