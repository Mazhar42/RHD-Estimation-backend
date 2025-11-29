from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from sqlalchemy import inspect, text
from .routers import items, projects, estimations, divisions, organizations
from . import crud, schemas
import os

# Create tables
Base.metadata.create_all(bind=engine)

insp = inspect(engine)
try:
    # Ensure items.organization exists (legacy support)
    columns = [c['name'] if isinstance(c, dict) else c.name for c in insp.get_columns('items')]
    if 'organization' not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE items ADD COLUMN organization VARCHAR(50) NOT NULL DEFAULT 'RHD'"))

    # Ensure attachment columns exist on estimation_lines
    est_line_columns = [c['name'] if isinstance(c, dict) else c.name for c in insp.get_columns('estimation_lines')]
    with engine.begin() as conn:
        if 'attachment_name' not in est_line_columns:
            conn.execute(text("ALTER TABLE estimation_lines ADD COLUMN attachment_name VARCHAR(255) NULL"))
        if 'attachment_base64' not in est_line_columns:
            conn.execute(text("ALTER TABLE estimation_lines ADD COLUMN attachment_base64 TEXT NULL"))

    # Create new tables if not exist
    # Note: Base.metadata.create_all handles creation, but we also backfill defaults below.
    with engine.begin() as conn:
        # Ensure organizations table has at least 'RHD' default
        conn.execute(text("""
            INSERT INTO organizations (name)
            SELECT 'RHD'
            WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE name = 'RHD')
        """))
        # Optionally ensure LGED exists for convenience
        conn.execute(text("""
            INSERT INTO organizations (name)
            SELECT 'LGED'
            WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE name = 'LGED')
        """))

    # Ensure divisions.organization_id column exists, and backfill to RHD
    div_columns = [c['name'] if isinstance(c, dict) else c.name for c in insp.get_columns('divisions')]
    if 'organization_id' not in div_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE divisions ADD COLUMN organization_id INTEGER NULL"))
        # Backfill: set organization_id to 'RHD' org id
        with engine.begin() as conn:
            # SQLite: fetch RHD org_id
            rhd_id = conn.execute(text("SELECT org_id FROM organizations WHERE name='RHD'"))
            rhd_id_val = rhd_id.scalar() if rhd_id else None
            if rhd_id_val is not None:
                conn.execute(text(f"UPDATE divisions SET organization_id = {int(rhd_id_val)} WHERE organization_id IS NULL"))
except Exception:
    # Avoid blocking startup; backend continues even if inspection fails
    pass

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
app.include_router(organizations.router)

@app.get("/health")
def health():
    return {"status": "ok"}
