"""
LLM context formatting utilities
Functions to prepare data for LLM consumption by removing unnecessary metadata
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LLMContextFormatter:
    """Utility class for formatting data for LLM context"""
    
    @staticmethod
    def format_rag_context(chroma_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Format ChromaDB query results for LLM context
        
        Args:
            chroma_results: Raw results from ChromaDB query (from query_chat_docs)
            
        Returns:
            List of context items with document and text only
        """
        try:
            context = []
            
            if not chroma_results or not chroma_results.get('success'):
                return context
            
            # Handle the new format from query_chat_docs
            relevant_chunks = chroma_results.get('relevant_chunks', [])
            
            for chunk in relevant_chunks:
                text = chunk.get('text', '').strip()
                if text:
                    # Extract document name from metadata
                    metadata = chunk.get('metadata', {})
                    document_name = (
                        metadata.get('document_name') or 
                        metadata.get('filename') or 
                        metadata.get('source') or 
                        metadata.get('document') or 
                        f"Document_Chunk_{chunk.get('chunk_id', 'unknown')}"
                    )
                    
                    context.append({
                        "document": document_name,
                        "text": text
                    })
            
            logger.info(f"[LLMContextFormatter] Formatted {len(context)} context items")
            return context
            
        except Exception as e:
            logger.error(f"[LLMContextFormatter] Error formatting RAG context: {e}")
            return []
    
    @staticmethod
    def format_chat_history(conversation_history: List[Dict[str, Any]], max_entries: int = 10) -> List[Dict[str, str]]:
        """
        Format chat conversation history for LLM context
        Removes timestamps, IDs, and other metadata
        Ensures proper user/assistant alternation for Perplexity API
        
        Args:
            conversation_history: Raw conversation history from MongoDB
            max_entries: Maximum number of entries to include
            
        Returns:
            List of messages in format [{"role": "user/assistant", "content": "..."}]
        """
        try:
            formatted_history = []
            
            if not conversation_history:
                return formatted_history
            
            # Take the most recent entries
            recent_history = conversation_history[-max_entries:] if len(conversation_history) > max_entries else conversation_history
            
            for entry in recent_history:
                # Each entry should have both user and assistant messages
                user_content = entry.get('user', '').strip()
                assistant_content = entry.get('assistant', '').strip()
                
                # Only add complete conversation pairs (user + assistant)
                # This ensures proper alternation
                if user_content and assistant_content:
                    formatted_history.append({
                        "role": "user",
                        "content": user_content
                    })
                    formatted_history.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
            
            logger.info(f"[LLMContextFormatter] Formatted {len(formatted_history)} history messages (alternating pairs)")
            return formatted_history
            
        except Exception as e:
            logger.error(f"[LLMContextFormatter] Error formatting chat history: {e}")
            return []
    
    @staticmethod
    def extract_citations_from_context(rag_context: List[Dict[str, str]], 
                                     assistant_response: str) -> List[Dict[str, Any]]:
        """
        Extract citations from RAG context based on assistant response
        
        Args:
            rag_context: Formatted RAG context
            assistant_response: Assistant's response text
            
        Returns:
            List of citation objects
        """
        try:
            citations = []
            
            for i, context_item in enumerate(rag_context):
                document = context_item.get("document", "")
                text = context_item.get("text", "")
                
                # Simple check if the context might be referenced in the response
                # This is a basic implementation - could be improved with more sophisticated matching
                if document and text and (
                    document.lower() in assistant_response.lower() or 
                    any(word in assistant_response.lower() for word in text.lower().split()[:10])
                ):
                    citations.append({
                        "citationId": f"auto_citation_{i}",
                        "source": document,
                        "text": text[:200] + "..." if len(text) > 200 else text,  # Truncate long text
                        "page": None,  # Could extract from metadata if available
                        "link": None   # Could be added if document links are available
                    })
            
            logger.info(f"[LLMContextFormatter] Extracted {len(citations)} citations")
            return citations
            
        except Exception as e:
            logger.error(f"[LLMContextFormatter] Error extracting citations: {e}")
            return []
    
    @staticmethod
    def prepare_llm_payload(rag_context: List[Dict[str, str]], 
                          chat_history: List[Dict[str, str]], 
                          user_prompt: str) -> Dict[str, Any]:
        """
        Prepare complete payload for LLM with optimized token usage
        
        Args:
            rag_context: Formatted RAG context
            chat_history: Formatted chat history
            user_prompt: Current user prompt
            
        Returns:
            Dictionary with context, history, and prompt
        """
        return {
            "context": rag_context,
            "history": chat_history,
            "prompt": user_prompt
        }
    
    @staticmethod
    def estimate_token_count(text: str) -> int:
        """
        Rough estimation of token count (approximately 4 characters per token)
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    @staticmethod
    def truncate_context_if_needed(rag_context: List[Dict[str, str]], 
                                 chat_history: List[Dict[str, str]],
                                 max_tokens: int = 8000) -> tuple:
        """
        Truncate context and history if they exceed token limits
        
        Args:
            rag_context: RAG context items
            chat_history: Chat history messages
            max_tokens: Maximum tokens allowed
            
        Returns:
            Tuple of (truncated_rag_context, truncated_chat_history)
        """
        try:
            # Estimate current token usage
            context_text = " ".join([item.get("text", "") for item in rag_context])
            history_text = " ".join([msg.get("content", "") for msg in chat_history])
            
            context_tokens = LLMContextFormatter.estimate_token_count(context_text)
            history_tokens = LLMContextFormatter.estimate_token_count(history_text)
            total_tokens = context_tokens + history_tokens
            
            if total_tokens <= max_tokens:
                return rag_context, chat_history
            
            # If exceeding limits, prioritize recent history and most relevant context
            # Keep at least 50% for context, 50% for history
            max_context_tokens = max_tokens // 2
            max_history_tokens = max_tokens // 2
            
            # Truncate context if needed
            truncated_context = []
            current_context_tokens = 0
            for item in rag_context:
                item_tokens = LLMContextFormatter.estimate_token_count(item.get("text", ""))
                if current_context_tokens + item_tokens <= max_context_tokens:
                    truncated_context.append(item)
                    current_context_tokens += item_tokens
                else:
                    break
            
            # Truncate history if needed (keep most recent)
            truncated_history = []
            current_history_tokens = 0
            for msg in reversed(chat_history):
                msg_tokens = LLMContextFormatter.estimate_token_count(msg.get("content", ""))
                if current_history_tokens + msg_tokens <= max_history_tokens:
                    truncated_history.insert(0, msg)
                    current_history_tokens += msg_tokens
                else:
                    break
            
            logger.info(f"[LLMContextFormatter] Truncated context from {len(rag_context)} to {len(truncated_context)} items")
            logger.info(f"[LLMContextFormatter] Truncated history from {len(chat_history)} to {len(truncated_history)} messages")
            
            return truncated_context, truncated_history
            
        except Exception as e:
            logger.error(f"[LLMContextFormatter] Error truncating context: {e}")
            return rag_context[:5], chat_history[-5:]  # Fallback to simple truncation


# Default export
__all__ = ['LLMContextFormatter']