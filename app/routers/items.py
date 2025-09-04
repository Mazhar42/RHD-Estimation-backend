from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import schemas, crud

router = APIRouter(prefix="/items", tags=["Items & Categories"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/categories", response_model=schemas.ItemCategory)
def create_category(payload: schemas.ItemCategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, payload)

@router.get("/categories", response_model=List[schemas.ItemCategory])
def list_categories(db: Session = Depends(get_db)):
    return crud.list_categories(db)

@router.post("", response_model=schemas.Item)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, payload)

@router.get("", response_model=List[schemas.Item])
def list_items(db: Session = Depends(get_db)):
    return crud.list_items(db)
