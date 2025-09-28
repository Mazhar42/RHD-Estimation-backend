from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/divisions/", response_model=list[schemas.Division])
def read_divisions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    divisions = crud.get_divisions(db, skip=skip, limit=limit)
    return divisions
