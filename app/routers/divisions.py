from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..database import SessionLocal
from ..security import get_current_user, check_permission

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/divisions/", response_model=list[schemas.Division])
def read_divisions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:read"))
):
    divisions = crud.get_divisions(db, skip=skip, limit=limit)
    return divisions
