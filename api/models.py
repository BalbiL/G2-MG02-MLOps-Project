from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional,List
from uuid import UUID

# -----------------------------
# This file contains the pydantic models to formalize data in the api transactions
# -----------------------------
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

class Interaction(BaseModel):
    user_id: UUID
    news_id: str
    event_type: str
    event_time: Optional[datetime] = None

class InviteRequest(BaseModel):
    email: EmailStr