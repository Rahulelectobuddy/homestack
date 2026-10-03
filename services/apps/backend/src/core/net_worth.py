import os
import logging
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field

from .market_prices import get_market_prices

logger = logging.getLogger(__name__)

# --- Pydantic DTO Schemas ---

class AccountBalanceBase(BaseModel):
    account_name: str = Field(..., example="HDFC Savings")
    account_type: str = Field(..., example="asset", description="'asset' or 'liability'")
    balance_inr: float = Field(..., ge=0, example=250000.0)
    monthly_return_pct: float = Field(default=0.0, example=0.5, description="Monthly expected yield/cost percentage")

class AccountBalanceCreate(AccountBalanceBase):
    pass

class AccountBalanceOut(AccountBalanceBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SpecialAssetUpdateItem(BaseModel):
    asset_key: str
    quantity: float = Field(..., ge=0)
    manual_price_override_inr: Optional[float] = None

class BulkSpecialAssetUpdate(BaseModel):
    uber_stock: Optional[float] = None
    accenture_stock: Optional[float] = None
    gold_10g: Optional[float] = None
    silver_1kg: Optional[float] = None
    holdings: Optional[List[SpecialAssetUpdateItem]] = None

class SpecialAssetHoldingOut(BaseModel):
    id: int
    asset_key: str
    asset_name: str
    quantity: float
    unit_price_usd: Optional[float] = None
    unit_price_inr: float
    total_valuation_inr: float
    manual_price_override_inr: Optional[float] = None

class NetWorthSummaryOut(BaseModel):
    net_worth_inr: float
    total_assets_inr: float
    total_liabilities_inr: float
    total_account_assets_inr: float
    special_investments_inr: float
    projected_monthly_income_inr: float
    usd_inr_rate: float
    special_investments_breakdown: List[SpecialAssetHoldingOut]
    accounts: List[AccountBalanceOut]
    market_prices: Dict[str, Any]

# --- In-Memory Fallback State (used if PostgreSQL DB is starting or unavailable) ---

_FALLBACK_ACCOUNTS = [
    {
        "id": 1,
        "account_name": "HDFC Savings Account",
        "account_type": "asset",
        "balance_inr": 250000.0,
        "monthly_return_pct": 0.35,
        "created_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-01T00:00:00Z",
    },
    {
        "id": 2,
        "account_name": "Zerodha Equity & MF",
        "account_type": "asset",
        "balance_inr": 450000.0,
        "monthly_return_pct": 1.00,
        "created_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-01T00:00:00Z",
    },
    {
        "id": 3,
        "account_name": "SBI Home Loan",
        "account_type": "liability",
        "balance_inr": 1500000.0,
        "monthly_return_pct": 0.71,
        "created_at": "2026-10-01T00:00:00Z",
        "updated_at": "2026-10-01T00:00:00Z",
    },
]

_FALLBACK_SPECIAL_HOLDINGS = [
    {"id": 1, "asset_key": "uber_stock", "asset_name": "Uber Technologies (UBER)", "quantity": 15.0, "manual_price_override_inr": None},
    {"id": 2, "asset_key": "accenture_stock", "asset_name": "Accenture plc (ACN)", "quantity": 5.0, "manual_price_override_inr": None},
    {"id": 3, "asset_key": "gold_10g", "asset_name": "Gold 24K (10-Gram units)", "quantity": 2.0, "manual_price_override_inr": None},
    {"id": 4, "asset_key": "silver_1kg", "asset_name": "Silver (1-Kg units)", "quantity": 1.0, "manual_price_override_inr": None},
]


def _get_db_connection():
    db_url = os.getenv("DATABASE_URL", "postgresql://homelab:homelab123@postgres:5432/homelab_db")
    return psycopg2.connect(db_url)


def init_db_tables():
    """Ensure net worth database tables exist and seed initial holdings."""
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS account_balances (
                id SERIAL PRIMARY KEY,
                account_name VARCHAR(255) NOT NULL,
                account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability')),
                balance_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
                monthly_return_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS special_asset_holdings (
                id SERIAL PRIMARY KEY,
                asset_key VARCHAR(50) UNIQUE NOT NULL,
                asset_name VARCHAR(100) NOT NULL,
                quantity NUMERIC(15, 4) NOT NULL DEFAULT 0.0000,
                manual_price_override_inr NUMERIC(15, 2) DEFAULT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Insert initial holdings if empty
        defaults = [
            ('uber_stock', 'Uber Technologies (UBER)', 15.0),
            ('accenture_stock', 'Accenture plc (ACN)', 5.0),
            ('gold_10g', 'Gold 24K (10-Gram units)', 2.0),
            ('silver_1kg', 'Silver (1-Kg units)', 1.0)
        ]
        for key, name, qty in defaults:
            cur.execute("""
                INSERT INTO special_asset_holdings (asset_key, asset_name, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (asset_key) DO NOTHING;
            """, (key, name, qty))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Database init table notice: {e}")


def fetch_all_accounts() -> List[Dict[str, Any]]:
    """Retrieve all asset accounts and liabilities from database with fallback."""
    init_db_tables()
    try:
        conn = _get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, account_name, account_type, balance_inr, monthly_return_pct, created_at, updated_at FROM account_balances ORDER BY id ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if rows:
            formatted = []
            for r in rows:
                formatted.append({
                    "id": r["id"],
                    "account_name": r["account_name"],
                    "account_type": r["account_type"],
                    "balance_inr": float(r["balance_inr"]),
                    "monthly_return_pct": float(r["monthly_return_pct"]),
                    "created_at": str(r["created_at"]) if r["created_at"] else None,
                    "updated_at": str(r["updated_at"]) if r["updated_at"] else None,
                })
            return formatted
    except Exception as e:
        logger.warning(f"Account DB fetch failed, using fallback memory state: {e}")
    return _FALLBACK_ACCOUNTS


def add_account(data: AccountBalanceCreate) -> Dict[str, Any]:
    """Add a new asset account or loan liability."""
    init_db_tables()
    try:
        conn = _get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO account_balances (account_name, account_type, balance_inr, monthly_return_pct)
            VALUES (%s, %s, %s, %s)
            RETURNING id, account_name, account_type, balance_inr, monthly_return_pct, created_at, updated_at
        """, (data.account_name, data.account_type, data.balance_inr, data.monthly_return_pct))
        new_acc = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if new_acc:
            return {
                "id": new_acc["id"],
                "account_name": new_acc["account_name"],
                "account_type": new_acc["account_type"],
                "balance_inr": float(new_acc["balance_inr"]),
                "monthly_return_pct": float(new_acc["monthly_return_pct"]),
                "created_at": str(new_acc["created_at"]),
                "updated_at": str(new_acc["updated_at"]),
            }
    except Exception as e:
        logger.warning(f"Add account DB failed, inserting to memory state: {e}")

    new_id = max([a["id"] for a in _FALLBACK_ACCOUNTS], default=0) + 1
    new_item = {
        "id": new_id,
        "account_name": data.account_name,
        "account_type": data.account_type,
        "balance_inr": float(data.balance_inr),
        "monthly_return_pct": float(data.monthly_return_pct),
        "created_at": "2026-10-03T00:00:00Z",
        "updated_at": "2026-10-03T00:00:00Z",
    }
    _FALLBACK_ACCOUNTS.append(new_item)
    return new_item


def delete_account_by_id(account_id: int) -> bool:
    """Delete an account or liability by primary key ID."""
    init_db_tables()
    deleted = False
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM account_balances WHERE id = %s", (account_id,))
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        if rows_affected > 0:
            deleted = True
    except Exception as e:
        logger.warning(f"Delete account DB failed: {e}")

    global _FALLBACK_ACCOUNTS
    initial_len = len(_FALLBACK_ACCOUNTS)
    _FALLBACK_ACCOUNTS = [a for a in _FALLBACK_ACCOUNTS if a["id"] != account_id]
    if len(_FALLBACK_ACCOUNTS) < initial_len:
        deleted = True

    return deleted


def fetch_special_holdings() -> List[Dict[str, Any]]:
    """Retrieve 4 special investment assets."""
    init_db_tables()
    try:
        conn = _get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, asset_key, asset_name, quantity, manual_price_override_inr FROM special_asset_holdings ORDER BY id ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if rows:
            return [
                {
                    "id": r["id"],
                    "asset_key": r["asset_key"],
                    "asset_name": r["asset_name"],
                    "quantity": float(r["quantity"]),
                    "manual_price_override_inr": float(r["manual_price_override_inr"]) if r["manual_price_override_inr"] is not None else None
                }
                for r in rows
            ]
    except Exception as e:
        logger.warning(f"Special holdings DB fetch failed, using fallback: {e}")
    return _FALLBACK_SPECIAL_HOLDINGS


def update_special_holdings(payload: BulkSpecialAssetUpdate) -> List[Dict[str, Any]]:
    """Bulk update quantities or manual price overrides for special investments."""
    init_db_tables()
    updates = {}
    if payload.uber_stock is not None:
        updates["uber_stock"] = payload.uber_stock
    if payload.accenture_stock is not None:
        updates["accenture_stock"] = payload.accenture_stock
    if payload.gold_10g is not None:
        updates["gold_10g"] = payload.gold_10g
    if payload.silver_1kg is not None:
        updates["silver_1kg"] = payload.silver_1kg
    
    if payload.holdings:
        for item in payload.holdings:
            updates[item.asset_key] = item.quantity

    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        for key, qty in updates.items():
            cur.execute("""
                UPDATE special_asset_holdings 
                SET quantity = %s, updated_at = CURRENT_TIMESTAMP
                WHERE asset_key = %s
            """, (qty, key))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Special holdings DB update warning: {e}")

    # Synchronize fallback memory state
    for h in _FALLBACK_SPECIAL_HOLDINGS:
        if h["asset_key"] in updates:
            h["quantity"] = float(updates[h["asset_key"]])

    return fetch_special_holdings()


async def calculate_net_worth_summary(force_refresh_market: bool = False) -> NetWorthSummaryOut:
    """
    Computes complete Net Worth Summary:
    Total Net Worth = (Total Account Assets + Valuation of 4 Special Investments) - Total Liabilities
    Projected Monthly Return Income = sum(Asset Balances * Monthly Return %) - sum(Liability Balances * Monthly Return %)
    """
    market = await get_market_prices(force_refresh=force_refresh_market)
    accounts = fetch_all_accounts()
    holdings = fetch_special_holdings()

    total_account_assets = 0.0
    total_liabilities = 0.0
    projected_monthly_income = 0.0

    for acc in accounts:
        bal = acc["balance_inr"]
        return_pct = acc["monthly_return_pct"]
        monthly_factor = bal * (return_pct / 100.0)

        if acc["account_type"] == "asset":
            total_account_assets += bal
            projected_monthly_income += monthly_factor
        elif acc["account_type"] == "liability":
            total_liabilities += bal
            projected_monthly_income -= monthly_factor

    usd_inr = market["usd_inr"]
    uber_usd = market["uber_usd"]
    acn_usd = market["accenture_usd"]
    gold_10g_inr = market["gold_10g_inr"]
    silver_1kg_inr = market["silver_1kg_inr"]

    special_investments_breakdown = []
    special_investments_total_inr = 0.0

    for h in holdings:
        key = h["asset_key"]
        qty = h["quantity"]
        override = h.get("manual_price_override_inr")

        unit_usd = None
        if key == "uber_stock":
            unit_usd = uber_usd
            unit_inr = override if override is not None else market["uber_inr"]
        elif key == "accenture_stock":
            unit_usd = acn_usd
            unit_inr = override if override is not None else market["accenture_inr"]
        elif key == "gold_10g":
            unit_inr = override if override is not None else gold_10g_inr
        elif key == "silver_1kg":
            unit_inr = override if override is not None else silver_1kg_inr
        else:
            unit_inr = override if override is not None else 0.0

        valuation = round(qty * unit_inr, 2)
        special_investments_total_inr += valuation

        special_investments_breakdown.append(
            SpecialAssetHoldingOut(
                id=h["id"],
                asset_key=key,
                asset_name=h["asset_name"],
                quantity=qty,
                unit_price_usd=unit_usd,
                unit_price_inr=unit_inr,
                total_valuation_inr=valuation,
                manual_price_override_inr=override,
            )
        )

    total_assets = round(total_account_assets + special_investments_total_inr, 2)
    total_liabilities = round(total_liabilities, 2)
    net_worth = round(total_assets - total_liabilities, 2)
    projected_monthly_income = round(projected_monthly_income, 2)

    return NetWorthSummaryOut(
        net_worth_inr=net_worth,
        total_assets_inr=total_assets,
        total_liabilities_inr=total_liabilities,
        total_account_assets_inr=round(total_account_assets, 2),
        special_investments_inr=round(special_investments_total_inr, 2),
        projected_monthly_income_inr=projected_monthly_income,
        usd_inr_rate=usd_inr,
        special_investments_breakdown=special_investments_breakdown,
        accounts=[AccountBalanceOut(**a) for a in accounts],
        market_prices=market,
    )
