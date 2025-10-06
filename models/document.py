"""
Document-related models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId


class UploadModel(BaseModel):
    """Model for uploaded documents in conversation"""
    docId: str  # Mongo ObjectId as string
    filename: str
    fileType: str
    fileSize: int
    uploadDate: datetime
    pageCount: Optional[int] = None
    previewText: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = "user upload"
    metadata: Optional[dict] = None
    status: str = "pending"
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


class DocumentModel(BaseModel):
    """Document model for file metadata"""
    docId: str  # Mongo ObjectId as string
    chat_id: str  # Reference to Chat _id
    filename: str
    fileType: str
    fileSize: int
    uploadDate: datetime
    pageCount: Optional[int] = None
    previewText: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = "user upload"
    metadata: Optional[dict] = None
    status: str = "pending"
    chroma_collection: str  # Name of ChromaDB collection for this chat
    chunk_ids: List[str] = Field(default_factory=list)  # ChromaDB chunk IDs
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }