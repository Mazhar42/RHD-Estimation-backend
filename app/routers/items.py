from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import schemas, crud, models
from ..security import get_current_user, check_permission
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
    from ..security import get_current_user, check_permission, is_admin_user
except ImportError:
    # Mock the security functions if not available
    def get_current_user():
        return None
    def check_permission(perm: str):
        return True
    def is_admin_user(user: models.User):
        return False

router = APIRouter(prefix="/items", tags=["Items & Divisions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/divisions", response_model=schemas.Division)
def create_division(
    payload: schemas.DivisionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
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
def list_divisions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:read"))
):
    return crud.list_divisions(db)

@router.delete("/divisions/{division_id}", response_model=schemas.Division)
def delete_division(
    division_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    division = crud.delete_division(db, division_id)
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    return division

@router.post("", response_model=schemas.Item)
def create_item(
    payload: schemas.ItemCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    return crud.create_item(db, payload)

@router.get("", response_model=List[schemas.Item])
def read_items(
    region: str | None = None, 
    organization: str | None = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:read"))
):
    try:
        return crud.get_items(db, region=region, organization=organization, skip=skip, limit=limit)
    except Exception as e:
        print(f"Error in read_items: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/special", response_model=List[schemas.SpecialItem])
def read_special_items(
    region: str | None = None, 
    organization: str | None = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:read"))
):
    try:
        return crud.get_special_items(db, region=region, organization=organization, skip=skip, limit=limit)
    except Exception as e:
        print(f"Error in read_special_items: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{item_id}", response_model=schemas.Item)
def update_item(
    item_id: int, 
    payload: schemas.ItemUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:update"))
):
    item = crud.update_item(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

from sqlalchemy.exc import IntegrityError

@router.delete("/{item_id}", response_model=schemas.Item)
def delete_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:delete"))
):
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
def export_items_csv(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:read"))
):
    """Export Item Master in pivoted, multi-region format with Organization.

    Header order (as requested):
    SI. No, Item Code, Major Division, Description, Unit,
    Dhaka Zone, Mymensingh Zone, Comilla Zone, Sylhet Zone, Khulna Zone,
    Barisal Zone, Gopalganj Zone, Rajshahi Zone, Rangpur Zone, Chattogram Zone, Organization
    """
    items = crud.list_items(db)

    # Map items by (division_id, item_code, organization) to pivot region rates
    grouped: dict[tuple, dict] = {}
    for it in items:
        key = (it.division_id, it.item_code, (getattr(it, "organization", None) or "RHD"))
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
def export_items_xlsx(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:read"))
):
    if Workbook is None:
        # Gracefully indicate XLSX export is not available without openpyxl
        raise HTTPException(status_code=501, detail="XLSX export not available: openpyxl is not installed")

    items = crud.list_items(db)
    # Pivot grouping
    grouped: dict[tuple, dict] = {}
    for it in items:
        key = (it.division_id, it.item_code, (getattr(it, "organization", None) or "RHD"))
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
    mode: str = Query("append", pattern="^(append|replace)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_permission("items:create"))
):
    # Read uploaded file bytes
    file_bytes = file.file.read()
    filename = file.filename or "uploaded"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    print(f"DEBUG: Import called with file={filename}, mode={mode}, size={len(file_bytes)} bytes")

    # Parse according to provided format
    try:
        if ext == "csv":
            text = file_bytes.decode("utf-8", errors="replace")
            print(f"DEBUG: CSV content first 200 chars: {text[:200]}")
            # Try linear format first, then pivoted as fallback
            try:
                parsed = parse_item_master_csv_text(text)
                print(f"DEBUG: Parsed {len(parsed)} rows from CSV (linear format)")
            except Exception as e1:
                print(f"DEBUG: Linear format failed: {e1}, trying pivoted...")
                parsed = parse_item_master_pivot_csv_text(text)
                print(f"DEBUG: Parsed {len(parsed)} rows from CSV (pivoted format)")
        elif ext in ("xlsx", "xlsm"):
            # Try linear format first, then pivoted as fallback
            try:
                parsed = parse_item_master_xlsx_bytes(file_bytes)
                print(f"DEBUG: Parsed {len(parsed)} rows from XLSX (linear format)")
            except Exception as e1:
                print(f"DEBUG: Linear format failed: {e1}, trying pivoted...")
                parsed = parse_item_master_pivot_xlsx_bytes(file_bytes)
                print(f"DEBUG: Parsed {len(parsed)} rows from XLSX (pivoted format)")
        else:
            # Try content-type as fallback
            if file.content_type and "csv" in file.content_type:
                text = file_bytes.decode("utf-8", errors="replace")
                try:
                    parsed = parse_item_master_csv_text(text)
                    print(f"DEBUG: Parsed {len(parsed)} rows from {file.content_type}")
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
        print(f"DEBUG: Parse error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    # Mode: replace or append
    if mode == "replace":
        # WARNING: This clears item master; may affect existing estimations
        crud.delete_all_items(db)

    # Upsert each entry; skip rows with missing/blank rate
    count = 0
    skipped = 0
    errors = []
    
    for idx, row in enumerate(parsed, 1):
        try:
            # Skip if rate is missing/blank
            r = row.get("rate")
            if r is None or (isinstance(r, str) and not r.strip()):
                skipped += 1
                continue
            
            # Validate and parse the row
            item_parsed = schemas.ItemParsed(**row)
            
            # Create or update the item
            crud.create_item_from_parsed_data(db, item_parsed)
            count += 1
            
        except ValueError as ve:
            # Validation error
            error_msg = f"Row {idx}: {str(ve)}"
            errors.append(error_msg)
            print(f"Import validation error: {error_msg}")
            try:
                db.rollback()
            except Exception:
                pass
        except Exception as e:
            # Other errors - continue but track them
            error_msg = f"Row {idx} ({row.get('item_code', 'unknown')}): {str(e)}"
            errors.append(error_msg)
            print(f"Import error: {error_msg}")
            try:
                db.rollback()
            except Exception:
                pass
    
    # Final commit to save everything
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to save imported items: {str(e)}"
        )
    
    return {
        "message": f"Import {mode} completed", 
        "processed": count, 
        "skipped": skipped,
        "errors": errors if errors else None
    }
