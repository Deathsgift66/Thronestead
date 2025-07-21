# Project Name: Thronestead©
# File Name: trade_logs.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: trade_logs.py
Role: API routes for trade logs.
Version: 2025-06-21
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models import TradeLog

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/trade-logs", tags=["trade_logs"])


@router.get("", summary="Retrieve recent trade logs")
def get_trade_logs(
    player_id: Optional[str] = Query(None, description="Filter logs by player UUID"),
    alliance_id: Optional[int] = Query(None, description="Filter logs by alliance ID"),
    trade_type: Optional[str] = Query(
        None, description="Type of trade (e.g. market, direct, system)"
    ),
    start_date: Optional[str] = Query(
        None,
        description="ISO timestamp to filter trades occurring on or after this time",
    ),
    end_date: Optional[str] = Query(
        None,
        description="ISO timestamp to filter trades occurring on or before this time",
    ),
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of logs to return"
    ),
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Return recent trade logs, optionally filtered by player, alliance, or trade type.
    """
    query = db.query(TradeLog)

    def _parse_iso(value: Optional[str], name: str) -> Optional[datetime]:
        if value is None:
            return None
        try:
            if value.endswith("Z"):
                return datetime.fromisoformat(value[:-1] + "+00:00")
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid {name} format") from exc

    if player_id:
        query = query.filter(
            or_(TradeLog.buyer_id == player_id, TradeLog.seller_id == player_id)
        )
    if alliance_id:
        query = query.filter(
            or_(
                TradeLog.buyer_alliance_id == alliance_id,
                TradeLog.seller_alliance_id == alliance_id,
            )
        )
    if trade_type:
        query = query.filter(TradeLog.trade_type == trade_type)
    start_dt = _parse_iso(start_date, "start_date")
    if start_dt:
        query = query.filter(TradeLog.timestamp >= start_dt)
    end_dt = _parse_iso(end_date, "end_date")
    if end_dt:
        query = query.filter(TradeLog.timestamp <= end_dt)

    try:
        rows = query.order_by(TradeLog.timestamp.desc()).limit(limit).all()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Database query failed") from exc

    logs = [
        {
            "trade_id": r.trade_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "resource": r.resource,
            "quantity": r.quantity,
            "unit_price": float(r.unit_price) if r.unit_price is not None else None,
            "buyer_id": str(r.buyer_id) if r.buyer_id else None,
            "seller_id": str(r.seller_id) if r.seller_id else None,
            "buyer_alliance_id": r.buyer_alliance_id,
            "seller_alliance_id": r.seller_alliance_id,
            "buyer_name": r.buyer_name,
            "seller_name": r.seller_name,
            "trade_type": r.trade_type,
            "trade_status": r.trade_status,
            "initiated_by_system": r.initiated_by_system,
        }
        for r in rows
    ]

    return {"logs": logs}
