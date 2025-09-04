from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import SessionLocal
from .. import schemas, crud

router = APIRouter(prefix="/estimations", tags=["Estimation Lines"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{estimation_id}/lines", response_model=schemas.EstimationLine)
def add_line(estimation_id: int, payload: schemas.EstimationLineCreate, db: Session = Depends(get_db)):
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

@router.get("/{estimation_id}/total")
def get_total(estimation_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    total = crud.estimation_total(db, estimation_id)
    return {"estimation_id": estimation_id, "grand_total": total}
