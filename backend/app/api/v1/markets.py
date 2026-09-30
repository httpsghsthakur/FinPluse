"""Market Data API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional

from app.api.deps import get_current_user
from app.db.models.user import User
from app.services.market_data.upstox import UpstoxProvider
from app.services.technical_analysis import TechnicalAnalysisEngine

router = APIRouter()
provider = UpstoxProvider()


@router.get("/overview")
async def get_market_overview(current_user: User = Depends(get_current_user)):
    """Get high-level market overview (NIFTY, BANK NIFTY, SENSEX, INDIA VIX)."""
    # Key Indian indices
    indices = [
        {"symbol": "NIFTY 50", "key": "NSE_INDEX|Nifty 50"},
        {"symbol": "BANK NIFTY", "key": "NSE_INDEX|Nifty Bank"},
        {"symbol": "SENSEX", "key": "BSE_INDEX|SENSEX"},
        {"symbol": "INDIA VIX", "key": "NSE_INDEX|India VIX"}
    ]
    
    results = []
    for idx in indices:
        quote = await provider.get_market_quote(idx["key"])
        if quote:
            results.append({
                "symbol": idx["symbol"],
                "ltp": quote.get("last_price"),
                "change": quote.get("net_change"),
                "change_percent": quote.get("net_change_percent"),
                "status": "active"
            })
        else:
            results.append({
                "symbol": idx["symbol"],
                "status": "unavailable"
            })
            
    return {"data": results}


@router.get("/stocks/search")
async def search_stocks(
    q: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user)
):
    """Search for stocks by symbol or name."""
    results = await provider.search_instruments(q)
    return {"data": results}


@router.get("/stocks/{instrument_key}")
async def get_stock_quote(
    instrument_key: str,
    current_user: User = Depends(get_current_user)
):
    """Get live quote and info for a specific stock."""
    quote = await provider.get_market_quote(instrument_key)
    if not quote:
        raise HTTPException(status_code=404, detail="Stock data unavailable")
    
    return {"data": quote}


@router.get("/stocks/{instrument_key}/candles")
async def get_stock_candles(
    instrument_key: str,
    interval: str = Query("1d"),
    from_date: str = Query(..., description="Format: YYYY-MM-DD"),
    to_date: str = Query(..., description="Format: YYYY-MM-DD"),
    include_technicals: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get historical candles and optionally compute technical indicators."""
    candles = await provider.get_historical_candles(instrument_key, interval, from_date, to_date)
    
    if include_technicals and candles:
        # Sort ascending by timestamp for accurate TA
        candles = sorted(candles, key=lambda x: x["timestamp"])
        candles = TechnicalAnalysisEngine.analyze(candles)
        
    return {"data": candles}
