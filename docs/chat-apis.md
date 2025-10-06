# Chat APIs Documentation

Comprehensive documentation for chat-based interactions, RAG queries, and document management within chats.

**Base URL:** `{serverURL}/api`
- **Local Development:** `http://localhost:5000/api`
- **Production:** `https://your-domain.com/api`

---

## Chat Management

### 1. Create Chat
**`POST {serverURL}/api/chats`**

Creates a new chat for a user and corresponding ChromaDB vector database.

**Request Body:**
```json
{
  "userId": "string (required)",
  "title": "string (optional, default: 'New Chat')"
}
```

**Response (201):**
```json
{
  "message": "Chat and vector database created successfully",
  "chat_id": "string",
  "user_id": "string",
  "title": "string",
  "vector_db": {
    "collection_name": "string",
    "created": true
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"userId": "64a7b1234567890123456789", "title": "My RAG Chat"}'
```

### 2. Get Chat
**`GET {serverURL}/api/chats/{chat_id}`**

Retrieve a specific chat by ID including conversation history.

**Response (200):**
```json
{
  "message": "Chat retrieved successfully",
  "chat": {
    "chat_id": "string",
    "userId": "string",
    "title": "string",
    "conversation_history": ["array"],
    "created_at": "string",
    "updated_at": "string"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/chats/64a7b1234567890123456789
```

### 3. Delete Chat
**`DELETE {serverURL}/api/chats/{chat_id}`**

Delete a chat and its associated vector database.

**Response (200):**
```json
{
  "message": "Chat and vector database deleted successfully",
  "chat_id": "string",
  "vector_db": {
    "deleted": true,
    "mongodb_documents_deleted": "number"
  }
}
```

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/chats/64a7b1234567890123456789
```

---

## RAG & Conversations

### 4. Add Prompt to Chat
**`POST {serverURL}/api/chats/{chat_id}/prompt`**

Add a user prompt to chat and process it with RAG + LLM for intelligent responses.

**Request Body:**
```json
{
  "prompt": "string (required)",
  "userId": "string (optional)"
}
```

**Response (200):**
```json
{
  "message": "Prompt processed successfully with RAG",
  "chat_id": "string",
  "prompt": "string",
  "response": "string",
  "citations": ["array of citation objects"],
  "context_items_used": "number",
  "history_messages_used": "number",
  "timestamp": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/chats/64a7b1234567890123456789/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the main points in the uploaded document?"}'
```

### 5. Add Assistant Response
**`POST {serverURL}/api/chats/{chat_id}/response`**

Manually add an assistant response to the latest conversation entry.

**Request Body:**
```json
{
  "response": "string (required)",
  "citations": ["array (optional)"]
}
```

**Response (200):**
```json
{
  "message": "Assistant response added successfully",
  "chat_id": "string",
  "response": "string",
  "citations_count": "number"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/chats/64a7b1234567890123456789/response \
  -H "Content-Type: application/json" \
  -d '{"response": "Based on the document, the main points are..."}'
```

---

## Document Management

### 6. Upload Document to Chat
**`POST {serverURL}/api/chats/{chat_id}/upload`**

Upload a document to a specific chat's vector database for RAG processing.

**Request:** Multipart form with `file` field (PDF, TXT, DOC, DOCX)

**Response (201):**
```json
{
  "message": "Document uploaded and processed successfully",
  "chat_id": "string",
  "document": {
    "doc_id": "string",
    "filename": "string",
    "chunks_count": "number",
    "collection_name": "string"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/chats/64a7b1234567890123456789/upload \
  -F "file=@document.pdf"
```

### 7. Query Chat Documents
**`POST {serverURL}/api/chats/{chat_id}/query`**

Query documents in a chat's vector database using semantic search.

**Request Body:**
```json
{
  "query": "string (required)",
  "n_results": "number (optional, 1-20, default: 5)"
}
```

**Response (200):**
```json
{
  "message": "Query executed successfully",
  "chat_id": "string",
  "query": "string",
  "results": {
    "count": "number",
    "chunks": ["array of relevant text chunks with metadata"]
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/chats/64a7b1234567890123456789/query \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning algorithms", "n_results": 3}'
```

### 8. Get Chat Documents Info
**`GET {serverURL}/api/chats/{chat_id}/documents`**

Get information about all documents in a chat.

**Response (200):**
```json
{
  "message": "Document information retrieved successfully",
  "chat_id": "string",
  "documents_info": {
    "total_documents": "number",
    "total_chunks": "number",
    "documents": ["array of document metadata"],
    "collection_name": "string"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/chats/64a7b1234567890123456789/documents
```

---

## System & Monitoring

### 9. Get All Vector Databases
**`GET {serverURL}/api/chats/vector-databases`**

Get information about all chat vector databases.

**Response (200):**
```json
{
  "message": "Chat vector databases retrieved successfully",
  "total_chat_dbs": "number",
  "chat_databases": ["array of database info"]
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/chats/vector-databases
```

### 10. Chat Health Check
**`GET {serverURL}/api/chats/health`**

Health check endpoint for chat APIs and chatbot service.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "chat_apis",
  "endpoints": ["array of available endpoints"],
  "features": ["array of supported features"]
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/chats/health
```

---

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

## RAG Workflow

1. **Create Chat:** Initialize a new chat session with vector database
2. **Upload Document:** Add PDF/DOC files which are automatically processed and embedded
3. **Ask Questions:** Send prompts that leverage uploaded documents for context-aware responses
4. **Get Responses:** Receive LLM-generated answers with citations and source attribution

---

*Last updated: October 6, 2025*