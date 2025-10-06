"""
User-related models and enums
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId


class UserType(str, Enum):
    """User type enumeration"""
    ADMIN = "ADMIN"
    LAWYER = "LAWYER"
    USER = "USER"


class UserModel(BaseModel):
    """User model with email, user type, and associated chats"""
    email: EmailStr
    user_type: UserType
    chats: List[str] = Field(default_factory=list)  # List of Chat ObjectIds as strings
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            ObjectId: str
        }