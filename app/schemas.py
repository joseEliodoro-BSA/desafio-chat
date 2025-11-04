from pydantic import BaseModel
from typing import List
from datetime import datetime

class UserSchema(BaseModel):
    id: str | None = None
    username: str

class MessageGlobal(BaseModel):
    id: str | None = None
    date: datetime | None = None
    username: str
    msg: str


class MessageCollection(BaseModel):
    messages: List[MessageGlobal]