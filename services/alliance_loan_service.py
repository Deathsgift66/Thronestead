"""Service functions for alliance loans and repayments."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from .resource_service import validate_resource


def create_loan(
    db: Session,
    alliance_id: int,
    borrower_user_id: str,
    resource_type: str,
    amount: int,
    interest_rate: float,
    due_date: datetime,
    schedule: Optional[Iterable[dict]] = None,
) -> int:
    """Create a loan and optional repayment schedule."""
    validate_resource(resource_type)
    row = db.execute(
        text(
            """
            INSERT INTO alliance_loans (
                alliance_id, borrower_user_id, resource_type, amount,
                interest_rate, due_date
            ) VALUES (
                :aid, :uid, :res, :amt, :rate, :due
            ) RETURNING loan_id
            """
        ),
        {
            "aid": alliance_id,
            "uid": borrower_user_id,
            "res": resource_type,
            "amt": amount,
            "rate": interest_rate,
            "due": due_date,
        },
    ).fetchone()
    loan_id = row[0]

    if schedule:
        for item in schedule:
            db.execute(
                text(
                    """
                    INSERT INTO alliance_loan_repayments (
                        loan_id, due_date, amount_due, status
                    ) VALUES (:lid, :due, :amt, 'pending')
                    """
                ),
                {"lid": loan_id, "due": item["due_date"], "amt": item["amount"]},
            )
    db.commit()
    return loan_id


def list_loans(db: Session, alliance_id: int) -> list[dict]:
    """Return loans and repayment schedules for an alliance."""
    loans = db.execute(
        text(
            """
            SELECT al.*
              FROM alliance_loans al
              JOIN users u ON u.user_id = al.borrower_user_id
             WHERE al.alliance_id = :aid AND NOT u.is_banned
             ORDER BY al.loan_id
            """
        ),
        {"aid": alliance_id},
    ).fetchall()

    results: list[dict] = []
    for loan in loans:
        sched = db.execute(
            text(
                """
                SELECT schedule_id, due_date, amount_due, amount_paid, status
                FROM alliance_loan_repayments
                WHERE loan_id = :lid
                ORDER BY due_date
                """
            ),
            {"lid": loan["loan_id"]},
        ).fetchall()
        results.append(
            {
                **dict(loan._mapping),
                "repayments": [dict(r._mapping) for r in sched],
            }
        )
    return results


def repay_schedule(db: Session, schedule_id: int, amount: int) -> None:
    """Apply a repayment amount to a schedule entry and loan."""
    row = db.execute(
        text(
            """
            SELECT loan_id, amount_due, amount_paid
            FROM alliance_loan_repayments
            WHERE schedule_id = :sid
            """
        ),
        {"sid": schedule_id},
    ).fetchone()
    if not row:
        raise ValueError("Schedule entry not found")

    new_paid = min(row.amount_paid + amount, row.amount_due)
    db.execute(
        text(
            """
            UPDATE alliance_loan_repayments
               SET amount_paid = :paid,
                   status = CASE WHEN :paid >= amount_due THEN 'paid' ELSE 'pending' END,
                   paid_at = CASE WHEN :paid >= amount_due THEN now() ELSE paid_at END
             WHERE schedule_id = :sid
            """
        ),
        {"sid": schedule_id, "paid": new_paid},
    )
    db.execute(
        text(
            """
            UPDATE alliance_loans
               SET amount_repaid = amount_repaid + :inc
             WHERE loan_id = :lid
            """
        ),
        {"lid": row.loan_id, "inc": amount},
    )
    db.commit()
