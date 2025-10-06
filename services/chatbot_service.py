"""
Chatbot service for orchestrating RAG workflow
Coordinates ChromaDB retrieval, context formatting, LLM calls, and response storage
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.chroma_utils import ChromaUtils
from utils.chat_utils import ChatUtils
from utils.user_utils import UserUtils
from utils.llm_context_utils import LLMContextFormatter
from llm.perplexity_llm import PerplexityLLM

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service class for handling complete chatbot workflow with RAG"""
    
    def __init__(self):
        """Initialize the chatbot service with required components"""
        try:
            # Initialize ChromaDB connection
            self.chroma_utils = ChromaUtils()
            
            # Initialize utility classes
            self.chat_utils = ChatUtils()
            self.user_utils = UserUtils()
            self.context_formatter = LLMContextFormatter()
            
            # Initialize Perplexity LLM
            self.llm = PerplexityLLM()
            
            # Configuration
            self.max_rag_results = 5
            self.max_chat_history = 10
            self.max_tokens = 8000
            
            logger.info("[ChatbotService] Initialized successfully")
            
        except Exception as e:
            logger.error(f"[ChatbotService] Failed to initialize: {e}")
            raise
    
    async def process_chat_prompt(self, chat_id: str, user_prompt: str, user_id: str = None) -> Dict[str, Any]:
        """
        Process a chat prompt with full RAG workflow
        
        Args:
            chat_id: Chat session ID
            user_prompt: User's input prompt
            user_id: Optional user ID for validation
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            logger.info(f"[ChatbotService] Processing prompt for chat_id: {chat_id}")
            
            # Step 1: Validate chat and user
            chat = self.chat_utils.get_chat(chat_id)
            if not chat:
                raise ValueError(f"Chat not found: {chat_id}")
            
            # If user_id provided, validate it matches the chat
            if user_id and chat.get('userId') != user_id:
                raise ValueError("User ID does not match chat owner")
            
            # Step 2: Add user prompt to chat
            self.chat_utils.add_prompt_to_chat(chat_id, user_prompt)
            
            # Step 3: Perform RAG retrieval
            rag_results = await self._retrieve_relevant_context(chat_id, user_prompt)
            formatted_rag_context = self.context_formatter.format_rag_context(rag_results)
            
            # Step 4: Get chat history
            chat_with_history = self.chat_utils.get_chat(chat_id)  # Refresh to get updated history
            conversation_history = chat_with_history.get('conversation_history', [])
            formatted_chat_history = self.context_formatter.format_chat_history(
                conversation_history, 
                self.max_chat_history
            )
            
            # Step 5: Optimize context for token limits
            optimized_context, optimized_history = self.context_formatter.truncate_context_if_needed(
                formatted_rag_context,
                formatted_chat_history,
                self.max_tokens
            )
            
            # Step 6: Generate LLM response
            llm_payload = self.context_formatter.prepare_llm_payload(
                optimized_context,
                optimized_history,
                user_prompt
            )
            
            assistant_response = await self._generate_llm_response(llm_payload)
            
            # Step 7: Extract citations
            citations = self.context_formatter.extract_citations_from_context(
                optimized_context,
                assistant_response
            )
            
            # Step 8: Store assistant response
            self.chat_utils.add_assistant_response_to_chat(
                chat_id,
                assistant_response,
                citations
            )
            
            # Step 9: Prepare response
            response_data = {
                "chatId": chat_id,
                "response": assistant_response,
                "citations": citations,
                "contextUsed": len(optimized_context),
                "historyUsed": len(optimized_history),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"[ChatbotService] Successfully processed prompt for chat_id: {chat_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"[ChatbotService] Error processing prompt: {e}")
            
            # Try to add error response to chat
            try:
                error_response = "I apologize, but I encountered an error while processing your request. Please try again."
                self.chat_utils.add_assistant_response_to_chat(chat_id, error_response, [])
            except:
                pass  # Don't fail if we can't add error response
            
            raise
    
    async def _retrieve_relevant_context(self, chat_id:str, query: str) -> Dict[str, Any]:
        """
        Retrieve relevant context from ChromaDB
        
        Args:
            query: Search query
            
        Returns:
            ChromaDB query results
        """
        try:
            logger.info(f"[ChatbotService] Retrieving context for query: {query[:100]}...")
            
            results = self.chroma_utils.query_chat_docs(chat_id, query)
            
            logger.info(f"[ChatbotService] Retrieved {len(results.get('documents', [[]])[0])} context items")
            return results
            
        except Exception as e:
            logger.error(f"[ChatbotService] Error retrieving context: {e}")
            return {}
    
    async def _generate_llm_response(self, payload: Dict[str, Any]) -> str:
        """
        Generate response from Perplexity LLM using official SDK
        
        Args:
            payload: Formatted payload with context, history, and prompt
            
        Returns:
            Generated response text
        """
        try:
            logger.info("[ChatbotService] Generating LLM response")
            
            # Use context-aware generation if context available
            if payload.get('context') or payload.get('history'):
                # Use synchronous method - the SDK handles the API calls
                response = self.llm.generate_with_context(
                    prompt=payload['prompt'],
                    context=payload.get('context', []),
                    history=payload.get('history', [])
                )
            else:
                # Fallback to basic generation
                response = self.llm.generate(payload['prompt'])
            
            logger.info("[ChatbotService] Successfully generated LLM response")
            return response
            
        except Exception as e:
            logger.error(f"[ChatbotService] Error generating LLM response: {e}")
            # Return a fallback response
            return "I apologize, but I'm having trouble accessing my language model right now. Please try again later."
    
    def get_chat_summary(self, chat_id: str) -> Dict[str, Any]:
        """
        Get a summary of the chat session
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            Chat summary with statistics
        """
        try:
            chat = self.chat_utils.get_chat(chat_id)
            if not chat:
                return {}
            
            conversation_history = chat.get('conversationHistory', [])
            
            return {
                "chatId": chat_id,
                "userId": chat.get('userId'),
                "title": chat.get('title', 'Untitled Chat'),
                "messageCount": len(conversation_history),
                "createdAt": chat.get('createdAt'),
                "updatedAt": chat.get('updatedAt'),
                "lastMessage": conversation_history[-1] if conversation_history else None
            }
            
        except Exception as e:
            logger.error(f"[ChatbotService] Error getting chat summary: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all service components
        
        Returns:
            Health status of each component
        """
        health = {
            "chatbot_service": True,
            "chroma_db": False,
            "mongodb": False,
            "perplexity_llm": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Check ChromaDB
            collection = self.chroma_utils.get_collection()
            health["chroma_db"] = collection is not None
        except:
            pass
        
        try:
            # Check MongoDB (try to get a collection)
            test_chat = self.chat_utils.get_chat("health_check_test")
            health["mongodb"] = True  # If no exception, MongoDB is accessible
        except:
            pass
        
        try:
            # Check Perplexity API (this would require actual API call)
            health["perplexity_llm"] = self.llm is not None
        except:
            pass
        
        return health


# Service instance (singleton pattern)
_chatbot_service_instance = None

def get_chatbot_service() -> ChatbotService:
    """Get singleton instance of ChatbotService"""
    global _chatbot_service_instance
    if _chatbot_service_instance is None:
        _chatbot_service_instance = ChatbotService()
    return _chatbot_service_instance


# Default export
__all__ = ['ChatbotService', 'get_chatbot_service']