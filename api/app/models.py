from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Any

Role = Literal["system","user","assistant","tool"]

class Message(BaseModel):
    role: Role
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)

class ChatChunk(BaseModel):
    delta: str | None = None
    done: bool | None = None
    error: str | None = None

