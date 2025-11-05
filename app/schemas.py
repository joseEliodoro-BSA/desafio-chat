from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime

class UserSchema(BaseModel):
    _id: str | None = None
    username: str

class MessageGlobal(BaseModel):
    msg: str
    username: str
    _id: str | None = None
    date: datetime | None = None
    chat: str | None = None
    username_receive: str | None = None
    
    @field_validator("date", mode="before")
    def convert_str_to_datetime(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
        return value

class UserCollection(BaseModel):
    messages: List[UserSchema]
    
class MessageCollection(BaseModel):
    messages: List[MessageGlobal]