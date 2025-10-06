# API Routes Documentation

This document provides comprehensive documentation for all API endpoints available in the CogniScript RAG Server. Each endpoint includes HTTP methods, request body schemas, and expected responses.

**Base URL Structure:** `{serverURL}/api/{endpoint}`
- **Local Development:** `http://localhost:5000/api/{endpoint}` (default port)
- **Production:** `https://your-domain.com/api/{endpoint}`

> **Tip:** You can also use the provided Postman collection (if available) for easy API testing. Both manual documentation and Postman export are recommended for best developer experience.

## Table of Contents
- [Chat APIs](./chat-apis.md) - Comprehensive chat and RAG functionality
- [Document Processing APIs](./doc-apis.md) - Document handling and processing
- [User Management APIs](./user-apis.md) - User creation and management
- [ChromaDB Integration](#chromadb-integration)

## Quick Reference

### Chat APIs
- `POST {serverURL}/api/chats` - Create new chat
- `POST {serverURL}/api/chats/{chat_id}/prompt` - Send prompt with RAG
- `POST {serverURL}/api/chats/{chat_id}/upload` - Upload document to chat
- `GET {serverURL}/api/chats/{chat_id}` - Get chat details
- [View all Chat APIs →](./chat-apis.md)

### Document Processing APIs  
- `POST {serverURL}/api/extract-text` - Extract text from PDF
- `POST {serverURL}/api/clean-text` - Clean and normalize text
- `POST {serverURL}/api/chunk-text` - Split text into chunks
- `POST {serverURL}/api/embed-text` - Generate text embeddings
- [View all Document APIs →](./doc-apis.md)

### User Management APIs
- `POST {serverURL}/api/users` - Create new user
- `GET {serverURL}/api/users/{user_id}` - Get user details
- `GET {serverURL}/api/users/{user_id}/chats` - Get user's chats
- `GET {serverURL}/api/users/email/{email}` - Get user by email
- [View all User APIs →](./user-apis.md)

## ChromaDB Integration

The server uses [ChromaDB](https://www.trychroma.com/) to store vector embeddings for documents:

- **🔐 Isolated Collections:** Each chat session has its own ChromaDB collection for document isolation
- **📊 Rich Metadata:** Documents stored with filename, chunk indices, and timestamps
- **🔍 Semantic Search:** Query endpoints use vector similarity search for relevant context retrieval
- **⚡ Fast Retrieval:** Optimized for low-latency RAG applications
- **🔄 CRUD Operations:** Full lifecycle management of vector databases

### **Supported Operations:**
- Create chat-specific vector databases
- Upload and embed documents with automatic chunking
- Semantic search across document collections
- Retrieve document metadata and statistics
- Delete collections and cleanup resources

## Error Responses

All endpoints may return these common error responses:

**400 Bad Request:**
```json
{
  "error": "Descriptive error message"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

---

*Last updated: October 6, 2025*
