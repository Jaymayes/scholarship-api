# Manual Intervention Manifest - ZT3G Auth Repair Sprint
**RUN_ID**: CEOSPRINT-20260123-EXEC-ZT3G-FIX-AUTH-009  
**Generated**: 2026-01-23T12:36:00Z  
**Status**: BLOCKED (External Access Required)

---

## Executive Summary

This workspace (A2 - scholarship-api) **cannot edit** the following services:
- **A1**: scholar-auth (https://replit.com/@jamarrlmayes/scholar-auth)
- **A5**: student-pilot (https://replit.com/@jamarrlmayes/student-pilot)
- **A6**: provider-register (https://replit.com/@jamarrlmayes/provider-register)

The CEO or workspace owner must apply the following changes.

---

## Current State Assessment

| Service | Health | Auth Endpoint | PKCE S256 | Status |
|---------|--------|--------------|-----------|--------|
| A1 scholar-auth | ✅ 200 | ✅ S256 in discovery | ✅ Ready | **OPERATIONAL** |
| A5 student-pilot | ✅ 200 | ❌ /api/auth/login 404 | ❌ Missing | **BLOCKED** |
| A6 provider-register | ✅ 200 | ⚠️ 302 (no PKCE) | ❌ Missing | **NEEDS UPGRADE** |
| A8 auto-com-center | ✅ 200 | N/A | N/A | **OPERATIONAL** |

---

## A1 (scholar-auth) - NO CHANGES REQUIRED ✅

A1 is **fully operational**:
- OIDC Discovery lists `code_challenge_methods_supported: ["S256"]` ✅
- Health: 200, Readyz: 200 ✅
- DB pool: healthy, circuit breaker closed ✅
- No 500 errors observed ✅

---

## A5 (student-pilot) - CREATE PKCE AUTH ENDPOINTS

### Problem
`/api/auth/login` returns **404** - endpoint does not exist.

### Required Files

**1. Create `utils/pkce.ts`**
```typescript
import crypto from 'crypto';

const b64u = (buf: Buffer): string => 
  buf.toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

export const generate = () => {
  const verifier = b64u(crypto.randomBytes(32));
  const challenge = b64u(
    crypto.createHash('sha256').update(verifier).digest()
  );
  return { verifier, challenge };
};

export const generateState = (): string => b64u(crypto.randomBytes(16));
export const generateNonce = (): string => b64u(crypto.randomBytes(16));
```

**2. Create or update `routes/auth.ts` (or equivalent)**
```typescript
import express from 'express';
import { generate, generateState, generateNonce } from '../utils/pkce';

const router = express.Router();

const OIDC_ISSUER_URL = process.env.OIDC_ISSUER_URL || 'https://scholar-auth-jamarrlmayes.replit.app';
const OIDC_CLIENT_ID = process.env.OIDC_CLIENT_ID || 'student-pilot';
const OIDC_CLIENT_SECRET = process.env.OIDC_CLIENT_SECRET;
const OIDC_REDIRECT_URI = process.env.OIDC_REDIRECT_URI || 'https://student-pilot-jamarrlmayes.replit.app/api/auth/callback';

// GET /api/auth/login - Initiate PKCE OAuth flow
router.get('/login', (req, res) => {
  const { verifier, challenge } = generate();
  const state = generateState();
  const nonce = generateNonce();
  
  // Store in session
  req.session.pkce = { verifier, state, nonce, ts: Date.now() };
  
  const params = new URLSearchParams({
    client_id: OIDC_CLIENT_ID,
    redirect_uri: OIDC_REDIRECT_URI,
    response_type: 'code',
    scope: 'openid profile email offline_access',
    state,
    nonce,
    code_challenge: challenge,
    code_challenge_method: 'S256'
  });
  
  res.redirect(302, `${OIDC_ISSUER_URL}/oidc/auth?${params}`);
});

// GET /api/auth/callback - Handle OAuth callback
router.get('/callback', async (req, res) => {
  const { code, state, error, error_description } = req.query;
  
  // Handle errors gracefully (no 500)
  if (error) {
    console.error('OAuth error:', { error, error_description });
    return res.redirect(`/login?error=${encodeURIComponent(String(error_description || error))}`);
  }
  
  const pkce = req.session?.pkce;
  if (!pkce || pkce.state !== state) {
    return res.redirect('/login?error=invalid_state');
  }
  
  // Check session age (5 min max)
  if (Date.now() - pkce.ts > 5 * 60 * 1000) {
    return res.redirect('/login?error=session_expired');
  }
  
  try {
    const tokenRes = await fetch(`${OIDC_ISSUER_URL}/oidc/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: String(code),
        redirect_uri: OIDC_REDIRECT_URI,
        client_id: OIDC_CLIENT_ID,
        ...(OIDC_CLIENT_SECRET && { client_secret: OIDC_CLIENT_SECRET }),
        code_verifier: pkce.verifier
      })
    });
    
    const tokens = await tokenRes.json();
    if (tokens.error) {
      throw new Error(tokens.error_description || tokens.error);
    }
    
    // Validate id_token (iss, aud, exp, nonce)
    // Set session and clean up PKCE
    req.session.user = tokens;
    delete req.session.pkce;
    
    res.redirect('/dashboard');
  } catch (err: any) {
    console.error('Token exchange failed:', err);
    res.redirect(`/login?error=${encodeURIComponent(err.message || 'token_exchange_failed')}`);
  }
});

// GET /api/auth/status
router.get('/status', (req, res) => {
  res.json({
    authenticated: !!req.session?.user,
    user: req.session?.user ? { email: req.session.user.email } : undefined
  });
});

// POST /api/auth/logout
router.post('/logout', (req, res) => {
  req.session.destroy(() => {
    res.clearCookie('connect.sid');
    res.redirect('/');
  });
});

export default router;
```

**3. Register routes in main app**
```typescript
// In app.ts or server.ts
import authRoutes from './routes/auth';
app.use('/api/auth', authRoutes);
```

**4. Environment Variables Required**
```env
OIDC_ISSUER_URL=https://scholar-auth-jamarrlmayes.replit.app
OIDC_CLIENT_ID=student-pilot
OIDC_CLIENT_SECRET=<your-client-secret>
OIDC_REDIRECT_URI=https://student-pilot-jamarrlmayes.replit.app/api/auth/callback
```

**5. Session Configuration**
```typescript
// Ensure session is configured
import session from 'express-session';

app.set('trust proxy', 1);
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,
    sameSite: 'none',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));
```

---

## A6 (provider-register) - ADD PKCE TO EXISTING AUTH

### Problem
`/api/auth/login` redirects to A1, but **without PKCE parameters**.

Current redirect URL:
```
/oidc/auth?client_id=provider-register&redirect_uri=...&response_type=code&scope=openid+email+profile&state=xxx
```

Required redirect URL:
```
/oidc/auth?client_id=provider-register&redirect_uri=...&response_type=code&scope=openid+email+profile&state=xxx&code_challenge=BASE64URL_HASH&code_challenge_method=S256
```

### Required Changes

**1. Find the auth login handler** (likely in `routes/auth.ts` or similar)

**2. Add PKCE helper** (same as A5, create `utils/pkce.ts`)

**3. Update `/api/auth/login` handler**
```typescript
// BEFORE (current - no PKCE)
const params = new URLSearchParams({
  client_id: 'provider-register',
  redirect_uri: REDIRECT_URI,
  response_type: 'code',
  scope: 'openid email profile',
  state: generatedState
});

// AFTER (with PKCE)
import { generate, generateState, generateNonce } from '../utils/pkce';

const { verifier, challenge } = generate();
const state = generateState();
const nonce = generateNonce();

req.session.pkce = { verifier, state, nonce, ts: Date.now() };

const params = new URLSearchParams({
  client_id: 'provider-register',
  redirect_uri: REDIRECT_URI,
  response_type: 'code',
  scope: 'openid email profile',
  state,
  nonce,
  code_challenge: challenge,           // ADD THIS
  code_challenge_method: 'S256'        // ADD THIS
});
```

**4. Update `/api/auth/callback` handler**
```typescript
// In token exchange, add code_verifier
const tokenRes = await fetch(`${OIDC_ISSUER_URL}/oidc/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: req.query.code,
    redirect_uri: REDIRECT_URI,
    client_id: 'provider-register',
    client_secret: process.env.OIDC_CLIENT_SECRET,
    code_verifier: req.session.pkce.verifier  // ADD THIS
  })
});
```

---

## A1 Client Registry Update (If Redirect URI Mismatch)

If A1 returns `invalid_redirect_uri`, update the client registry in A1's database:

```sql
-- For A5 (student-pilot)
UPDATE clients 
SET redirect_uris = ARRAY['https://student-pilot-jamarrlmayes.replit.app/api/auth/callback']
WHERE client_id = 'student-pilot';

-- For A6 (provider-register)
UPDATE clients 
SET redirect_uris = ARRAY['https://provider-register-jamarrlmayes.replit.app/api/auth/callback']
WHERE client_id = 'provider-register';
```

**IMPORTANT**: After updating, **restart A1** to flush cached registry.

---

## Verification Commands (Run After Fixes)

```bash
# Verify A5 PKCE
curl -sI "https://student-pilot-jamarrlmayes.replit.app/api/auth/login" | grep -i location
# EXPECTED: Location contains code_challenge= and code_challenge_method=S256

# Verify A6 PKCE  
curl -sI "https://provider-register-jamarrlmayes.replit.app/api/auth/login" | grep -i location
# EXPECTED: Location contains code_challenge= and code_challenge_method=S256

# Verify A1 accepts PKCE
curl -s "https://scholar-auth-jamarrlmayes.replit.app/.well-known/openid-configuration" | jq '.code_challenge_methods_supported'
# EXPECTED: ["S256"]
```

---

## Replit URLs for Direct Access

| Service | Replit URL |
|---------|------------|
| A1 scholar-auth | https://replit.com/@jamarrlmayes/scholar-auth |
| A5 student-pilot | https://replit.com/@jamarrlmayes/student-pilot |
| A6 provider-register | https://replit.com/@jamarrlmayes/provider-register |

---

## Attestation

**Status**: BLOCKED (External Access Required)

Cannot proceed with ZT3G verification until PKCE is implemented in A5 and added to A6.
CEO or workspace owner must apply these changes in the respective Replit workspaces.
