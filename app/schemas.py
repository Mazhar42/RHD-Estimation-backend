from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Division Schemas
class DivisionBase(BaseModel):
    name: str

class DivisionCreate(DivisionBase):
    pass

class Division(DivisionBase):
    division_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Item Schemas
class ItemBase(BaseModel):
    item_code: str
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str

class ItemCreate(ItemBase):
    division_id: int

class ItemUpdate(BaseModel):
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: Optional[str] = None
    division_id: Optional[int] = None

class ItemParsed(BaseModel):
    division: str
    item_code: str
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = None
    region: str

class Item(ItemBase):
    item_id: int
    division_id: int
    division: Division

    model_config = ConfigDict(from_attributes=True)

# Project Schemas
class ProjectBase(BaseModel):
    project_name: str
    client_name: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    project_id: int
    
    model_config = ConfigDict(from_attributes=True)

# Estimation Schemas
class EstimationLineBase(BaseModel):
    item_id: int
    sub_description: Optional[str] = None
    no_of_units: int = 1
    length: Optional[float] = None
    width: Optional[float] = None
    thickness: Optional[float] = None
    quantity: Optional[float] = None

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

    model_config = ConfigDict(from_attributes=True)

class EstimationLineDelete(BaseModel):
    line_ids: List[int]