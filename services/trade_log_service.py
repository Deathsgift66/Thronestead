from __future__ import annotations

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def record_trade(
    db: Session,
    resource: str,
    quantity: int,
    unit_price: float | None,
    buyer_id: str | None,
    seller_id: str | None,
    buyer_alliance_id: int | None,
    seller_alliance_id: int | None,
    buyer_name: str | None,
    seller_name: str | None,
    trade_type: str,
    trade_status: str = "completed",
    initiated_by_system: bool = False,
) -> int:
    """Insert a trade log row and return the trade_id."""
    result = db.execute(
        text(
            """
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
            ) RETURNING trade_id
            """
        ),
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
    trade_id = row[0] if row else 0
    db.commit()
    return trade_id


def update_trade_status(db: Session, trade_id: int, status: str) -> None:
    """Update trade_status for an existing trade log."""
    db.execute(
        text(
            "UPDATE trade_logs SET trade_status = :st, last_updated = now() "
            "WHERE trade_id = :tid"
        ),
        {"st": status, "tid": trade_id},
    )
    db.commit()
