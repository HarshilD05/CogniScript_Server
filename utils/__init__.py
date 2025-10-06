"""
Utils package for LawLibra RAG Server
Provides centralized access to all utility classes
"""

# Import all utility classes to make them accessible at package level
from .user_utils import UserUtils
from .chat_utils import ChatUtils
from .chroma_utils import ChromaUtils

# Import other existing utilities
try:
    from .doc_utils import *
except ImportError:
    pass

try:
    from .doc_workflow import *
except ImportError:
    pass

try:
    from .rag_utils import *
except ImportError:
    pass

# Make utility classes available when importing from utils package
__all__ = [
    # User utilities
    'UserUtils',
    
    # Chat utilities
    'ChatUtils',
    
    # ChromaDB utilities
    'ChromaUtils',
    
    # Note: Other utilities (doc_utils, doc_workflow, rag_utils) 
    # will be available if they exist in the utils directory
]