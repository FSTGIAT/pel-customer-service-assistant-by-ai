from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
import json
from typing import Dict, Any



class ChatMessage(BaseModel):
    id: Optional[UUID] = None
    session_id: UUID
    message_type: str = Field(..., pattern='^(user|bot|system)$')
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pdf_context: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('message_type')
    def validate_message_type(cls, v):
        if v not in ('user', 'bot', 'system'):
            raise ValueError('message_type must be user, bot, or system')
        return v

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
    total_count: int
    has_more: bool