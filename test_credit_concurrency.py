#!/usr/bin/env python3
"""
Acceptance tests for credit ledger concurrency and idempotency
Per master prompt requirements
"""
import asyncio
import aiohttp
import time
from typing import List, Dict, Any

BASE_URL = "http://localhost:5000"

# Mock JWT token (for testing - replace with real auth in production)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJ0ZXN0LWFkbWluIiwicm9sZXMiOlsiYWRtaW4iXSwiZW1haWwiOiJhZG1pbkB0ZXN0LmNvbSIsImlhdCI6MTcwMDAwMDAwMCwiZXhwIjoyMDAwMDAwMDAwLCJpc3MiOiJzY2hvbGFyX2F1dGgifQ.test"
STUDENT_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJ0ZXN0LXN0dWRlbnQiLCJyb2xlcyI6WyJzdHVkZW50Il0sImVtYWlsIjoic3R1ZGVudEB0ZXN0LmNvbSIsImlhdCI6MTcwMDAwMDAwMCwiZXhwIjoyMDAwMDAwMDAwLCJpc3MiOiJzY2hvbGFyX2F1dGgifQ.test"


async def test_concurrent_debits_same_idempotency_key():
    """
    Test: 100 parallel debit requests with same Idempotency-Key
    Expected: Exactly one ledger entry, others get cached response
    """
    print("\n" + "="*80)
    print("TEST 1: 100 Parallel Debits with Same Idempotency Key")
    print("="*80)
    
    user_id = "test-student"
    idempotency_key = f"test-concurrent-{int(time.time()*1000)}"
    
    # First, credit the account with enough balance
    async with aiohttp.ClientSession() as session:
        print(f"\n📝 Setup: Crediting user {user_id} with 1000.0 credits...")
        credit_resp = await session.post(
            f"{BASE_URL}/api/v1/credits/credit",
            json={
                "user_id": user_id,
                "amount": 1000.0,
                "reason": "Test credit for concurrency test"
            },
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Idempotency-Key": f"setup-credit-{idempotency_key}"
            }
        )
        credit_data = await credit_resp.json()
        print(f"✅ Initial balance: {credit_data.get('balance', 'N/A')}")
    
    # Now launch 100 parallel debit requests with the SAME idempotency key
    async def make_debit_request(session: aiohttp.ClientSession, request_num: int):
        try:
            start = time.time()
            resp = await session.post(
                f"{BASE_URL}/api/v1/credits/debit",
                json={
                    "user_id": user_id,
                    "amount": 10.0,
                    "purpose": f"Parallel test request #{request_num}"
                },
                headers={
                    "Authorization": f"Bearer {STUDENT_TOKEN}",
                    "Idempotency-Key": idempotency_key
                }
            )
            elapsed = (time.time() - start) * 1000
            data = await resp.json()
            return {
                "request_num": request_num,
                "status": resp.status,
                "balance": data.get("balance"),
                "id": data.get("id"),
                "elapsed_ms": elapsed
            }
        except Exception as e:
            return {
                "request_num": request_num,
                "status": "error",
                "error": str(e)
            }
    
    print(f"\n🚀 Launching 100 parallel debit requests...")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [make_debit_request(session, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
    
    total_time = (time.time() - start_time) * 1000
    
    # Analyze results
    successful = [r for r in results if r.get("status") == 200]
    errors = [r for r in results if r.get("status") != 200]
    unique_ids = set(r.get("id") for r in successful if r.get("id"))
    unique_balances = set(r.get("balance") for r in successful if r.get("balance") is not None)
    
    print(f"\n📊 RESULTS:")
    print(f"   Total requests: 100")
    print(f"   Successful (200): {len(successful)}")
    print(f"   Errors: {len(errors)}")
    print(f"   Unique ledger IDs: {len(unique_ids)}")
    print(f"   Unique balances returned: {len(unique_balances)}")
    print(f"   Total time: {total_time:.2f}ms")
    print(f"   Avg latency: {sum(r.get('elapsed_ms', 0) for r in successful) / len(successful) if successful else 0:.2f}ms")
    
    # Master prompt requirement: exactly one ledger entry
    if len(unique_ids) == 1:
        print(f"\n✅ PASS: Exactly one ledger entry created (ID: {list(unique_ids)[0]})")
    else:
        print(f"\n❌ FAIL: Expected 1 ledger entry, got {len(unique_ids)}")
        print(f"   IDs: {unique_ids}")
    
    if len(unique_balances) == 1:
        print(f"✅ PASS: All responses returned same balance ({list(unique_balances)[0]})")
    else:
        print(f"❌ FAIL: Inconsistent balances returned: {unique_balances}")
    
    return len(unique_ids) == 1 and len(unique_balances) == 1


async def test_overdraw():
    """
    Test: Attempt to debit more than available balance
    Expected: 409 status with clear error message
    """
    print("\n" + "="*80)
    print("TEST 2: Overdraw Protection")
    print("="*80)
    
    user_id = "test-overdraw-user"
    
    async with aiohttp.ClientSession() as session:
        # Credit user with 50 credits
        print(f"\n📝 Setup: Crediting user {user_id} with 50.0 credits...")
        await session.post(
            f"{BASE_URL}/api/v1/credits/credit",
            json={
                "user_id": user_id,
                "amount": 50.0,
                "reason": "Overdraw test setup"
            },
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Idempotency-Key": f"overdraw-setup-{int(time.time()*1000)}"
            }
        )
        
        # Attempt to debit 100 credits (more than available)
        print(f"\n🚀 Attempting to debit 100.0 credits (should fail)...")
        resp = await session.post(
            f"{BASE_URL}/api/v1/credits/debit",
            json={
                "user_id": user_id,
                "amount": 100.0,
                "purpose": "Overdraw attempt"
            },
            headers={
                "Authorization": f"Bearer {STUDENT_TOKEN}",
                "Idempotency-Key": f"overdraw-test-{int(time.time()*1000)}"
            }
        )
        
        data = await resp.json()
        
        print(f"\n📊 RESULTS:")
        print(f"   Status code: {resp.status}")
        print(f"   Response: {data}")
        
        if resp.status == 409:
            print(f"\n✅ PASS: Overdraw rejected with 409 status")
            if "insufficient" in data.get("detail", "").lower():
                print(f"✅ PASS: Clear error message about insufficient balance")
                return True
            else:
                print(f"⚠️  WARNING: Error message could be clearer")
                return True
        else:
            print(f"\n❌ FAIL: Expected 409, got {resp.status}")
            return False


async def test_idempotent_replay():
    """
    Test: Same idempotency key returns cached result
    Expected: Same transaction ID and balance on replay
    """
    print("\n" + "="*80)
    print("TEST 3: Idempotent Replay")
    print("="*80)
    
    user_id = "test-replay-user"
    idempotency_key = f"replay-test-{int(time.time()*1000)}"
    
    async with aiohttp.ClientSession() as session:
        # First request
        print(f"\n📝 First request...")
        resp1 = await session.post(
            f"{BASE_URL}/api/v1/credits/credit",
            json={
                "user_id": user_id,
                "amount": 25.0,
                "reason": "Idempotency test"
            },
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Idempotency-Key": idempotency_key
            }
        )
        data1 = await resp1.json()
        
        # Second request with same key
        print(f"\n📝 Second request (replay with same key)...")
        resp2 = await session.post(
            f"{BASE_URL}/api/v1/credits/credit",
            json={
                "user_id": user_id,
                "amount": 25.0,
                "reason": "Idempotency test"
            },
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Idempotency-Key": idempotency_key
            }
        )
        data2 = await resp2.json()
        
        print(f"\n📊 RESULTS:")
        print(f"   First response:  ID={data1.get('id')}, Balance={data1.get('balance')}")
        print(f"   Second response: ID={data2.get('id')}, Balance={data2.get('balance')}")
        
        if data1.get('id') == data2.get('id') and data1.get('balance') == data2.get('balance'):
            print(f"\n✅ PASS: Idempotent replay returned exact same result")
            return True
        else:
            print(f"\n❌ FAIL: Responses differ")
            return False


async def main():
    print("\n" + "="*80)
    print("CREDIT LEDGER CONCURRENCY & IDEMPOTENCY ACCEPTANCE TESTS")
    print("Per Master Prompt Requirements")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Concurrent Debits (100 parallel, same key)", await test_concurrent_debits_same_idempotency_key()))
    results.append(("Overdraw Protection", await test_overdraw()))
    results.append(("Idempotent Replay", await test_idempotent_replay()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n{'='*80}")
    print(f"OVERALL: {passed_count}/{total_count} tests passed")
    print(f"{'='*80}\n")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
