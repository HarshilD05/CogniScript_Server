"""
Services package for LawLibra RAG Server
Provides high-level orchestration services
"""

from .chatbot_service import ChatbotService, get_chatbot_service

__all__ = ['ChatbotService', 'get_chatbot_service']