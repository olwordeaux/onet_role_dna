#!/usr/bin/env python3
"""
Incorporate employment history into O*NET profiles
Creates multiple CSV outputs for different use cases
"""

import pandas as pd
from datetime import datetime
import io

# Employment history data
employment_data = """soc_code,company_name,from_date,to_date
13-2072.00,Parson's Technology,1/1/98,10/9/01
11-3031.00,First Choice Mortgage,10/10/01,2/14/03
13-2072.00,Specialty Lending,2/16/03,7/19/04
11-3031.00,Family Lending,7/20/04,10/13/07
11-1021.00,Global State Mortgage,10/13/07,3/12/09
15-2031.00,O.N.E. Consulting,3/20/09,11/18/18
53-7065.00,Wells Fargo,10/18/18,12/15/24"""

def parse_employment_data(data_string):
    """Parse employment data from string"""
    return pd.read_csv(io.StringIO(data_string))

def parse_dates(date_str):
    """Parse date string in M/D/YY format"""
    try:
        return pd.to_datetime(date_str, format='%m/%d/%y')
    except:
        return None

def calculate_duration(from_date, to_date):
    """Calculate employment duration in months"""
    try:
        from_dt = pd.to_datetime(from_date, format='%m/%d/%y')
        to_dt = pd.to_datetime(to_date, format='%m/%d/%y')
        duration = (to_dt.year - from_dt.year) * 12 + (to_dt.month - from_dt.month)
        return max(0, duration)
    except:
        return None

def main():
    print("=" * 100)
    print("EMPLOYMENT HISTORY INTEGRATION")
    print("=" * 100)
    print()
    
    # Load profiles
    print("📥 Loading profiles.csv...")
    profiles = pd.read_csv('profiles.csv')
    print(f"   ✓ Loaded {len(profiles)} profiles")
    
    # Load employment data
    print("📥 Loading employment history...")
    employment = parse_employment_data(employment_data)
    employment['from_date'] = employment['from_date'].apply(parse_dates)
    employment['to_date'] = employment['to_date'].apply(parse_dates)
    employment['duration_months'] = employment.apply(
        lambda row: calculate_duration(row['from_date'], row['to_date']), axis=1
    )
    print(f"   ✓ Loaded {len(employment)} employment records")
    print()
    
    # 1. Employment History CSV (standalone)
    print("📄 Creating employment_history.csv...")
    emp_export = employment.copy()
    emp_export['from_date'] = employment['from_date'].dt.strftime('%m/%d/%Y')
    emp_export['to_date'] = employment['to_date'].dt.strftime('%m/%d/%Y')
    emp_export.to_csv('employment_history.csv', index=False)
    print(f"   ✓ {len(emp_export)} records exported\n")
    
    # 2. Expanded profiles with employment (one row per job)
    print("📄 Creating expanded_profiles_with_employment.csv...")
    # Get profile titles
    profile_lookup = profiles[['soc_code', 'title']].set_index('soc_code').to_dict()['title']
    
    expanded = []
    for _, emp_row in employment.iterrows():
        code = emp_row['soc_code']
        if code in profile_lookup:
            # Merge with profile data
            profile_row = profiles[profiles['soc_code'] == code].iloc[0]
            merged = profile_row.to_dict()
            merged['company_name'] = emp_row['company_name']
            merged['from_date'] = emp_row['from_date']
            merged['to_date'] = emp_row['to_date']
            merged['duration_months'] = emp_row['duration_months']
            expanded.append(merged)
        else:
            # Create partial record for SOC codes not in profiles
            merged = {
                'soc_code': code,
                'title': 'Unknown Occupation',
                'company_name': emp_row['company_name'],
                'from_date': emp_row['from_date'],
                'to_date': emp_row['to_date'],
                'duration_months': emp_row['duration_months'],
            }
            expanded.append(merged)
    
    expanded_df = pd.DataFrame(expanded)
    expanded_df['from_date'] = expanded_df['from_date'].dt.strftime('%m/%d/%Y')
    expanded_df['to_date'] = expanded_df['to_date'].dt.strftime('%m/%d/%Y')
    expanded_df.to_csv('expanded_profiles_with_employment.csv', index=False)
    print(f"   ✓ {len(expanded_df)} records exported\n")
    
    # 3. Profiles with employment summary (aggregate stats)
    print("📄 Creating profiles_with_employment_summary.csv...")
    
    # Calculate employment stats per SOC code
    emp_stats = employment.groupby('soc_code').agg({
        'company_name': 'count',  # number of jobs
        'duration_months': 'sum',  # total months employed
    }).rename(columns={'company_name': 'num_jobs', 'duration_months': 'total_months_employed'})
    
    emp_stats['avg_job_duration_months'] = emp_stats['total_months_employed'] / emp_stats['num_jobs']
    emp_stats = emp_stats.reset_index()
    
    # Merge with profiles
    summary = profiles.merge(emp_stats, on='soc_code', how='left')
    summary['num_jobs'] = summary['num_jobs'].fillna(0).astype(int)
    summary['total_months_employed'] = summary['total_months_employed'].fillna(0).astype(int)
    summary['avg_job_duration_months'] = summary['avg_job_duration_months'].fillna(0)
    summary['has_employment_history'] = (summary['num_jobs'] > 0).astype(int)
    
    summary.to_csv('profiles_with_employment_summary.csv', index=False)
    print(f"   ✓ {len(summary)} profiles with employment summary exported\n")
    
    # 4. Company-Occupation Mapping
    print("📄 Creating company_occupation_mapping.csv...")
    company_map = employment[['soc_code', 'company_name']].copy()
    company_map['title'] = company_map['soc_code'].map(profile_lookup).fillna('Unknown')
    company_map.to_csv('company_occupation_mapping.csv', index=False)
    print(f"   ✓ {len(company_map)} company-occupation mappings exported\n")
    
    # Summary statistics
    print("=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    print()
    print(f"Profiles with employment history:  {(summary['has_employment_history'].sum())}/{len(summary)}")
    print(f"Total employment records:          {len(employment)}")
    print(f"Unique companies:                  {employment['company_name'].nunique()}")
    print(f"Date range:                        {employment['from_date'].min().strftime('%m/%d/%Y')} - {employment['to_date'].max().strftime('%m/%d/%Y')}")
    print()
    
    print("Employment by SOC Code:")
    print(summary[summary['num_jobs'] > 0][['soc_code', 'title', 'num_jobs', 'total_months_employed', 'avg_job_duration_months']].to_string(index=False))
    print()
    
    print("=" * 100)
    print("FILES GENERATED")
    print("=" * 100)
    print("""
1. employment_history.csv
   - Standalone employment data
   - Columns: soc_code, company_name, from_date, to_date, duration_months
   - Use for: HR systems, career tracking

2. expanded_profiles_with_employment.csv
   - All profile columns + employment details (one row per job)
   - Columns: [all profile columns] + company_name, from_date, to_date, duration_months
   - Use for: Individual career records, detailed analysis

3. profiles_with_employment_summary.csv
   - Original profiles + aggregated employment statistics
   - New columns: num_jobs, total_months_employed, avg_job_duration_months, has_employment_history
   - Use for: ML features, career progression analysis

4. company_occupation_mapping.csv
   - Mapping between companies and SOC codes/titles
   - Columns: soc_code, company_name, title
   - Use for: Company-occupation relationships, network analysis
    """)
    
    print("✨ Integration complete!")

if __name__ == '__main__':
    main()
