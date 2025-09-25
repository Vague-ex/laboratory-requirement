from pydantic import BaseModel

class Item(BaseModel):
    name: str
    quantity: int
    unit_cost: float
    last_sale_date: str  # ISO date string
