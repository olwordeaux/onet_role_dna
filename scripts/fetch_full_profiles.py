"""
Data fetch script that polls the O*NET Web Services API, compiles full detailed
profiles, tracks download progress, and saves them to standardized paths.
"""

import time
from urllib.parse import parse_qs

from OnetWebService import OnetWebService
from tqdm import tqdm

from onet_role_dna.writer import write_data_file

API_KEY = "jD5Xi-hGSyq-gVapp-QiCbI"   # replace if different
client = OnetWebService(API_KEY)


def fetch_all_pages(rel_path, query_params=None):
    """Follow pagination links and return all elements (list)."""
    elements = []
    path = rel_path
    params = query_params if query_params else []
    while True:
        result = client.call(path, *params)
        if "error" in result:
            raise Exception(f"API error for {path}: {result['error']}")
        # Find the array key (usually 'task' or 'element')
        data_key = None
        for k, v in result.items():
            if k not in ("start", "end", "total", "next") and isinstance(v, list):
                data_key = k
                break
        if data_key and result[data_key]:
            elements.extend(result[data_key])
        if result.get("next"):
            next_url = result["next"]
            if next_url.startswith("https://api-v2.onetcenter.org/"):
                path_part = next_url[len("https://api-v2.onetcenter.org/"):]
            else:
                path_part = next_url.lstrip("/")
            if "?" in path_part:
                path, query = path_part.split("?", 1)
                qs = parse_qs(query)
                params = [(k, v[0]) for k, v in qs.items()]
            else:
                path = path_part
                params = []
        else:
            break
        time.sleep(0.1)  # polite delay
    return elements


def fetch_single(rel_path, query_params=None):
    """Fetch a single object (non-paginated)."""
    result = client.call(rel_path, *(query_params or []))
    if "error" in result:
        raise Exception(f"API error for {rel_path}: {result['error']}")
    return result


def build_full_profile(soc_code):
    tqdm.write(f"Fetching overview for {soc_code}...")
    overview = client.call(f"online/occupations/{soc_code}/")
    if "error" in overview:
        raise Exception(f"Overview error: {overview['error']}")

    profile = overview.copy()   # start with overview
    profile["details"] = {}     # where we'll store detailed sections

    details_contents = overview.get("details_contents", [])

    # Sub-progress bar for the specific sections of this occupation
    for item in tqdm(details_contents, desc=f"  Loading {soc_code}", leave=False, unit="section"):
        title = item.get("title")
        href = item.get("href")
        if not href:
            continue
        rel_path = href.replace("https://api-v2.onetcenter.org/", "")
        try:
            data = fetch_all_pages(rel_path)
            if not data:
                data = fetch_single(rel_path)
            profile["details"][title.lower().replace(" ", "_")] = data
        except Exception as e:  # noqa: BLE001
            tqdm.write(f"    Error fetching {title} for {soc_code}: {e}")
            profile["details"][title.lower().replace(" ", "_")] = None
        time.sleep(0.2)

    return profile


def main():
    soc_codes = [
        "13-2072.00",
        "11-3031.00",
        "11-1021.00",
        "15-2031.00",
        "41-3091.00"
    ]

    fetched_profiles = []


    # Outer progress bar for the occupations list
    for code in tqdm(soc_codes, desc="Total Fetch Progress", unit="occupation"):
        try:
            full = build_full_profile(code)
            fetched_profiles.append(full)
        except Exception as e:  # noqa: BLE001
            tqdm.write(f"ERROR: Failed to build profile for {code}. Reason: {e}")
        time.sleep(0.5)

    if not fetched_profiles:
        return

    # Write the compiled profiles natively using our standardized, compliant writer
    try:
        write_data_file(
            directory="data",
            project="onet",
            content="full-profiles",
            version="v0.1.0",
            data=fetched_profiles,
            ext="jsonl"
        )
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
