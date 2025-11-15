import os
import sys
from typing import List, Dict

# Ensure we can import from app package when running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import crud, schemas
from app.data_parser import parse_rates, parse_rates_csv


DEFAULT_FILES = [
    # Prefer backend-local CSV
    os.path.join(os.path.dirname(__file__), "..", "Rates.csv"),
    # Project root CSV
    os.path.join(os.path.dirname(__file__), "..", "..", "Rates.csv"),
    # Project root XLSX
    os.path.join(os.path.dirname(__file__), "..", "..", "RatesExcel.xlsx"),
]


def find_input_file(cli_path: str | None = None) -> str:
    """Return the first existing path among CLI input and defaults."""
    if cli_path:
        if os.path.exists(cli_path):
            return cli_path
        raise FileNotFoundError(f"Specified file not found: {cli_path}")
    for p in DEFAULT_FILES:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No rates file found. Expected one of: Rates.csv or RatesExcel.xlsx")


def seed_data(input_file: str | None = None) -> int:
    print("Starting to seed rates into items...")
    target_file = find_input_file(input_file)
    print(f"Using input file: {target_file}")

    # Parse input file
    try:
        parsed: List[Dict] = parse_rates(target_file)
    except ValueError as ve:
        # If extension unsupported but it's CSV in disguise, fallback
        print(f"Parser dispatch failed: {ve}. Falling back to CSV parser...")
        parsed = parse_rates_csv(target_file)

    print(f"Parsed {len(parsed)} rows. Upserting into DB...")
    db = SessionLocal()
    items_count = 0
    try:
        for row in parsed:
            # Convert dict to Pydantic and upsert
            item_parsed = schemas.ItemParsed(**row)
            crud.create_item_from_parsed_data(db, item_parsed)
            items_count += 1
        print("Seeding complete. No commit batching necessary; CRUD commits per item.")
    except Exception as e:
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()
        print("Database session closed.")
    return items_count


if __name__ == "__main__":
    # Optional CLI arg: file path
    cli_arg = sys.argv[1] if len(sys.argv) > 1 else None
    total = seed_data(cli_arg)
    print(f"Seeding completed! Total items processed: {total}")
