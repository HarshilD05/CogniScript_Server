"""
Chat-related models
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .citation import CitationModel
from .document import UploadModel


class ConversationEntry(BaseModel):
    """Individual conversation entry in chat history"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: str = ""  # User message text
    assistant: str = ""  # Assistant response text
    uploads: List[UploadModel] = Field(default_factory=list)
    citations: List[CitationModel] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


class ChatModel(BaseModel):
    """Chat model containing conversation history"""
    userId: str  # Reference to User ObjectId
    title: Optional[str] = "New Chat"
    conversation_history: List[ConversationEntry] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "active"
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }