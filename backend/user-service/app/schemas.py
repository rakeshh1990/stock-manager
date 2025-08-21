from pydantic import BaseModel
from typing import List

class PortfolioIn(BaseModel):
    user_id: int
    symbols: List[str]

class PortfolioOut(BaseModel):
    id: int
    user_id: int
    symbols: List[str]
