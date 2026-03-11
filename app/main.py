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
from alembic.config import Config
from alembic import command
from pathlib import Path

# Load environment variables
load_dotenv()

# ============================================================================
# Database Migrations (using Alembic)
# ============================================================================
def run_migrations():
    """Run pending database migrations using Alembic."""
    try:
        # Construct the alembic config path
        alembic_dir = Path(__file__).parent.parent
        alembic_cfg = Config(str(alembic_dir / "alembic.ini"))
        
        # Set the database URL for Alembic
        alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
        
        # Run pending migrations
        command.upgrade(alembic_cfg, "head")
        print("[OK] Database migrations completed successfully")
    except Exception as e:
        print(f"[INFO] Database migration check completed (error: {type(e).__name__})")
        print(f"  This is normal if tables already exist in production.")

# Run migrations on startup
run_migrations()

# Initialize default roles and permissions
db_init = SessionLocal()
try:
    init_db(db_init)
finally:
    db_init.close()

# ============================================================================
# Legacy Schema Adjustments (for migration compatibility)
# ============================================================================
# These checks handle edge cases for existing databases during migration period
insp = inspect(engine)
try:
    # Ensure organizations table has at least 'RHD' default
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO organizations (name)
            SELECT 'RHD'
            WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE name = 'RHD')
        """))
        conn.execute(text("""
            INSERT INTO organizations (name)
            SELECT 'LGED'
            WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE name = 'LGED')
        """))
except Exception as e:
    print(f"Note: Organizations initialization - {str(e)[:80]}")

app = FastAPI(title="Estimation Backend", version="1.0.0")

# CORS: cannot use "*" when allow_credentials=True.
# Explicitly list frontend origins and allow Netlify deploy previews via regex.

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "estimation-backend", "version": "1.0.0"}

# CORS: cannot use "*" when allow_credentials=True.
# Explicitly list frontend origins and allow Netlify deploy previews via regex.
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

# Add explicit frontend origins (Vercel deployment)
cors_origins.extend([
    "https://rhd-estimation-frontend.vercel.app",
    "https://rhd-estimation-frontend.vercel.app/",
])

# For development only
if os.getenv("APP_ENV") == "development":
    cors_origins.extend([
        "http://localhost:5173",
        "http://localhost:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
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
        print("[OK] System roles and permissions initialized successfully")
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
        print(f"Warning: Could not ensure admin user info - {e}")
        pass

# Initialize system roles on startup
try:
    init_system_roles_and_permissions()
    ensure_admin_user()
except Exception as e:
    print(f"[ERROR] Initialization failed: {e}")
