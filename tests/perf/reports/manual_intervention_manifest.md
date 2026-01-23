# Manual Intervention Manifest - ZT3G Auth Fix
**RUN_ID**: CEOSPRINT-20260123-EXEC-ZT3G-FIX-AUTH-005  
**Generated**: 2026-01-23T11:01:00Z  
**Status**: BLOCKED (External Access Required)

---

## Executive Summary

This workspace (A2 - scholarship-api) **cannot edit** the following services:
- **A1**: scholar-auth (https://replit.com/@jamarrlmayes/scholar-auth)
- **A5**: student-pilot (https://replit.com/@jamarrlmayes/student-pilot)
- **A6**: provider-register (https://replit.com/@jamarrlmayes/provider-register)

The following PKCE implementation changes are required in those workspaces.

---

## Issue Analysis

### A1 (scholar-auth) - OPERATIONAL ✅
- OIDC Discovery: Lists `code_challenge_methods_supported: ["S256"]`
- Health/Readyz: Both return 200
- **No changes required** - A1 already supports PKCE

### A5 (student-pilot) - NEEDS PKCE IMPLEMENTATION ❌
- `/api/auth/login`: Returns 404 (endpoint missing)
- Auth endpoints exist but don't redirect with PKCE

### A6 (provider-register) - NEEDS PKCE UPGRADE ⚠️
- `/api/auth/login`: Returns 302 to A1 ✅
- **BUT**: Redirect URL missing `code_challenge` and `code_challenge_method` parameters
- Example current redirect:
  ```
  /oidc/auth?client_id=provider-register&redirect_uri=...&response_type=code&scope=openid+email+profile&state=xxx
  ```
- **Required** redirect should include:
  ```
  ...&code_challenge=BASE64URL_HASH&code_challenge_method=S256
  ```

---

## Required Changes

### A5 (student-pilot) - Create PKCE Auth Endpoints

**File**: `routes/auth.js` or `src/auth/routes.ts` (create if missing)

```javascript
const crypto = require('crypto');

// Helper functions
function base64URLEncode(buffer) {
  return buffer.toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

function generatePKCE() {
  const verifier = base64URLEncode(crypto.randomBytes(32));
  const challenge = base64URLEncode(
    crypto.createHash('sha256').update(verifier).digest()
  );
  return { verifier, challenge };
}

// GET /api/auth/login
app.get('/api/auth/login', (req, res) => {
  const { verifier, challenge } = generatePKCE();
  const state = base64URLEncode(crypto.randomBytes(16));
  const nonce = base64URLEncode(crypto.randomBytes(16));
  
  // Store in session
  req.session.pkce = { verifier, state, nonce, ts: Date.now() };
  
  const params = new URLSearchParams({
    client_id: process.env.OIDC_CLIENT_ID || 'student-pilot',
    redirect_uri: process.env.OIDC_REDIRECT_URI || 'https://student-pilot-jamarrlmayes.replit.app/api/auth/callback',
    response_type: 'code',
    scope: 'openid email profile',
    state,
    nonce,
    code_challenge: challenge,
    code_challenge_method: 'S256'
  });
  
  const authUrl = `${process.env.OIDC_ISSUER_URL || 'https://scholar-auth-jamarrlmayes.replit.app'}/oidc/auth?${params}`;
  res.redirect(302, authUrl);
});

// GET /api/auth/callback
app.get('/api/auth/callback', async (req, res) => {
  const { code, state, error, error_description } = req.query;
  
  if (error) {
    console.error('OAuth error:', { error, error_description });
    return res.redirect(`/login?error=${encodeURIComponent(error_description || error)}`);
  }
  
  const pkce = req.session?.pkce;
  if (!pkce || pkce.state !== state) {
    return res.redirect('/login?error=invalid_state');
  }
  
  try {
    const tokenRes = await fetch(`${process.env.OIDC_ISSUER_URL}/oidc/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: process.env.OIDC_REDIRECT_URI,
        client_id: process.env.OIDC_CLIENT_ID,
        client_secret: process.env.OIDC_CLIENT_SECRET,
        code_verifier: pkce.verifier
      })
    });
    
    const tokens = await tokenRes.json();
    if (tokens.error) throw new Error(tokens.error_description || tokens.error);
    
    // Set session and redirect
    req.session.user = tokens;
    delete req.session.pkce;
    res.redirect('/dashboard');
  } catch (err) {
    console.error('Token exchange failed:', err);
    res.redirect('/login?error=token_exchange_failed');
  }
});
```

**Environment Variables Required**:
```
OIDC_CLIENT_ID=student-pilot
OIDC_CLIENT_SECRET=<secret>
OIDC_ISSUER_URL=https://scholar-auth-jamarrlmayes.replit.app
OIDC_REDIRECT_URI=https://student-pilot-jamarrlmayes.replit.app/api/auth/callback
```

---

### A6 (provider-register) - Add PKCE to Existing Auth

**Current Issue**: The `/api/auth/login` endpoint redirects to A1 but WITHOUT PKCE parameters.

**Fix**: Update the auth route to include PKCE. Look for the file handling `/api/auth/login` and add:

```javascript
// Add PKCE generation
const { verifier, challenge } = generatePKCE(); // Use same helper as above

// Store verifier in session
req.session.pkce_verifier = verifier;

// Add to redirect URL
const params = new URLSearchParams({
  // ... existing params
  code_challenge: challenge,
  code_challenge_method: 'S256'
});
```

**Update callback** to include `code_verifier` in token exchange:
```javascript
body: new URLSearchParams({
  // ... existing params
  code_verifier: req.session.pkce_verifier
})
```

---

## Replit URLs for Direct Access

| Service | Replit URL |
|---------|------------|
| A1 scholar-auth | https://replit.com/@jamarrlmayes/scholar-auth |
| A5 student-pilot | https://replit.com/@jamarrlmayes/student-pilot |
| A6 provider-register | https://replit.com/@jamarrlmayes/provider-register |

---

## Verification Commands (Run After Fixes)

```bash
# Verify A5 PKCE
curl -sI "https://student-pilot-jamarrlmayes.replit.app/api/auth/login" | grep -i location
# Should contain: code_challenge=... and code_challenge_method=S256

# Verify A6 PKCE
curl -sI "https://provider-register-jamarrlmayes.replit.app/api/auth/login" | grep -i location
# Should contain: code_challenge=... and code_challenge_method=S256
```

---

## Current Service Status

| Service | Health | Auth Flow | PKCE |
|---------|--------|-----------|------|
| A1 scholar-auth | ✅ 200 | ✅ S256 supported | ✅ Ready |
| A5 student-pilot | ✅ 200 | ❌ /api/auth/login 404 | ❌ Needs implementation |
| A6 provider-register | ✅ 200 | ⚠️ Redirects | ❌ Missing code_challenge |
| A8 auto-com-center | ✅ 200 | N/A | N/A |

---

## Attestation

**Status**: BLOCKED (External Access Required)

Cannot proceed with ZT3G verification until PKCE is implemented in A5 and A6.
CEO or workspace owner must apply these changes in the respective Replit workspaces.
