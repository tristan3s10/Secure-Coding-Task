
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserOut, status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = models.User(email=payload.email, hashed_password=hash_password(payload.password), role=models.RoleEnum(payload.role))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=schemas.UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user
