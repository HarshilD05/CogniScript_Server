import uuid
import fitz  # PyMuPDF - for page number extraction
from typing import Dict, List, Any
# from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from langchain_huggingface import HuggingFaceEndpointEmbeddings
import os
import re
import dotenv

import chromadb
from config.chroma import CHROMA_DB_PATH

# Load environment variables
dotenv.load_dotenv()

# Configuration
CHUNK_INFO = {
    'chunk_size': 500,
    'chunk_overlap': 50
}


class DocProcessor:
    """
    LangChain Workflow for processing PDFs into chunked, embedded documents
    with detailed metadata including page numbers.
    """

    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the workflow with embedding model."""
        self.embedding_model = embedding_model
        self.embedder = HuggingFaceEndpointEmbeddings(
            model=self.embedding_model,
            huggingfacehub_api_token=os.getenv('HUGGINGFACEHUB_API_TOKEN', None)  # Optional token for private models
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)

    def extract_text_with_pages(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF while preserving page number information.
        Returns list of {text: str, page_no: int} dictionaries.
        """
        page_texts = []

        # Use PyMuPDF directly to get page-wise text with page numbers
        with fitz.open(pdf_path) as doc :
            page_num = 0
            for page in doc:
                text = page.get_text()
                if text.strip():  # Only include pages with text
                    page_texts.append({
                        'text': self.clean_text(text),
                        'page_no': page_num + 1  # 1-indexed page numbers
                    })

                page_num += 1

        return page_texts

    def clean_text(self, text: str) -> str:
        """Clean text by removing multiple spaces, newlines, and repeated punctuation patterns."""
        # Remove lines with only dots, dashes, or underscores
        text = re.sub(r'\n[\.\-_ ]{5,}\n', '\n', text)
        # Remove all occurrences of long runs of dots, dashes, underscores
        text = re.sub(r'[.\-_]{2,}', ' ', text)
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', text)
        # Replace multiple spaces with a single space
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def chunk_text_with_metadata(self, page_texts: List[Dict],
                                 chunk_size: int = CHUNK_INFO.get(
                                     'chunk_size'),
                                 chunk_overlap: int = CHUNK_INFO.get('chunk_overlap')) -> List[Dict]:
        """
        Chunk text while preserving page number metadata.
        Returns list of {text: str, page_no: int, chunk_in_page: int}.
        """
        all_chunks = []

        # Initialize text splitter with token-based chunking
        splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=self.tokenizer,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=False
        )

        for page_data in page_texts:
            page_text = page_data['text']
            page_no = page_data['page_no']

            # Split the page text into chunks
            chunks = splitter.split_text(page_text)

            # Add metadata to each chunk
            for chunk_idx, chunk in enumerate(chunks):
                if chunk.strip():  # Only include non-empty chunks
                    all_chunks.append({
                        'text': chunk.strip(),
                        'page_no': page_no,
                        'chunk_in_page': chunk_idx + 1
                    })

        return all_chunks

    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for all chunks.
        Adds 'embedding' field to each chunk dictionary.
        """
        embedded_chunks = []

        # Extract text for batch embedding
        chunk_texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings in batch for efficiency
        try:
            embeddings = self.embedder.embed_documents(chunk_texts)
        except Exception as e:
            # Fallback to individual embedding if batch fails
            print(f"Batch embedding failed, using individual embedding: {e}")
            embeddings = []
            for text in chunk_texts:
                embedding = self.embedder.embed_query(text)
                embeddings.append(embedding)

        # Combine chunks with embeddings
        for chunk, embedding in zip(chunks, embeddings):
            embedded_chunk = chunk.copy()
            embedded_chunk['embedding'] = embedding
            embedded_chunks.append(embedded_chunk)

        return embedded_chunks

    def process_pdf(self, pdf_path: str, doc_name: str = None) -> Dict[str, Any]:
        """
        Complete workflow to process PDF and return the required output format.

        Args:
            pdf_path: Path to the PDF file
            doc_name: Optional document name (defaults to filename)

        Returns:
            Dictionary in the required format with docId and chunks
        """

        # Step 1: Generate document ID
        doc_id = str(uuid.uuid4())

        # Step 2: Extract document name if not provided
        if doc_name is None:
            doc_name = os.path.basename(pdf_path)

        print(f"Processing PDF: {doc_name}")
        print(f"Document ID: {doc_id}")

        # Step 3: Extract text from PDF with page information
        print("Extracting text from PDF pages...")
        page_texts = self.extract_text_with_pages(pdf_path)
        print(f"Extracted text from {len(page_texts)} pages")

        # Step 4: Chunk text data while preserving metadata
        print("Chunking text data...")
        chunks = self.chunk_text_with_metadata(page_texts)
        print(f"Created {len(chunks)} text chunks")

        # Step 5: Generate embeddings for chunks
        print("Generating embeddings...")
        embedded_chunks = self.embed_chunks(chunks)
        print(f"Generated embeddings for {len(embedded_chunks)} chunks")

        # Step 6: Format output according to requirements
        formatted_chunks = []
        for chunk_idx, chunk in enumerate(embedded_chunks):
            formatted_chunk = {
                'chunk_id': f"{doc_id}_{chunk_idx + 1}",
                'text': chunk['text'],
                'metadata': {
                    'doc_name': doc_name,
                    'pageNo': chunk['page_no']
                },
                'embedding': chunk['embedding']
            }
            formatted_chunks.append(formatted_chunk)

        # Step 7: Create final output
        result = {
            'docId': doc_id,
            'chunks': formatted_chunks
        }

        print(
            f"Processing complete! Generated {len(formatted_chunks)} chunks")
        return result

# Convenience function for easy usage


def process_pdf_document(pdf_path: str, doc_name: str = None) -> Dict[str, Any]:
    """
    Convenience function to process a PDF document.

    Args:
        pdf_path: Path to the PDF file
        doc_name: Optional document name

    Returns:
        Processed document with chunks and embeddings
    """
    # Initialize the workflow
    workflow = DocProcessor()

    # Process the PDF
    result = workflow.process_pdf(pdf_path, doc_name)

    return result

# # Alternative approach using LangChain's PyMuPDFLoader
# def langchain_pdf_workflow(pdf_path: str, doc_name: str = None) -> Dict[str, Any]:
#     """
#     Alternative implementation using LangChain's built-in PyMuPDFLoader.
#     This approach uses LangChain's document structure more directly.
#     """

#     # Step 1: Generate document ID and extract doc name
#     doc_id = str(uuid.uuid4())
#     if doc_name is None:
#         doc_name = os.path.basename(pdf_path)

#     print(f"Processing PDF with LangChain: {doc_name}")

#     # Step 2: Load PDF using LangChain's PyMuPDFLoader
#     loader = PyMuPDFLoader(pdf_path, mode="page")  # Page mode preserves page numbers
#     documents = loader.load()
#     print(f"Loaded {len(documents)} pages")

#     # Step 3: Initialize text splitter and embedder
#     tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
#     splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
#         tokenizer=tokenizer,
#         chunk_size=CHUNK_INFO.get('chunk_size'),
#         chunk_overlap=CHUNK_INFO.get('chunk_overlap'),
#         separators=["\n\n", "\n", ". ", " ", ""],
#         keep_separator=False
#     )
#     embedder = HuggingFaceEndpointEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")

#     # Step 4: Process each document (page)
#     all_chunks = []
#     chunk_counter = 1

#     for doc in documents:
#         page_no = doc.metadata.get('page', 0) + 1  # Convert to 1-indexed
#         page_text = doc.page_content

#         # Clean and chunk the page text
#         cleaned_text = re.sub(r'\n+', '\n', page_text)
#         cleaned_text = re.sub(r' +', ' ', cleaned_text).strip()

#         chunks = splitter.split_text(cleaned_text)

#         # Process each chunk
#         for chunk_text in chunks:
#             if chunk_text.strip():
#                 # Generate embedding
#                 embedding = embedder.embed_query(chunk_text.strip())

#                 # Create formatted chunk
#                 formatted_chunk = {
#                     'chunk_id': f"{doc_id}_{chunk_counter}",
#                     'text': chunk_text.strip(),
#                     'metadata': {
#                         'doc_name': doc_name,
#                         'pageNo': page_no
#                     },
#                     'embedding': embedding
#                 }
#                 all_chunks.append(formatted_chunk)
#                 chunk_counter += 1

#     print(f"Generated {len(all_chunks)} chunks with embeddings")

#     # Step 5: Create final output
#     result = {
#         'docId': doc_id,
#         'chunks': all_chunks
#     }

#     print(f"LangChain processing complete! Generated {len(all_chunks)} chunks")
#     return result


def queryChroma(collection, query : str) : 

    # Use the same embedder as DocProcessor
    embedder = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=os.getenv('HUGGINGFACEHUB_API_TOKEN', None)
    )
    # Embed the query
    query_embedding = embedder.embed_query(query)

    # Connect to ChromaDB and collection
    import chromadb
    from config.chroma import CHROMA_DB_PATH
    collection_name = "lawlibra_docs"
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(collection_name)

    # Query the collection for most relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5  # You can make this configurable
    )

    # Format and return the results
    relevant_chunks = []
    for i in range(len(results['ids'][0])):
        relevant_chunks.append({
            'id': results['ids'][0][i],
            'text': results['documents'][0][i],
            'distance': results['distances'][0][i],
            'metadata': results['metadatas'][0][i]
        })
    return relevant_chunks


def upload_docs(pdf_files : List[str], collection_name : str) : 

    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(collection_name)
    
    for pdf_path in pdf_files:
        print(f"Processing PDF: {pdf_path}")
        # Ensure the PDF file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        result = process_pdf_document(pdf_path, os.path.basename(pdf_path))

        print(f"Document ID: {result['docId']}")
        print(f"Number of chunks: {len(result['chunks'])}")

        # Store each chunk in ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        for chunk in result['chunks']:
            ids.append(chunk['chunk_id'])
            documents.append(chunk['text'])
            embeddings.append(chunk['embedding'])
            metadatas.append(chunk['metadata'])

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"Stored {len(ids)} chunks in ChromaDB collection '{collection_name}' for document {result['docId']}")



# Example usage
if __name__ == "__main__":
    # Example 1: Using the main workflow
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads"))
    pdf_files = [os.path.join(uploads_dir, f) for f in os.listdir(uploads_dir) if f.endswith('.pdf')]

    # Use a single collection for all docs, or customize as needed
    collection_name = "lawlibra_docs"
    
    upload_docs(pdf_files, collection_name)

     
    #  Part 2 Querying the DB
    query = "Which Coutries have a Regional Variations for the Laws?"
    # Query the ChromaDB with the given query
    results = queryChroma(query)

    # Print the results
    print("Query Results:")
    for result in results:
        print(f"ID: {result['id']}")
        print(f"Text: {result['text']}")
        print(f"Distance: {result['distance']}")
        print(f"Metadata: {result['metadata']}")
        print("-" * 50)

