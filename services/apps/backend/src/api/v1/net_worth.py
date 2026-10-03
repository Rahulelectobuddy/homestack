from ...core.net_worth import (
    NetWorthSummaryOut,
    AccountBalanceCreate,
    AccountBalanceUpdate,
    AccountBalanceOut,
    AccountAuditLogOut,
    BulkSpecialAssetUpdate,
    SpecialAssetHoldingOut,
    ProjectionsDataOut,
    NetWorthSnapshotOut,
    fetch_all_accounts,
    add_account,
    update_account_by_id,
    delete_account_by_id,
    fetch_audit_logs,
    save_net_worth_snapshot,
    fetch_special_holdings,
    update_special_holdings,
    calculate_net_worth_summary,
    get_projection_vs_actual_data,
)

router = APIRouter(prefix="/api/v1/net-worth", tags=["Net Worth Tracker"])


@router.get("/summary", response_model=NetWorthSummaryOut)
async def get_net_worth_summary():
    """
    Returns full Net Worth aggregation, account breakdown, and current live investment valuations.
    """
    return await calculate_net_worth_summary(force_refresh_market=False)


@router.get("/projections", response_model=ProjectionsDataOut)
async def get_net_worth_projections():
    """
    Returns Projection vs Actual time-series trajectory over a 12-month window.
    """
    return await get_projection_vs_actual_data()


@router.post("/snapshots")
async def trigger_net_worth_snapshot():
    """
    Trigger snapshot creation (invoked weekly by Airflow pipeline).
    """
    return await save_net_worth_snapshot()


@router.get("/audit-logs", response_model=List[AccountAuditLogOut])
async def get_account_audit_logs(account_id: Optional[int] = None):
    """
    Fetch audit history logs of all changes to bank accounts and loan liabilities.
    """
    logs = fetch_audit_logs(account_id=account_id)
    return [AccountAuditLogOut(**l) for l in logs]


@router.put("/accounts/{account_id}", response_model=AccountBalanceOut)
async def update_net_worth_account(account_id: int, account_update: AccountBalanceUpdate):
    """
    Update an existing account balance, type, or monthly return rate and record audit log.
    """
    updated = update_account_by_id(account_id, account_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    return AccountBalanceOut(**updated)




@router.post("/refresh", response_model=NetWorthSummaryOut)
async def refresh_net_worth_prices():
    """
    Triggers live market price fetching, updates holding valuations, and returns updated summary.
    """
    return await calculate_net_worth_summary(force_refresh_market=True)


@router.get("/accounts", response_model=List[AccountBalanceOut])
async def list_net_worth_accounts():
    """
    List all bank accounts and loans.
    """
    accounts = fetch_all_accounts()
    return [AccountBalanceOut(**a) for a in accounts]


@router.post("/accounts", response_model=AccountBalanceOut, status_code=status.HTTP_201_CREATED)
async def create_net_worth_account(account: AccountBalanceCreate):
    """
    Create a new asset account or loan liability.
    """
    if account.account_type not in ["asset", "liability"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account type must be 'asset' or 'liability'"
        )
    created = add_account(account)
    return AccountBalanceOut(**created)


@router.delete("/accounts/{account_id}")
async def delete_net_worth_account(account_id: int):
    """
    Delete an existing account or loan by ID.
    """
    deleted = delete_account_by_id(account_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID {account_id} not found"
        )
    return {"status": "success", "message": f"Account {account_id} deleted successfully"}


@router.get("/assets")
async def get_special_investment_assets():
    """
    Fetch current quantities of the 4 special investment assets.
    """
    return fetch_special_holdings()


@router.post("/assets")
async def bulk_update_special_assets(payload: BulkSpecialAssetUpdate):
    """
    Bulk update quantities for Uber shares, Accenture shares, Gold 10g units, and Silver 1kg units.
    """
    updated_holdings = update_special_holdings(payload)
    summary = await calculate_net_worth_summary(force_refresh_market=False)
    return {
        "status": "success",
        "message": "Special investment assets updated successfully",
        "holdings": updated_holdings,
        "summary": summary
    }
