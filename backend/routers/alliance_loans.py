"""API routes for alliance loans."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import AllianceLoan, AllianceLoanRepayment, User
from services.alliance_loan_service import create_loan, list_loans, repay_schedule
from ..database import get_db
from ..security import require_user_id

router = APIRouter(prefix="/api/alliance-loans", tags=["alliance_loans"])


class RepaymentItem(BaseModel):
    due_date: datetime
    amount: int


class LoanCreatePayload(BaseModel):
    borrower_user_id: str
    resource_type: str
    amount: int
    interest_rate: float = 0.05
    due_date: datetime
    schedule: Optional[List[RepaymentItem]] = None


class RepayPayload(BaseModel):
    schedule_id: int
    amount: int


def get_alliance_info(db: Session, user_id: str) -> tuple[int, str]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    return user.alliance_id, user.alliance_role or "Member"


@router.get("")
def list_alliance_loans(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    aid, _ = get_alliance_info(db, user_id)
    return {"loans": list_loans(db, aid)}


@router.post("/create")
def create_alliance_loan(
    payload: LoanCreatePayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid, role = get_alliance_info(db, user_id)
    if role not in {"Leader", "Co-Leader", "Officer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    schedule = (
        [{"due_date": i.due_date, "amount": i.amount} for i in payload.schedule]
        if payload.schedule
        else None
    )
    loan_id = create_loan(
        db,
        alliance_id=aid,
        borrower_user_id=payload.borrower_user_id,
        resource_type=payload.resource_type,
        amount=payload.amount,
        interest_rate=payload.interest_rate,
        due_date=payload.due_date,
        schedule=schedule,
    )
    return {"loan_id": loan_id}


@router.post("/repay")
def repay_loan(
    payload: RepayPayload,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    # Ensure the repayment entry exists and belongs to user's alliance
    repayment = (
        db.query(AllianceLoanRepayment)
        .join(AllianceLoan, AllianceLoan.loan_id == AllianceLoanRepayment.loan_id)
        .filter(AllianceLoanRepayment.schedule_id == payload.schedule_id)
        .first()
    )
    if not repayment:
        raise HTTPException(status_code=404, detail="Schedule not found")
    loan = db.query(AllianceLoan).filter(AllianceLoan.loan_id == repayment.loan_id).first()
    aid, role = get_alliance_info(db, user_id)
    if loan.alliance_id != aid:
        raise HTTPException(status_code=403, detail="Not your alliance loan")
    if loan.borrower_user_id != user_id and role not in {"Leader", "Co-Leader"}:
        raise HTTPException(status_code=403, detail="Cannot repay this loan")

    repay_schedule(db, payload.schedule_id, payload.amount)
    return {"status": "repaid"}
