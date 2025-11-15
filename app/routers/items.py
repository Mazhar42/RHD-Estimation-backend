from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import schemas, crud, models
from ..data_parser import parse_item_master_csv_text, parse_item_master_xlsx_bytes
import io
import csv
from fastapi.responses import StreamingResponse, Response
try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

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

@router.delete("/divisions/{division_id}", response_model=schemas.Division)
def delete_division(division_id: int, db: Session = Depends(get_db)):
    division = crud.delete_division(db, division_id)
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    return division

@router.post("", response_model=schemas.Item)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, payload)

@router.get("", response_model=List[schemas.Item])
def read_items(region: str | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        return crud.get_items(db, region=region, skip=skip, limit=limit)
    except Exception as e:
        print(f"Error in read_items: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{item_id}", response_model=schemas.Item)

def update_item(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = crud.update_item(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}", response_model=schemas.Item)

def delete_item(item_id: int, db: Session = Depends(get_db)):
    # Prevent 500 by checking FK references before delete
    ref_count = db.query(models.EstimationLine).filter(models.EstimationLine.item_id == item_id).count()
    if ref_count > 0:
        raise HTTPException(status_code=409, detail=f"Item is referenced by {ref_count} estimation line(s); remove references before deletion.")
    item = crud.delete_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# ===== Export Items =====
@router.get("/export.csv")
def export_items_csv(db: Session = Depends(get_db)):
    items = crud.list_items(db)
    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["Division", "Item Code", "Description", "Unit", "Rate", "Region"]
    writer.writerow(headers)
    for it in items:
        writer.writerow([
            it.division.name if it.division else "",
            it.item_code,
            it.item_description,
            it.unit or "",
            float(it.rate) if it.rate is not None else "",
            it.region,
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=ItemMaster.csv"
    })

@router.get("/export.xlsx")
def export_items_xlsx(db: Session = Depends(get_db)):
    if Workbook is None:
        # Gracefully indicate XLSX export is not available without openpyxl
        raise HTTPException(status_code=501, detail="XLSX export not available: openpyxl is not installed")
    items = crud.list_items(db)
    wb = Workbook()
    ws = wb.active
    ws.title = "Item Master"
    headers = ["Division", "Item Code", "Description", "Unit", "Rate", "Region"]
    ws.append(headers)
    for it in items:
        ws.append([
            it.division.name if it.division else "",
            it.item_code,
            it.item_description,
            it.unit or "",
            float(it.rate) if it.rate is not None else None,
            it.region,
        ])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return Response(content=bio.read(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
        "Content-Disposition": "attachment; filename=ItemMaster.xlsx"
    })

# ===== Import Items =====
@router.post("/import")
def import_items(
    file: UploadFile = File(...),
    mode: str = Query("append", regex="^(append|replace)$"),
    db: Session = Depends(get_db)
):
    # Read uploaded file bytes
    file_bytes = file.file.read()
    filename = file.filename or "uploaded"
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    # Parse according to provided format
    try:
        if ext == "csv":
            text = file_bytes.decode("utf-8", errors="replace")
            parsed = parse_item_master_csv_text(text)
        elif ext in ("xlsx", "xlsm"):
            parsed = parse_item_master_xlsx_bytes(file_bytes)
        else:
            # Try content-type as fallback
            if file.content_type and "csv" in file.content_type:
                text = file_bytes.decode("utf-8", errors="replace")
                parsed = parse_item_master_csv_text(text)
            elif file.content_type and "spreadsheet" in file.content_type:
                parsed = parse_item_master_xlsx_bytes(file_bytes)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Upload CSV or XLSX in Item Master format.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    # Mode: replace or append
    if mode == "replace":
        # WARNING: This clears item master; may affect existing estimations
        crud.delete_all_items(db)

    # Upsert each entry
    count = 0
    for row in parsed:
        try:
            item_parsed = schemas.ItemParsed(**row)
            crud.create_item_from_parsed_data(db, item_parsed)
            count += 1
        except Exception as e:
            # Continue on errors; collect stats
            print(f"Import error for row {row.get('item_code')}: {e}")

    return {"message": f"Import {mode} completed", "processed": count}
