
# COMPREHENSIVE QA TEST REPORT
**Generated:** 2025-09-30 13:41:17  
**API Endpoint:** https://scholarship-api-jamarrlmayes.replit.app

## 📊 EXECUTIVE SUMMARY

**Total Tests Executed:** 13  
**Passed:** 7 (53.8%)  
**Failed:** 6 (46.2%)

## 🧪 DETAILED TEST RESULTS


### Health check endpoint
- **Endpoint:** `/health`
- **Status:** ✅ PASS
- **Response Time:** 70ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 70ms
- **Trace ID:** 39c1260f-c1f9-4fca-8b1e-01ad313ad94d

### API info endpoint
- **Endpoint:** `/api`
- **Status:** ✅ PASS
- **Response Time:** 20ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 20ms
- **Trace ID:** a7ce8ee7-cd90-434f-8e70-6226cf9b47c0

### Simple login endpoint
- **Endpoint:** `/api/v1/auth/login-simple`
- **Status:** ❌ FAIL
- **Response Time:** 20ms
- **Status Code:** 403 (Expected: 200)
- **Details:** Response time: 20ms
- **Trace ID:** 87730b28-ab49-4347-a403-ef481ddb59eb

### Basic search query - engineering
- **Endpoint:** `/api/v1/search?q=engineering`
- **Status:** ❌ FAIL
- **Response Time:** 44ms
- **Status Code:** 429 (Expected: 200)
- **Details:** Response time: 44ms
- **Trace ID:** de9cb3cd-00a3-43c9-a104-65d64603b054

### Search with pagination
- **Endpoint:** `/api/v1/search?q=stem&page=1&page_size=10`
- **Status:** ❌ FAIL
- **Response Time:** 42ms
- **Status Code:** 429 (Expected: 200)
- **Details:** Response time: 42ms
- **Trace ID:** 77021e8d-7c2a-434b-aad0-33d176790f8c

### Empty search query
- **Endpoint:** `/api/v1/search?q=`
- **Status:** ❌ FAIL
- **Response Time:** 36ms
- **Status Code:** 429 (Expected: 400)
- **Details:** Response time: 36ms
- **Trace ID:** 4b2bae6a-221f-41a6-b88c-9f4bcc757845

### List all scholarships
- **Endpoint:** `/api/v1/scholarships`
- **Status:** ❌ FAIL
- **Response Time:** 50ms
- **Status Code:** 500 (Expected: 200)
- **Details:** Response time: 50ms

### Eligibility check
- **Endpoint:** `/api/v1/eligibility/check`
- **Status:** ❌ FAIL
- **Response Time:** 21ms
- **Status Code:** 403 (Expected: 200)
- **Details:** Response time: 21ms
- **Trace ID:** 29559e18-2f0e-497d-bf0f-939712e3566b

### Rate limit test 1/5
- **Endpoint:** `/health`
- **Status:** ✅ PASS
- **Response Time:** 35ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 35ms
- **Trace ID:** d5dd24ec-d3d9-4caf-8a94-b0de5d0cae01

### Rate limit test 2/5
- **Endpoint:** `/health`
- **Status:** ✅ PASS
- **Response Time:** 39ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 39ms
- **Trace ID:** d94222ae-8ffd-40bb-9d47-860cfefbb2f2

### Rate limit test 3/5
- **Endpoint:** `/health`
- **Status:** ✅ PASS
- **Response Time:** 37ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 37ms
- **Trace ID:** e44e30f5-7b3c-4022-a585-bcf909b3b8df

### Rate limit test 4/5
- **Endpoint:** `/health`
- **Status:** ✅ PASS
- **Response Time:** 19ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 19ms
- **Trace ID:** 017f4fe3-823d-4cbd-af04-4f563ec1183c

### Rate limit test 5/5
- **Endpoint:** `/health`
- **Status:** ✅ PASS
- **Response Time:** 34ms
- **Status Code:** 200 (Expected: 200)
- **Details:** Response time: 34ms
- **Trace ID:** 15cda3de-1b05-4fbf-b3ec-21c4ece4147f
