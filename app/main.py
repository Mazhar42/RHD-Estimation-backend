from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from sqlalchemy import inspect, text
from .routers import items, projects, estimations, divisions, organizations, auth
from . import crud, schemas
from .initial_data import init_db
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize default roles and permissions
db_init = SessionLocal()
try:
    init_db(db_init)
finally:
    db_init.close()

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
        if 'length_expr' not in est_line_columns:
            conn.execute(text("ALTER TABLE estimation_lines ADD COLUMN length_expr VARCHAR(255) NULL"))
        if 'width_expr' not in est_line_columns:
            conn.execute(text("ALTER TABLE estimation_lines ADD COLUMN width_expr VARCHAR(255) NULL"))
        if 'thickness_expr' not in est_line_columns:
            conn.execute(text("ALTER TABLE estimation_lines ADD COLUMN thickness_expr VARCHAR(255) NULL"))

    special_req_columns = [c['name'] if isinstance(c, dict) else c.name for c in insp.get_columns('special_item_requests')]
    with engine.begin() as conn:
        if 'length_expr' not in special_req_columns:
            conn.execute(text("ALTER TABLE special_item_requests ADD COLUMN length_expr VARCHAR(255) NULL"))
        if 'width_expr' not in special_req_columns:
            conn.execute(text("ALTER TABLE special_item_requests ADD COLUMN width_expr VARCHAR(255) NULL"))
        if 'thickness_expr' not in special_req_columns:
            conn.execute(text("ALTER TABLE special_item_requests ADD COLUMN thickness_expr VARCHAR(255) NULL"))

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

    project_columns = [c['name'] if isinstance(c, dict) else c.name for c in insp.get_columns('projects')]
    with engine.begin() as conn:
        if 'created_by_id' not in project_columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN created_by_id INTEGER NULL"))
        if 'updated_by_id' not in project_columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN updated_by_id INTEGER NULL"))
        if 'created_at' not in project_columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
        if 'updated_at' not in project_columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))

    estimation_columns = [c['name'] if isinstance(c, dict) else c.name for c in insp.get_columns('estimations')]
    with engine.begin() as conn:
        if 'created_by_id' not in estimation_columns:
            conn.execute(text("ALTER TABLE estimations ADD COLUMN created_by_id INTEGER NULL"))
        if 'updated_by_id' not in estimation_columns:
            conn.execute(text("ALTER TABLE estimations ADD COLUMN updated_by_id INTEGER NULL"))
        if 'created_at' not in estimation_columns:
            conn.execute(text("ALTER TABLE estimations ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
        if 'updated_at' not in estimation_columns:
            conn.execute(text("ALTER TABLE estimations ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))

    with engine.begin() as conn:
        conn.execute(text("UPDATE projects SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)"))
        conn.execute(text("UPDATE projects SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"))
        conn.execute(text("UPDATE estimations SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)"))
        conn.execute(text("UPDATE estimations SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"))

    # Ensure items.item_code can hold longer codes on PostgreSQL
    # For SQLite, declared lengths are not enforced; no change required
    try:
        if engine.dialect.name == 'postgresql':
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE items ALTER COLUMN item_code TYPE VARCHAR(255)"))
                # Adjust uniqueness: make items unique per item_code + region + organization
                # Drop old constraint if present; then create a unique index across 3 columns
                try:
                    conn.execute(text("ALTER TABLE items DROP CONSTRAINT IF EXISTS uq_item_code_region"))
                except Exception:
                    pass
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_item_code_region_org_idx ON items (item_code, region, organization)"
                ))
    except Exception:
        # Non-fatal: skip if column already migrated or DB does not permit
        pass
except Exception:
    # Avoid blocking startup; backend continues even if inspection fails
    pass

app = FastAPI(title="Estimation Backend", version="1.0.0")

# CORS: cannot use "*" when allow_credentials=True.
# Explicitly list frontend origins and allow Netlify deploy previews via regex.
origins = [
    "https://rhd-estimation.netlify.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"(https://.*\.netlify\.app|http://localhost:\d+|http://127.0.0.1:\d+)",  # allow Netlify preview sites and all localhost ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(projects.router)
app.include_router(estimations.router)
app.include_router(divisions.router)
app.include_router(organizations.router)

# Initialize system roles and permissions
def init_system_roles_and_permissions():
    """Initialize default system roles and permissions."""
    try:
        from .security import get_db as get_db_session
        db = next(get_db_session())
        
        # Create system roles if they don't exist
        system_roles = ["superadmin", "admin", "user"]
        for role_name in system_roles:
            existing_role = crud.get_role_by_name(db, role_name)
            if not existing_role:
                crud.create_role(
                    db,
                    schemas.RoleCreate(
                        name=role_name,
                        description=f"System {role_name} role"
                    ),
                    is_system_role=True
                )
        
        # Create default permissions if they don't exist
        permissions = [
            ("read:items", "Read items"),
            ("create:items", "Create items"),
            ("update:items", "Update items"),
            ("delete:items", "Delete items"),
            ("read:projects", "Read projects"),
            ("create:projects", "Create projects"),
            ("update:projects", "Update projects"),
            ("delete:projects", "Delete projects"),
            ("read:estimations", "Read estimations"),
            ("create:estimations", "Create estimations"),
            ("update:estimations", "Update estimations"),
            ("delete:estimations", "Delete estimations"),
            ("manage:users", "Manage users"),
            ("manage:roles", "Manage roles"),
            ("manage:permissions", "Manage permissions"),
        ]
        
        for perm_name, perm_desc in permissions:
            existing = crud.get_permission_by_name(db, perm_name)
            if not existing:
                crud.create_permission(
                    db,
                    schemas.PermissionCreate(
                        name=perm_name,
                        description=perm_desc
                    )
                )
        
        # Assign permissions to superadmin role
        superadmin_role = crud.get_role_by_name(db, "superadmin")
        if superadmin_role:
            all_permissions = crud.get_all_permissions(db, limit=1000)
            for perm in all_permissions:
                if perm not in superadmin_role.permissions:
                    crud.assign_permission_to_role(db, superadmin_role.role_id, perm.permission_id)
        
        db.close()
        print("✓ System roles and permissions initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize system roles - {e}")
        pass

def ensure_admin_user():
    try:
        from .security import get_db as get_db_session
        db = next(get_db_session())
        user = crud.get_user_by_username(db, "rayhan37")
        if not user:
            user = crud.get_user_by_email(db, "mazharrayhan3737@gmail.com")
        if user:
            admin_role = crud.get_role_by_name(db, "admin")
            if admin_role:
                crud.assign_role_to_user(db, user.user_id, admin_role.role_id)
        db.close()
    except Exception as e:
        print(f"Warning: Could not ensure admin user - {e}")
        pass

# Initialize system roles on startup
init_system_roles_and_permissions()
ensure_admin_user()

@app.get("/health")
def health():
    return {"status": "ok"}
