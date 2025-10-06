"""
Citation-related models
"""

from pydantic import BaseModel
from typing import Optional
from bson import ObjectId


class CitationModel(BaseModel):
    """Model for citations in conversation"""
    citationId: str  # Mongo ObjectId as string
    source: str
    text: str
    page: Optional[int] = None
    link: Optional[str] = None
    
    class Config:
        json_encoders = {
            ObjectId: str
        }