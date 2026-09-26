import os
from datetime import datetime, timedelta

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "redbus_tracker.db")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

# RedBus Route Config
SOURCE = "Pune"
DESTINATION = "Indore"
REDBUS_ROUTE_SLUG = "pune-to-indore"
BASE_URL = f"https://www.redbus.in/bus-tickets/{REDBUS_ROUTE_SLUG}"

# Default Scraping Parameters
DEFAULT_HEADLESS = True
DEFAULT_SCRAPE_DAYS = 21
DEFAULT_TOILET_ONLY = True
VIEWPORT = {"width": 1280, "height": 800}
PAGE_LOAD_TIMEOUT_MS = 60000
SCROLL_PAUSE_TIME_SEC = 2
MAX_SCROLL_ATTEMPTS = 15

# User Agents Pool for Rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def format_date_for_redbus(dt: datetime) -> str:
    """Format date for RedBus URL / query format (e.g. 25-Sep-2026)."""
    return dt.strftime("%d-%b-%Y")

def get_default_travel_dates(days_ahead=21):
    """Generate list of travel dates starting from tomorrow for N days ahead (default 21)."""
    today = datetime.now()
    dates = []
    for i in range(1, days_ahead + 1):
        target_date = today + timedelta(days=i)
        dates.append(target_date.strftime("%Y-%m-%d"))
    return dates
