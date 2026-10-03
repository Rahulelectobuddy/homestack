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
    Tries free APIs, falls back to estimated spot-based rates or fallback constants.
    """
    gold_fallback = FALLBACK_PRICES["gold_10g_inr"]
    silver_fallback = FALLBACK_PRICES["silver_1kg_inr"]

    try:
        # Try fetching spot metals in USD (e.g. from free gold-api)
        resp_gold = await client.get("https://api.gold-api.com/price/XAU", timeout=4.0)
        resp_silver = await client.get("https://api.gold-api.com/price/XAG", timeout=4.0)

        gold_usd_oz = None
        silver_usd_oz = None

        if resp_gold.status_code == 200:
            gold_usd_oz = resp_gold.json().get("price")
        if resp_silver.status_code == 200:
            silver_usd_oz = resp_silver.json().get("price")

        if gold_usd_oz and usd_inr > 0:
            # 1 troy oz = 31.1034768 grams. 10g = (gold_usd_oz / 31.1034768) * 10 * usd_inr
            # Add approx local import duty/GST multiplier (~1.15 in India)
            gold_10g = (float(gold_usd_oz) / 31.1034768) * 10.0 * usd_inr * 1.15
            gold_fallback = round(gold_10g, 2)

        if silver_usd_oz and usd_inr > 0:
            # 1 troy oz = 0.0311034768 kg. 1kg = (silver_usd_oz / 0.0311034768) * usd_inr * 1.15
            silver_1kg = (float(silver_usd_oz) / 31.1034768) * usd_inr * 1.15
            silver_fallback = round(silver_1kg, 2)
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
