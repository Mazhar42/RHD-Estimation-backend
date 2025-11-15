from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import SessionLocal
from .. import schemas, crud, models

router = APIRouter(prefix="/estimations", tags=["Estimation Lines"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{estimation_id}/lines", response_model=schemas.EstimationLine)
def add_line(estimation_id: int, payload: schemas.EstimationLineCreate, db: Session = Depends(get_db)):
    est = db.get(models.Estimation, estimation_id)
    if not est:
        raise HTTPException(status_code=404, detail="Estimation not found")
    item = db.get(models.Item, payload.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.create_estimation_line(db, estimation_id, payload)

@router.delete("/lines")
def delete_lines(payload: schemas.EstimationLineDelete, db: Session = Depends(get_db)):
    deleted_count = crud.delete_estimation_lines(db, payload.line_ids)
    return {"message": f"{deleted_count} lines deleted successfully."}

@router.put("/lines/{line_id}", response_model=schemas.EstimationLine)
def update_line(line_id: int, payload: schemas.EstimationLineCreate, db: Session = Depends(get_db)):
    updated_line = crud.update_estimation_line(db, line_id, payload)
    if updated_line is None:
        raise HTTPException(status_code=404, detail="Line not found")
    return updated_line

@router.get("/{estimation_id}/lines", response_model=List[schemas.EstimationLine])
def list_lines(estimation_id: int, db: Session = Depends(get_db)):
    return crud.list_estimation_lines(db, estimation_id)

@router.delete("/{estimation_id}", response_model=schemas.Estimation)
def delete_estimation(estimation_id: int, db: Session = Depends(get_db)):
    estimation = crud.delete_estimation(db, estimation_id)
    if not estimation:
        raise HTTPException(status_code=404, detail="Estimation not found")
    return estimation

@router.get("/{estimation_id}/total")
def get_total(estimation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    total = crud.estimation_total(db, estimation_id)
    return {"estimation_id": estimation_id, "grand_total": total}
