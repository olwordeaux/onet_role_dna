"""
Test script to query the O*NET Web Services Database table index
and retrieve table schemas and data dictionary links programmatically.
"""

import requests

API_KEY = "jD5Xi-hGSyq-gVapp-QiCbI"
BASE_URL = "https://api-v2.onetcenter.org/"
headers = {"X-API-Key": API_KEY}

print("--- Step 1: Listing Available O*NET Database Tables ---")
try:
    res = requests.get(f"{BASE_URL}database/", headers=headers, timeout=10)
    if res.status_code != 200:
        print(f"Failed to list tables: {res.status_code}")
        print(res.text)
        exit(1)

    tables = res.json()
    print(f"Found {len(tables)} tables. Displaying first 3:")
    for t in tables[:3]:
        print(f"  * Table ID: {t.get('table_id')} | Title: {t.get('title')}")

    if not tables:
        print("No tables available. Aborting.")
        exit(0)

    # Get the first table ID to fetch its schema
    target_table = tables[0].get("table_id")
    print(f"\n--- Step 2: Fetching Schema & Data Dictionary for: {target_table} ---")

    info_url = f"{BASE_URL}database/info/{target_table}"
    info_res = requests.get(info_url, headers=headers, timeout=10)
    if info_res.status_code != 200:
        print(f"Failed to get table info: {info_res.status_code}")
        exit(1)

    info = info_res.json()
    print(f"Table Title:         {info.get('title')}")
    print(f"Description:         {info.get('description')}")
    print(f"Data Dictionary URL: {info.get('data_dictionary')}\n")

    print("Column Definitions (First 5 Fields):")
    for col in info.get("column", [])[:5]:
        print(f"  - Field:       {col.get('column_id')} ({col.get('type')})")
        print(f"    Title:       {col.get('title')}")
        print(f"    Description: {col.get('description')}")
        print()

except Exception as e:
    print(f"An error occurred: {e}")
