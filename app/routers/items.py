from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import schemas, crud, models
from ..services.parsers import (
    parse_item_master_csv_text,
    parse_item_master_xlsx_bytes,
    parse_item_master_pivot_csv_text,
    parse_item_master_pivot_xlsx_bytes,
)
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
    # Handle duplicate division names gracefully
    try:
        return crud.create_division(db, payload)
    except Exception as e:
        from sqlalchemy.exc import IntegrityError
        if isinstance(e, IntegrityError):
            db.rollback()
            raise HTTPException(status_code=409, detail="Division already exists")
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
def read_items(region: str | None = None, organization: str | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        return crud.get_items(db, region=region, organization=organization, skip=skip, limit=limit)
    except Exception as e:
        print(f"Error in read_items: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{item_id}", response_model=schemas.Item)

def update_item(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = crud.update_item(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

from sqlalchemy.exc import IntegrityError

...

@router.delete("/{item_id}", response_model=schemas.Item)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    # Handle FK constraints via DB; return a stable copy before deletion to avoid expired-instance issues
    try:
        obj = db.get(models.Item, item_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Item not found")
        # Prepare response before the object is deleted/expired
        response_payload = schemas.Item.model_validate(obj)
        db.delete(obj)
        db.commit()
        return response_payload
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Item is referenced by one or more estimation lines; remove references before deletion.",
        )

# ===== Export Items =====
@router.get("/export.csv")
def export_items_csv(db: Session = Depends(get_db)):
    """Export Item Master in pivoted, multi-region format with Organization.

    Header order (as requested):
    SI. No, Item Code, Major Division, Description, Unit,
    Dhaka Zone, Mymensingh Zone, Comilla Zone, Sylhet Zone, Khulna Zone,
    Barisal Zone, Gopalganj Zone, Rajshahi Zone, Rangpur Zone, Chattogram Zone, Organization
    """
    items = crud.list_items(db)

    # Map items by (division_id, item_code) to pivot region rates
    grouped: dict[tuple, dict] = {}
    for it in items:
        key = (it.division_id, it.item_code)
        if key not in grouped:
            grouped[key] = {
                "item_code": it.item_code,
                "division_name": it.division.name if it.division else "",
                "description": it.item_description or "",
                "unit": it.unit or "",
                "organization": (getattr(it, "organization", None) or "RHD"),
                "rates": {},
            }
        # Normalize region name to match requested header spelling
        region = it.region or ""
        if region == "Cumilla Zone":
            region = "Comilla Zone"
        grouped[key]["rates"][region] = float(it.rate) if it.rate is not None else None

    region_headers = [
        "Dhaka Zone",
        "Mymensingh Zone",
        "Comilla Zone",
        "Sylhet Zone",
        "Khulna Zone",
        "Barisal Zone",
        "Gopalganj Zone",
        "Rajshahi Zone",
        "Rangpur Zone",
        "Chattogram Zone",
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        "SI. No",
        "Item Code",
        "Major Division",
        "Description",
        "Unit",
        *region_headers,
        "Organization",
    ]
    writer.writerow(headers)

    # Sort rows by division then item code for stable output
    sorted_rows = sorted(grouped.values(), key=lambda r: (r["division_name"], r["item_code"]))
    for idx, row in enumerate(sorted_rows, start=1):
        line = [
            idx,
            row["item_code"],
            row["division_name"],
            row["description"],
            row["unit"],
        ]
        for rh in region_headers:
            val = row["rates"].get(rh)
            line.append(val if val is not None else "")
        line.append(row["organization"])
        writer.writerow(line)

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
    # Pivot grouping
    grouped: dict[tuple, dict] = {}
    for it in items:
        key = (it.division_id, it.item_code)
        if key not in grouped:
            grouped[key] = {
                "item_code": it.item_code,
                "division_name": it.division.name if it.division else "",
                "description": it.item_description or "",
                "unit": it.unit or "",
                "organization": (getattr(it, "organization", None) or "RHD"),
                "rates": {},
            }
        region = it.region or ""
        if region == "Cumilla Zone":
            region = "Comilla Zone"
        grouped[key]["rates"][region] = float(it.rate) if it.rate is not None else None

    region_headers = [
        "Dhaka Zone",
        "Mymensingh Zone",
        "Comilla Zone",
        "Sylhet Zone",
        "Khulna Zone",
        "Barisal Zone",
        "Gopalganj Zone",
        "Rajshahi Zone",
        "Rangpur Zone",
        "Chattogram Zone",
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Item Master"
    headers = [
        "SI. No",
        "Item Code",
        "Major Division",
        "Description",
        "Unit",
        *region_headers,
        "Organization",
    ]
    ws.append(headers)

    sorted_rows = sorted(grouped.values(), key=lambda r: (r["division_name"], r["item_code"]))
    for idx, row in enumerate(sorted_rows, start=1):
        line = [
            idx,
            row["item_code"],
            row["division_name"],
            row["description"],
            row["unit"],
        ]
        for rh in region_headers:
            val = row["rates"].get(rh)
            line.append(val if val is not None else None)
        line.append(row["organization"])
        ws.append(line)

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
            # Try linear format first, then pivoted as fallback
            try:
                parsed = parse_item_master_csv_text(text)
            except Exception:
                parsed = parse_item_master_pivot_csv_text(text)
        elif ext in ("xlsx", "xlsm"):
            # Try linear format first, then pivoted as fallback
            try:
                parsed = parse_item_master_xlsx_bytes(file_bytes)
            except Exception:
                parsed = parse_item_master_pivot_xlsx_bytes(file_bytes)
        else:
            # Try content-type as fallback
            if file.content_type and "csv" in file.content_type:
                text = file_bytes.decode("utf-8", errors="replace")
                try:
                    parsed = parse_item_master_csv_text(text)
                except Exception:
                    parsed = parse_item_master_pivot_csv_text(text)
            elif file.content_type and "spreadsheet" in file.content_type:
                try:
                    parsed = parse_item_master_xlsx_bytes(file_bytes)
                except Exception:
                    parsed = parse_item_master_pivot_xlsx_bytes(file_bytes)
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
            try:
                db.rollback()
            except Exception:
                pass
            print(f"Import error for row {row.get('item_code')}: {e}")

    return {"message": f"Import {mode} completed", "processed": count}
