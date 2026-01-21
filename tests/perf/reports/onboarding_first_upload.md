# Onboarding Orchestrator + First-Upload Pivot

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1-058  
**Service**: onboarding-orchestrator  
**Sprint**: V2 Sprint-1 (72h)

## Overview

The Onboarding Orchestrator manages the user signup flow with an immediate pivot to document upload, maximizing conversion by capturing user intent while motivation is highest.

## Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     User Signup Event                         │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              Create "Guest" Record in DataService             │
│         (minimal data: email, created_at, status=guest)       │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│           Immediate Prompt: Upload Transcript/Essay           │
│      "Get matched with scholarships in 60 seconds"            │
└───────────────────────────┬──────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    ┌───────────────┐               ┌───────────────┐
    │ User Uploads  │               │ User Skips    │
    │   Document    │               │   Upload      │
    └───────┬───────┘               └───────┬───────┘
            │                               │
            ▼                               ▼
    ┌───────────────┐               ┌───────────────┐
    │ DocumentUploaded              │ Schedule       │
    │ Event → A8    │               │ Follow-up     │
    └───────┬───────┘               └───────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────┐
│                   NLP Analyzer Service                        │
│    - Extract GPA, major, activities, achievements             │
│    - Generate implicit_fit scores per scholarship category    │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              Persist Scores via DataService                   │
│    POST /api/v1/users/{id}/implicit_fit                       │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              Write Events to A8 Event Bus                     │
│    - DocumentUploaded { user_id, doc_type, size }             │
│    - DocumentScored { user_id, categories, scores }           │
└──────────────────────────────────────────────────────────────┘
```

## Event Schemas

### DocumentUploaded
```json
{
  "event": "DocumentUploaded",
  "version": "1.0",
  "timestamp": "2026-01-21T08:00:00Z",
  "data": {
    "user_id": "uuid",
    "document_type": "transcript|essay|resume",
    "file_size_bytes": 102400,
    "source": "onboarding|dashboard"
  }
}
```

### DocumentScored
```json
{
  "event": "DocumentScored",
  "version": "1.0",
  "timestamp": "2026-01-21T08:00:05Z",
  "data": {
    "user_id": "uuid",
    "document_id": "uuid",
    "implicit_fit_scores": {
      "stem": 0.85,
      "arts": 0.45,
      "athletics": 0.20,
      "community_service": 0.75
    },
    "extracted_gpa": 3.7,
    "extracted_major": "Computer Science"
  }
}
```

## NLP Analyzer Integration

### Input
- Document binary (PDF, DOCX, TXT)
- User ID for correlation

### Output
- Extracted structured data (GPA, major, activities)
- Category fit scores (0.0 - 1.0)
- Confidence level

### Performance Targets
| Metric | Target |
|--------|--------|
| Processing time | <5 seconds |
| Extraction accuracy | >90% |
| Score correlation | >0.8 with manual review |

## UX Improvements (From Paid Pilot)

### Sticky "Resume Upload" CTA
- Persisted in local storage
- Shows prefilled step state on return
- 100% rollout (CEO authorized)

### Value-Pack Nudge
- 3-pack anchor pricing
- 100% rollout (CEO authorized)

## Success Metrics

| Metric | Target | Tracking |
|--------|--------|----------|
| Upload rate (signup +60s) | >40% | A8 funnel |
| Time to first match | <90s | A8 event delta |
| Score accuracy | >90% | Manual sample |
| Conversion (upload→purchase) | >15% | A8 funnel |

## Sprint-1 Deliverables

| Deliverable | Status |
|-------------|--------|
| Flow design | ✅ Complete |
| Event schemas | ✅ Complete |
| NLP integration spec | ✅ Complete |
| UX improvements defined | ✅ Complete |

**Status**: ✅ DESIGN COMPLETE
