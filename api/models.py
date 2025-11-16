from pydantic import BaseModel
from datetime import datetime

class News(BaseModel):
    id: str
    category: str
    subcategory: str
    title:str
    abstract:str
    inserted_at:datetime
