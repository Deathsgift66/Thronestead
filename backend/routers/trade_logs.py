from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TradeLog

router = APIRouter(prefix="/api/trade-logs", tags=["trade_logs"])


@router.get("")
def get_trade_logs(
    player_id: str | None = Query(None),
    alliance_id: int | None = Query(None),
    trade_type: str | None = Query(None),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    query = db.query(TradeLog)
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

    rows = (
        query.order_by(TradeLog.timestamp.desc()).limit(limit).all()
    )

    result = []
    for r in rows:
        result.append(
            {
                "trade_id": r.trade_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "resource": r.resource,
                "quantity": r.quantity,
                "unit_price": float(r.unit_price)
                if r.unit_price is not None
                else None,
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
        )
    return {"logs": result}
