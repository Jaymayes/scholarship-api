# Hybrid Search Hard Filters Tuning Runbook

## Purpose
This runbook provides guidance for tuning the "Hard Filters" in the hybrid search system if valid scholarships are being hidden (False Negatives).

## Overview
The hybrid search applies hard eligibility filters to reduce False Positives (showing students scholarships they can't apply for). However, overly strict filters may cause False Negatives (hiding scholarships students ARE eligible for).

## Hard Filter Configuration

| Filter | Logic | Tunable Parameter |
|--------|-------|-------------------|
| Deadline | `scholarship.deadline >= NOW()` | N/A (always enforced) |
| GPA | `student.gpa >= scholarship.min_gpa` | Tolerance threshold |
| Residency | `student.state IN scholarship.residency_states` | State mapping |
| Major | `student.major IN scholarship.fields_of_study` | Field synonyms |

## Common False Negative Scenarios

### 1. GPA Threshold Too Strict
**Symptom**: Students with borderline GPAs (e.g., 3.48) are filtered from scholarships requiring 3.5 GPA.

**Solution**: Add a tolerance threshold in `hybrid_search_service.py`:
```python
GPA_TOLERANCE = 0.05  # Allow 3.45 GPA for 3.5 requirement

if student.gpa < (min_gpa - GPA_TOLERANCE):
    passed = False  # Only fail if significantly below
```

### 2. Major/Field Mismatch Due to Naming
**Symptom**: "Computer Science" student not matching "technology" scholarship.

**Solution**: Add field synonyms in `hybrid_search_service.py`:
```python
FIELD_SYNONYMS = {
    "computer_science": ["technology", "engineering", "science"],
    "biology": ["science", "medicine"],
    "economics": ["business", "social_sciences"]
}
```

### 3. State Residency Mismatch
**Symptom**: Student from "New York" not matching scholarship for "NY".

**Solution**: Normalize state inputs:
```python
STATE_MAPPINGS = {
    "new york": "NY",
    "california": "CA",
    # etc
}
```

## Tuning Procedure

1. **Identify False Negatives**:
   - Compare hybrid search results vs standard search results
   - Check logs for `filter_details` to see which filter caused removal

2. **Adjust Filter Tolerance**:
   ```python
   # In services/hybrid_search_service.py
   GPA_TOLERANCE = 0.05  # Adjust based on FN rate
   ```

3. **Test Impact**:
   ```bash
   # Before tuning
   curl "http://localhost:5000/api/v1/search/hybrid/public?student_gpa=3.48&limit=20"
   
   # After tuning (should show more results)
   ```

4. **Monitor FPR**:
   - Track `fpr_reduction_estimate` in responses
   - Target: 40-60% reduction while maintaining <5% False Negative rate

## Emergency Rollback

If hybrid search causes significant False Negatives:

1. Route traffic to standard search endpoint:
   ```python
   # In routers/search.py
   USE_HYBRID_SEARCH = False  # Toggle off
   ```

2. Or disable specific hard filters:
   ```python
   # In hybrid_search_service.py
   DISABLED_FILTERS = ["major"]  # Skip major filter
   ```

## Monitoring

Key metrics to track:
- `hybrid_search_filtered_out_count` - High values may indicate over-filtering
- `hybrid_search_fpr_reduction_estimate` - Target: 40-60%
- User complaints about missing scholarships

## Contact

For escalations:
- ML Team: ml-team@scholarai.example.com
- On-call: #ml-oncall Slack channel
