# A1 Cookie Validation
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030

## Status: BLOCKED

### Required Configuration
```javascript
app.set('trust proxy', 1);

const cookieOptions = {
  secure: true,
  sameSite: 'none',
  httpOnly: true,
  path: '/'
};
```

### Verification Command
```bash
curl -c cookies.txt -b cookies.txt "https://<A1_HOST>/auth/login" -v 2>&1 | grep "Set-Cookie"
```

**Expected**: `Set-Cookie: ... SameSite=None; Secure; HttpOnly`

## Verdict: BLOCKED - External workspace not accessible
