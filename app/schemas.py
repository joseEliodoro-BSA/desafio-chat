from pydantic import BaseModel, BeforeValidator, Field
from typing import Annotated, List, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserSchema(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id") # None = None
    username: str
    online: bool = False
    in_chat: bool = False

class Message(BaseModel):
    msg: str
    username: str
    _id: str | None = None
    date: float | None = None
    chat: str | None = None
    username_receive: str | None = None
    
    # @field_validator("date", mode="before")
    # def convert_str_to_datetime(cls, value):
    #     if isinstance(value, str):
    #         return datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
    #     return value
