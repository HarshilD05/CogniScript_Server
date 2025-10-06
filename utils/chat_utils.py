"""
Chat utility functions for chat management operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from models import ChatModel, ConversationEntry, CitationModel
from config.mongodb import get_mongodb_collection
import logging

logger = logging.getLogger(__name__)


class ChatUtils:
    """Utility class for chat operations"""
    
    @staticmethod
    def create_chat(user_id: str, title: Optional[str] = None) -> Optional[str]:
        """
        Create a new chat for a user
        
        Args:
            user_id: User ObjectId as string
            title: Optional chat title
            
        Returns:
            Chat ID as string if successful, None if failed
        """
        try:
            # Create chat model (MongoDB will auto-generate _id)
            chat = ChatModel(
                userId=user_id,
                title=title or "New Chat",
                conversation_history=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status="active"
            )
            
            # Insert into MongoDB
            chats_collection = get_mongodb_collection('chats')
            result = chats_collection.insert_one(chat.dict())
            
            if result.inserted_id:
                # Use the inserted_id as the chat_id
                chat_id = str(result.inserted_id)
                
                # Update user's chat list
                users_collection = get_mongodb_collection('users')
                users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$push": {"chats": chat_id}, "$set": {"updated_at": datetime.utcnow()}}
                )
                
                logger.info(f"[ChatUtils] Created new chat {chat_id} for user {user_id}")
                return chat_id
            else:
                logger.error(f"[ChatUtils] Failed to insert chat into database")
                return None
                
        except Exception as e:
            logger.error(f"[ChatUtils] Error creating chat: {e}")
            return None
    
    @staticmethod
    def add_prompt_to_chat(chat_id: str, user_prompt: str) -> bool:
        """
        Add a user prompt to chat conversation history
        
        Args:
            chat_id: Chat ObjectId as string
            user_prompt: User's message text
            
        Returns:
            True if successful, False if failed
        """
        try:
            # Create conversation entry with user prompt only
            conversation_entry = ConversationEntry(
                timestamp=datetime.utcnow(),
                user=user_prompt,
                assistant="",  # Empty initially
                uploads=[],
                citations=[]
            )
            
            # Update chat in MongoDB
            chats_collection = get_mongodb_collection('chats')
            result = chats_collection.update_one(
                {"_id": ObjectId(chat_id)},
                {
                    "$push": {"conversation_history": conversation_entry.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"[ChatUtils] Added prompt to chat {chat_id}")
                return True
            else:
                logger.warning(f"[ChatUtils] No chat found with ID {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"[ChatUtils] Error adding prompt to chat: {e}")
            return False
    
    @staticmethod
    def add_assistant_response_to_chat(chat_id: str, response: str, citations: List[Dict[str, Any]] = None) -> bool:
        """
        Add assistant response to the latest conversation entry in chat
        
        Args:
            chat_id: Chat ObjectId as string
            response: Assistant's response text
            citations: List of citations as dictionaries
            
        Returns:
            True if successful, False if failed
        """
        try:
            # Process citations
            citation_models = []
            if citations:
                for citation in citations:
                    citation_model = CitationModel(
                        citationId=str(ObjectId()),
                        source=citation.get('source', ''),
                        text=citation.get('text', ''),
                        page=citation.get('page'),
                        link=citation.get('link')
                    )
                    citation_models.append(citation_model.dict())
            
            # Update the latest conversation entry in the chat
            chats_collection = get_mongodb_collection('chats')
            
            # First, get the chat to find the last conversation entry
            chat_doc = chats_collection.find_one({"_id": ObjectId(chat_id)})
            if not chat_doc or not chat_doc.get('conversation_history'):
                logger.error(f"[ChatUtils] No conversation history found for chat {chat_id}")
                return False
            
            # Update only the last conversation entry
            last_index = len(chat_doc['conversation_history']) - 1
            result = chats_collection.update_one(
                {"_id": ObjectId(chat_id)},
                {
                    "$set": {
                        f"conversation_history.{last_index}.assistant": response,
                        f"conversation_history.{last_index}.citations": citation_models,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"[ChatUtils] Added assistant response to chat {chat_id}")
                return True
            else:
                logger.warning(f"[ChatUtils] Failed to update assistant response for chat {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"[ChatUtils] Error adding assistant response to chat: {e}")
            return False
    
    @staticmethod
    def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chat by ID
        
        Args:
            chat_id: Chat ObjectId as string
            
        Returns:
            Chat document or None
        """
        try:
            chats_collection = get_mongodb_collection('chats')
            chat = chats_collection.find_one({"_id": ObjectId(chat_id)})
            
            if chat:
                # Convert ObjectId to string for JSON serialization
                chat['_id'] = str(chat['_id'])
                return chat
            return None
            
        except Exception as e:
            logger.error(f"[ChatUtils] Error getting chat: {e}")
            return None
    
    @staticmethod
    def get_user_chats(user_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all chats for a user
        
        Args:
            user_id: User ObjectId as string
            limit: Maximum number of chats to return
            skip: Number of chats to skip
            
        Returns:
            List of chat documents
        """
        try:
            chats_collection = get_mongodb_collection('chats')
            chats = list(chats_collection.find(
                {"userId": user_id}
            ).sort("updated_at", -1).skip(skip).limit(limit))
            
            # Convert ObjectIds to strings
            for chat in chats:
                chat['_id'] = str(chat['_id'])
                
            return chats
            
        except Exception as e:
            logger.error(f"[ChatUtils] Error getting user chats: {e}")
            return []
    
    @staticmethod
    def delete_chat(chat_id: str) -> bool:
        """
        Delete a chat
        
        Args:
            chat_id: Chat ObjectId as string
            
        Returns:
            True if successful, False if failed
        """
        try:
            chats_collection = get_mongodb_collection('chats')
            result = chats_collection.delete_one({"_id": ObjectId(chat_id)})
            
            if result.deleted_count > 0:
                logger.info(f"[ChatUtils] Deleted chat {chat_id}")
                return True
            else:
                logger.warning(f"[ChatUtils] No chat found with ID {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"[ChatUtils] Error deleting chat: {e}")
            return False


# Default export
__all__ = ['ChatUtils']