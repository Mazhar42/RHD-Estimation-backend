from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import schemas, crud

router = APIRouter(prefix="/items", tags=["Items & Divisions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/divisions", response_model=schemas.Division)
def create_division(payload: schemas.DivisionCreate, db: Session = Depends(get_db)):
    return crud.create_division(db, payload)

@router.get("/divisions", response_model=List[schemas.Division])
def list_divisions(db: Session = Depends(get_db)):
    return crud.list_divisions(db)

@router.post("", response_model=schemas.Item)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, payload)

@router.get("", response_model=List[schemas.Item])
def list_items(db: Session = Depends(get_db)):
    try:
        return crud.list_items(db)
    except Exception as e:
        print(f"Error in list_items: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{item_id}", response_model=schemas.Item)

def update_item(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = crud.update_item(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}", response_model=schemas.Item)

def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.delete_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
