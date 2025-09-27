"""
Host Allowlist Verification for Staging Deployment
Executive mandate: Confirm SEO and health-check hosts are covered
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.staging_config import STAGING_HOST_ALLOWLIST, validate_host_allowlist_coverage

def verify_critical_host_coverage():
    """Verify all critical hosts are covered in allowlist"""
    
    print("🔍 HOST ALLOWLIST VERIFICATION")
    print("=" * 50)
    
    # Check coverage
    coverage = validate_host_allowlist_coverage()
    
    print("✅ CRITICAL HOST COVERAGE:")
    for check, status in coverage.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {check}: {status}")
    
    print(f"\n📋 TOTAL ALLOWLIST ENTRIES: {len(STAGING_HOST_ALLOWLIST)}")
    
    print("\n🛡️ SEO AUTO PAGE MAKER DOMAINS:")
    seo_domains = [host for host in STAGING_HOST_ALLOWLIST if any(term in host.lower() for term in ['seo', 'auto-pages', 'scholarships', 'education'])]
    for domain in seo_domains:
        print(f"  ✅ {domain}")
    
    print("\n🏥 HEALTH CHECK & MONITORING DOMAINS:")
    health_domains = [host for host in STAGING_HOST_ALLOWLIST if any(term in host.lower() for term in ['health', 'monitoring', 'uptime', 'lb-health', 'elb'])]
    for domain in health_domains:
        print(f"  ✅ {domain}")
    
    print("\n🕷️ SEARCH ENGINE CRAWLER DOMAINS:")
    print("  ℹ️ NOTE: Crawlers send target site's Host header, not their own identity")
    print("  ℹ️ Crawler access controlled by allowlist of our service domains")
    
    print("\n🔧 REPLIT STAGING DOMAINS:")
    replit_domains = [host for host in STAGING_HOST_ALLOWLIST if any(term in host for term in ['replit', 'repl.co', 'picard', 'kirk', 'spock'])]
    for domain in replit_domains:
        print(f"  ✅ {domain}")
    
    # Executive confirmation
    all_critical_covered = all(coverage.values())
    min_seo_coverage = len(seo_domains) >= 4  # We have 4 SEO domains
    min_health_coverage = len(health_domains) >= 3
    min_replit_coverage = len(replit_domains) >= 5
    
    print(f"\n🎯 EXECUTIVE CONFIRMATION:")
    print(f"  ✅ All critical checks passed: {all_critical_covered}")
    print(f"  ✅ SEO domain coverage adequate: {min_seo_coverage} ({len(seo_domains)} domains)")
    print(f"  ✅ Health check coverage adequate: {min_health_coverage} ({len(health_domains)} domains)")
    print(f"  ✅ Replit staging coverage adequate: {min_replit_coverage} ({len(replit_domains)} domains)")
    print(f"  ℹ️ Crawler access: Controlled via service domain allowlist (no separate entries needed)")
    
    overall_status = all_critical_covered and min_seo_coverage and min_health_coverage and min_replit_coverage
    
    if overall_status:
        print(f"\n🎉 HOST ALLOWLIST VERIFICATION: ✅ PASSED")
        print(f"   Ready for staging deployment with full SEO/health protection")
    else:
        print(f"\n⚠️ HOST ALLOWLIST VERIFICATION: ❌ FAILED")
        print(f"   Critical domains missing - staging deployment blocked")
    
    return {
        "verification_status": "PASSED" if overall_status else "FAILED",
        "total_hosts": len(STAGING_HOST_ALLOWLIST),
        "seo_domains": len(seo_domains),
        "health_domains": len(health_domains), 
        "replit_domains": len(replit_domains),
        "coverage_checks": coverage,
        "executive_approved": overall_status
    }

if __name__ == "__main__":
    result = verify_critical_host_coverage()
    print(f"\nResult: {result}")