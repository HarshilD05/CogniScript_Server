# Document Processing APIs Documentation

Comprehensive documentation for document text extraction, cleaning, chunking, and embedding generation.

**Base URL:** `{serverURL}/api`
- **Local Development:** `http://localhost:5000/api`
- **Production:** `https://your-domain.com/api`

---

## Text Extraction

### 1. Extract Text from PDF
**`POST {serverURL}/api/extract-text`**

Extract text content from uploaded PDF files.

**Request:** Multipart form with `file` field (PDF only)

**Response (200):**
```json
{
  "message": "Text extracted successfully",
  "text": "string",
  "filename": "string",
  "text_length": "number"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/extract-text \
  -F "file=@document.pdf"
```

---

## Text Processing

### 2. Clean Text
**`POST {serverURL}/api/clean-text`**

Clean text by removing multiple spaces, newlines, and repeated punctuation.

**Request Body:**
```json
{
  "text": "string (required)"
}
```

**Response (200):**
```json
{
  "message": "Text cleaned successfully",
  "original_text": "string",
  "cleaned_text": "string",
  "original_length": "number",
  "cleaned_length": "number"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/clean-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This   is    some    messy    text\\n\\nwith   extra   spaces."}'
```

### 3. Chunk Text
**`POST {serverURL}/api/chunk-text`**

Split text into chunks with overlap using recursive character text splitter.

**Request Body:**
```json
{
  "text": "string (required)",
  "chunk_size": "number (optional, default: 500)",
  "chunk_overlap": "number (optional, default: 50)"
}
```

**Response (200):**
```json
{
  "chunks": ["array of text chunks"],
  "total_chunks": "number",
  "chunk_size": "number",
  "chunk_overlap": "number",
  "original_text_length": "number"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/chunk-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a long document that needs to be split into smaller chunks...",
    "chunk_size": 300,
    "chunk_overlap": 50
  }'
```

---

## Embedding Generation

### 4. Generate Text Embedding
**`POST {serverURL}/api/embed-text`**

Generate embeddings for text using HuggingFace model.

**Request Body:**
```json
{
  "text": "string (required)"
}
```

**Response (200):**
```json
{
  "text": "string",
  "embedding": ["array of float values"],
  "embedding_length": "number"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/embed-text \
  -H "Content-Type: application/json" \
  -d '{"text": "Machine learning is a subset of artificial intelligence."}'
```

### 5. Generate Chunk Embeddings
**`POST {serverURL}/api/embed-chunks`**

Generate embeddings for multiple text chunks.

**Request Body:**
```json
{
  "chunks": ["array of strings (required)"]
}
```

**Response (200):**
```json
{
  "embeddings": [
    {
      "chunk_index": "number",
      "text": "string",
      "embedding": ["array of float values"]
    }
  ],
  "total_chunks": "number",
  "successful_embeddings": "number"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/embed-chunks \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": [
      "First chunk of text to be embedded.",
      "Second chunk of text to be embedded.",
      "Third chunk of text to be embedded."
    ]
  }'
```

---

## Use Cases

### Document Processing Pipeline
1. **Extract Text:** Upload PDF and extract raw text content
2. **Clean Text:** Remove noise and normalize the extracted text
3. **Chunk Text:** Split into manageable pieces for embedding
4. **Generate Embeddings:** Create vector representations for semantic search

### Testing & Development
These endpoints are particularly useful for:
- **Testing extraction algorithms** on different PDF formats
- **Experimenting with chunk sizes** for optimal RAG performance
- **Validating embeddings** before storing in ChromaDB
- **Debugging document processing** pipeline issues

---

## Supported File Types

- **PDF:** Primary format for document ingestion
- **Text Input:** Direct text processing via API body
- **Future Support:** DOC, DOCX (via chat upload endpoints)

---

## Error Responses

All endpoints may return these common error responses:

**400 Bad Request:**
```json
{
  "error": "Descriptive error message"
}
```

**415 Unsupported Media Type:**
```json
{
  "error": "File type not allowed",
  "allowed_types": ["pdf"]
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

---

## Technical Notes

- **Text Extraction:** Uses PyPDF2 for PDF processing
- **Text Cleaning:** Custom algorithms for noise removal
- **Text Chunking:** LangChain RecursiveCharacterTextSplitter
- **Embeddings:** HuggingFace transformers with configurable models
- **Processing Limits:** Configurable via environment variables

---

*Last updated: October 6, 2025*