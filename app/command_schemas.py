from pydantic import BaseModel, Field
from typing import Optional

class Command(BaseModel):
    command: str


class CommandSendMessage(Command):
    msg: str

class CommandSendPrivateMessage(CommandSendMessage):
    receiver: str

class CommandConnectRoom(Command):
    room: str
    password: Optional[str] = Field(default=None)

class CommandCreateRoom(CommandConnectRoom):
    limit: Optional[int] = Field(default=3)
