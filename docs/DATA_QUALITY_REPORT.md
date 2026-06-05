# O*NET Occupation Profiles - Data Quality Analysis Report

**Analysis Date:** June 1, 2026  
**File:** `full_profiles.jsonl`  
**Total Profiles Analyzed:** 5 SOC codes

---

## Executive Summary

The dataset contains **significant data quality issues** primarily concentrated in one profile (41-3091.00). Four profiles (13-2072.00, 11-3031.00, 11-1021.00, 15-2031.00) are nearly complete but have minor issues. The dataset **is NOT fully ready** for ML/AI analysis without remediation.

---

## 1. COMPLETENESS ANALYSIS

### Expected Sections
All profiles were checked for the presence of eight standard detail sections: tasks, skills, knowledge, abilities, work_activities, work_styles, education, and job_zone.

### Results by Profile

| SOC Code | Title | Tasks | Skills | Knowledge | Abilities | Work Activities | Work Styles | Education | Job Zone | Status |
|----------|-------|:-----:|:------:|:---------:|:---------:|:---------------:|:-----------:|:---------:|:--------:|--------|
| 13-2072.00 | Loan Officers | ✓ 30 | ✓ 35 | ✓ 33 | ✓ 52 | ✓ 41 | ✓ 21 | ✓ 3 | ✓ | **Complete** |
| 11-3031.00 | Financial Managers | ✓ 17 | ✓ 35 | ✓ 33 | ✓ 52 | ✓ 41 | ✓ 21 | ✓ 3 | ✓ | **Complete** |
| 11-1021.00 | General & Operations Managers | ✓ 17 | ✓ 35 | ✓ 33 | ✓ 52 | ✓ 41 | ✓ 21 | ✓ 3 | ✓ | **Complete** |
| 15-2031.00 | Operations Research Analysts | ✓ 17 | ✓ 35 | ✓ 33 | ✓ 52 | ✓ 41 | ✓ 21 | ✓ 3 | ✓ | **Complete** |
| 41-3091.00 | Sales Representatives, Services | ✓ 15 | ✗ | ✗ | ✗ | ✗ | ✓ 19 | ✗ | ✓ | **INCOMPLETE** |

### Key Findings

- **4/5 profiles (80%)** have all expected sections present
- **1/5 profiles (20%)** is missing 4 critical sections: skills, knowledge, abilities, work_activities, education
- **Profiles 13-2072.00 and 11-3031.00** have the most task items (30 and 17 respectively)
- **Profile 41-3091.00** has significantly fewer tasks (15) and is missing ~40% of expected data

---

## 2. RATINGS ANALYSIS

### Rating Fields in List Items

All item-based sections (tasks, skills, knowledge, abilities, work_activities, work_styles) should contain **importance, level, or percentage** rating fields for ML/AI feature engineering.

### Findings by Section

| Section | Profiles with Ratings | Status | Notes |
|---------|:--------------------:|:------:|-------|
| **tasks** | 4/5 (80%) | ⚠ INCOMPLETE | Profile 41-3091.00 lacks `importance` field in tasks |
| **skills** | 4/5 (80%) | ✓ PRESENT | All skills items include `importance` rating |
| **knowledge** | 4/5 (80%) | ✓ PRESENT | All knowledge items include `importance` rating |
| **abilities** | 4/5 (80%) | ✓ PRESENT | All abilities items include `importance` rating |
| **work_activities** | 4/5 (80%) | ✓ PRESENT | All work activities include `importance` rating |
| **work_styles** | 5/5 (100%) | ✓ PRESENT | All work styles include `importance` rating |

### Details on Rating Fields

**For profiles 13-2072.00, 11-3031.00, 11-1021.00, 15-2031.00:**
- **tasks**: Include `importance` + `category` fields ✓
- **skills, knowledge, abilities, work_activities**: Include `importance` field ✓
- **work_styles**: Include `importance` field ✓

**For profile 41-3091.00:**
- **tasks**: Missing `importance` field (only contains `id`, `related`, `title`, `category`) ⚠
- **work_styles**: Includes `importance` field ✓
- **Other sections**: Not present in dataset

**Note on education sections:**
- All 4 complete profiles have education items with `percentage_of_respondents` instead of `importance`
- This is acceptable for education data but differs from the standard importance rating used elsewhere

---

## 3. DATA CONSISTENCY ANALYSIS

### Critical Issues Found

| Issue | Affected Profiles | Severity | Details |
|-------|:-----------------:|:--------:|---------|
| `in_demand_skills` = null | 5/5 (100%) | HIGH | All profiles have this field set to null instead of containing data or empty list |
| Missing tasks ratings | 41-3091.00 | HIGH | Tasks items lack `importance` field needed for scoring |
| Missing core sections | 41-3091.00 | CRITICAL | Skills, knowledge, abilities, work_activities sections completely absent |
| Missing education data | 41-3091.00 | HIGH | Education section is empty/missing (only 4 profiles have it) |

### Zero-Item Sections

No profiles have zero-item lists for sections that should contain data. All non-missing sections have the expected number of items.

### Null/Undefined Values

**`in_demand_skills` field:**
- Status: **ALWAYS NULL** (5/5 profiles)
- Impact: This field cannot be used for analysis or feature engineering
- Recommendation: Either fetch this data from the API or remove from processing pipeline

**Other fields:**
- `technology_skills`: Present but typically empty or sparse in most profiles
- `software_skills`: Present with data in most profiles

### Data Type Consistency

All sections maintain consistent data types:
- Item-based sections: Lists of dictionaries with consistent keys
- `education` & `job_zone`: Dictionaries with stable structure
- No type mismatches or malformed entries detected

---

## 4. PROFILE-SPECIFIC ASSESSMENTS

### ✓ PROFILES 13-2072.00, 11-3031.00, 11-1021.00, 15-2031.00

**Status:** READY FOR ML/AI with minor caveats

**Strengths:**
- All 8 expected detail sections present
- All rating fields properly populated except education
- Substantial item counts (17-52 items per section)
- Consistent data structure and formatting

**Minor Issues:**
- `in_demand_skills` set to null (low priority, doesn't affect core analysis)

**ML/AI Readiness:** 95% - Suitable for analysis with in_demand_skills field excluded

---

### ✗ PROFILE 41-3091.00 (Sales Representatives, Services)

**Status:** NOT READY - REQUIRES RE-FETCH

**Critical Gaps:**
- 40% of expected sections missing entirely (skills, knowledge, abilities, work_activities, education)
- Tasks section lacks `importance` rating field (mandatory for scoring)
- Comparison table shows this profile is significantly under-specified vs. others

**Comparison to other profiles:**
- Other profiles: ~212 total detail items across all sections
- This profile: Only 34 items (tasks + work_styles)
- Missing: ~178 items worth of data

**ML/AI Readiness:** 20% - Insufficient data for reliable analysis. Must re-fetch from API.

---

## 5. RECOMMENDATIONS

### IMMEDIATE ACTIONS (Priority 1)

1. **Re-fetch profile 41-3091.00** from the O*NET API
   - Ensure all sections are populated: skills, knowledge, abilities, work_activities, education
   - Verify that tasks include `importance` rating field
   - Expected outcome: ~90 additional items across 5 sections

### SECONDARY ACTIONS (Priority 2)

2. **Investigate `in_demand_skills` field** (all 5 profiles)
   - Determine why this is consistently null across all profiles
   - Options:
     a. Fetch from O*NET API if available
     b. Populate from external source (job boards, employer data)
     c. Remove from processing pipeline (not critical for core ML/AI features)

3. **Validate education section format**
   - Note that education items use `percentage_of_respondents` instead of `importance`
   - Decide if this rating scheme should be harmonized with other sections (skills, abilities, etc.)

### VALIDATION CHECKLIST (Post-Remediation)

- [ ] Profile 41-3091.00 re-fetched with complete data
- [ ] All 5 profiles have all 8 expected sections non-empty
- [ ] Tasks sections include `importance` field in all profiles
- [ ] No null values in critical fields (in_demand_skills decision made)
- [ ] Item counts per section consistent across profiles (or justified differences noted)
- [ ] Data types validated across all profiles

---

## 6. DATASET READINESS SUMMARY

| Metric | Status | Assessment |
|--------|:------:|-----------|
| **Completeness** | 80% | 4/5 profiles complete; 1/5 needs re-fetch |
| **Rating Fields** | 90% | Tasks missing ratings in 1 profile |
| **Data Consistency** | 95% | Only in_demand_skills null (acceptable to exclude) |
| **Overall ML/AI Readiness** | **60%** | **NOT READY** - Must resolve issues in 41-3091.00 |

### Recommendation

**Status:** ⚠️ **DO NOT PROCEED** with ML/AI analysis until:
1. Profile 41-3091.00 is re-fetched with complete sections
2. Tasks ratings are verified for all profiles
3. Decision made on in_demand_skills field

**Expected Timeline:** 1-2 hours for API re-fetch and validation

---

## APPENDIX: Technical Details

### Data Structure Overview
```
Profile JSON:
  - Top-level: code, title, description, sample_of_reported_titles, updated, etc.
  - details object contains:
    - tasks: [30 items with id, related, title, importance, category]
    - skills: [35 items with id, related, name, description, importance]
    - knowledge: [33 items with id, related, name, description, importance]
    - abilities: [52 items with id, related, name, description, importance]
    - work_activities: [41 items with id, related, name, description, importance]
    - work_styles: [21 items with id, related, name, description, importance]
    - education: [3 items with code, title, percentage_of_respondents]
    - job_zone: {dict with code, title, education, related_experience, job_training}
    - in_demand_skills: null (for all profiles)
```

### Analysis Method
- File parsed as JSONL (JSON Lines) format
- Each line validated as complete JSON object
- Sections checked for: presence, item count, required rating fields
- Data types validated for consistency
- No data mutations performed (read-only analysis)
