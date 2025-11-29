from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from . import models, schemas

def get_organization_by_name(db: Session, name: str):
    return db.query(models.Organization).filter(models.Organization.name == name).first()

def get_division_by_name(db: Session, name: str, organization_id: int | None = None):
    q = db.query(models.Division).filter(models.Division.name == name)
    if organization_id is not None:
        q = q.filter(models.Division.organization_id == organization_id)
    return q.first()

def create_item_from_parsed_data(db: Session, item_data: schemas.ItemParsed):
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

    # Find or create division scoped to organization
    division = get_division_by_name(db, item_data.division, organization_id=org.org_id)
    if not division:
        division = create_division(db, schemas.DivisionCreate(name=item_data.division, organization_id=org.org_id))
    
    # Check if item already exists for this item_code and region
    existing_item = get_item_by_code_and_region(db, item_data.item_code, item_data.region)

    if existing_item:
        # Update existing item
        existing_item.item_description = item_data.item_description
        existing_item.unit = item_data.unit
        existing_item.rate = item_data.rate
        existing_item.division_id = division.division_id
        db.add(existing_item)
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        # Create new item
        item_create_data = schemas.ItemCreate(
            division_id=division.division_id,
            item_code=item_data.item_code,
            item_description=item_data.item_description,
            unit=item_data.unit,
            rate=item_data.rate,
            region=item_data.region,
            organization=org.name
        )
        return create_item(db, item_create_data)

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

def get_items(db: Session, region: str | None = None, organization: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Item).options(joinedload(models.Item.division))
    if region:
        query = query.filter(models.Item.region == region)
    if organization:
        query = query.filter(models.Item.organization == organization)
    return query.offset(skip).limit(limit).all()

def get_item_by_code_and_region(db: Session, item_code: str, region: str):
    return db.query(models.Item).filter(models.Item.item_code == item_code, models.Item.region == region).first()

def create_item(db: Session, data: schemas.ItemCreate):
    obj = models.Item(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def list_items(db: Session):
    stmt = select(models.Item).options(joinedload(models.Item.division))
    return db.execute(stmt).scalars().all()

def update_item(db: Session, item_id: int, data: schemas.ItemUpdate):
    item = db.get(models.Item, item_id)
    if not item:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def delete_item(db: Session, item_id: int):
    item = db.get(models.Item, item_id)
    if not item:
        return None
    db.delete(item)
    db.commit()
    return item

def delete_all_items(db: Session) -> int:
    """Delete all items from the item master. Returns number of rows deleted."""
    stmt = models.Item.__table__.delete()
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def create_project(db: Session, data: schemas.ProjectCreate):
    obj = models.Project(**data.model_dump())
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
    return db.execute(select(models.Project)).scalars().all()

def update_project(db: Session, project_id: int, data: schemas.ProjectUpdate):
    project = db.get(models.Project, project_id)
    if not project:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def create_estimation(db: Session, project_id: int, data: schemas.EstimationCreate):
    obj = models.Estimation(project_id=project_id, **data.model_dump())
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
    stmt = select(models.Estimation).where(models.Estimation.project_id == project_id)
    return db.execute(stmt).scalars().all()

def update_estimation(db: Session, estimation_id: int, data: schemas.EstimationUpdate):
    estimation = db.get(models.Estimation, estimation_id)
    if not estimation:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(estimation, key, value)
    db.add(estimation)
    db.commit()
    db.refresh(estimation)
    return estimation

def get_item_rate(db: Session, item_id: int):
    rate = db.execute(select(models.Item.rate).where(models.Item.item_id == item_id)).scalar_one_or_none()
    return float(rate) if rate is not None else None

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
    line_rate = get_item_rate(db, data.item_id) or 0.0
    # calculate quantity
    calc_qty = calculate_qty(data.no_of_units, data.length, data.width, data.thickness, data.quantity)
    amount = round(calc_qty * float(line_rate), 2) if line_rate is not None else None

    obj = models.EstimationLine(
        estimation_id=estimation_id,
        item_id=data.item_id,
        sub_description=data.sub_description,
        no_of_units=data.no_of_units or 1,
        length=data.length,
        width=data.width,
        thickness=data.thickness,
        quantity=data.quantity,
        calculated_qty=calc_qty,
        rate=line_rate,
        amount=amount,
        attachment_name=data.attachment_name,
        attachment_base64=data.attachment_base64,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete_estimation_lines(db: Session, line_ids: list[int]):
    stmt = models.EstimationLine.__table__.delete().where(models.EstimationLine.line_id.in_(line_ids))
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def update_estimation_line(db: Session, line_id: int, data: schemas.EstimationLineCreate):
    line = db.get(models.EstimationLine, line_id)
    if not line:
        return None

    # Update fields from payload
    # Note: item_id is not updated
    line.sub_description = data.sub_description
    line.no_of_units = data.no_of_units or 1
    line.length = data.length
    line.width = data.width
    line.thickness = data.thickness
    line.quantity = data.quantity
    # Update attachment fields if provided
    line.attachment_name = data.attachment_name
    line.attachment_base64 = data.attachment_base64

    # Recalculate based on potentially new dimensions
    line.calculated_qty = calculate_qty(line.no_of_units, line.length, line.width, line.thickness, line.quantity)
    
    # Rate is not updated from payload, it's fixed at creation. Amount is recalculated.
    line.amount = round(line.calculated_qty * float(line.rate), 2) if line.rate is not None else None
    
    db.add(line)
    db.commit()
    db.refresh(line)
    return line

def list_estimation_lines(db: Session, estimation_id: int):
    stmt = select(models.EstimationLine).where(models.EstimationLine.estimation_id == estimation_id).options(
        joinedload(models.EstimationLine.item).joinedload(models.Item.division)
    )
    return db.execute(stmt).scalars().all()

def estimation_total(db: Session, estimation_id: int):
    total = db.execute(
        select(func.coalesce(func.sum(models.EstimationLine.amount), 0)).where(models.EstimationLine.estimation_id == estimation_id)
    ).scalar_one()
    return float(total or 0.0)

def get_estimation_with_lines(db: Session, estimation_id: int):
    est = db.execute(
        select(models.Estimation).where(models.Estimation.estimation_id == estimation_id)
    ).scalar_one()
    lines = list_estimation_lines(db, estimation_id)
    return est, lines
