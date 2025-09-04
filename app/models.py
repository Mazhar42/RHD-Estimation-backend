from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class ItemCategory(Base):
    __tablename__ = "item_categories"
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    items = relationship("Item", back_populates="category", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("item_categories.category_id"), nullable=False)
    item_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    category = relationship("ItemCategory", back_populates="items")
    # historical relationships from earlier design not strictly required
    estimation_lines = relationship("EstimationLine", back_populates="item")

class Project(Base):
    __tablename__ = "projects"
    project_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    estimations = relationship("Estimation", back_populates="project", cascade="all, delete-orphan")

class Estimation(Base):
    __tablename__ = "estimations"
    estimation_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    estimation_name: Mapped[str] = mapped_column(String(255), nullable=False)

    project = relationship("Project", back_populates="estimations")
    lines = relationship("EstimationLine", back_populates="estimation", cascade="all, delete-orphan")

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
    quantity: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    calculated_qty: Mapped[float | None] = mapped_column(Numeric(15,3), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15,2), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(15,2), nullable=True)

    estimation = relationship("Estimation", back_populates="lines")
    item = relationship("Item", back_populates="estimation_lines")
