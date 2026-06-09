"""
O*NET Database Schema Caching Module.
Implements a hybrid approach to pull, compile, and cache the full O*NET
data dictionary containing column schemas and metadata for all 45 tables.
"""

import json
import pathlib
import time
from typing import Any

import requests
from tqdm import tqdm

BASE_URL = "https://api-v2.onetcenter.org/"


def get_data_dictionary(
    api_key: str,
    cache_dir: str | pathlib.Path = "data/.cache",
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Retrieves the complete compiled O*NET data dictionary.
    Loads from local cache if present, otherwise pulls dynamically from the API.
    """
    cache_path = pathlib.Path(cache_dir) / "onet_data_dictionary.json"

    # 1. Check if we can load from the local cache first
    if cache_path.exists() and not force_refresh:
        try:
            with open(cache_path, encoding="utf-8") as f:
                print(f"Loaded full data dictionary from local cache: {cache_path}")
                return json.load(f)
        except Exception as e:
            print(f"Failed to read cache, falling back to live API download: {e}")

    # 2. Compile full data dictionary dynamically from the API
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"X-API-Key": api_key}

    print("Compiling full O*NET Database Dictionary dynamically from the live API...")
    try:
        # Fetch the index list of all database tables
        res = requests.get(f"{BASE_URL}database/", headers=headers, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to list tables: HTTP {res.status_code}")

        tables = res.json()
        print(f"Discovered {len(tables)} tables. Fetching column schemas...")

        dictionary: dict[str, Any] = {}

        # 3. Pull each table's schema sequentially with a nice progress bar
        for t in tqdm(tables, desc="Downloading Schemas", unit="table"):
            table_id = t.get("table_id")
            if not table_id:
                continue

            info_url = f"{BASE_URL}database/info/{table_id}"
            info_res = requests.get(info_url, headers=headers, timeout=15)

            if info_res.status_code == 200:
                dictionary[table_id] = info_res.json()
            else:
                print(f"\n[Warning] Failed to fetch schema for {table_id}: HTTP {info_res.status_code}")

            # Polite short sleep to prevent API rate limiting
            time.sleep(0.1)

        # 4. Save the compiled dictionary to the local cache folder
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(dictionary, f, indent=2, sort_keys=True, ensure_ascii=False)

        print(f"\nSUCCESS: Data dictionary cached successfully at: {cache_path}")
        return dictionary

    except Exception as e:
        print(f"\nERROR: Failed to compile the data dictionary: {e}")
        return {}


if __name__ == "__main__":
    # Test execution when run as a standalone script
    API_KEY = "jD5Xi-hGSyq-gVapp-QiCbI"
    dict_data = get_data_dictionary(API_KEY, force_refresh=False)
    print(f"Ready: Data dictionary contains {len(dict_data)} tables.")
