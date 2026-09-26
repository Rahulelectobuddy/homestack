#!/bin/bash
set -e

echo "🚀 RedBus Scraper Container Started."
echo "📅 Schedule: Scraper will run immediately on start and repeat every 3 hours."

INTERVAL_SECONDS=10800

# Loop indefinitely to execute cli.py every 3 hours
while true; do
    echo "=================================================="
    echo "⏰ [$(date '+%Y-%m-%d %H:%M:%S')] Triggering Scheduled RedBus Scrape..."
    echo "=================================================="
    
    python /app/cli.py || echo "⚠️ Scrape run completed with warnings or errors."
    
    echo "=================================================="
    echo "😴 Scrape run finished. Sleeping for 3 hours..."
    echo "=================================================="
    sleep $INTERVAL_SECONDS
done
