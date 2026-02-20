from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import schemas, crud, models
from ..security import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects & Estimations"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=schemas.Project)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_project(db, payload, current_user.user_id)

@router.delete("/{project_id}", response_model=schemas.Project)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = crud.delete_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("", response_model=List[schemas.Project])
def list_projects(db: Session = Depends(get_db)):
    try:
        return crud.list_projects(db)
    except Exception as e:
        print(f"Error in list_projects: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.patch("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    updated = crud.update_project(db, project_id, payload, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated

@router.post("/{project_id}/estimations", response_model=schemas.Estimation)
def create_estimation(
    project_id: int,
    payload: schemas.EstimationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_estimation(db, project_id, payload, current_user.user_id)

@router.get("/{project_id}/estimations", response_model=List[schemas.Estimation])
def list_estimations(project_id: int, db: Session = Depends(get_db)):
    return crud.list_estimations_for_project(db, project_id)
