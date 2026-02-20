from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import SessionLocal
from .. import schemas, crud, models
from ..security import get_current_user

router = APIRouter(prefix="/estimations", tags=["Estimation Lines"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_admin_user(user: models.User) -> bool:
    return any(r.name in ("admin", "superadmin") for r in (user.roles or []))

@router.post("/{estimation_id}/lines", response_model=schemas.EstimationLine)
def add_line(estimation_id: int, payload: schemas.EstimationLineCreate, db: Session = Depends(get_db)):
    est = db.get(models.Estimation, estimation_id)
    if not est:
        raise HTTPException(status_code=404, detail="Estimation not found")
    item = db.get(models.Item, payload.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.create_estimation_line(db, estimation_id, payload)

@router.post("/{estimation_id}/special-item-requests", response_model=schemas.SpecialItemRequest)
def create_special_item_request(
    estimation_id: int,
    payload: schemas.SpecialItemRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    est = db.get(models.Estimation, estimation_id)
    if not est:
        raise HTTPException(status_code=404, detail="Estimation not found")
    return crud.create_special_item_request(db, estimation_id, payload, current_user.user_id)

@router.get("/{estimation_id}/special-item-requests", response_model=List[schemas.SpecialItemRequest])
def list_special_item_requests(
    estimation_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if is_admin_user(current_user):
        return crud.list_special_item_requests(db, estimation_id=estimation_id, status=status)
    return crud.list_special_item_requests_for_user(db, estimation_id=estimation_id, user_id=current_user.user_id, status=status)

@router.post("/special-item-requests/{request_id}/approve", response_model=schemas.SpecialItemRequest)
def approve_special_item_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    req = crud.approve_special_item_request(db, request_id, current_user.user_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@router.post("/special-item-requests/{request_id}/reject", response_model=schemas.SpecialItemRequest)
def reject_special_item_request(
    request_id: int,
    payload: schemas.SpecialItemRequestReject,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    req = crud.reject_special_item_request(db, request_id, current_user.user_id, payload.reason)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

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

@router.patch("/{estimation_id}", response_model=schemas.Estimation)
def update_estimation(
    estimation_id: int,
    payload: schemas.EstimationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    updated = crud.update_estimation(db, estimation_id, payload, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Estimation not found")
    return updated
