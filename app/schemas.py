from pydantic import BaseModel, Field
from typing import Optional, List

# ----- Item Category -----
class ItemCategoryBase(BaseModel):
    name: str

class ItemCategoryCreate(ItemCategoryBase):
    pass

class ItemCategory(ItemCategoryBase):
    category_id: int
    class Config:
        from_attributes = True

# ----- Items (Product Master) -----
class ItemBase(BaseModel):
    item_code: str
    item_description: str
    unit: Optional[str] = None
    rate: Optional[float] = Field(default=None, description="Default rate per unit")
    category_id: int

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    item_id: int
    category: Optional[ItemCategory] = None
    class Config:
        from_attributes = True

# ----- Projects -----
class ProjectBase(BaseModel):
    project_name: str
    client_name: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    project_id: int
    class Config:
        from_attributes = True

# ----- Estimations -----
class EstimationBase(BaseModel):
    estimation_name: str

class EstimationCreate(EstimationBase):
    pass

class Estimation(EstimationBase):
    estimation_id: int
    project_id: int
    class Config:
        from_attributes = True

# ----- Estimation Lines -----
class EstimationLineBase(BaseModel):
    item_id: int
    sub_description: Optional[str] = None
    no_of_units: Optional[int] = 1
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
    amount: Optional[float] = None
    item: Optional[Item] = None
    rate: Optional[float] = None
    class Config:
        from_attributes = True

class EstimationWithLines(Estimation):
    lines: List[EstimationLine] = []

class EstimationLineDelete(BaseModel):
    line_ids: List[int]
