#!/usr/bin/env python3
"""
Initial readiness probe - performs GET-only checks on all 8 apps
Generates preliminary findings for production readiness assessment
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

TIMEOUT = 10
CONFIG_PATH = Path(__file__).parent.parent / "shared" / "config.json"

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def check_app(app_key, app_config):
    """Perform read-only checks on a single app"""
    url = app_config["url"]
    name = app_config["name"]
    app_type = app_config["type"]
    
    result = {
        "app": app_key,
        "name": name,
        "type": app_type,
        "url": url,
        "reachable": False,
        "status_code": None,
        "ttfb_ms": None,
        "security_headers": {},
        "endpoints_checked": {},
        "issues": [],
        "readiness_score": 0
    }
    
    try:
        start = time.time()
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        ttfb = (time.time() - start) * 1000
        
        result["reachable"] = True
        result["status_code"] = response.status_code
        result["ttfb_ms"] = round(ttfb, 2)
        
        headers = response.headers
        result["security_headers"] = {
            "strict-transport-security": headers.get("strict-transport-security", "MISSING"),
            "content-security-policy": headers.get("content-security-policy", "MISSING"),
            "x-frame-options": headers.get("x-frame-options", "MISSING"),
            "x-content-type-options": headers.get("x-content-type-options", "MISSING"),
            "referrer-policy": headers.get("referrer-policy", "MISSING"),
            "permissions-policy": headers.get("permissions-policy", "MISSING")
        }
        
        if app_type == "api_service":
            endpoints = ["/health", "/status", "/metrics", "/docs", "/openapi.json", "/robots.txt"]
            for endpoint in endpoints:
                try:
                    ep_url = urljoin(url, endpoint)
                    ep_resp = requests.get(ep_url, timeout=5)
                    result["endpoints_checked"][endpoint] = ep_resp.status_code
                except:
                    result["endpoints_checked"][endpoint] = "FAILED"
        
        if response.status_code >= 400:
            result["issues"].append(f"HTTP {response.status_code} on root")
            result["readiness_score"] = 2
        elif ttfb > 3000:
            result["issues"].append(f"Slow TTFB: {ttfb:.0f}ms")
            result["readiness_score"] = 3
        else:
            missing_headers = [k for k, v in result["security_headers"].items() if v == "MISSING"]
            if len(missing_headers) > 3:
                result["issues"].append(f"Missing {len(missing_headers)} security headers")
                result["readiness_score"] = 4
            else:
                result["readiness_score"] = 5
                
    except requests.exceptions.Timeout:
        result["issues"].append("Connection timeout")
        result["readiness_score"] = 0
    except requests.exceptions.ConnectionError:
        result["issues"].append("Connection failed - app not reachable")
        result["readiness_score"] = 0
    except Exception as e:
        result["issues"].append(f"Error: {str(e)}")
        result["readiness_score"] = 1
    
    return result

def generate_report(results):
    """Generate markdown report from results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = Path(__file__).parent / f"readiness_report_{timestamp}.md"
    
    with open(report_path, "w") as f:
        f.write("# Scholar AI Advisor Ecosystem - Production Readiness Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write("## Executive Summary\n\n")
        
        total_apps = len(results)
        reachable = sum(1 for r in results if r["reachable"])
        avg_score = sum(r["readiness_score"] for r in results) / total_apps if total_apps > 0 else 0
        
        f.write(f"- **Total Apps:** {total_apps}\n")
        f.write(f"- **Reachable:** {reachable}/{total_apps}\n")
        f.write(f"- **Average Readiness Score:** {avg_score:.1f}/5.0\n\n")
        
        f.write("## Readiness Summary\n\n")
        f.write("| App | Type | Status | TTFB | Score | Issues |\n")
        f.write("|-----|------|--------|------|-------|--------|\n")
        
        for r in results:
            status = "✅" if r["reachable"] else "❌"
            ttfb = f"{r['ttfb_ms']}ms" if r['ttfb_ms'] else "N/A"
            score_emoji = ["❌", "🔴", "🟠", "🟡", "🟢", "✅"][r["readiness_score"]]
            issues = "; ".join(r["issues"][:2]) if r["issues"] else "None"
            
            f.write(f"| {r['name']} | {r['type']} | {status} | {ttfb} | {score_emoji} {r['readiness_score']}/5 | {issues} |\n")
        
        f.write("\n## Detailed Findings\n\n")
        
        for r in results:
            f.write(f"### {r['name']} ({r['app']})\n\n")
            f.write(f"- **URL:** {r['url']}\n")
            f.write(f"- **Type:** {r['type']}\n")
            f.write(f"- **Reachable:** {'Yes' if r['reachable'] else 'No'}\n")
            f.write(f"- **Status Code:** {r['status_code'] or 'N/A'}\n")
            f.write(f"- **TTFB:** {r['ttfb_ms']}ms\n" if r['ttfb_ms'] else "- **TTFB:** N/A\n")
            f.write(f"- **Readiness Score:** {r['readiness_score']}/5\n\n")
            
            if r["security_headers"]:
                f.write("**Security Headers:**\n")
                for header, value in r["security_headers"].items():
                    status = "✅" if value != "MISSING" else "❌"
                    f.write(f"- {status} `{header}`: {value if value != 'MISSING' else 'MISSING'}\n")
                f.write("\n")
            
            if r["endpoints_checked"]:
                f.write("**API Endpoints:**\n")
                for endpoint, status_code in r["endpoints_checked"].items():
                    status = "✅" if isinstance(status_code, int) and 200 <= status_code < 400 else "❌"
                    f.write(f"- {status} `{endpoint}`: {status_code}\n")
                f.write("\n")
            
            if r["issues"]:
                f.write("**Issues:**\n")
                for issue in r["issues"]:
                    f.write(f"- ⚠️ {issue}\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        f.write("## Readiness Scoring Guide\n\n")
        f.write("- **0** - Not reachable\n")
        f.write("- **1** - Major blockers (SSL/JS errors prevent use)\n")
        f.write("- **2** - Critical issues (HTTP errors, broken primary functionality)\n")
        f.write("- **3** - Usable with non-critical issues\n")
        f.write("- **4** - Near-ready (minor issues only)\n")
        f.write("- **5** - Production-ready\n\n")
        
        f.write("---\n\n")
        f.write("*This is a read-only assessment. No data was modified during testing.*\n")
    
    return report_path

def main():
    print("🔍 Scholar AI Advisor Ecosystem - Production Readiness Probe")
    print("=" * 70)
    print()
    
    config = load_config()
    apps = config["apps"]
    
    print(f"Checking {len(apps)} apps...\n")
    
    results = []
    for app_key, app_config in apps.items():
        print(f"Checking {app_config['name']}... ", end="", flush=True)
        result = check_app(app_key, app_config)
        results.append(result)
        
        status = "✅" if result["reachable"] else "❌"
        score = result["readiness_score"]
        print(f"{status} {score}/5")
    
    print()
    print("Generating report...")
    report_path = generate_report(results)
    
    print(f"\n✅ Report generated: {report_path}")
    print()
    
    avg_score = sum(r["readiness_score"] for r in results) / len(results)
    reachable = sum(1 for r in results if r["reachable"])
    
    print(f"📊 Summary:")
    print(f"   - Reachable: {reachable}/{len(results)}")
    print(f"   - Average Score: {avg_score:.1f}/5.0")
    
    if avg_score >= 4.5:
        print(f"   - Status: ✅ Ecosystem ready for production")
    elif avg_score >= 3.5:
        print(f"   - Status: 🟢 Near-ready (minor issues)")
    elif avg_score >= 2.5:
        print(f"   - Status: 🟡 Needs work (non-critical issues)")
    else:
        print(f"   - Status: 🔴 Not ready (critical issues)")
    
    return results

if __name__ == "__main__":
    main()
