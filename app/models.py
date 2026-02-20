from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Text, UniqueConstraint, Boolean, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base
from datetime import datetime

# Association table for User-Role many-to-many relationship
user_roles_association = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True)
)

# Association table for Role-Permission many-to-many relationship
role_permissions_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True)
)

class Permission(Base):
    __tablename__ = "permissions"
    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    roles = relationship("Role", secondary=role_permissions_association, back_populates="permissions")

class Role(Base):
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    users = relationship("User", secondary=user_roles_association, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions_association, back_populates="roles")

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    roles = relationship("Role", secondary=user_roles_association, back_populates="users")

class Organization(Base):
    __tablename__ = "organizations"
    org_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    divisions = relationship("Division", back_populates="organization", cascade="all, delete-orphan")
    regions = relationship("Region", back_populates="organization", cascade="all, delete-orphan")

class Region(Base):
    __tablename__ = "regions"
    region_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.org_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    organization = relationship("Organization", back_populates="regions")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_region_name"),
    )

class Division(Base):
    __tablename__ = "divisions"
    division_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # Link division to owning organization (startup migration will backfill to RHD)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.org_id"), nullable=True)

    organization = relationship("Organization", back_populates="divisions")
    items = relationship("Item", back_populates="division", cascade="all, delete-orphan")
    special_items = relationship("SpecialItem", back_populates="division", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    division_id: Mapped[int] = mapped_column(ForeignKey("divisions.division_id"), nullable=False)
    item_code: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    region: Mapped[str] = mapped_column(String(50), nullable=False, server_default="Default")
    # Organization owning the rate; default to 'RHD'
    organization: Mapped[str] = mapped_column(String(50), nullable=False, server_default="RHD")

    division = relationship("Division", back_populates="items")
    # historical relationships from earlier design not strictly required
    estimation_lines = relationship("EstimationLine", back_populates="item")
    special_item = relationship("SpecialItem", back_populates="item", uselist=False)

    __table_args__ = (
        UniqueConstraint("item_code", "region", "organization", name="uq_item_code_region_org"),
    )

class SpecialItem(Base):
    __tablename__ = "special_items"
    special_item_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"), nullable=False, unique=True)
    division_id: Mapped[int] = mapped_column(ForeignKey("divisions.division_id"), nullable=False)
    item_code: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    region: Mapped[str] = mapped_column(String(50), nullable=False, server_default="Default")
    organization: Mapped[str] = mapped_column(String(50), nullable=False, server_default="RHD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    division = relationship("Division", back_populates="special_items")
    item = relationship("Item", back_populates="special_item")

class Project(Base):
    __tablename__ = "projects"
    project_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    estimations = relationship("Estimation", back_populates="project", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

class Estimation(Base):
    __tablename__ = "estimations"
    estimation_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    estimation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="estimations")
    lines = relationship("EstimationLine", back_populates="estimation", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

class EstimationLine(Base):
    __tablename__ = "estimation_lines"
    line_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    estimation_id: Mapped[int] = mapped_column(ForeignKey("estimations.estimation_id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.item_id"), nullable=False)

    sub_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    no_of_units: Mapped[int] = mapped_column(Integer, default=1)
    length: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    width: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    thickness: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    length_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thickness_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    calculated_qty: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15,2), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(15,2), nullable=True)
    # Optional attachment for Special Item lines
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_base64: Mapped[str | None] = mapped_column(Text, nullable=True)

    estimation = relationship("Estimation", back_populates="lines")
    item = relationship("Item", back_populates="estimation_lines")

class SpecialItemRequest(Base):
    __tablename__ = "special_item_requests"
    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    estimation_id: Mapped[int] = mapped_column(ForeignKey("estimations.estimation_id"), nullable=False)
    division_id: Mapped[int] = mapped_column(ForeignKey("divisions.division_id"), nullable=False)
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    organization: Mapped[str] = mapped_column(String(50), nullable=False, server_default="RHD")
    item_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    sub_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    no_of_units: Mapped[int] = mapped_column(Integer, default=1)
    length: Mapped[float | None] = mapped_column(Numeric(15, 3), nullable=True)
    width: Mapped[float | None] = mapped_column(Numeric(15, 3), nullable=True)
    thickness: Mapped[float | None] = mapped_column(Numeric(15, 3), nullable=True)
    length_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    width_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thickness_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(15, 3), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.item_id"), nullable=True)
    special_item_id: Mapped[int | None] = mapped_column(ForeignKey("special_items.special_item_id"), nullable=True)
    line_id: Mapped[int | None] = mapped_column(ForeignKey("estimation_lines.line_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    estimation = relationship("Estimation")
    division = relationship("Division")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    item = relationship("Item")
    special_item = relationship("SpecialItem")
    line = relationship("EstimationLine")
