# 🤖 CogniScript RAG Server

**A powerful Retrieval-Augmented Generation (RAG) chatbot server built with Flask, ChromaDB, and modern NLP techniques.**

CogniScript enables intelligent document-based conversations by combining the power of Large Language Models (LLMs) with semantic document retrieval. Upload documents, create isolated chat sessions, and get contextually-aware responses backed by your own knowledge base.

---

## ✨ Key Features

### 🧠 **Advanced RAG Pipeline**
- **Intelligent Context Retrieval:** Uses ChromaDB vector similarity search to find relevant document sections
- **Multi-Document Support:** Upload PDFs, DOCs, and text files with automatic processing
- **Smart Chunking:** Recursive text splitting with configurable overlap for optimal embedding

### 💬 **Isolated Chat Sessions**
- **Per-Chat Vector Databases:** Each conversation has its own ChromaDB collection
- **Conversation History:** Maintains context across multiple exchanges
- **Citation Tracking:** Automatic source attribution for generated responses

### 🔧 **Flexible Document Processing**
- **Text Extraction:** Extract content from various document formats
- **Text Cleaning:** Remove noise and normalize content for better embeddings
- **High Dimension Embeddings:** HuggingFace model integration for high-quality vector representations

### 🚀 **Production-Ready APIs**
- **RESTful Design:** Clean, well-documented endpoints for all operations  
- **Error Handling:** Comprehensive error responses and logging
- **Health Monitoring:** Built-in health checks for system components
- **Scalable Architecture:** Modular design supporting easy extension

---

## 🚀 Quick Start

1. **Clone the repository:**
	```powershell
	git clone <repo-url>
	cd CogniScript_Server
	```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   
   **Windows:**
   ```powershell
   .\venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   - Copy `.env.example` to `.env` and edit the values as needed for your setup:
     
     **Windows:**
     ```powershell
     copy .env.example .env
     ```
     
     **macOS/Linux:**
     ```bash
     cp .env.example .env
     ```
     
   - Edit `.env` in your editor and fill in all required values (MongoDB, API keys, etc.)

6. **Run the server:**
   ```bash
   python app.py
   ```

7. **Test the APIs:**
   - See [docs/routes.md](docs/routes.md) for a full list of API endpoints and usage
   - (Optional) Import the Postman collection (if provided) for easy API testing

---

## 🏗️ Architecture Overview

CogniScript follows a modular, scalable architecture designed for production RAG applications:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │────│   Flask APIs     │────│   ChromaDB      │
│                 │    │                  │    │                 │
│ • Web Interface │    │ • Chat Routes    │    │ • Vector Store  │
│ • Mobile App    │    │ • Doc Routes     │    │ • Collections   │
│ • Postman       │    │ • User Routes    │    │ • Embeddings    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │     MongoDB      │
                       │                  │
                       │ • User Data      │
                       │ • Chat History   │
                       │ • Metadata       │
                       └──────────────────┘
```

### 🔄 **Document Ingestion Workflow**
1. **Upload:** Client uploads document via `/chats/{chat_id}/upload`
2. **Extract:** Text extraction from PDF/DOC using specialized libraries
3. **Clean:** Text normalization and noise removal
4. **Chunk:** Recursive splitting with configurable overlap
5. **Embed:** Generate vector embeddings using HuggingFace models
6. **Store:** Save vectors and metadata to ChromaDB collection

### 💭 **RAG Query Workflow**
1. **Prompt:** User sends query via `/chats/{chat_id}/prompt`
2. **Embed:** Convert query to vector embedding
3. **Search:** Find relevant document chunks using vector similarity
4. **Context:** Format retrieved chunks as context for LLM
5. **Generate:** LLM generates response using context + conversation history
6. **Cite:** Extract and return source citations for transparency

---

## 🗄️ **ChromaDB Integration**

CogniScript leverages **ChromaDB** for efficient vector storage and retrieval:

- **🔐 Isolated Collections:** Each chat session gets its own ChromaDB collection (`{collection_prefix}{chat_id}`)
- **📊 Rich Metadata:** Documents stored with filename, chunk indices, and timestamps
- **🔍 Semantic Search:** Query documents using natural language with vector similarity
- **⚡ Fast Retrieval:** Optimized for low-latency RAG applications
- **🔄 CRUD Operations:** Full lifecycle management of vector databases

### **Supported Operations:**
- Create chat-specific vector databases
- Upload and embed documents with automatic chunking
- Semantic search across document collections
- Retrieve document metadata and statistics
- Delete collections and cleanup resources

---

## 📖 **API Documentation**

### 🔗 **Complete Endpoint Reference**
See [**docs/routes.md**](docs/routes.md) for comprehensive API documentation including:
- All available endpoints with HTTP methods
- Request body schemas and parameters
- Expected response formats and status codes
- Error handling and validation rules

### 🧪 **Testing & Development**
- **Postman Collection:** Import the provided JSON for easy API testing
- **Health Endpoints:** Built-in health checks for system monitoring
- **Detailed Logging:** Comprehensive error tracking and debugging support

---

## 🚀 **Getting Started Examples**

### **Create a User and Chat Session**
```bash
# Create a new user
curl -X POST http://localhost:3000/users \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "user_type": "standard"}'

# Create a new chat
curl -X POST http://localhost:3000/chats \
  -H "Content-Type: application/json" \
  -d '{"userId": "user_id_here", "title": "My First RAG Chat"}'
```

### **Upload a Document and Ask Questions**
```bash
# Upload a document to the chat
curl -X POST http://localhost:3000/chats/{chat_id}/upload \
  -F "file=@your_document.pdf"

# Ask a question about the document
curl -X POST http://localhost:3000/chats/{chat_id}/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the main points discussed in the document?"}'
```

---

## 🛠️ **Tech Stack**

- **Backend:** Flask (Python)
- **Vector Database:** ChromaDB
- **Document Database:** MongoDB
- **ML/NLP:** HuggingFace Transformers
- **Document Processing:** PyPDF2, python-docx
- **Text Processing:** LangChain text splitters

---

## 🤝 **Contributing**

We welcome contributions! Whether you're fixing bugs, improving documentation, or adding new features:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests if applicable
4. **Commit your changes:** `git commit -m 'Add amazing feature'`
5. **Push to the branch:** `git push origin feature/amazing-feature`
6. **Open a Pull Request**

For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **ChromaDB** for providing an excellent vector database solution
- **HuggingFace** for state-of-the-art embedding models
- **LangChain** for text processing utilities
- **Flask** community for the robust web framework

---

<div align="center">

**⭐ If you find CogniScript helpful, please give it a star! ⭐**

Made with ❤️ for the RAG community

</div>
