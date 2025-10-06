"""
Models package for LawLibra RAG Server
Provides centralized access to all Pydantic models
"""

# Import all models to make them accessible at package level
from .user import UserModel, UserType
from .chat import ChatModel, ConversationEntry
from .document import DocumentModel, UploadModel
from .citation import CitationModel

# Make models available when importing from models package
__all__ = [
    # User models
    'UserModel',
    'UserType',
    
    # Chat models
    'ChatModel',
    'ConversationEntry',
    
    # Document models
    'DocumentModel',
    'UploadModel',
    
    # Citation models
    'CitationModel',
]