# Post-Republish Diff

**Run ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2S2-FIX-027  

---

## Changes Applied to A0 (This Session)

1. **DataService health endpoints** - Added to public bypass list in api_key_guard.py
2. **Security documentation** - Updated dataservice_security.md with role validation notes
3. **Checksums** - All artifacts regenerated with fresh hashes

---

## Changes NOT Applied (External Apps Blocked)

The following fixes from Phase A could not be applied as the apps are inaccessible:

- A1: trust proxy + SameSite cookie fix
- A2-A4: Health endpoint standardization
- A5: Stripe integration (keys, stripe.js, checkout CTA)
- A6: JSON-only /api/providers
- A7: Sitemap verification
- A8: Telemetry fallback/backfill (rate limited)

See manual_intervention_manifest.md for detailed fix instructions.
