import os
import argparse
import sys
from datetime import datetime, timedelta

import config
import exporter
from scraper import run_scraper_sync

def main():
    parser = argparse.ArgumentParser(description="RedBus Pune -> Indore Bus Fare & Availability Scraper CLI")
    parser.add_argument("--date", type=str, help="Specific travel date YYYY-MM-DD", default=None)
    parser.add_argument("--days", type=int, help="Number of travel dates ahead to scrape (Default: 21 days)", default=21)
    parser.add_argument("--toilet-only", action="store_true", default=True, help="Filter only buses with toilet amenities (Default: True)")
    parser.add_argument("--all-buses", action="store_true", help="Include all buses regardless of toilet amenity")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible (non-headless) mode")
    parser.add_argument("--debug", action="store_true", help="Save PNG screenshots and HTML snapshots to debug_snapshots/ folder")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format (Default: csv)")
    parser.add_argument("--output", type=str, help="Custom output file path", default=None)

    args = parser.parse_args()

    headless = not args.no_headless
    debug = args.debug
    toilet_only = not args.all_buses if args.all_buses else args.toilet_only
    days = args.days if not args.date else 1

    if args.date:
        print(f"🚀 Launching RedBus Scraper for Pune -> Indore | Date: {args.date} (Toilet Only: {toilet_only}, Headless: {headless}, Debug: {debug})...")
        results = run_scraper_sync(travel_date=args.date, days=1, toilet_only=toilet_only, headless=headless, debug=debug)
    else:
        print(f"🚀 Launching RedBus Scraper for Pune -> Indore | Next {days} Days (Toilet Only: {toilet_only}, Headless: {headless}, Debug: {debug})...")
        results = run_scraper_sync(days=days, toilet_only=toilet_only, headless=headless, debug=debug)

    print(f"\n✅ Scraping completed! Extracted {len(results)} bus records.")

    if results:
        # 1. Print formatted terminal table
        print("\n" + exporter.format_terminal_table(results))

        # 2. Export timestamped CSV for pipeline ingestion
        csv_path = exporter.export_to_csv(
            records=results, 
            travel_date=args.date if args.date else None, 
            output_path=args.output if args.format == "csv" else None
        )
        latest_csv = os.path.join(config.EXPORTS_DIR, "redbus_latest_fares.csv")
        print(f"\n📁 Timestamped CSV Exported : {csv_path}")
        print(f"📁 Pipeline Target CSV Updated: {latest_csv}")

        # 3. Export JSON if requested
        if args.format == "json" and args.output:
            json_path = exporter.export_to_json(results, args.output)
            print(f"📁 JSON File Exported        : {json_path}")

if __name__ == "__main__":
    main()
