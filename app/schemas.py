from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

# =============== Authentication Schemas ===============

# Permission Schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    permission_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Role(RoleBase):
    role_id: int
    is_system_role: bool
    created_at: datetime
    permissions: List[Permission] = []
    
    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str

class User(UserBase):
    user_id: int
    is_active: bool
    created_at: datetime
    roles: List[Role] = []
    
    model_config = ConfigDict(from_attributes=True)

class UserWithPassword(User):
    hashed_password: str

class AuditUser(BaseModel):
    user_id: int
    username: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

# =============== Other Schemas ===============
class DivisionBase(BaseModel):
    name: str

class DivisionCreate(DivisionBase):
    # Optional during transition; default will be RHD if omitted
    organization_id: Optional[int] = None

class Division(DivisionBase):
    division_id: int
    organization_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

# Organization Schemas
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    org_id: int

    model_config = ConfigDict(from_attributes=True)

class OrganizationUpdate(BaseModel):
    name: str | None = None

# Region Schemas
class RegionBase(BaseModel):
    name: str

class RegionCreate(RegionBase):
    organization_id: int

class Region(RegionBase):
    region_id: int
    organization_id: int

    model_config = ConfigDict(from_attributes=True)

class RegionUpdate(BaseModel):
    name: str | None = None

# Item Schemas
class ItemBase(BaseModel):
    item_code: str
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str
    organization: str = "RHD"

class ItemCreate(ItemBase):
    division_id: int

class ItemUpdate(BaseModel):
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: Optional[str] = None
    division_id: Optional[int] = None
    organization: Optional[str] = None

class ItemParsed(BaseModel):
    division: str
    item_code: str
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str
    organization: Optional[str] = "RHD"

class Item(ItemBase):
    item_id: int
    division_id: int
    division: Division

    model_config = ConfigDict(from_attributes=True)

class SpecialItemBase(BaseModel):
    item_code: str
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str
    organization: str = "RHD"

class SpecialItem(SpecialItemBase):
    special_item_id: int
    item_id: int
    division_id: int
    division: Division
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Project Schemas
class ProjectBase(BaseModel):
    project_name: str
    client_name: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    project_id: int
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[AuditUser] = None
    updated_by: Optional[AuditUser] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    client_name: Optional[str] = None

# Estimation Schemas
class EstimationLineBase(BaseModel):
    item_id: int
    sub_description: Optional[str] = None
    no_of_units: int = 1
    length: Optional[float] = None
    width: Optional[float] = None
    thickness: Optional[float] = None
    length_expr: Optional[str] = None
    width_expr: Optional[str] = None
    thickness_expr: Optional[str] = None
    quantity: Optional[float] = None
    # Optional attachment for Special Item lines
    attachment_name: Optional[str] = None
    attachment_base64: Optional[str] = None

class SpecialItemRequestCreate(BaseModel):
    division_id: int
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str
    organization: str = "RHD"
    attachment_name: Optional[str] = None
    attachment_base64: Optional[str] = None
    sub_description: Optional[str] = None
    no_of_units: int = 1
    length: Optional[float] = None
    width: Optional[float] = None
    thickness: Optional[float] = None
    length_expr: Optional[str] = None
    width_expr: Optional[str] = None
    thickness_expr: Optional[str] = None
    quantity: Optional[float] = None

class SpecialItemRequestReject(BaseModel):
    reason: Optional[str] = None

class SpecialItemRequest(BaseModel):
    request_id: int
    estimation_id: int
    division_id: int
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str
    organization: str
    item_code: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_base64: Optional[str] = None
    sub_description: Optional[str] = None
    no_of_units: int
    length: Optional[float] = None
    width: Optional[float] = None
    thickness: Optional[float] = None
    length_expr: Optional[str] = None
    width_expr: Optional[str] = None
    thickness_expr: Optional[str] = None
    quantity: Optional[float] = None
    status: str
    reason: Optional[str] = None
    requested_by_id: int
    reviewed_by_id: Optional[int] = None
    item_id: Optional[int] = None
    special_item_id: Optional[int] = None
    line_id: Optional[int] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    requested_by: Optional[AuditUser] = None
    reviewed_by: Optional[AuditUser] = None

    model_config = ConfigDict(from_attributes=True)

class EstimationLineCreate(EstimationLineBase):
    pass

class EstimationLine(EstimationLineBase):
    line_id: int
    estimation_id: int
    calculated_qty: Optional[float] = None
    rate: Optional[float] = None
    amount: Optional[float] = None
    item: Item

    model_config = ConfigDict(from_attributes=True)

class EstimationBase(BaseModel):
    estimation_name: str

class EstimationCreate(EstimationBase):
    pass

class Estimation(EstimationBase):
    estimation_id: int
    project_id: int
    lines: List[EstimationLine] = []
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[AuditUser] = None
    updated_by: Optional[AuditUser] = None

    model_config = ConfigDict(from_attributes=True)

class EstimationUpdate(BaseModel):
    estimation_name: Optional[str] = None

class EstimationLineDelete(BaseModel):
    line_ids: List[int]
