"""
User utility functions for user management operations
"""

from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from models import UserModel
from config.mongodb import get_mongodb_collection
import logging

logger = logging.getLogger(__name__)


class UserUtils:
    """Utility class for user operations"""
    
    @staticmethod
    def create_user(email: str, user_type: str) -> Optional[str]:
        """
        Create a new user
        
        Args:
            email: User email address
            user_type: User type (ADMIN, LAWYER, USER)
            
        Returns:
            User ID as string if successful, None if failed
        """
        try:
            # Create user model
            user = UserModel(
                email=email,
                user_type=user_type,
                chats=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Insert into MongoDB
            users_collection = get_mongodb_collection('users')
            result = users_collection.insert_one(user.dict())
            
            if result.inserted_id:
                user_id = str(result.inserted_id)
                logger.info(f"[UserUtils] Created new user {user_id}")
                return user_id
            else:
                logger.error(f"[UserUtils] Failed to insert user into database")
                return None
                
        except Exception as e:
            logger.error(f"[UserUtils] Error creating user: {e}")
            return None
    
    @staticmethod
    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ObjectId as string
            
        Returns:
            User document or None
        """
        try:
            users_collection = get_mongodb_collection('users')
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            
            if user:
                # Convert ObjectId to string for JSON serialization
                user['_id'] = str(user['_id'])
                return user
            return None
            
        except Exception as e:
            logger.error(f"[UserUtils] Error getting user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: User email address
            
        Returns:
            User document or None
        """
        try:
            users_collection = get_mongodb_collection('users')
            user = users_collection.find_one({"email": email})
            
            if user:
                # Convert ObjectId to string for JSON serialization
                user['_id'] = str(user['_id'])
                return user
            return None
            
        except Exception as e:
            logger.error(f"[UserUtils] Error getting user by email: {e}")
            return None
    
    @staticmethod
    def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update user information
        
        Args:
            user_id: User ObjectId as string
            update_data: Dictionary of fields to update
            
        Returns:
            True if successful, False if failed
        """
        try:
            users_collection = get_mongodb_collection('users')
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            result = users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"[UserUtils] Updated user {user_id}")
                return True
            else:
                logger.warning(f"[UserUtils] No user found with ID {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"[UserUtils] Error updating user: {e}")
            return False
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """
        Delete a user
        
        Args:
            user_id: User ObjectId as string
            
        Returns:
            True if successful, False if failed
        """
        try:
            users_collection = get_mongodb_collection('users')
            result = users_collection.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count > 0:
                logger.info(f"[UserUtils] Deleted user {user_id}")
                return True
            else:
                logger.warning(f"[UserUtils] No user found with ID {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"[UserUtils] Error deleting user: {e}")
            return False


# Default export
__all__ = ['UserUtils']