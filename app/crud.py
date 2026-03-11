from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, tuple_
from . import models, schemas
from sqlalchemy.exc import IntegrityError
from .security import get_password_hash, verify_password
from datetime import datetime
import re

# =============== User CRUD Operations ===============

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a new user."""
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> models.User | None:
    """Get a user by username."""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Get a user by email."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """Get a user by ID."""
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_all_users(db: Session, skip: int = 0, limit: int = 100, search: str | None = None) -> list[models.User]:
    """Get all users with optional search."""
    query = db.query(models.User)
    if search:
        term = f"%{search}%"
        query = query.filter(
            func.lower(models.User.username).like(term.lower()) |
            func.lower(models.User.email).like(term.lower()) |
            func.lower(models.User.full_name).like(term.lower())
        )
    return query.offset(skip).limit(limit).all()

def get_user_count(db: Session) -> int:
    return db.query(func.count(models.User.user_id)).scalar() or 0

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User | None:
    """Update a user."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    if user_update.email:
        db_user.email = user_update.email
    if user_update.full_name:
        db_user.full_name = user_update.full_name
    if user_update.password:
        db_user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def deactivate_user(db: Session, user_id: int) -> models.User | None:
    """Deactivate a user."""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.is_active = False
        db.commit()
        db.refresh(db_user)
    return db_user

def activate_user(db: Session, user_id: int) -> models.User | None:
    """Activate a user."""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.is_active = True
        db.commit()
        db.refresh(db_user)
    return db_user

# =============== Role CRUD Operations ===============

def create_role(db: Session, role: schemas.RoleCreate, is_system_role: bool = False) -> models.Role:
    """Create a new role."""
    db_role = models.Role(
        name=role.name,
        description=role.description,
        is_system_role=is_system_role
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def get_role_by_name(db: Session, name: str) -> models.Role | None:
    """Get a role by name."""
    return db.query(models.Role).filter(models.Role.name == name).first()

def get_role_by_id(db: Session, role_id: int) -> models.Role | None:
    """Get a role by ID."""
    return db.query(models.Role).filter(models.Role.role_id == role_id).first()

def get_all_roles(db: Session, skip: int = 0, limit: int = 100) -> list[models.Role]:
    """Get all roles."""
    return db.query(models.Role).offset(skip).limit(limit).all()

def update_role(db: Session, role_id: int, role_update: schemas.RoleUpdate) -> models.Role | None:
    """Update a role."""
    db_role = get_role_by_id(db, role_id)
    if not db_role:
        return None
    
    if role_update.name:
        db_role.name = role_update.name
    if role_update.description:
        db_role.description = role_update.description
    
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int) -> bool:
    """Delete a role (if not system role)."""
    db_role = get_role_by_id(db, role_id)
    if not db_role or db_role.is_system_role:
        return False
    
    db.delete(db_role)
    db.commit()
    return True

def assign_role_to_user(db: Session, user_id: int, role_id: int) -> bool:
    """Assign a role to a user."""
    db_user = get_user_by_id(db, user_id)
    db_role = get_role_by_id(db, role_id)
    
    if not db_user or not db_role:
        return False
    
    if db_role not in db_user.roles:
        db_user.roles.append(db_role)
        db.commit()
    return True

def remove_role_from_user(db: Session, user_id: int, role_id: int) -> bool:
    """Remove a role from a user."""
    db_user = get_user_by_id(db, user_id)
    db_role = get_role_by_id(db, role_id)
    
    if not db_user or not db_role:
        return False
    
    if db_role in db_user.roles:
        db_user.roles.remove(db_role)
        db.commit()
    return True

# =============== Permission CRUD Operations ===============

def create_permission(db: Session, permission: schemas.PermissionCreate) -> models.Permission:
    """Create a new permission."""
    db_permission = models.Permission(
        name=permission.name,
        description=permission.description
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

def get_permission_by_name(db: Session, name: str) -> models.Permission | None:
    """Get a permission by name."""
    return db.query(models.Permission).filter(models.Permission.name == name).first()

def get_permission_by_id(db: Session, permission_id: int) -> models.Permission | None:
    """Get a permission by ID."""
    return db.query(models.Permission).filter(models.Permission.permission_id == permission_id).first()

def get_all_permissions(db: Session, skip: int = 0, limit: int = 100) -> list[models.Permission]:
    """Get all permissions."""
    return db.query(models.Permission).offset(skip).limit(limit).all()

def assign_permission_to_role(db: Session, role_id: int, permission_id: int) -> bool:
    """Assign a permission to a role."""
    db_role = get_role_by_id(db, role_id)
    db_permission = get_permission_by_id(db, permission_id)
    
    if not db_role or not db_permission:
        return False
    
    if db_permission not in db_role.permissions:
        db_role.permissions.append(db_permission)
        db.commit()
    return True

def remove_permission_from_role(db: Session, role_id: int, permission_id: int) -> bool:
    """Remove a permission from a role."""
    db_role = get_role_by_id(db, role_id)
    db_permission = get_permission_by_id(db, permission_id)
    
    if not db_role or not db_permission:
        return False
    
    if db_permission in db_role.permissions:
        db_role.permissions.remove(db_permission)
        db.commit()
    return True

# =============== Organization CRUD Operations ===============
def get_organization_by_name(db: Session, name: str):
    return db.query(models.Organization).filter(models.Organization.name == name).first()

def get_division_by_name(db: Session, name: str, organization_id: int | None = None):
    q = db.query(models.Division).filter(models.Division.name == name)
    if organization_id is not None:
        q = q.filter(models.Division.organization_id == organization_id)
    return q.first()

def get_item_by_code_region_org(db: Session, item_code: str, region: str, organization: str):
    """Get an item by its code, region, and organization (unique key)."""
    return db.query(models.Item).filter(
        models.Item.item_code == item_code,
        models.Item.region == region,
        models.Item.organization == organization,
    ).first()

def create_item_from_parsed_data(db: Session, item_data: schemas.ItemParsed):
    # Defensive validation: skip placeholder or empty identifiers
    code_clean = (item_data.item_code or "").strip()
    desc_clean = (item_data.item_description or "").strip()
    if not code_clean and not desc_clean:
        raise ValueError("Empty item row: missing both code and description")
    if code_clean.lower() in ("none", "null", "-") or desc_clean.lower() in ("none", "null", "-"):
        raise ValueError("Invalid placeholder values for item code/description")

    # Resolve organization
    org_name = item_data.organization or "RHD"
    org = get_organization_by_name(db, org_name)
    if not org:
        org = create_organization(db, schemas.OrganizationCreate(name=org_name))

    # Ensure region exists for organization
    if item_data.region:
        existing_regions = list_regions_for_org(db, org.org_id)
        if not any(r.name == item_data.region for r in existing_regions):
            create_region(db, schemas.RegionCreate(name=item_data.region, organization_id=org.org_id))

    # Divisions are global by name (unique); prefer name-only lookup to avoid duplicates
    division = get_division_by_name(db, item_data.division)
    if not division:
        try:
            division = create_division(db, schemas.DivisionCreate(name=item_data.division, organization_id=org.org_id))
        except IntegrityError:
            # Another transaction may have created the same division concurrently
            db.rollback()
            division = get_division_by_name(db, item_data.division)
    
    # Check if item already exists for this item_code, region, and organization
    existing_item = get_item_by_code_region_org(db, item_data.item_code, item_data.region, org.name)

    if existing_item:
        # Update existing item
        existing_item.item_description = item_data.item_description
        existing_item.unit = item_data.unit
        existing_item.rate = item_data.rate
        existing_item.division_id = division.division_id
        # Keep organization aligned to owning org
        existing_item.organization = org.name
        db.add(existing_item)
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        # Create new item
        item_create_data = schemas.ItemCreate(
            division_id=division.division_id,
            item_code=code_clean,
            item_description=desc_clean,
            unit=item_data.unit,
            rate=item_data.rate,
            region=item_data.region,
            organization=org.name
        )
        return create_item(db, item_create_data)

def create_item_from_parsed_data_bulk(db: Session, item_data: schemas.ItemParsed):
    """Same as create_item_from_parsed_data but without per-row commit (for bulk imports)."""
    code_clean = (item_data.item_code or "").strip()
    desc_clean = (item_data.item_description or "").strip()
    if not code_clean and not desc_clean:
        raise ValueError("Empty item row: missing both code and description")
    if code_clean.lower() in ("none", "null", "-") or desc_clean.lower() in ("none", "null", "-"):
        raise ValueError("Invalid placeholder values for item code/description")

    org_name = item_data.organization or "RHD"
    org = get_organization_by_name(db, org_name)
    if not org:
        org = create_organization(db, schemas.OrganizationCreate(name=org_name))

    if item_data.region:
        existing_regions = list_regions_for_org(db, org.org_id)
        if not any(r.name == item_data.region for r in existing_regions):
            create_region(db, schemas.RegionCreate(name=item_data.region, organization_id=org.org_id))

    division = get_division_by_name(db, item_data.division)
    if not division:
        try:
            division = create_division(db, schemas.DivisionCreate(name=item_data.division, organization_id=org.org_id))
        except IntegrityError:
            db.rollback()
            division = get_division_by_name(db, item_data.division)

    existing_item = get_item_by_code_region_org(db, item_data.item_code, item_data.region, org.name)

    if existing_item:
        existing_item.item_description = item_data.item_description
        existing_item.unit = item_data.unit
        existing_item.rate = item_data.rate
        existing_item.division_id = division.division_id
        existing_item.organization = org.name
        db.add(existing_item)
        # No commit here — caller handles the transaction
        return existing_item
    else:
        obj = models.Item(
            division_id=division.division_id,
            item_code=code_clean,
            item_description=desc_clean,
            unit=item_data.unit,
            rate=item_data.rate,
            region=item_data.region,
            organization=org.name,
        )
        db.add(obj)
        # No commit here — caller handles the transaction
        return obj

def bulk_import_items_optimized(db: Session, items_data: list[schemas.ItemParsed], mode: str = "append"):
    """
    Optimized bulk import that minimizes DB queries by pre-fetching data.
    """
    if not items_data:
        return {"count": 0, "skipped": 0, "errors": []}
    
    # 1. Pre-fetch reference data (Organizations, Divisions, Regions)
    # ----------------------------------------------------------------
    # Organizations
    all_orgs = {org.name: org for org in list_organizations(db)}
    
    # Divisions (map name -> Division obj) - careful with duplicates across orgs if any
    # Assuming division names are unique globally or we handle it per org
    # Current schema: divisions are unique by name mostly.
    # Let's fetch all divisions and map by name.
    all_divisions = {div.name: div for div in list_divisions(db)}
    
    # Regions (map (org_id, name) -> Region obj)
    all_regions = {}
    for region in db.query(models.Region).all():
        all_regions[(region.organization_id, region.name)] = region
        
    # 2. Pre-fetch existing Items (if mode != replace)
    # ----------------------------------------------------------------
    # Map (item_code, region, organization) -> Item obj
    existing_items_map = {}
    if mode != "replace":
        # Fetch only necessary columns to build the map if memory is concern, 
        # but we need the object to update it.
        # Warning: loading 50k objects into session might be heavy, but better than 50k selects.
        # We can use yield_per if needed, but for now fetch all.
        items_query = db.query(models.Item)
        # If too many items, this might be slow, but still faster than N queries.
        for item in items_query.all():
            key = (item.item_code, item.region, item.organization)
            existing_items_map[key] = item
            
    # 3. Process items in memory
    # ----------------------------------------------------------------
    count = 0
    errors = []
    
    # Cache for newly created reference data in this transaction
    new_orgs = {} # name -> obj
    new_divisions = {} # name -> obj
    new_regions = {} # (org_id, name) -> obj
    
    for idx, row in enumerate(items_data, 1):
        try:
            # Validate basic fields
            code_clean = (row.item_code or "").strip()
            desc_clean = (row.item_description or "").strip()
            if not code_clean and not desc_clean:
                continue # Skip empty rows
                
            if code_clean.lower() in ("none", "null", "-") or desc_clean.lower() in ("none", "null", "-"):
                continue

            # Organization
            org_name = row.organization or "RHD"
            org = all_orgs.get(org_name) or new_orgs.get(org_name)
            if not org:
                org = models.Organization(name=org_name)
                db.add(org)
                db.flush() # Need ID for regions/divisions
                all_orgs[org_name] = org
                new_orgs[org_name] = org
            
            # Region
            region_name = row.region
            if region_name:
                reg_key = (org.org_id, region_name)
                region = all_regions.get(reg_key) or new_regions.get(reg_key)
                if not region:
                    region = models.Region(name=region_name, organization_id=org.org_id)
                    db.add(region)
                    db.flush() # Need ID? Not really, but good to be safe
                    all_regions[reg_key] = region
                    new_regions[reg_key] = region
            
            # Division
            div_name = row.division
            division = all_divisions.get(div_name) or new_divisions.get(div_name)
            if not division:
                # Create division
                division = models.Division(name=div_name, organization_id=org.org_id)
                db.add(division)
                db.flush()
                all_divisions[div_name] = division
                new_divisions[div_name] = division
            
            # Item
            item_key = (code_clean, region_name, org_name)
            existing_item = existing_items_map.get(item_key)
            
            if existing_item:
                # Update
                existing_item.item_description = desc_clean
                existing_item.unit = row.unit
                existing_item.rate = row.rate
                existing_item.division_id = division.division_id
                existing_item.organization = org_name
                # db.add(existing_item) # Already in session
            else:
                # Create
                new_item = models.Item(
                    division_id=division.division_id,
                    item_code=code_clean,
                    item_description=desc_clean,
                    unit=row.unit,
                    rate=row.rate,
                    region=region_name,
                    organization=org_name,
                )
                db.add(new_item)
                existing_items_map[item_key] = new_item # Add to map to prevent duplicates in same batch
            
            count += 1
            
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")
            
    # 4. Commit all changes
    # ----------------------------------------------------------------
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
        
    return {"count": count, "errors": errors}

def get_divisions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Division).offset(skip).limit(limit).all()

def create_division(db: Session, data: schemas.DivisionCreate):
    payload = data.model_dump()
    # Default organization to RHD if not provided
    if payload.get("organization_id") is None:
        # Find or create RHD organization
        org = db.query(models.Organization).filter(models.Organization.name == "RHD").first()
        if not org:
            org = models.Organization(name="RHD")
            db.add(org)
            db.commit()
            db.refresh(org)
        payload["organization_id"] = org.org_id
    obj = models.Division(**payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_divisions(db: Session):
    return db.execute(select(models.Division)).scalars().all()

def delete_division(db: Session, division_id: int):
    division = db.get(models.Division, division_id)
    if not division:
        return None
    db.delete(division)
    db.commit()
    return division

# ===== Organizations =====
def create_organization(db: Session, data: schemas.OrganizationCreate):
    obj = models.Organization(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_organizations(db: Session):
    return db.execute(select(models.Organization)).scalars().all()

def delete_organization(db: Session, org_id: int):
    org = db.get(models.Organization, org_id)
    if not org:
        return None
    db.delete(org)
    db.commit()
    return org

def update_organization(db: Session, org_id: int, data: schemas.OrganizationUpdate):
    obj = db.get(models.Organization, org_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(obj)
    return obj

# ===== Regions (per organization) =====
def create_region(db: Session, data: schemas.RegionCreate):
    obj = models.Region(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_regions_for_org(db: Session, organization_id: int):
    stmt = select(models.Region).where(models.Region.organization_id == organization_id)
    return db.execute(stmt).scalars().all()

def delete_region(db: Session, region_id: int):
    reg = db.get(models.Region, region_id)
    if not reg:
        return None
    db.delete(reg)
    db.commit()
    return reg

def update_region(db: Session, region_id: int, data: schemas.RegionUpdate):
    obj = db.get(models.Region, region_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(obj)
    return obj

def get_items(db: Session, region: str | None = None, organization: str | None = None, skip: int = 0, limit: int = 100,
              search: str | None = None, item_code: str | None = None, item_description: str | None = None,
              division_id: int | None = None, unit: str | None = None,
              rate_min: float | None = None, rate_max: float | None = None,
              sort_by: str = "item_code", order: str = "asc"):
    """Get paginated items with optional server-side filtering and sorting.

    skip and limit are in terms of unique (division_id, item_code) pairs so that
    limit=50 always returns exactly 50 grouped items regardless of region count.
    """
    # Determine sort column
    if sort_by == "rate":
        sort_column = models.Item.rate
    elif sort_by == "region":
        sort_column = models.Item.region
    elif sort_by == "division":
        sort_column = models.Item.division_id
    else:
        sort_column = models.Item.item_code

    order_expr = sort_column.desc() if order.lower() == "desc" else sort_column.asc()

    # Step 1: get the Nth page of distinct (division_id, item_code) pairs
    pairs_q = (
        db.query(models.Item.division_id, models.Item.item_code)
        .outerjoin(models.SpecialItem, models.Item.item_id == models.SpecialItem.item_id)
        .filter(models.SpecialItem.special_item_id == None)
    )
    if region:
        pairs_q = pairs_q.filter(models.Item.region == region)
    if organization:
        pairs_q = pairs_q.filter(models.Item.organization == organization)
    if division_id is not None:
        pairs_q = pairs_q.filter(models.Item.division_id == division_id)
    if unit:
        pairs_q = pairs_q.filter(models.Item.unit == unit)
    if rate_min is not None:
        pairs_q = pairs_q.filter(models.Item.rate >= rate_min)
    if rate_max is not None:
        pairs_q = pairs_q.filter(models.Item.rate <= rate_max)
    if search:
        st = f"%{search}%"
        pairs_q = pairs_q.filter(
            db.func.lower(models.Item.item_code).like(st.lower()) |
            db.func.lower(models.Item.item_description).like(st.lower())
        )
    if item_code:
        pairs_q = pairs_q.filter(db.func.lower(models.Item.item_code).like(f"%{item_code.lower()}%"))
    if item_description:
        pairs_q = pairs_q.filter(db.func.lower(models.Item.item_description).like(f"%{item_description.lower()}%"))

    pairs = (
        pairs_q.distinct()
        .order_by(order_expr, models.Item.division_id.asc())
        .offset(skip).limit(limit)
        .all()
    )

    if not pairs:
        return []

    # Step 2: fetch all region rows for those pairs
    return (
        db.query(models.Item)
        .options(joinedload(models.Item.division))
        .outerjoin(models.SpecialItem, models.Item.item_id == models.SpecialItem.item_id)
        .filter(models.SpecialItem.special_item_id == None)
        .filter(tuple_(models.Item.division_id, models.Item.item_code).in_(pairs))
        .order_by(order_expr, models.Item.division_id.asc(), models.Item.region.asc())
        .all()
    )

def count_items(db: Session, region: str | None = None, organization: str | None = None,
                search: str | None = None, item_code: str | None = None, item_description: str | None = None,
                division_id: int | None = None, unit: str | None = None,
                rate_min: float | None = None, rate_max: float | None = None) -> int:
    """Count distinct (division_id, item_code) pairs — i.e. the number of unique grouped items."""
    pairs_q = (
        db.query(models.Item.division_id, models.Item.item_code)
        .outerjoin(models.SpecialItem, models.Item.item_id == models.SpecialItem.item_id)
        .filter(models.SpecialItem.special_item_id == None)
    )
    if region:
        pairs_q = pairs_q.filter(models.Item.region == region)
    if organization:
        pairs_q = pairs_q.filter(models.Item.organization == organization)
    if division_id is not None:
        pairs_q = pairs_q.filter(models.Item.division_id == division_id)
    if unit:
        pairs_q = pairs_q.filter(models.Item.unit == unit)
    if rate_min is not None:
        pairs_q = pairs_q.filter(models.Item.rate >= rate_min)
    if rate_max is not None:
        pairs_q = pairs_q.filter(models.Item.rate <= rate_max)
    if search:
        st = f"%{search}%"
        pairs_q = pairs_q.filter(
            db.func.lower(models.Item.item_code).like(st.lower()) |
            db.func.lower(models.Item.item_description).like(st.lower())
        )
    if item_code:
        pairs_q = pairs_q.filter(db.func.lower(models.Item.item_code).like(f"%{item_code.lower()}%"))
    if item_description:
        pairs_q = pairs_q.filter(db.func.lower(models.Item.item_description).like(f"%{item_description.lower()}%"))
    subq = pairs_q.distinct().subquery()
    return db.query(func.count()).select_from(subq).scalar() or 0

def create_item(db: Session, data: schemas.ItemCreate):
    obj = models.Item(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_items(db: Session):
    stmt = select(models.Item).options(joinedload(models.Item.division))
    # Exclude special items
    stmt = stmt.outerjoin(models.SpecialItem, models.Item.item_id == models.SpecialItem.item_id).filter(models.SpecialItem.special_item_id == None)
    return db.execute(stmt).scalars().all()

def update_item(db: Session, item_id: int, data: schemas.ItemUpdate):
    item = db.get(models.Item, item_id)
    if not item:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    # If this item is linked to a SpecialItem, update that too
    if item.special_item:
        for key, value in update_data.items():
            if hasattr(item.special_item, key):
                setattr(item.special_item, key, value)
        db.add(item.special_item)

    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def delete_item(db: Session, item_id: int):
    item = db.get(models.Item, item_id)
    if not item:
        return None
    
    # Ensure associated special_item is deleted
    if item.special_item:
        db.delete(item.special_item)
        
    db.delete(item)
    db.commit()
    return item

def delete_all_items(db: Session) -> int:
    """Delete all items from the item master. Returns number of rows deleted."""
    stmt = models.Item.__table__.delete()
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def get_special_items(db: Session, region: str | None = None, organization: str | None = None, skip: int = 0, limit: int = 100,
                      search: str | None = None, division_id: int | None = None, unit: str | None = None,
                      rate_min: float | None = None, rate_max: float | None = None,
                      sort_by: str = "item_code", order: str = "asc"):
    """Get paginated special items. skip/limit are in terms of unique (division_id, item_code) pairs."""
    if sort_by == "rate":
        sort_column = models.SpecialItem.rate
    elif sort_by == "region":
        sort_column = models.SpecialItem.region
    elif sort_by == "division":
        sort_column = models.SpecialItem.division_id
    else:
        sort_column = models.SpecialItem.item_code

    order_expr = sort_column.desc() if order.lower() == "desc" else sort_column.asc()

    # Step 1: page of distinct (division_id, item_code) pairs
    pairs_q = db.query(models.SpecialItem.division_id, models.SpecialItem.item_code)
    if region:
        pairs_q = pairs_q.filter(models.SpecialItem.region == region)
    if organization:
        pairs_q = pairs_q.filter(models.SpecialItem.organization == organization)
    if division_id is not None:
        pairs_q = pairs_q.filter(models.SpecialItem.division_id == division_id)
    if unit:
        pairs_q = pairs_q.filter(models.SpecialItem.unit == unit)
    if rate_min is not None:
        pairs_q = pairs_q.filter(models.SpecialItem.rate >= rate_min)
    if rate_max is not None:
        pairs_q = pairs_q.filter(models.SpecialItem.rate <= rate_max)
    if search:
        st = f"%{search}%"
        pairs_q = pairs_q.filter(
            db.func.lower(models.SpecialItem.item_code).like(st.lower()) |
            db.func.lower(models.SpecialItem.item_description).like(st.lower())
        )

    pairs = (
        pairs_q.distinct()
        .order_by(order_expr, models.SpecialItem.division_id.asc())
        .offset(skip).limit(limit)
        .all()
    )

    if not pairs:
        return []

    # Step 2: all region rows for those pairs
    return (
        db.query(models.SpecialItem)
        .options(joinedload(models.SpecialItem.division))
        .filter(tuple_(models.SpecialItem.division_id, models.SpecialItem.item_code).in_(pairs))
        .order_by(order_expr, models.SpecialItem.division_id.asc(), models.SpecialItem.region.asc())
        .all()
    )

def create_special_item_from_item(db: Session, item: models.Item):
    special_item = models.SpecialItem(
        item_id=item.item_id,
        division_id=item.division_id,
        item_code=item.item_code,
        item_description=item.item_description,
        unit=item.unit,
        rate=item.rate,
        region=item.region,
        organization=item.organization,
    )
    db.add(special_item)
    db.commit()
    db.refresh(special_item)
    return special_item

def create_project(db: Session, data: schemas.ProjectCreate, user_id: int | None = None):
    obj = models.Project(
        **data.model_dump(),
        created_by_id=user_id,
        updated_by_id=user_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete_project(db: Session, project_id: int):
    project = db.get(models.Project, project_id)
    if not project:
        return None
    db.delete(project)
    db.commit()
    return project

def list_projects(db: Session):
    stmt = select(models.Project).options(
        joinedload(models.Project.created_by),
        joinedload(models.Project.updated_by)
    )
    return db.execute(stmt).scalars().all()

def update_project(db: Session, project_id: int, data: schemas.ProjectUpdate, user_id: int | None = None):
    project = db.get(models.Project, project_id)
    if not project:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    project.updated_by_id = user_id or project.updated_by_id
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def create_estimation(db: Session, project_id: int, data: schemas.EstimationCreate, user_id: int | None = None):
    obj = models.Estimation(
        project_id=project_id,
        **data.model_dump(),
        created_by_id=user_id,
        updated_by_id=user_id
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete_estimation(db: Session, estimation_id: int):
    estimation = db.get(models.Estimation, estimation_id)
    if not estimation:
        return None
    db.delete(estimation)
    db.commit()
    return estimation

def list_estimations_for_project(db: Session, project_id: int):
    stmt = (
        select(models.Estimation)
        .where(models.Estimation.project_id == project_id)
        .options(
            joinedload(models.Estimation.created_by),
            joinedload(models.Estimation.updated_by)
        )
    )
    return db.execute(stmt).scalars().all()

def update_estimation(db: Session, estimation_id: int, data: schemas.EstimationUpdate, user_id: int | None = None):
    estimation = db.get(models.Estimation, estimation_id)
    if not estimation:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(estimation, key, value)
    estimation.updated_by_id = user_id or estimation.updated_by_id
    db.add(estimation)
    db.commit()
    db.refresh(estimation)
    return estimation

def get_item_rate(db: Session, item_id: int):
    rate = db.execute(select(models.Item.rate).where(models.Item.item_id == item_id)).scalar_one_or_none()
    return float(rate) if rate is not None else None

def normalize_region_key(region: str | None) -> str:
    s = str(region or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("cumilla", "comilla")
    s = s.replace("chittagong", "chattogram")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def region_matches(a: str | None, b: str | None) -> bool:
    ka = normalize_region_key(a)
    kb = normalize_region_key(b)
    if not ka or not kb:
        return False
    return ka == kb or ka in kb or kb in ka

def find_rate_item_by_region_alias(db: Session, item: models.Item):
    if not item:
        return None
    candidates = (
        db.query(models.Item)
        .filter(models.Item.item_code == item.item_code)
        .filter(models.Item.division_id == item.division_id)
        .filter(models.Item.organization == item.organization)
        .all()
    )
    for cand in candidates:
        cand_rate = float(cand.rate) if cand.rate is not None else None
        if cand_rate and cand_rate > 0 and region_matches(cand.region, item.region):
            return cand
    return None

def sync_estimation_line_rates(db: Session, lines: list[models.EstimationLine]):
    updated = False
    synced_lines = []
    for line in lines:
        item = line.item
        if not item:
            continue
        if item.special_item:
            synced_lines.append(line)
            continue
        line_rate_val = float(line.rate) if line.rate is not None else None
        item_rate_val = float(item.rate) if item.rate is not None else None
        if (line_rate_val is None or line_rate_val == 0) and item_rate_val and item_rate_val > 0:
            line.rate = item_rate_val
            line.calculated_qty = calculate_qty(
                line.no_of_units, line.length, line.width, line.thickness, line.quantity
            )
            line.amount = round(line.calculated_qty * float(line.rate), 2)
            updated = True
            synced_lines.append(line)
            continue
        if (line_rate_val is None or line_rate_val == 0) and (not item_rate_val or item_rate_val == 0):
            candidate = find_rate_item_by_region_alias(db, item)
            if candidate:
                line.item_id = candidate.item_id
                line.item = candidate
                line.rate = float(candidate.rate)
                line.calculated_qty = calculate_qty(
                    line.no_of_units, line.length, line.width, line.thickness, line.quantity
                )
                line.amount = round(line.calculated_qty * float(line.rate), 2)
                updated = True
                synced_lines.append(line)
                continue
        if line_rate_val and line_rate_val > 0:
            synced_lines.append(line)
            continue
    if updated:
        db.commit()
    return synced_lines

def get_estimation_rate_report(db: Session, estimation_id: int):
    stmt = select(models.EstimationLine).where(models.EstimationLine.estimation_id == estimation_id).options(
        joinedload(models.EstimationLine.item).joinedload(models.Item.division),
        joinedload(models.EstimationLine.item).joinedload(models.Item.special_item)
    )
    lines = db.execute(stmt).scalars().all()
    report = []
    for line in lines:
        item = line.item
        if not item:
            report.append({
                "line_id": line.line_id,
                "item_id": None,
                "item_code": None,
                "division": None,
                "organization": None,
                "region": None,
                "line_rate": float(line.rate) if line.rate is not None else None,
                "item_rate": None,
                "reason": "missing item reference",
            })
            continue
        if item.special_item:
            continue
        item_rate_val = float(item.rate) if item.rate is not None else None
        if item_rate_val and item_rate_val > 0:
            continue
        candidate = find_rate_item_by_region_alias(db, item)
        if candidate:
            continue
        candidates = (
            db.query(models.Item)
            .filter(models.Item.item_code == item.item_code)
            .filter(models.Item.division_id == item.division_id)
            .filter(models.Item.organization == item.organization)
            .all()
        )
        alt_rates = [
            c for c in candidates if c.rate is not None and float(c.rate) > 0
        ]
        best_alt = max(alt_rates, key=lambda c: float(c.rate)) if alt_rates else None
        reason = (
            "rate exists in other region"
            if best_alt
            else "no master rate for code/region/organization/division"
        )
        report.append({
            "line_id": line.line_id,
            "item_id": item.item_id,
            "item_code": item.item_code,
            "division": item.division.name if item.division else None,
            "organization": item.organization,
            "region": item.region,
            "line_rate": float(line.rate) if line.rate is not None else None,
            "item_rate": item_rate_val,
            "alt_region": best_alt.region if best_alt else None,
            "alt_rate": float(best_alt.rate) if best_alt else None,
            "reason": reason,
        })
    return report

def calculate_qty(no_of_units: int | None, length, width, thickness, quantity):
    if quantity is not None:
        return float(quantity)
    qty = float(no_of_units or 1)
    for d in (length, width, thickness):
        if d is not None:
            qty *= float(d)
    return qty

def create_estimation_line(db: Session, estimation_id: int, data: schemas.EstimationLineCreate):
    # determine rate: prefer provided rate else item's default rate
    line_rate = get_item_rate(db, data.item_id)
    item_id = data.item_id
    if not line_rate or line_rate == 0:
        base_item = db.get(models.Item, data.item_id)
        candidate = find_rate_item_by_region_alias(db, base_item)
        if candidate:
            item_id = candidate.item_id
            line_rate = float(candidate.rate)
    # calculate quantity
    calc_qty = calculate_qty(data.no_of_units, data.length, data.width, data.thickness, data.quantity)
    amount = round(calc_qty * float(line_rate), 2) if line_rate is not None else None

    obj = models.EstimationLine(
        estimation_id=estimation_id,
        item_id=item_id,
        sub_description=data.sub_description,
        no_of_units=data.no_of_units or 1,
        no_of_units_expr=data.no_of_units_expr,
        length=data.length,
        width=data.width,
        thickness=data.thickness,
        length_expr=data.length_expr,
        width_expr=data.width_expr,
        thickness_expr=data.thickness_expr,
        quantity=data.quantity,
        calculated_qty=calc_qty,
        rate=line_rate,
        amount=amount,
        attachment_name=data.attachment_name,
        attachment_base64=data.attachment_base64,
    )
    db.add(obj)
    
    # Update parent estimation updated_at
    est = db.get(models.Estimation, estimation_id)
    if est:
        est.updated_at = datetime.utcnow()
        db.add(est)

    db.commit()
    db.refresh(obj)
    return obj

def delete_estimation_lines(db: Session, line_ids: list[int]):
    # Get affected estimation IDs before deletion
    stmt_select = select(models.EstimationLine.estimation_id).where(models.EstimationLine.line_id.in_(line_ids)).distinct()
    estimation_ids = db.execute(stmt_select).scalars().all()

    stmt = models.EstimationLine.__table__.delete().where(models.EstimationLine.line_id.in_(line_ids))
    result = db.execute(stmt)
    
    # Update updated_at for affected estimations
    if estimation_ids:
        db.execute(
            models.Estimation.__table__.update()
            .where(models.Estimation.estimation_id.in_(estimation_ids))
            .values(updated_at=datetime.utcnow())
        )
        
    db.commit()
    return result.rowcount

def update_estimation_line(db: Session, line_id: int, data: schemas.EstimationLineCreate):
    line = db.get(models.EstimationLine, line_id)
    if not line:
        return None

    # Update fields from payload
    if data.item_id and data.item_id != line.item_id:
        line.item_id = data.item_id
        # Update rate based on new item
        line_rate = get_item_rate(db, data.item_id)
        line.rate = line_rate

    line.sub_description = data.sub_description
    line.no_of_units = data.no_of_units or 1
    line.no_of_units_expr = data.no_of_units_expr
    line.length = data.length
    line.width = data.width
    line.thickness = data.thickness
    line.length_expr = data.length_expr
    line.width_expr = data.width_expr
    line.thickness_expr = data.thickness_expr
    line.quantity = data.quantity
    # Update attachment fields if provided
    line.attachment_name = data.attachment_name
    line.attachment_base64 = data.attachment_base64

    # Recalculate based on potentially new dimensions
    line.calculated_qty = calculate_qty(line.no_of_units, line.length, line.width, line.thickness, line.quantity)
    
    # Rate is not updated from payload, it's fixed at creation. Amount is recalculated.
    line.amount = round(line.calculated_qty * float(line.rate), 2) if line.rate is not None else None
    
    db.add(line)

    # Update parent estimation updated_at
    est = db.get(models.Estimation, line.estimation_id)
    if est:
        est.updated_at = datetime.utcnow()
        db.add(est)

    db.commit()
    db.refresh(line)
    return line

def create_special_item_request(db: Session, estimation_id: int, data: schemas.SpecialItemRequestCreate, user_id: int):
    item_code = f"SP-{int(datetime.utcnow().timestamp() * 1000)}"
    obj = models.SpecialItemRequest(
        estimation_id=estimation_id,
        division_id=data.division_id,
        item_description=data.item_description,
        unit=data.unit,
        rate=data.rate,
        region=data.region,
        organization=data.organization,
        item_code=item_code,
        attachment_name=data.attachment_name,
        attachment_base64=data.attachment_base64,
        sub_description=data.sub_description,
        no_of_units=data.no_of_units,
        length=data.length,
        width=data.width,
        thickness=data.thickness,
        length_expr=data.length_expr,
        width_expr=data.width_expr,
        thickness_expr=data.thickness_expr,
        quantity=data.quantity,
        requested_by_id=user_id,
        status="pending",
    )
    db.add(obj)

    # Update parent estimation updated_at and updated_by_id
    est = db.get(models.Estimation, estimation_id)
    if est:
        est.updated_at = datetime.utcnow()
        est.updated_by_id = user_id
        db.add(est)

    db.commit()
    db.refresh(obj)
    return obj

def list_special_item_requests(db: Session, estimation_id: int | None = None, status: str | None = None):
    query = db.query(models.SpecialItemRequest).options(
        joinedload(models.SpecialItemRequest.requested_by),
        joinedload(models.SpecialItemRequest.reviewed_by),
        joinedload(models.SpecialItemRequest.division),
    )
    if estimation_id is not None:
        query = query.filter(models.SpecialItemRequest.estimation_id == estimation_id)
    if status:
        query = query.filter(models.SpecialItemRequest.status == status)
    return query.order_by(models.SpecialItemRequest.created_at.desc()).all()

def list_special_item_requests_for_user(db: Session, estimation_id: int | None, user_id: int, status: str | None = None):
    query = db.query(models.SpecialItemRequest).options(
        joinedload(models.SpecialItemRequest.requested_by),
        joinedload(models.SpecialItemRequest.reviewed_by),
        joinedload(models.SpecialItemRequest.division),
    ).filter(models.SpecialItemRequest.requested_by_id == user_id)
    if estimation_id is not None:
        query = query.filter(models.SpecialItemRequest.estimation_id == estimation_id)
    if status:
        query = query.filter(models.SpecialItemRequest.status == status)
    return query.order_by(models.SpecialItemRequest.created_at.desc()).all()

def approve_special_item_request(db: Session, request_id: int, reviewer_id: int):
    req = db.get(models.SpecialItemRequest, request_id)
    if not req:
        return None
    if req.status != "pending":
        return req

    item = models.Item(
        division_id=req.division_id,
        item_code=req.item_code or f"SP-{req.division_id:02d}/01/{req.request_id:03d}",
        item_description=req.item_description,
        unit=req.unit,
        rate=req.rate,
        region=req.region,
        organization=req.organization,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    special_item = create_special_item_from_item(db, item)

    line_payload = schemas.EstimationLineCreate(
        item_id=item.item_id,
        sub_description=req.sub_description,
        no_of_units=req.no_of_units,
        no_of_units_expr=req.no_of_units_expr,
        length=req.length,
        width=req.width,
        thickness=req.thickness,
        length_expr=req.length_expr,
        width_expr=req.width_expr,
        thickness_expr=req.thickness_expr,
        quantity=req.quantity,
        attachment_name=req.attachment_name,
        attachment_base64=req.attachment_base64,
    )
    line = create_estimation_line(db, req.estimation_id, line_payload)

    req.status = "approved"
    req.reviewed_by_id = reviewer_id
    req.reviewed_at = datetime.utcnow()
    req.item_id = item.item_id
    req.special_item_id = special_item.special_item_id
    req.line_id = line.line_id
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def reject_special_item_request(db: Session, request_id: int, reviewer_id: int, reason: str | None = None):
    req = db.get(models.SpecialItemRequest, request_id)
    if not req:
        return None
    if req.status != "pending":
        return req
    req.status = "rejected"
    req.reviewed_by_id = reviewer_id
    req.reviewed_at = datetime.utcnow()
    req.reason = reason
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def list_estimation_lines(db: Session, estimation_id: int):
    stmt = select(models.EstimationLine).where(models.EstimationLine.estimation_id == estimation_id).options(
        joinedload(models.EstimationLine.item).joinedload(models.Item.division),
        joinedload(models.EstimationLine.item).joinedload(models.Item.special_item)
    )
    lines = db.execute(stmt).scalars().all()
    return sync_estimation_line_rates(db, lines)

def estimation_total(db: Session, estimation_id: int):
    lines = list_estimation_lines(db, estimation_id)
    return float(sum((line.amount or 0) for line in lines))

def get_estimation_with_lines(db: Session, estimation_id: int):
    est = db.execute(
        select(models.Estimation).where(models.Estimation.estimation_id == estimation_id)
    ).scalar_one()
    lines = list_estimation_lines(db, estimation_id)
    return est, lines

def update_special_item_request(db: Session, request_id: int, data: schemas.SpecialItemRequestCreate) -> models.SpecialItemRequest | None:
    req = db.get(models.SpecialItemRequest, request_id)
    if not req:
        return None
    if req.status != "pending":
        # Only pending requests can be updated
        return None
    
    # Update fields
    req.division_id = data.division_id
    req.item_description = data.item_description
    req.unit = data.unit
    req.rate = data.rate
    req.region = data.region
    req.organization = data.organization
    req.attachment_name = data.attachment_name
    if data.attachment_base64:
        req.attachment_base64 = data.attachment_base64
    req.sub_description = data.sub_description
    req.no_of_units = data.no_of_units
    req.length = data.length
    req.width = data.width
    req.thickness = data.thickness
    req.length_expr = data.length_expr
    req.width_expr = data.width_expr
    req.thickness_expr = data.thickness_expr
    req.quantity = data.quantity

    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def delete_special_item_request(db: Session, request_id: int) -> bool:
    req = db.get(models.SpecialItemRequest, request_id)
    if not req:
        return False
    if req.status == "approved":
        # Approved requests cannot be deleted directly (delete the resulting line instead)
        return False
    
    db.delete(req)
    db.commit()
    return True
