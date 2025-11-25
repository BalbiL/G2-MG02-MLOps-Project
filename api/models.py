from pydantic import BaseModel
from datetime import datetime
from typing import Optional,List
from uuid import UUID

class News(BaseModel):
    id: str
    category: str
    subcategory: str
    title:str
    abstract:str
    inserted_at:datetime


class Recommendation(BaseModel):
    news_ids: List[str]
    score: float
    generation_time: Optional[datetime] = None



class UserTopics(BaseModel):
    user_id:UUID
    topics:Optional[List[str]]=[]