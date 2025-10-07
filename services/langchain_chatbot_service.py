"""
Enhanced Chatbot service using modern LangChain architecture
Integrates RAG with message history management and multiple LLM provider support
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# LangChain imports - modern architecture with conditional imports
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

try:
    from langchain_perplexity import ChatPerplexity
except ImportError:
    ChatPerplexity = None
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.chroma_utils import ChromaUtils
from utils.chat_utils import ChatUtils
from utils.user_utils import UserUtils
from utils.llm_context_utils import LLMContextFormatter

load_dotenv()

logger = logging.getLogger(__name__)


class LangChainChatbotService:
    """Enhanced chatbot service using LangChain for conversation management"""
    
    # Supported providers and their corresponding classes
    PROVIDERS = {
        "OpenAI": ChatOpenAI,
        "Gemini": ChatGoogleGenerativeAI,
        "Groq": ChatGroq,
        "Anthropic": ChatAnthropic,
        "Perplexity": ChatPerplexity
    }
    
    # Default model configurations for each provider
    DEFAULT_MODELS = {
        "OpenAI": "gpt-3.5-turbo",
        "Gemini": "gemini-2.5-flash",
        "Groq": "mixtral-8x7b-32768",
        "Anthropic": "claude-3-sonnet-20240229",
        "Perplexity": "sonar"  # Updated to correct Perplexity model name
    }
    
    def __init__(self):
        """Initialize the chatbot service with modern LangChain components"""
        try:
            # Initialize ChromaDB and utility classes
            self.chroma_utils = ChromaUtils()
            self.chat_utils = ChatUtils()
            self.user_utils = UserUtils()
            self.context_formatter = LLMContextFormatter()
            
            # Configuration from environment
            self.max_rag_results = int(os.getenv("MAX_RAG_RESULTS", 5))
            self.max_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", 8000))
            
            # Store message histories per chat_id (modern approach)
            self._message_histories: Dict[str, BaseChatMessageHistory] = {}
            
            # Create prompt template for RAG conversations
            self._prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful AI assistant with access to relevant context. Use the provided context to answer questions accurately. If the context doesn't contain relevant information, say so clearly."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            
            logger.info("[LangChainChatbotService] Initialized successfully with modern LangChain architecture")
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Failed to initialize: {e}")
            raise
    
    def _create_llm(self, 
                   provider: Optional[str] = None,
                   model: Optional[str] = None,
                   temperature: float = 0.7,
                   max_tokens: int = 1000) -> BaseLanguageModel:
        """
        Create an LLM instance based on the specified or environment-configured provider
        """
        # Get provider from parameter or environment
        provider = provider or os.getenv("LLM_PROVIDER", "Perplexity")
        
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {list(self.PROVIDERS.keys())}")
        
        # Get API key for the provider
        api_key_var = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(api_key_var)
        
        if not api_key:
            raise ValueError(f"API key not found for {provider}. Please set {api_key_var} environment variable.")
        
        # Get model name
        model = model or self.DEFAULT_MODELS.get(provider)
        
        # Create LLM instance based on provider
        try:
            llm_class = self.PROVIDERS[provider]
            
            if provider == "OpenAI":
                llm = llm_class(
                    openai_api_key=api_key,
                    model_name=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == "Gemini":
                llm = llm_class(
                    google_api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            elif provider == "Groq":
                llm = llm_class(
                    groq_api_key=api_key,
                    model_name=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == "Anthropic":
                llm = llm_class(
                    anthropic_api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == "Perplexity":
                llm = llm_class(
                    pplx_api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            logger.info(f"[LangChainChatbotService] Created {provider} LLM with model: {model}")
            return llm
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Failed to create {provider} LLM: {e}")
            raise
    
    def _get_message_history(self, chat_id: str) -> BaseChatMessageHistory:
        """
        Get or create message history for a chat session
        """
        if chat_id not in self._message_histories:
            self._message_histories[chat_id] = InMemoryChatMessageHistory()
            logger.info(f"[LangChainChatbotService] Created new message history for chat_id: {chat_id}")
        
        return self._message_histories[chat_id]
    
    def _create_conversation_runnable(self, llm: Optional[BaseLanguageModel] = None):
        """
        Create a modern LangChain runnable with message history
        """
        try:
            # Create LLM if not provided
            if llm is None:
                llm = self._create_llm()
            
            # Create the chain: prompt + llm
            chain = self._prompt_template | llm
            
            # Wrap with message history for conversation management
            runnable_with_history = RunnableWithMessageHistory(
                chain,
                self._get_message_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            logger.info(f"[LangChainChatbotService] Created conversation runnable")
            return runnable_with_history
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Failed to create conversation runnable: {e}")
            raise
    
    def _get_or_create_conversation(self):
        """Get or create the conversation runnable (singleton pattern)"""
        if not hasattr(self, '_conversation_runnable'):
            try:
                self._conversation_runnable = self._create_conversation_runnable()
                logger.info(f"[LangChainChatbotService] Created conversation runnable")
            except Exception as e:
                logger.error(f"[LangChainChatbotService] Failed to create conversation runnable: {e}")
                raise
        
        return self._conversation_runnable
    
    async def process_chat_prompt(self, chat_id: str, user_prompt: str, user_id: str = None) -> Dict[str, Any]:
        """
        Process a chat prompt with RAG workflow and LangChain memory management
        
        Args:
            chat_id: Chat session ID
            user_prompt: User's input prompt
            user_id: Optional user ID for validation
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            logger.info(f"[LangChainChatbotService] Processing prompt for chat_id: {chat_id}")
            
            # Step 1: Validate chat and user
            chat = self.chat_utils.get_chat(chat_id)
            if not chat:
                raise ValueError(f"Chat not found: {chat_id}")
            
            if user_id and chat.get('userId') != user_id:
                raise ValueError("User ID does not match chat owner")
            
            # Step 2: Add user prompt to MongoDB chat history
            self.chat_utils.add_prompt_to_chat(chat_id, user_prompt)
            
            # Step 3: Perform RAG retrieval
            rag_results = await self._retrieve_relevant_context(chat_id, user_prompt)
            formatted_rag_context = self.context_formatter.format_rag_context(rag_results)
            
            # Step 4: Get conversation runnable
            conversation_runnable = self._get_or_create_conversation()
            
            # Step 5: Prepare prompt with RAG context
            final_prompt = self._prepare_final_prompt(user_prompt, formatted_rag_context)
            
            # Step 6: Generate response using modern LangChain runnable
            response_data = await self._generate_langchain_response(conversation_runnable, chat_id, final_prompt)
            
            # Step 7: Extract citations from RAG context
            citations = self.context_formatter.extract_citations_from_context(
                formatted_rag_context,
                response_data["response"]
            )
            
            # Step 8: Store assistant response in MongoDB
            self.chat_utils.add_assistant_response_to_chat(
                chat_id,
                response_data["response"],
                citations
            )
            
            # Step 9: Prepare final response
            final_response = {
                "chatId": chat_id,
                "response": response_data["response"],
                "citations": citations,
                "contextUsed": len(formatted_rag_context),
                "historyUsed": response_data.get("history_messages_count", 0),
                "memorySummaryUsed": response_data.get("has_summary", False),
                "llmProvider": os.getenv("LLM_PROVIDER", "Unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"[LangChainChatbotService] Successfully processed prompt for chat_id: {chat_id}")
            return final_response
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Error processing prompt: {e}")
            
            # Try to add error response to chat
            try:
                error_response = "I apologize, but I encountered an error while processing your request. Please try again."
                self.chat_utils.add_assistant_response_to_chat(chat_id, error_response, [])
            except:
                pass  # Don't fail if we can't add error response
            
            raise
    
    def _prepare_final_prompt(self, user_prompt: str, rag_context: List[Dict[str, str]]) -> str:
        """
        Prepare the final prompt that includes RAG context
        
        Args:
            user_prompt: Original user prompt
            rag_context: Retrieved context from ChromaDB
            
        Returns:
            Final prompt with context integrated
        """
        if not rag_context:
            return user_prompt
        
        # Format context for inclusion in prompt
        context_text = "\\n\\n".join([
            f"Document: {ctx.get('filename', 'Unknown')}\\n{ctx.get('text', '')}"
            for ctx in rag_context
        ])
        
        # Include context in the user message
        final_prompt = f"""Context from uploaded documents:
{context_text}

Question: {user_prompt}"""
        
        return final_prompt
    
    async def _generate_langchain_response(self, conversation_runnable, chat_id: str, user_input: str) -> Dict[str, Any]:
        """
        Generate response using modern LangChain runnable with message history
        
        Args:
            conversation_runnable: LangChain runnable with message history
            chat_id: Chat session ID for message history
            user_input: User input with RAG context
            
        Returns:
            Response data with metadata
        """
        try:
            logger.info("[LangChainChatbotService] Generating LangChain response")
            
            # Invoke the runnable with message history
            # The runnable automatically manages conversation history per chat_id
            result = conversation_runnable.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": chat_id}}
            )
            
            # Get message history for metadata
            message_history = self._get_message_history(chat_id)
            history_messages_count = len(message_history.messages)
            
            # Extract the actual response content
            response_content = result.content if hasattr(result, 'content') else str(result)
            
            response_data = {
                "response": response_content,
                "history_messages_count": history_messages_count,
                "has_summary": False  # Modern approach doesn't use summaries in the same way
            }
            
            logger.info("[LangChainChatbotService] Successfully generated LangChain response")
            return response_data
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Error generating LangChain response: {e}")
            # Return fallback response
            return {
                "response": "I apologize, but I'm having trouble accessing my language model right now. Please try again later.",
                "history_messages_count": 0,
                "has_summary": False
            }
    
    async def _retrieve_relevant_context(self, chat_id: str, query: str) -> Dict[str, Any]:
        """
        Retrieve relevant context from ChromaDB
        
        Args:
            chat_id: Chat session ID
            query: Search query
            
        Returns:
            ChromaDB query results
        """
        try:
            logger.info(f"[LangChainChatbotService] Retrieving context for query: {query[:100]}...")
            
            results = self.chroma_utils.query_chat_docs(chat_id, query, self.max_rag_results)
            
            if results.get('success'):
                context_count = len(results.get('relevant_chunks', []))
                logger.info(f"[LangChainChatbotService] Retrieved {context_count} context items")
            else:
                logger.warning(f"[LangChainChatbotService] No context retrieved: {results.get('error', 'Unknown error')}")
            
            return results
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Error retrieving context: {e}")
            return {"success": False, "relevant_chunks": []}
    
    def clear_conversation_memory(self, chat_id: str) -> bool:
        """
        Clear conversation memory for a specific chat
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            True if successful
        """
        try:
            if chat_id in self._message_histories:
                self._message_histories[chat_id].clear()
                logger.info(f"[LangChainChatbotService] Cleared memory for chat_id: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Error clearing memory: {e}")
            return False
    
    def remove_conversation(self, chat_id: str) -> bool:
        """
        Remove conversation message history entirely
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            True if successful
        """
        try:
            if chat_id in self._message_histories:
                del self._message_histories[chat_id]
                logger.info(f"[LangChainChatbotService] Removed conversation history for chat_id: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Error removing conversation: {e}")
            return False
    
    def get_conversation_info(self, chat_id: str) -> Dict[str, Any]:
        """
        Get information about a conversation's message history
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            Conversation memory information
        """
        try:
            if chat_id not in self._message_histories:
                return {"exists": False}
            
            message_history = self._message_histories[chat_id]
            
            return {
                "exists": True,
                "message_count": len(message_history.messages),
                "has_summary": False,  # Modern approach doesn't use automatic summarization
                "summary_preview": None
            }
            
        except Exception as e:
            logger.error(f"[LangChainChatbotService] Error getting conversation info: {e}")
            return {"exists": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all service components including LangChain
        
        Returns:
            Health status of each component
        """
        health = {
            "chatbot_service": True,
            "chroma_db": False,
            "mongodb": False,
            "langchain_llm": False,
            "llm_provider": os.getenv("LLM_PROVIDER", "Unknown"),
            "active_conversations": len(self._message_histories),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Check ChromaDB
            collection = self.chroma_utils.get_collection()
            health["chroma_db"] = collection is not None
        except:
            pass
        
        try:
            # Check MongoDB
            test_chat = self.chat_utils.get_chat("health_check_test")
            health["mongodb"] = True
        except:
            pass
        
        try:
            # Check LangChain LLM
            llm = self._create_llm()
            health["langchain_llm"] = llm is not None
            health["provider_info"] = {
                "current_provider": os.getenv("LLM_PROVIDER", "Perplexity"),
                "available_providers": list(self.PROVIDERS.keys()),
                "is_configured": bool(os.getenv(f"{os.getenv('LLM_PROVIDER', 'Perplexity').upper()}_API_KEY"))
            }
        except Exception as e:
            health["llm_error"] = str(e)
        
        return health


# Service instance (singleton pattern)
_langchain_chatbot_service_instance = None

def get_langchain_chatbot_service() -> LangChainChatbotService:
    """Get singleton instance of LangChainChatbotService"""
    global _langchain_chatbot_service_instance
    if _langchain_chatbot_service_instance is None:
        _langchain_chatbot_service_instance = LangChainChatbotService()
    return _langchain_chatbot_service_instance


# Default export
__all__ = ['LangChainChatbotService', 'get_langchain_chatbot_service']