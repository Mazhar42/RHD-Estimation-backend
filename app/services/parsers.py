import csv
from typing import List, Dict, Any

try:
    # Optional dependency for reading .xlsx
    from openpyxl import load_workbook
except Exception:
    load_workbook = None


# ==== Item Master Import (User-provided export format) ====
ITEM_MASTER_HEADERS = [
    "Division", "Item Code", "Description", "Unit", "Rate", "Region"
]

# Pivoted Item Master headers (export format)
PIVOT_REGION_COLUMNS = [
    "Dhaka Zone", "Mymensingh Zone", "Comilla Zone", "Sylhet Zone",
    "Khulna Zone", "Barisal Zone", "Gopalganj Zone", "Rajshahi Zone",
    "Rangpur Zone", "Chattogram Zone"
]

def parse_item_master_pivot_csv_text(text: str) -> List[Dict[str, Any]]:
    """Parse pivoted Item Master CSV text to a list of dicts expected by ItemParsed.

    Flexible header parsing:
    - Accept base headers using common synonyms and case-insensitive matching.
    - Treat any non-base columns (except optional SI. No and Organization) as region columns.
    """
    data: List[Dict[str, Any]] = []
    reader = csv.DictReader(text.splitlines())
    fieldnames_raw = reader.fieldnames or []
    # Normalize headers: strip and lower for matching, keep original for value access
    norm = lambda s: str(s or "").strip().lower()
    field_map = {norm(h): h for h in fieldnames_raw}

    # Synonyms for base columns
    base_synonyms = {
        "item_code": ["item code", "code", "itemcode", "item"],
        "division": ["major division", "Division", "division name"],
        "description": ["description", "item description", "desc"],
        "unit": ["unit", "units"],
        "organization": ["organization", "org","organisation"],
        "si_no": ["si. no", "si no", "serial", "sl", "sl."],
    }

    def resolve_header(key: str) -> str | None:
        for cand in base_synonyms[key]:
            if cand in field_map:
                return field_map[cand]
        return None

    item_code_h = resolve_header("item_code")
    division_h = resolve_header("division")
    description_h = resolve_header("description")
    unit_h = resolve_header("unit")
    org_h = resolve_header("organization")
    si_h = resolve_header("si_no")

    missing = [label for label, h in {
        "Item Code": item_code_h,
        "Major Division": division_h,
        "Description": description_h,
        "Unit": unit_h,
    }.items() if h is None]
    if missing:
        raise ValueError(f"Missing expected base headers in pivot Item Master CSV: {missing}")

    # Region headers = all headers minus base and optional SI/Organization
    base_set = {item_code_h, division_h, description_h, unit_h}
    optional_set = {si_h, org_h}
    region_headers = [h for h in fieldnames_raw if h not in base_set and h not in optional_set]
    # Backward compatibility: allow 'Cumilla Zone' as 'Comilla Zone'
    region_headers = ["Comilla Zone" if h == "Cumilla Zone" else h for h in region_headers]

    def clean_str(value) -> str:
        s = str(value).strip() if value is not None else ""
        return "" if s.lower() in ("none", "null", "-") else s

    def clean_unit(value) -> str | None:
        s = str(value).strip() if value is not None else ""
        return None if s == "" or s.lower() in ("none", "null", "-") else s

    for row in reader:
        division = clean_str(row.get(division_h))
        item_code = clean_str(row.get(item_code_h))
        description = clean_str(row.get(description_h))
        unit = clean_unit(row.get(unit_h))
        org_raw = row.get(org_h) if org_h else None
        organization = clean_str(org_raw) or "RHD"
        if not item_code and not description:
            continue

        for region in region_headers:
            rate_str = row.get(region)
            rate = None
            if rate_str not in (None, "", "-"):
                try:
                    rate = float(rate_str)
                except ValueError:
                    rate = None
            entry: Dict[str, Any] = {
                "division": division,
                "item_code": item_code,
                "item_description": description,
                "unit": unit,
                "rate": rate,
                "region": region,
                "organization": organization,
            }
            data.append(entry)
    return data

def parse_item_master_csv_text(text: str) -> List[Dict[str, Any]]:
    """Parse Item Master CSV text (string) to a list of dicts expected by ItemParsed."""
    data: List[Dict[str, Any]] = []
    reader = csv.DictReader(text.splitlines())
    # Basic header validation
    missing = [h for h in ITEM_MASTER_HEADERS if h not in reader.fieldnames]
    if missing:
        raise ValueError(f"Missing expected headers in Item Master CSV: {missing}")
    def clean_str(value) -> str:
        s = str(value).strip() if value is not None else ""
        return "" if s.lower() in ("none", "null", "-") else s

    def clean_unit(value) -> str | None:
        s = str(value).strip() if value is not None else ""
        return None if s == "" or s.lower() in ("none", "null", "-") else s

    for row in reader:
        rate_val = row.get("Rate")
        try:
            rate = float(rate_val) if rate_val not in (None, "", "-") else None
        except ValueError:
            rate = None
        entry = {
            "division": clean_str(row.get("Division")),
            "item_code": clean_str(row.get("Item Code")),
            "item_description": clean_str(row.get("Description")),
            "unit": clean_unit(row.get("Unit")),
            "rate": rate,
            "region": clean_str(row.get("Region")),
        }
        # Skip rows missing essential identifiers
        if not entry["item_code"] and not entry["item_description"]:
            continue
        data.append(entry)
    return data

def parse_item_master_xlsx_bytes(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse Item Master XLSX in memory to list of dicts expected by ItemParsed."""
    if load_workbook is None:
        raise ImportError("openpyxl is not installed. Please add 'openpyxl' to requirements or install it.")
    from io import BytesIO
    wb = load_workbook(filename=BytesIO(file_bytes), data_only=True)
    ws = wb.active
    # Headers
    headers = [cell.value if cell.value is not None else "" for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    header_index = {str(h).strip(): idx for idx, h in enumerate(headers)}
    missing = [h for h in ITEM_MASTER_HEADERS if h not in header_index]
    if missing:
        raise ValueError(f"Missing expected headers in Item Master XLSX: {missing}")
    data: List[Dict[str, Any]] = []
    def clean_str(value) -> str:
        s = str(value).strip() if value is not None else ""
        return "" if s.lower() in ("none", "null", "-") else s

    def clean_unit(value) -> str | None:
        s = str(value).strip() if value is not None else ""
        return None if s == "" or s.lower() in ("none", "null", "-") else s

    for row in ws.iter_rows(min_row=2):
        def val(hname):
            idx = header_index[hname]
            cell = row[idx]
            return cell.value if cell.value is not None else None
        rate_cell = val("Rate")
        try:
            rate = float(rate_cell) if rate_cell not in (None, "", "-") else None
        except (ValueError, TypeError):
            rate = None
        entry = {
            "division": clean_str(val("Division")),
            "item_code": clean_str(val("Item Code")),
            "item_description": clean_str(val("Description")),
            "unit": clean_unit(val("Unit")),
            "rate": rate,
            "region": clean_str(val("Region")),
        }
        if not entry["item_code"] and not entry["item_description"]:
            continue
        data.append(entry)
    return data

def parse_item_master_pivot_xlsx_bytes(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse pivoted Item Master XLSX in memory to list of dicts expected by ItemParsed.

    Flexible header parsing with case-insensitive synonyms and dynamic region columns.
    """
    if load_workbook is None:
        raise ImportError("openpyxl is not installed. Please add 'openpyxl' to requirements or install it.")
    from io import BytesIO
    wb = load_workbook(filename=BytesIO(file_bytes), data_only=True)
    ws = wb.active
    headers = [cell.value if cell.value is not None else "" for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    header_index = {str(h).strip(): idx for idx, h in enumerate(headers)}
    # Build normalized lookup for synonyms
    norm = lambda s: str(s or "").strip().lower()
    norm_index = {norm(h): idx for h, idx in header_index.items()}
    base_synonyms = {
        "item_code": ["item code", "code", "itemcode", "item"],
        "division": ["major division", "division", "division name"],
        "description": ["description", "item description", "desc"],
        "unit": ["unit", "units"],
        "organization": ["organization", "org"],
        "si_no": ["si. no", "si no", "serial", "sl", "sl."],
    }
    def find_idx(key: str) -> int | None:
        for cand in base_synonyms[key]:
            if cand in norm_index:
                return norm_index[cand]
        return None
    idx_item_code = find_idx("item_code")
    idx_division = find_idx("division")
    idx_description = find_idx("description")
    idx_unit = find_idx("unit")
    idx_org = find_idx("organization")
    idx_si = find_idx("si_no")
    missing_base = [label for label, idx in {
        "Item Code": idx_item_code,
        "Major Division": idx_division,
        "Description": idx_description,
        "Unit": idx_unit,
    }.items() if idx is None]
    if missing_base:
        raise ValueError(f"Missing expected base headers in pivot Item Master XLSX: {missing_base}")

    # Region headers: any headers not part of base or optional SI/Organization
    base_indices = {idx_item_code, idx_division, idx_description, idx_unit}
    optional_indices = {idx_si, idx_org}
    region_headers = []
    for h, idx in header_index.items():
        if idx in base_indices or idx in optional_indices:
            continue
        # Normalize Cumilla → Comilla
        if h == "Cumilla Zone":
            h = "Comilla Zone"
        region_headers.append(h)

    data: List[Dict[str, Any]] = []
    def clean_str(value) -> str:
        s = str(value).strip() if value is not None else ""
        return "" if s.lower() in ("none", "null", "-") else s

    def clean_unit(value) -> str | None:
        s = str(value).strip() if value is not None else ""
        return None if s == "" or s.lower() in ("none", "null", "-") else s

    for row in ws.iter_rows(min_row=2):
        def val(hname):
            idx = header_index.get(hname)
            if idx is None:
                return None
            cell = row[idx]
            return cell.value if cell.value is not None else None

        division = clean_str(row[idx_division].value if idx_division is not None else None)
        item_code = clean_str(row[idx_item_code].value if idx_item_code is not None else None)
        description = clean_str(row[idx_description].value if idx_description is not None else None)
        unit_cell = row[idx_unit] if idx_unit is not None else None
        unit = clean_unit(unit_cell.value if unit_cell else None)
        org_cell = row[idx_org] if idx_org is not None else None
        organization = clean_str(org_cell.value if org_cell else None) or "RHD"

        if not item_code and not description:
            continue

        for region in region_headers:
            rate_cell = val(region)
            if rate_cell is None and region == "Comilla Zone":
                rate_cell = val("Cumilla Zone")
            rate = None
            if rate_cell not in (None, "-"):
                try:
                    rate = float(rate_cell)
                except (ValueError, TypeError):
                    rate = None
            entry = {
                "division": division,
                "item_code": item_code,
                "item_description": description,
                "unit": unit,
                "rate": rate,
                "region": region,
                "organization": organization,
            }
            data.append(entry)
    return data

# Removed CLI demo block to avoid unused runtime code in production
