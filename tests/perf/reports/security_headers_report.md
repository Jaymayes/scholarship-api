# Security Headers Report

**RUN_ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-017
**Timestamp**: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Headers by App


### A1 (scholar-auth)

| Header | Value |
|--------|-------|
| Strict-Transport-Security | strict-transport-security: max-age=63072000; includeSubDomai |
| Content-Security-Policy | content-security-policy: default-src 'self'; script-src 'sel |
| X-Frame-Options | x-frame-options: DENY |
| X-Content-Type-Options | x-content-type-options: nosniff |


### A2 (scholarship-api)

| Header | Value |
|--------|-------|
| Strict-Transport-Security | strict-transport-security: max-age=63072000; includeSubDomai |
| Content-Security-Policy | content-security-policy: default-src 'none'; connect-src 'se |
| X-Frame-Options | x-frame-options: DENY |
| X-Content-Type-Options | x-content-type-options: nosniff |


### A4 (auto-page-maker)

| Header | Value |
|--------|-------|
| Strict-Transport-Security | strict-transport-security: max-age=63072000; includeSubDomai |
| Content-Security-Policy | content-security-policy: default-src 'self';script-src 'self |
| X-Frame-Options | x-frame-options: DENY |
| X-Content-Type-Options | x-content-type-options: nosniff |


### A5 (student-pilot)

| Header | Value |
|--------|-------|
| Strict-Transport-Security | strict-transport-security: max-age=63072000; includeSubDomai |
| Content-Security-Policy | content-security-policy: default-src 'self';base-uri 'none'; |
| X-Frame-Options | x-frame-options: DENY |
| X-Content-Type-Options | x-content-type-options: nosniff |


### A6 (scholarship-sage)

| Header | Value |
|--------|-------|
| Strict-Transport-Security | strict-transport-security: max-age=63072000; includeSubDomai |
| Content-Security-Policy | content-security-policy: default-src 'self'; script-src 'sel |
| X-Frame-Options | x-frame-options: DENY |
| X-Content-Type-Options | x-content-type-options: nosniff |


### A7 (scholaraiadvisor.com)

| Header | Value |
|--------|-------|
| Strict-Transport-Security | strict-transport-security: max-age=63072000; includeSubDomai |
| Content-Security-Policy | content-security-policy: default-src 'self';script-src 'self |
| X-Frame-Options | x-frame-options: DENY |
| X-Content-Type-Options | x-content-type-options: nosniff |


## Summary

Most Replit-hosted apps have basic security headers applied by the platform.
Additional hardening can be added at the application level.

## Blocked Apps (A3, A8)

Security headers not checked - apps returning 404.
