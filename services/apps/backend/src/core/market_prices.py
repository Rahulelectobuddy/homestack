import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Fallback default prices per specification
FALLBACK_PRICES = {
    "uber_usd": 76.50,
    "accenture_usd": 348.20,
    "usd_inr": 83.75,
    "gold_10g_inr": 75500.00,
    "silver_1kg_inr": 89000.00,
}

# In-memory short-term cache (TTL: 10 minutes)
_CACHE_TTL_SECONDS = 600
_cached_market_data: Optional[Dict[str, Any]] = None
_last_fetch_time: Optional[datetime] = None


async def _fetch_yahoo_price(client: httpx.AsyncClient, symbol: str, fallback: float) -> float:
    """Fetch live stock price from Yahoo Finance chart API with fallback."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = await client.get(url, headers=headers, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice")
            if price and float(price) > 0:
                return float(price)
    except Exception as e:
        logger.warning(f"Failed to fetch stock price for {symbol}: {e}")
    return fallback


async def _fetch_usd_inr_rate(client: httpx.AsyncClient, fallback: float) -> float:
    """Fetch USD/INR FX rate from open.er-api.com with fallback."""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        resp = await client.get(url, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            rates = data.get("rates", {})
            inr = rates.get("INR")
            if inr and float(inr) > 0:
                return float(inr)
    except Exception as e:
        logger.warning(f"Failed to fetch USD/INR rate: {e}")
    return fallback


async def _fetch_metals_prices(client: httpx.AsyncClient, usd_inr: float) -> tuple[float, float]:
    """
    Fetch Gold (10g) & Silver (1kg) rates in INR.
    Tries free APIs, validates unit scale, and falls back to standard Indian retail rate constants.
    """
    gold_fallback = FALLBACK_PRICES["gold_10g_inr"]
    silver_fallback = FALLBACK_PRICES["silver_1kg_inr"]

    try:
        resp_gold = await client.get("https://api.gold-api.com/price/XAU", timeout=4.0)
        resp_silver = await client.get("https://api.gold-api.com/price/XAG", timeout=4.0)

        gold_usd_oz = None
        silver_usd = None

        if resp_gold.status_code == 200:
            gold_usd_oz = resp_gold.json().get("price")
        if resp_silver.status_code == 200:
            silver_usd = resp_silver.json().get("price")

        if gold_usd_oz and usd_inr > 0:
            val = float(gold_usd_oz)
            if val > 500:  # Valid USD price per troy oz
                # 1 troy oz = 31.1034768g. 10g = (val / 31.1034768) * 10 * usd_inr * 1.15 (import duty/GST)
                gold_10g = (val / 31.1034768) * 10.0 * usd_inr * 1.15
                gold_fallback = round(gold_10g, 2)

        if silver_usd and usd_inr > 0:
            val = float(silver_usd)
            # 1 KG = 32.1507466 troy oz
            if val > 10.0:  # Price per troy oz (e.g. $30/oz)
                silver_1kg_usd = val * 32.1507466
            else:  # Price per gram (e.g. $0.98/g)
                silver_1kg_usd = val * 1000.0

            silver_1kg_inr = silver_1kg_usd * usd_inr * 1.12  # Add local Indian retail tax/duty factor
            if silver_1kg_inr >= 50000:  # Sanity check for 1kg Indian Silver rate
                silver_fallback = round(silver_1kg_inr, 2)

    except Exception as e:
        logger.warning(f"Metals API lookup note: using standard rates or fallback ({e})")

    return gold_fallback, silver_fallback


async def get_market_prices(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Asynchronously retrieves current market prices for UBER, ACN, USD/INR, Gold 10g, and Silver 1kg.
    Implements short-term memory caching and robust fallbacks so API failures never crash the system.
    """
    global _cached_market_data, _last_fetch_time

    now = datetime.now()
    if not force_refresh and _cached_market_data and _last_fetch_time:
        if (now - _last_fetch_time).total_seconds() < _CACHE_TTL_SECONDS:
            return _cached_market_data

    async with httpx.AsyncClient(timeout=6.0) as client:
        # Run fetches concurrently
        uber_task = _fetch_yahoo_price(client, "UBER", FALLBACK_PRICES["uber_usd"])
        acn_task = _fetch_yahoo_price(client, "ACN", FALLBACK_PRICES["accenture_usd"])
        usd_inr_task = _fetch_usd_inr_rate(client, FALLBACK_PRICES["usd_inr"])

        uber_usd, acn_usd, usd_inr = await asyncio.gather(uber_task, acn_task, usd_inr_task)
        gold_10g_inr, silver_1kg_inr = await _fetch_metals_prices(client, usd_inr)

    uber_inr = round(uber_usd * usd_inr, 2)
    acn_inr = round(acn_usd * usd_inr, 2)

    _cached_market_data = {
        "uber_usd": round(uber_usd, 2),
        "accenture_usd": round(acn_usd, 2),
        "usd_inr": round(usd_inr, 2),
        "gold_10g_inr": round(gold_10g_inr, 2),
        "silver_1kg_inr": round(silver_1kg_inr, 2),
        "uber_inr": uber_inr,
        "accenture_inr": acn_inr,
        "is_cached": not force_refresh,
        "last_updated": now.isoformat()
    }
    _last_fetch_time = now

    return _cached_market_data
