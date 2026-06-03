#!/usr/bin/env python3
"""
Detailed analysis with table format and extra checks.
"""

import json

def analyze_detailed():
    profiles = []
    with open('/workspaces/onet_role_dna/full_profiles.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                profiles.append(json.loads(line))
    
    print("\n" + "=" * 120)
    print("DETAILED COMPLETENESS TABLE")
    print("=" * 120)
    print()
    
    sections = ['tasks', 'skills', 'knowledge', 'abilities', 'work_activities', 'work_styles', 'education', 'job_zone']
    
    # Header
    header = f"{'SOC Code':20} | {'Title':40} |"
    for sec in sections:
        header += f" {sec:10} |"
    print(header)
    print("-" * len(header))
    
    # Rows
    for profile in profiles:
        code = profile.get('code', '')
        title = profile.get('title', '')[:38]
        details = profile.get('details', {})
        
        row = f"{code:20} | {title:40} |"
        for section in sections:
            if section in details:
                data = details[section]
                if isinstance(data, list):
                    count = len(data)
                    row += f" {count:10} |"
                else:
                    row += f" {'•':10} |"
            else:
                row += f" {'✗':10} |"
        print(row)
    
    print()
    print("=" * 120)
    print("\nLEGEND:")
    print("  Numbers = Count of items in list")
    print("  • = Present but not a list")
    print("  ✗ = Missing/Empty")
    
    print("\n" + "=" * 120)
    print("DETAILED SECTION ANALYSIS (FOR SECTIONS WITH ITEMS)")
    print("=" * 120)
    print()
    
    for profile in profiles:
        code = profile.get('code', '')
        title = profile.get('title', '')
        details = profile.get('details', {})
        
        print(f"\n{code} - {title}")
        print("-" * 100)
        
        # Check each section
        for section in sections:
            if section in details:
                data = details[section]
                if isinstance(data, list):
                    if len(data) > 0:
                        first = data[0]
                        if isinstance(first, dict):
                            keys = list(first.keys())
                            has_rating = any(k in keys for k in ['importance', 'level', 'percentage', 'value', 'rating'])
                            print(f"  {section:20} {len(data):3} items  | Keys: {', '.join(keys[:6])}")
                            if not has_rating:
                                print(f"                        ⚠ NO RATING FIELD")
                        else:
                            print(f"  {section:20} {len(data):3} items  | Items are not dicts")
                    else:
                        print(f"  {section:20}   0 items  | EMPTY LIST")
                elif isinstance(data, dict):
                    print(f"  {section:20}   dict   | Keys: {', '.join(list(data.keys())[:5])}")
                else:
                    print(f"  {section:20}   value  | Type: {type(data).__name__}")
            else:
                print(f"  {section:20}   MISSING")
        
        # Check for null values
        print("\n  Extra checks:")
        if 'in_demand_skills' in details:
            val = details['in_demand_skills']
            if val is None:
                print(f"    ⚠ in_demand_skills = null")
            elif isinstance(val, list) and len(val) == 0:
                print(f"    ⚠ in_demand_skills = empty list")
        
        if 'technology_skills' in details:
            val = details['technology_skills']
            if val is None:
                print(f"    ⚠ technology_skills = null")
            elif isinstance(val, list) and len(val) == 0:
                print(f"    ⚠ technology_skills = empty list")
        
        if 'software_skills' in details:
            val = details['software_skills']
            if val is None:
                print(f"    ⚠ software_skills = null")
            elif isinstance(val, list) and len(val) == 0:
                print(f"    ⚠ software_skills = empty list")

if __name__ == '__main__':
    analyze_detailed()
