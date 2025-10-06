#!/usr/bin/env python3
"""
Synthetic Monitoring Script - Run health checks continuously
"""

import asyncio
import argparse
from observability.synthetic_monitors import monitoring_service
from utils.logger import get_logger

logger = get_logger("synthetic_monitors_cli")


async def main():
    parser = argparse.ArgumentParser(description="Run synthetic monitors")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--username", type=str, default="admin", help="Username for login checks")
    parser.add_argument("--password", type=str, default="admin123", help="Password for login checks")
    parser.add_argument("--base-url", type=str, default="http://localhost:5000", help="Base URL to monitor")
    parser.add_argument("--once", action="store_true", help="Run checks once and exit")
    
    args = parser.parse_args()
    
    monitoring_service.base_url = args.base_url
    monitoring_service.setup_monitors(args.username, args.password)
    
    logger.info(f"🚀 Starting synthetic monitoring on {args.base_url}")
    logger.info(f"📊 Check interval: {args.interval}s")
    logger.info(f"👤 Using credentials: {args.username}")
    
    if args.once:
        logger.info("Running single check...")
        results = await monitoring_service.run_all_checks()
        print("\n" + "="*60)
        print("SYNTHETIC MONITORING RESULTS")
        print("="*60)
        for check in results["checks"]:
            status = "✅" if check["success"] else "❌"
            print(f"{status} {check['monitor']}: {check['latency_ms']:.2f}ms")
        
        if results["alerts"]:
            print("\n⚠️  ALERTS:")
            for alert in results["alerts"]:
                print(f"  - {alert['monitor']}: {alert['success_rate']*100:.1f}% (threshold: {alert['threshold']*100:.1f}%)")
        else:
            print("\n✅ No alerts")
        print("="*60 + "\n")
    else:
        try:
            await monitoring_service.start_monitoring(args.interval)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping monitoring...")
            monitoring_service.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
