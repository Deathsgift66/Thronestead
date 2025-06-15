# Project Name: Kingmakers Rise©
# File Name: trade_log_service.py
# Version: 6.13.2025.19.49 (Enhanced)
# Developer: Deathsgift66
# Description: Service functions to record and update trade transactions between kingdoms/alliances.

from __future__ import annotations
import logging
from typing import Optional

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover
    def text(q):  # type: ignore
        return q

    Session = object

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Trade Logging Services
# ------------------------------------------------------------

def record_trade(
    db: Session,
    resource: str,
    quantity: int,
    unit_price: Optional[float],
    buyer_id: Optional[str],
    seller_id: Optional[str],
    buyer_alliance_id: Optional[int],
    seller_alliance_id: Optional[int],
    buyer_name: Optional[str],
    seller_name: Optional[str],
    trade_type: str,
    trade_status: str = "completed",
    initiated_by_system: bool = False,
) -> int:
    """
    Logs a trade into the trade_logs table and returns the trade_id.

    Args:
        db: Active DB session
        resource: Resource being traded (e.g., 'gold', 'food')
        quantity: Amount of resource traded
        unit_price: Price per unit, if applicable
        buyer_id: UUID of the buyer kingdom
        seller_id: UUID of the seller kingdom
        buyer_alliance_id: Alliance ID of buyer
        seller_alliance_id: Alliance ID of seller
        buyer_name: Display name of buyer
        seller_name: Display name of seller
        trade_type: e.g., 'market_sale', 'direct_transfer', 'system_trade'
        trade_status: Status of the trade (default 'completed')
        initiated_by_system: True if automated system action

    Returns:
        int: ID of newly recorded trade (or 0 on failure)
    """
    try:
        result = db.execute(
            text("""
                INSERT INTO trade_logs (
                    resource, quantity, unit_price,
                    buyer_id, seller_id,
                    buyer_alliance_id, seller_alliance_id,
                    buyer_name, seller_name,
                    trade_type, trade_status, initiated_by_system
                ) VALUES (
                    :res, :qty, :price,
                    :buyer, :seller,
                    :buyer_a, :seller_a,
                    :buyer_n, :seller_n,
                    :ttype, :tstatus, :sys
                )
                RETURNING trade_id
            """),
            {
                "res": resource,
                "qty": quantity,
                "price": unit_price,
                "buyer": buyer_id,
                "seller": seller_id,
                "buyer_a": buyer_alliance_id,
                "seller_a": seller_alliance_id,
                "buyer_n": buyer_name,
                "seller_n": seller_name,
                "ttype": trade_type,
                "tstatus": trade_status,
                "sys": initiated_by_system,
            },
        )
        row = result.fetchone()
        trade_id = int(row[0]) if row else 0
        db.commit()
        return trade_id

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Trade log failed for %s x%d", resource, quantity)
        return 0


def update_trade_status(db: Session, trade_id: int, status: str) -> None:
    """
    Updates the trade status for an existing trade log row.

    Args:
        trade_id: ID of trade to update
        status: New status (e.g., 'cancelled', 'refunded')
    """
    try:
        db.execute(
            text("""
                UPDATE trade_logs
                   SET trade_status = :st, last_updated = now()
                 WHERE trade_id = :tid
            """),
            {"st": status, "tid": trade_id},
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.warning("Failed to update trade_id %s to status '%s'", trade_id, status)
