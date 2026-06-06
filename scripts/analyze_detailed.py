#!/usr/bin/env python3
"""
Detailed analysis with table format and extra checks.
"""

import json


def analyze_detailed():
    profiles = []
    with open('/workspaces/onet_role_dna/full_profiles.jsonl') as f:
        for line in f:
            if line.strip():
                profiles.append(json.loads(line))


    sections = ['tasks', 'skills', 'knowledge', 'abilities', 'work_activities', 'work_styles', 'education', 'job_zone']

    # Header
    header = f"{'SOC Code':20} | {'Title':40} |"
    for sec in sections:
        header += f" {sec:10} |"

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



    for profile in profiles:
        code = profile.get('code', '')
        title = profile.get('title', '')
        details = profile.get('details', {})


        # Check each section
        for section in sections:
            if section in details:
                data = details[section]
                if isinstance(data, list):
                    if len(data) > 0:
                        first = data[0]
                        if isinstance(first, dict):
                            keys = list(first.keys())
                            has_rating = any(k in keys for k in ['importance', 'level', 'percentage', 'value', 'rating'])  # noqa: E501
                            if not has_rating:
                                pass
                        else:
                            pass
                    else:
                        pass
                elif isinstance(data, dict):
                    pass
                else:
                    pass
            else:
                pass

        # Check for null values
        if 'in_demand_skills' in details:
            val = details['in_demand_skills']
            if val is None:
                pass
            elif isinstance(val, list) and len(val) == 0:
                pass

        if 'technology_skills' in details:
            val = details['technology_skills']
            if val is None:
                pass
            elif isinstance(val, list) and len(val) == 0:
                pass

        if 'software_skills' in details:
            val = details['software_skills']
            if val is None:
                pass
            elif isinstance(val, list) and len(val) == 0:
                pass

if __name__ == '__main__':
    analyze_detailed()
