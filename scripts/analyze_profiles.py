#!/usr/bin/env python3
"""
Analyze full_profiles.jsonl for data quality.
"""

import json

# Expected sections in details object
EXPECTED_SECTIONS = ['tasks', 'skills', 'knowledge', 'abilities', 'work_activities', 'work_styles', 'education', 'job_zone']
# Sections that should have items with ratings
SECTIONS_WITH_RATINGS = ['tasks', 'skills', 'knowledge', 'abilities', 'work_activities', 'work_styles']

def analyze_profile(profile):
    """Analyze a single profile."""
    results = {
        'code': profile.get('code'),
        'title': profile.get('title'),
        'completeness': {},
        'ratings': {},
        'issues': []
    }
    
    details = profile.get('details', {})
    
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
            
            results['completeness'][section] = {
                'present': present,
                'count': count
            }
        else:
            results['completeness'][section] = {
                'present': False,
                'count': 0
            }
    
    # 2. Check for ratings in list items
    for section in SECTIONS_WITH_RATINGS:
        if section in details:
            section_data = details[section]
            if isinstance(section_data, list) and len(section_data) > 0:
                first_item = section_data[0]
                if isinstance(first_item, dict):
                    # Check for common rating fields
                    has_rating = any(key in first_item for key in ['importance', 'level', 'percentage', 'value', 'rating'])
                    results['ratings'][section] = {
                        'has_rating': has_rating,
                        'keys': list(first_item.keys()) if first_item else []
                    }
                    if not has_rating:
                        results['issues'].append(f"  • {section}: No rating field (importance/level/percentage) found in first item")
                else:
                    results['ratings'][section] = {'has_rating': False, 'keys': []}
    
    # 3. Data consistency checks
    # Check for missing or empty education
    if 'education' not in details or not details['education']:
        results['issues'].append("  • education: Missing or empty")
    
    # Check for missing or empty job_zone
    if 'job_zone' not in details or not details['job_zone']:
        results['issues'].append("  • job_zone: Missing or empty")
    
    # Check for null values in specific fields
    for key in ['in_demand_skills', 'software_skills', 'technology_skills']:
        if key in details and details[key] is None:
            results['issues'].append(f"  • {key}: Set to null")
    
    # Check for zero-item sections that should have data
    for section in ['skills', 'knowledge', 'abilities', 'work_activities']:
        if section in details:
            if isinstance(details[section], list) and len(details[section]) == 0:
                results['issues'].append(f"  • {section}: Empty list (expected to have items)")
    
    return results

def main():
    profiles = []
    with open('/workspaces/onet_role_dna/full_profiles.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                profiles.append(json.loads(line))
    
    print("=" * 80)
    print("O*NET OCCUPATION PROFILES - DATA QUALITY ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    all_results = []
    for profile in profiles:
        result = analyze_profile(profile)
        all_results.append(result)
    
    # Print detailed analysis
    for result in all_results:
        print(f"PROFILE: {result['code']} - {result['title']}")
        print("-" * 80)
        
        print("\n1. COMPLETENESS (Detail Sections):")
        for section in EXPECTED_SECTIONS:
            info = result['completeness'][section]
            status = "✓ Present" if info['present'] else "✗ Missing/Empty"
            if info['present']:
                print(f"   {section:20} {status:20} (items: {info['count']})")
            else:
                print(f"   {section:20} {status}")
        
        print("\n2. RATINGS (First Item Analysis):")
        if result['ratings']:
            for section, rating_info in result['ratings'].items():
                status = "✓ Has rating" if rating_info['has_rating'] else "✗ No rating"
                print(f"   {section:20} {status}")
                print(f"      Fields: {', '.join(rating_info['keys'][:5])}")
        else:
            print("   No data available for rating check")
        
        print("\n3. DATA CONSISTENCY ISSUES:")
        if result['issues']:
            for issue in result['issues']:
                print(issue)
        else:
            print("   ✓ No issues found")
        
        print("\n" + "=" * 80 + "\n")
    
    # Summary and Recommendations
    print("SUMMARY & RECOMMENDATIONS")
    print("-" * 80)
    
    # Check what's universally missing
    sections_missing_count = {section: 0 for section in EXPECTED_SECTIONS}
    ratings_missing_count = {section: 0 for section in SECTIONS_WITH_RATINGS}
    
    for result in all_results:
        for section in EXPECTED_SECTIONS:
            if not result['completeness'][section]['present']:
                sections_missing_count[section] += 1
        for section in SECTIONS_WITH_RATINGS:
            if section in result['ratings'] and not result['ratings'][section]['has_rating']:
                ratings_missing_count[section] += 1
    
    print("\n1. MISSING SECTIONS ACROSS PROFILES:")
    missing_sections = [s for s, count in sections_missing_count.items() if count > 0]
    if missing_sections:
        for section in missing_sections:
            print(f"   • {section}: Missing in {sections_missing_count[section]}/5 profiles")
    else:
        print("   ✓ All expected sections present in all profiles")
    
    print("\n2. MISSING RATINGS ACROSS PROFILES:")
    missing_ratings = [s for s, count in ratings_missing_count.items() if count > 0]
    if missing_ratings:
        for section in missing_ratings:
            print(f"   • {section}: No rating field in {ratings_missing_count[section]}/5 profiles")
    else:
        print("   ✓ All list sections have rating fields")
    
    print("\n3. TOTAL ISSUES FOUND:")
    total_issues = sum(len(r['issues']) for r in all_results)
    print(f"   • Total data quality issues: {total_issues}")
    
    print("\n4. RECOMMENDATIONS:")
    if total_issues == 0 and not missing_sections and not missing_ratings:
        print("   ✓ Dataset appears complete and consistent. Ready for ML/AI analysis.")
    else:
        if missing_sections or missing_ratings:
            print("   • Re-fetch profiles for sections marked as missing or lacking ratings")
        if total_issues > 0:
            print(f"   • Investigate and fix {total_issues} data consistency issues found")
        print("   • Validate that all ratings fields are populated correctly after re-fetch")

if __name__ == '__main__':
    main()
