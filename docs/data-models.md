# 📊 Data Models & Storage Architecture

This document provides a comprehensive overview of how CogniScript stores and manages data across **MongoDB** and **ChromaDB**.

---

## 🗂️ Storage Overview

CogniScript uses a **dual-database architecture** to optimize for different data access patterns:

- **MongoDB** - Document database for structured data (users, chats, metadata)
- **ChromaDB** - Vector database for semantic search (document embeddings, RAG retrieval)

```
┌─────────────────────────────────────────────────────────────┐
│                    CogniScript Data Flow                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Upload Document                                       │
│       │                                                     │
│       ├──► MongoDB: Store document metadata                 │
│       │    - Filename, size, type                           │
│       │    - Upload date, page count                        │
│       │    - Reference to chat and user                     │
│       │                                                     │
│       └──► ChromaDB: Store vector embeddings                │
│            - Text chunks with embeddings                    │
│            - Metadata for each chunk                        │
│            - Collection per chat session                    │
│                                                             │
│  User Sends Prompt                                          │
│       │                                                     │
│       ├──► ChromaDB: Query similar chunks                   │
│       │    - Vector similarity search                       │
│       │    - Return relevant context                        │
│       │                                                     │
│       └──► MongoDB: Store conversation                      │
│            - User prompt                                    │
│            - AI response                                    │
│            - Citations from ChromaDB                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ MongoDB Collections

### 1️⃣ **Users Collection**

Stores user account information and their associated chat sessions.

**Model:** `UserModel` (`models/user.py`)

```python
{
  "_id": ObjectId("..."),           # MongoDB generated ID
  "email": "user@example.com",      # User email (validated)
  "user_type": "USER",              # Enum: ADMIN | LAWYER | USER
  "chats": [                        # Array of chat ObjectIds (strings)
    "673abc123def456789012345",
    "673abc123def456789012346"
  ],
  "created_at": "2025-11-23T10:00:00Z",
  "updated_at": "2025-11-23T10:00:00Z"
}
```

**Fields:**
- `_id` - Unique MongoDB ObjectId
- `email` - EmailStr (validated email address)
- `user_type` - Enum: `ADMIN`, `LAWYER`, or `USER`
- `chats` - List of chat session IDs (references to Chat collection)
- `created_at` - Timestamp of user creation
- `updated_at` - Last modification timestamp

**Relationships:**
- One user → Many chats (1:N)

---

### 2️⃣ **Chats Collection**

Stores conversation sessions with complete message history.

**Model:** `ChatModel` (`models/chat.py`)

```python
{
  "_id": ObjectId("673abc123def456789012345"),  # MongoDB generated ID
  "userId": "673user123456789012345",           # Reference to User._id
  "title": "Legal Document Analysis",           # Chat session title
  "status": "active",                           # active | archived | deleted
  "conversation_history": [                     # Array of ConversationEntry
    {
      "timestamp": "2025-11-23T10:05:00Z",
      "user": "What are the key points in the contract?",
      "assistant": "Based on the uploaded document...",
      "uploads": [                              # Array of UploadModel
        {
          "docId": "673doc123456789012345",
          "filename": "contract.pdf",
          "fileType": ".pdf",
          "fileSize": 1048576,
          "uploadDate": "2025-11-23T10:04:00Z",
          "pageCount": 25,
          "previewText": "This agreement is made...",
          "tags": ["contract", "legal"],
          "source": "user upload",
          "metadata": {},
          "status": "processed"
        }
      ],
      "citations": [                            # Array of CitationModel
        {
          "citationId": "cit001",
          "source": "contract.pdf",
          "text": "Party A agrees to...",
          "page": 3,
          "link": null
        }
      ]
    }
  ],
  "created_at": "2025-11-23T10:00:00Z",
  "updated_at": "2025-11-23T10:05:00Z"
}
```

**Fields:**
- `_id` - Unique chat session ID
- `userId` - Reference to the user who owns this chat
- `title` - Human-readable chat title
- `status` - Chat state: `active`, `archived`, or `deleted`
- `conversation_history` - Array of conversation turns
- `created_at` - Chat creation timestamp
- `updated_at` - Last message timestamp

**ConversationEntry Fields:**
- `timestamp` - When this exchange occurred
- `user` - User's message text
- `assistant` - AI's response text
- `uploads` - Documents uploaded in this turn
- `citations` - Source citations for the response

**Relationships:**
- Many chats → One user (N:1)
- One chat → Many documents (1:N via conversation_history)
- One chat → One ChromaDB collection (1:1)

---

### 3️⃣ **Documents Collection** (Implicit)

Document metadata is stored within the chat's `conversation_history` array and also tracked separately for ChromaDB reference.

**Model:** `DocumentModel` (`models/document.py`)

```python
{
  "docId": "673doc123456789012345",             # Unique document ID
  "chat_id": "673abc123def456789012345",        # Reference to Chat._id
  "filename": "contract.pdf",
  "fileType": ".pdf",
  "fileSize": 1048576,                          # Size in bytes
  "uploadDate": "2025-11-23T10:04:00Z",
  "pageCount": 25,
  "previewText": "This agreement is made between...",
  "tags": ["contract", "legal", "2025"],
  "source": "user upload",
  "metadata": {
    "total_chunks": 47,                         # Number of text chunks
    "processing_model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "status": "processed",                        # pending | processing | processed | error
  "chroma_collection": "673abc123def456789012345_docs",  # ChromaDB collection name
  "chunk_ids": [                                # Array of ChromaDB chunk IDs
    "673doc123456789012345_chunk_0",
    "673doc123456789012345_chunk_1",
    "..."
  ],
  "created_at": "2025-11-23T10:04:00Z",
  "updated_at": "2025-11-23T10:04:30Z"
}
```

**Fields:**
- `docId` - Unique document identifier
- `chat_id` - Links to parent chat session
- `filename` - Original filename
- `fileType` - File extension (`.pdf`, `.docx`, `.txt`)
- `fileSize` - File size in bytes
- `uploadDate` - Upload timestamp
- `pageCount` - Number of pages (for PDFs)
- `previewText` - First 200 characters
- `tags` - Searchable tags
- `source` - Origin of document
- `metadata` - Additional processing information
- `status` - Processing state
- `chroma_collection` - Name of ChromaDB collection
- `chunk_ids` - IDs of chunks stored in ChromaDB

**Relationships:**
- Many documents → One chat (N:1)
- One document → Many ChromaDB chunks (1:N)

---

### 4️⃣ **Citation Model**

Citations are embedded within conversation entries.

**Model:** `CitationModel` (`models/citation.py`)

```python
{
  "citationId": "cit001",                       # Unique citation ID
  "source": "contract.pdf",                     # Source document filename
  "text": "Party A agrees to deliver...",      # Cited text snippet
  "page": 3,                                    # Page number (optional)
  "link": null                                  # External link (optional)
}
```

---

## 🧲 ChromaDB Collections

### Collection Structure

Each chat session gets its own isolated ChromaDB collection for document embeddings.

**Collection Naming Convention:**
```
{chat_id}_docs
```

**Example:** `673abc123def456789012345_docs`

---

### Vector Storage Schema

**Collection Metadata:**
```python
{
  "chat_id": "673abc123def456789012345",
  "created_at": "2025-11-23T10:00:00Z"
}
```

**Document Chunks:**
Each document is split into chunks, embedded, and stored as:

```python
{
  # Unique chunk identifier
  "id": "673doc123456789012345_chunk_0",
  
  # Original text content
  "document": "This agreement is made between Party A and Party B...",
  
  # Vector embedding (384 dimensions for all-MiniLM-L6-v2)
  "embedding": [0.123, -0.456, 0.789, ...],  # 384-dimensional vector
  
  # Rich metadata for retrieval
  "metadata": {
    "chat_id": "673abc123def456789012345",
    "doc_id": "673doc123456789012345",
    "filename": "contract.pdf",
    "upload_date": "2025-11-23T10:04:00Z",
    "user_id": "673user123456789012345",
    "pageNo": 1,                               # Page number in original doc
    "chunkNo": 0,                              # Chunk index
    "chunkSize": 512,                          # Characters in this chunk
    "overlap": 50                              # Character overlap with previous chunk
  }
}
```

**Embedding Model:**
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Provider:** HuggingFace Transformers

---

### Chunk Processing Details

**Text Chunking Strategy:**
1. **Chunk Size:** 1000 characters (configurable)
2. **Overlap:** 200 characters (configurable)
3. **Method:** Recursive character text splitting (LangChain)
4. **Preserves:** Sentence boundaries, paragraph structure

**Example:**
```
Original Document (5000 chars)
    ↓
Split into chunks with overlap
    ↓
[Chunk 0: chars 0-1000]
[Chunk 1: chars 800-1800]   ← 200 char overlap
[Chunk 2: chars 1600-2600]  ← 200 char overlap
...
    ↓
Generate embeddings for each chunk
    ↓
Store in ChromaDB with metadata
```

---

## 🔄 Data Relationships

### Entity Relationship Diagram

```
┌──────────────┐
│    Users     │
│   (MongoDB)  │
│──────────────│
│ • _id (PK)   │
│ • email      │
│ • user_type  │
│ • chats[]    │────┐
└──────────────┘    │
                    │ 1:N
                    │
                    ▼
              ┌──────────────┐
              │    Chats     │
              │  (MongoDB)   │
              │──────────────│
              │ • _id (PK)   │
              │ • userId(FK) │
              │ • title      │
              │ • conv_hist[]│
              └──────────────┘
                    │ 1:1
                    │
                    ├─────────────────────┐
                    │                     │
                    ▼                     ▼
          ┌──────────────────┐   ┌──────────────────┐
          │   Documents      │   │  ChromaDB Coll   │
          │   (Embedded in   │   │  (Vector Store)  │
          │   Conversation)  │   │──────────────────│
          │──────────────────│   │ • collection_id  │
          │ • docId          │   │ • chunks[]       │
          │ • filename       │   │   - id           │
          │ • chroma_coll    │◄──│   - embedding    │
          │ • chunk_ids[]    │───│   - document     │
          │ • metadata       │   │   - metadata     │
          └──────────────────┘   └──────────────────┘
                    │
                    │ 1:N
                    ▼
          ┌──────────────────┐
          │   Citations      │
          │   (Embedded)     │
          │──────────────────│
          │ • citationId     │
          │ • source         │
          │ • text           │
          │ • page           │
          └──────────────────┘
```

---

## 🔍 Query Patterns

### 1. **RAG Query Flow**

When a user asks a question:

```sql
-- Step 1: Query ChromaDB (Vector Search)
SELECT chunks 
FROM {chat_id}_docs 
ORDER BY cosine_similarity(query_embedding, chunk_embedding) DESC 
LIMIT 5

-- Step 2: Retrieve metadata from MongoDB
SELECT filename, pageNo, uploadDate 
FROM Documents 
WHERE docId IN (chunk.metadata.doc_id)

-- Step 3: Generate response with LLM + context

-- Step 4: Store conversation in MongoDB
UPDATE Chats 
SET conversation_history = [..., new_entry]
WHERE _id = chat_id
```

### 2. **Document Upload Flow**

```python
# Step 1: Extract text from document
extracted_text = extract_pdf_text(file)

# Step 2: Split into chunks
chunks = split_text(extracted_text, chunk_size=1000, overlap=200)

# Step 3: Generate embeddings
embeddings = embedding_model.encode(chunks)

# Step 4: Store in ChromaDB
chroma_collection.add(
    ids=chunk_ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=chunk_metadata
)

# Step 5: Store document metadata in MongoDB
documents_collection.insert_one(document_model)

# Step 6: Add to chat conversation history
chats_collection.update_one(
    {"_id": chat_id},
    {"$push": {"conversation_history.uploads": upload_model}}
)
```

### 3. **User Chat History Retrieval**

```javascript
// Get all chats for a user
db.users.findOne(
  { "_id": user_id },
  { "chats": 1 }
)

// Get full chat details
db.chats.find(
  { "_id": { "$in": user.chats } }
)
```

---

## 📦 Storage Optimization

### MongoDB Indexing

**Recommended indexes for optimal performance:**

```javascript
// Users collection
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "created_at": -1 })

// Chats collection
db.chats.createIndex({ "userId": 1 })
db.chats.createIndex({ "created_at": -1 })
db.chats.createIndex({ "status": 1 })
db.chats.createIndex({ "userId": 1, "created_at": -1 })

// For conversation search
db.chats.createIndex({ "conversation_history.timestamp": -1 })
```

### ChromaDB Collection Management

**Collection per chat benefits:**
- ✅ **Isolation:** Each chat's documents are completely isolated
- ✅ **Performance:** Smaller collections = faster queries
- ✅ **Cleanup:** Easy deletion when chat is removed
- ✅ **Scalability:** Horizontal scaling per collection

**Naming convention:**
```
{chat_id}_docs
```

**Cleanup strategy:**
- When chat is deleted → Delete ChromaDB collection
- Orphaned collections cleaned up via scheduled task
- Document removal → Remove chunks from collection

---

## 🔐 Data Integrity

### Referential Integrity Rules

1. **User → Chats**
   - When user is deleted, optionally delete or orphan chats
   - Chat IDs in user.chats array must exist in chats collection

2. **Chat → Documents**
   - When chat is deleted, delete ChromaDB collection
   - Document references must be cleaned up

3. **Chat → ChromaDB Collection**
   - One-to-one relationship
   - Collection name derived from chat_id

### Data Consistency

**On Document Upload:**
```
1. Create ChromaDB collection (if not exists)
2. Process document → chunks
3. Store chunks in ChromaDB
4. Store metadata in MongoDB
5. Update chat conversation_history
6. If any step fails → rollback previous steps
```

**On Chat Deletion:**
```
1. Remove chat from user.chats array
2. Delete ChromaDB collection
3. Delete chat document from MongoDB
4. Clean up any orphaned references
```

---

## 📈 Scalability Considerations

### Current Design Limits

- **MongoDB:** ~16MB per document (conversation_history can grow large)
- **ChromaDB:** No practical limit on collection count
- **Embeddings:** 384 dimensions × 4 bytes = 1.5KB per chunk

### Optimization Strategies

1. **Archive old conversations** to separate collection
2. **Paginate conversation_history** for large chats
3. **Compress embeddings** using quantization
4. **Shard MongoDB** by userId for horizontal scaling
5. **Cache frequently accessed** ChromaDB queries

---

## 🛠️ Database Maintenance

### Backup Strategy

**MongoDB:**
```bash
mongodump --uri="mongodb+srv://..." --out=/backup/$(date +%Y%m%d)
```

**ChromaDB:**
```bash
# Backup entire ChromaDB directory
tar -czf chromadb_backup_$(date +%Y%m%d).tar.gz ./chromaDB/
```

### Health Checks

Monitor these metrics:
- MongoDB connection status
- ChromaDB collection count
- Average query response time
- Storage size growth rate
- Orphaned collections count

---

## 📚 Model Files Reference

All data models are defined in the `models/` directory:

- **`models/user.py`** - User account model
- **`models/chat.py`** - Chat session and conversation history
- **`models/document.py`** - Document metadata and upload info
- **`models/citation.py`** - Citation and source reference model

Utility functions for database operations:

- **`utils/chroma_utils.py`** - ChromaDB operations
- **`utils/chat_utils.py`** - MongoDB chat operations
- **`utils/user_utils.py`** - MongoDB user operations
- **`utils/doc_utils.py`** - Document processing utilities

---

<div align="center">

**📊 Understanding the data models helps you extend CogniScript effectively!**

For API usage, see [routes.md](routes.md)

</div>
