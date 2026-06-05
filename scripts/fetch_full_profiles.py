import sys, json, time
from OnetWebService import OnetWebService

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
        if "next" in result and result["next"]:
            # Parse the next URL to get new path and query
            next_url = result["next"]
            # Remove base URL and leading slash
            # For simplicity, we'll extract the path and query manually
            if next_url.startswith("https://api-v2.onetcenter.org/"):
                path_part = next_url[len("https://api-v2.onetcenter.org/"):]
            else:
                path_part = next_url.lstrip("/")
            if "?" in path_part:
                path, query = path_part.split("?", 1)
                from urllib.parse import parse_qs
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
    print(f"Fetching overview for {soc_code}...", file=sys.stderr)
    overview = client.call(f"online/occupations/{soc_code}/")
    if "error" in overview:
        raise Exception(f"Overview error: {overview['error']}")

    profile = overview.copy()   # start with overview
    profile["details"] = {}     # where we'll store detailed sections

    # Iterate through details_contents (these are the endpoints with ratings)
    for item in overview.get("details_contents", []):
        title = item.get("title")
        href = item.get("href")
        if not href:
            continue
        # Convert full URL to relative path (strip base URL)
        rel_path = href.replace("https://api-v2.onetcenter.org/", "")
        print(f"  Fetching {title} for {soc_code}...", file=sys.stderr)
        try:
            # Some endpoints may be paginated (e.g., tasks, skills)
            # We'll try to fetch all pages first; if it fails, fallback to single fetch
            data = fetch_all_pages(rel_path)
            # If data is empty, maybe it's a single object (like education, job zone)
            if not data:
                data = fetch_single(rel_path)
            profile["details"][title.lower().replace(" ", "_")] = data
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)
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
    for code in soc_codes:
        try:
            full = build_full_profile(code)
            print(json.dumps(full))
        except Exception as e:
            print(json.dumps({"code": code, "error": str(e)}), file=sys.stderr)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
