# PR Proposal: Issue D - A8 Demo Mode Revenue Visualization

## Status: ⚠️ REQUIRES A8 PROJECT ACCESS

### Problem

Finance tile shows $0 revenue because:
1. All test/demo transactions are filtered out
2. STRIPE_MODE=test events are excluded from live view
3. A3 orchestration may not have run to generate real transactions

This creates confusion where dashboard appears broken when it's actually working correctly (just with no live data).

### Proposed Fix

```python
from enum import Enum

class ViewMode(str, Enum):
    LIVE = "live"
    DEMO = "demo"
    ALL = "all"

@router.get("/api/revenue/summary")
async def revenue_summary(
    mode: ViewMode = ViewMode.LIVE,
    include_test: bool = False
):
    """
    Revenue summary with mode toggle
    - LIVE: Only production Stripe transactions
    - DEMO: Only test mode transactions (labeled)
    - ALL: Both (for debugging)
    """
    
    if mode == ViewMode.DEMO:
        query = """
            SELECT * FROM revenue_events 
            WHERE stripe_mode = 'test' OR namespace = 'simulated_audit'
        """
        label = "⚠️ DEMO MODE - Test Data Only"
        
    elif mode == ViewMode.ALL:
        query = "SELECT * FROM revenue_events"
        label = "⚠️ ALL DATA - Includes Test"
        
    else:  # LIVE (default)
        query = """
            SELECT * FROM revenue_events 
            WHERE stripe_mode = 'live' 
            AND namespace IS NULL
        """
        label = "Live Data"
    
    data = await db.fetch_all(query)
    total = sum(e['amount_cents'] for e in data) / 100
    
    return {
        "mode": mode,
        "label": label,
        "total_revenue_usd": total,
        "transaction_count": len(data),
        "data": data[:100]  # Limit response size
    }
```

### UI Treatment

```html
<!-- Demo Mode Badge -->
<div class="revenue-tile">
  <div v-if="mode === 'demo'" class="demo-badge">
    ⚠️ DEMO MODE - Test Data Only
  </div>
  <div class="revenue-amount">${{ total }}</div>
</div>

<style>
.demo-badge {
  background: #fef3c7;
  color: #92400e;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 8px;
}
</style>
```

### Namespace Filtering

All audit/test events include:
```json
{
  "namespace": "simulated_audit",
  "simulated": true,
  "stripe_mode": "test"
}
```

These are filtered from LIVE mode but visible in DEMO mode.

### "$0 Revenue" Explanation

The $0 revenue is **NOT a bug**. It indicates:
1. No real Stripe payments have been processed
2. A3 orchestration (which generates real transactions) hasn't run
3. All visible data is test/demo mode

**To see non-zero revenue**: Either run A3 orchestration with real payments, or use Demo Mode toggle.

### Rollback Plan

1. Remove mode parameter
2. Keep existing live-only filter
3. Users can access test data via direct DB queries

### Action Required

This fix requires access to the A8 (auto_com_center) project. Cannot be implemented from A2.
