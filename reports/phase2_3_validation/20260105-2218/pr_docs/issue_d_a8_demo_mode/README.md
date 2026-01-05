# Issue D: A8 Demo Mode Toggle

## Status: NEW IMPLEMENTATION (Requires A8 Project Access)

## Problem
- Finance tile shows $0 revenue even though test events exist
- Test/demo data is correctly filtered from live view
- But there's no way to VIEW test data for demos and validation
- Creates confusion about whether system is working

## Solution
Feature-flagged "Demo Mode" toggle that:
1. When ON: Shows simulated/test revenue with clear "SIMULATED" labels
2. When OFF: Filters out test data (current behavior preserved)
3. Clear UI badge distinguishing demo from live mode
4. Scoped filtering by namespace and stripe_mode

## Design

### Filter Logic
```python
if demo_mode_enabled:
    # Show test data with labels
    query = "WHERE namespace = 'simulated_audit' OR stripe_mode = 'test'"
    label = "⚠️ DEMO MODE - Simulated Data"
else:
    # Live mode: exclude all test data
    query = "WHERE stripe_mode = 'live' AND namespace IS NULL"
    label = "Live Data"
```

### UI Treatment
- Visible badge in header: "🧪 DEMO MODE" or "📊 LIVE"
- Tile borders: Orange for demo, standard for live
- All values labeled when in demo mode

## Feature Flag
```python
DEMO_MODE_ENABLED = os.getenv("DEMO_MODE_ENABLED", "false").lower() == "true"
```

## Risk Analysis
- **Low Risk**: Read-only display change
- **Rollback**: Set `DEMO_MODE_ENABLED=false`
- **Safety**: Test data NEVER pollutes live analytics (filter logic unchanged)

## Endpoints
```
GET /api/tiles/revenue?mode=demo    # Show simulated data
GET /api/tiles/revenue?mode=live    # Show live data only (default)
GET /api/config/demo-mode           # Get current demo mode state
POST /api/config/demo-mode          # Toggle demo mode (admin only)
```

## Files to Create/Modify
- `routes/tiles.py` (add mode parameter)
- `services/revenue_aggregator.py` (add filter logic)
- `components/DemoModeBadge.vue` (UI badge)
- `store/config.js` (demo mode state)
