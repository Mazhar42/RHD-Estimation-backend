from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .routers import items, projects, estimations, divisions
from .models import Item, Division
from .data_parser import parse_rates_csv
from . import crud, schemas
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Estimation Backend", version="1.0.0")

# CORS: cannot use "*" when allow_credentials=True.
# Explicitly list frontend origins and allow Netlify deploy previews via regex.
origins = [
    "https://rhd-estimation.netlify.app",
    "http://localhost:5175",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.netlify\.app",  # allow Netlify preview sites
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routers
app.include_router(items.router)
app.include_router(projects.router)
app.include_router(estimations.router)
app.include_router(divisions.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/seed-rates-data")
def seed_rates_data(db: Session = Depends(get_db)):
    # Path to Rates.csv
    current_dir = os.path.dirname(__file__)
    csv_file_path = os.path.join(current_dir, "..", "Rates.csv")

    if not os.path.exists(csv_file_path):
        raise HTTPException(status_code=404, detail=f"Rates.csv not found at {csv_file_path}")

    parsed_data = parse_rates_csv(csv_file_path)
    
    items_created_or_updated = 0
    for item_data in parsed_data:
        # Convert dict to Pydantic model
        item_parsed_schema = schemas.ItemParsed(**item_data)
        crud.create_item_from_parsed_data(db, item_parsed_schema)
        items_created_or_updated += 1
    
    return {"message": f"Successfully seeded {items_created_or_updated} items from Rates.csv"}
