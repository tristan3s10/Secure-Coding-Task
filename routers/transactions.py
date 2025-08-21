
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tx = models.Transaction(**payload.model_dump(), user_id=current_user.id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    q: Optional[str] = Query(default=None, max_length=255, description="Filter by description substring"),
    min_amount: Optional[float] = Query(default=None, gt=0),
    max_amount: Optional[float] = Query(default=None, gt=0),
):
    query = db.query(models.Transaction)
    # RBAC: basic users can only see their own
    if current_user.role != models.RoleEnum.admin:
        query = query.filter(models.Transaction.user_id == current_user.id)
    # Safe filtering: SQLAlchemy builds parameterized queries under the hood — no raw SQL strings here.
    conditions = []
    if q is not None:
        # Using contains() ensures parameterization; no string concatenation into SQL.
        conditions.append(models.Transaction.description.contains(q))
    if min_amount is not None:
        conditions.append(models.Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(models.Transaction.amount <= max_amount)
    if conditions:
        query = query.filter(and_(*conditions))
    return query.order_by(models.Transaction.date.desc(), models.Transaction.id.desc()).all()

@router.get("/{tx_id}", response_model=schemas.TransactionOut)
def get_transaction(
    tx_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.RoleEnum.admin and tx.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return tx

@router.put("/{tx_id}", response_model=schemas.TransactionOut)
def update_transaction(
    payload: schemas.TransactionUpdate,
    tx_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.RoleEnum.admin and tx.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.delete("/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.RoleEnum.admin and tx.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(tx)
    db.commit()
    return
