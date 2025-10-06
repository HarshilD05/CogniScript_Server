"""
ChromaDB utility functions for vector database operations
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from bson import ObjectId

from config.chroma import CHROMA_DB_PATH
from config.mongodb import get_mongodb_collection
from models.document import DocumentModel
from utils.doc_workflow import DocProcessor
from langchain_huggingface import HuggingFaceEndpointEmbeddings
import dotenv
import logging

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class ChromaUtils:
    """Utility class for ChromaDB operations"""
    
    def __init__(self):
        """Initialize ChromaUtils with ChromaDB client and embedder"""
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.doc_processor = DocProcessor()
        self.embedder = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.getenv('HUGGINGFACEHUB_API_TOKEN', None)
        )

    def create_chat_vector_db(self, chat_id: str) -> Dict[str, Any]:
        """
        Create a ChromaDB collection for a specific chat
        
        Args:
            chat_id: Chat ID to create vector database for
            
        Returns:
            Dictionary with creation status and collection info
        """
        try:
            # Sanitize chat_id for collection name (replace problematic characters)
            collection_name = f"{chat_id.replace('/', '_').replace('-', '_')}_docs"
            
            # Check if collection already exists
            existing_collections = self.chroma_client.list_collections()
            collection_names = [col.name for col in existing_collections]
            
            if collection_name in collection_names:
                logger.info(f"Collection {collection_name} already exists")
                return {
                    'success': True,
                    'chat_id': chat_id,
                    'collection_name': collection_name,
                    'message': 'Collection already exists',
                    'created': False
                }
            
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"chat_id": chat_id, "created_at": datetime.utcnow().isoformat()}
            )
            
            logger.info(f"Created ChromaDB collection: {collection_name} for chat: {chat_id}")
            
            return {
                'success': True,
                'chat_id': chat_id,
                'collection_name': collection_name,
                'message': 'Vector database created successfully',
                'created': True
            }
            
        except Exception as e:
            logger.error(f"Error creating ChromaDB collection for chat {chat_id}: {str(e)}")
            return {
                'success': False,
                'chat_id': chat_id,
                'error': str(e),
                'message': 'Failed to create vector database'
            }

    def upload_document(self, chat_id: str, temp_file_path: str, filename: str, 
                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload and process document through the document workflow pipeline
        
        Args:
            chat_id: Chat ID to associate document with
            temp_file_path: Path to the temporary uploaded file
            filename: Original filename
            user_id: Optional user ID for document metadata
            
        Returns:
            Dictionary with upload status and document information
        """
        try:
            # Ensure collection exists
            collection_name = f"{chat_id.replace('/', '_').replace('-', '_')}_docs"
            
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except Exception:
                # Create collection if it doesn't exist
                create_result = self.create_chat_vector_db(chat_id)
                if not create_result['success']:
                    return create_result
                collection = self.chroma_client.get_collection(collection_name)
            
            # Process document through the workflow
            logger.info(f"Processing document: {filename} for chat: {chat_id}")
            
            # Use the doc_workflow to process the PDF
            processed_doc = self.doc_processor.process_pdf(temp_file_path, filename)
            
            # Extract document metadata
            doc_id = processed_doc['docId']
            chunks = processed_doc['chunks']
            
            # Store chunks in ChromaDB
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            
            for chunk in chunks:
                ids.append(chunk['chunk_id'])
                documents.append(chunk['text'])
                embeddings.append(chunk['embedding'])
                
                # Enhance metadata with chat and document info
                chunk_metadata = chunk['metadata'].copy()
                chunk_metadata.update({
                    'chat_id': chat_id,
                    'doc_id': doc_id,
                    'filename': filename,
                    'upload_date': datetime.utcnow().isoformat(),
                    'user_id': user_id
                })
                metadatas.append(chunk_metadata)
            
            # Add to ChromaDB collection
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            # Create DocumentModel for MongoDB
            file_size = os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0
            
            document_model = DocumentModel(
                docId=doc_id,
                chat_id=chat_id,
                filename=filename,
                fileType=os.path.splitext(filename)[1].lower(),
                fileSize=file_size,
                uploadDate=datetime.utcnow(),
                pageCount=len(set(chunk['metadata']['pageNo'] for chunk in chunks)),
                previewText=chunks[0]['text'][:200] + "..." if chunks else None,
                tags=[],
                source="user upload",
                metadata={
                    'total_chunks': len(chunks),
                    'processing_model': 'sentence-transformers/all-MiniLM-L6-v2'
                },
                status="processed",
                chroma_collection=collection_name,
                chunk_ids=ids,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store in MongoDB
            docs_collection = get_mongodb_collection('documents')
            result = docs_collection.insert_one(document_model.dict())
            
            if result.inserted_id:
                logger.info(f"Document {filename} processed and stored successfully for chat {chat_id}")
                
                return {
                    'success': True,
                    'doc_id': doc_id,
                    'chat_id': chat_id,
                    'filename': filename,
                    'collection_name': collection_name,
                    'chunks_count': len(chunks),
                    'chunk_ids': ids,
                    'mongodb_id': str(result.inserted_id),
                    'message': 'Document uploaded and processed successfully'
                }
            else:
                # Clean up ChromaDB if MongoDB insertion fails
                collection.delete(ids=ids)
                return {
                    'success': False,
                    'error': 'Failed to store document metadata in MongoDB',
                    'message': 'Document processing failed'
                }
                
        except Exception as e:
            logger.error(f"Error uploading document {filename} for chat {chat_id}: {str(e)}")
            return {
                'success': False,
                'chat_id': chat_id,
                'filename': filename,
                'error': str(e),
                'message': 'Failed to upload and process document'
            }

    def query_chat_docs(self, chat_id: str, query: str, n_results: int = 7) -> Dict[str, Any]:
        """
        Query documents in a specific chat's vector database
        
        Args:
            chat_id: Chat ID to query documents for
            query: Search query string
            n_results: Number of results to return (default: 5)
            
        Returns:
            Dictionary with query results and relevant chunks
        """
        try:
            collection_name = f"{chat_id.replace('/', '_').replace('-', '_')}_docs"
            
            # Get the collection
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except Exception:
                return {
                    'success': False,
                    'chat_id': chat_id,
                    'query': query,
                    'error': 'Collection not found',
                    'message': 'No documents found for this chat'
                }
            
            # Generate query embedding
            query_embedding = self.embedder.embed_query(query)
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            relevant_chunks = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    chunk_data = {
                        'chunk_id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'relevance_rank': i + 1
                    }
                    relevant_chunks.append(chunk_data)
            
            logger.info(f"Query executed for chat {chat_id}: Found {len(relevant_chunks)} relevant chunks")
            
            return {
                'success': True,
                'chat_id': chat_id,
                'query': query,
                'results_count': len(relevant_chunks),
                'relevant_chunks': relevant_chunks,
                'collection_name': collection_name,
                'message': f'Found {len(relevant_chunks)} relevant chunks'
            }
            
        except Exception as e:
            logger.error(f"Error querying documents for chat {chat_id}: {str(e)}")
            return {
                'success': False,
                'chat_id': chat_id,
                'query': query,
                'error': str(e),
                'message': 'Failed to query documents'
            }

    def get_chat_documents_info(self, chat_id: str) -> Dict[str, Any]:
        """
        Get information about all documents in a chat's vector database, including chunk IDs
        
        Args:
            chat_id: Chat ID to get document info for
            
        Returns:
            Dictionary with document information, statistics, and chunk IDs for each document
        """
        try:
            collection_name = f"{chat_id.replace('/', '_').replace('-', '_')}_docs"
            
            # Get the collection
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except Exception:
                return {
                    'success': False,
                    'chat_id': chat_id,
                    'error': 'Collection not found',
                    'message': 'No documents found for this chat'
                }
            
            # Get all documents from the collection
            all_docs = collection.get()
            
            # Analyze documents
            doc_stats = {}
            total_chunks = len(all_docs['ids']) if all_docs['ids'] else 0
            
            if all_docs['metadatas'] and all_docs['ids']:
                for i, metadata in enumerate(all_docs['metadatas']):
                    doc_id = metadata.get('doc_id', 'unknown')
                    filename = metadata.get('filename', 'unknown')
                    chunk_id = all_docs['ids'][i]
                    
                    if doc_id not in doc_stats:
                        doc_stats[doc_id] = {
                            'filename': filename,
                            'chunk_count': 0,
                            'chunk_ids': []
                        }
                    
                    doc_stats[doc_id]['chunk_count'] += 1
                    doc_stats[doc_id]['chunk_ids'].append(chunk_id)
            
            return {
                'success': True,
                'chat_id': chat_id,
                'collection_name': collection_name,
                'total_chunks': total_chunks,
                'total_documents': len(doc_stats),
                'documents': doc_stats,
                'message': f'Found {len(doc_stats)} documents with {total_chunks} total chunks and their IDs'
            }
            
        except Exception as e:
            logger.error(f"Error getting document info for chat {chat_id}: {str(e)}")
            return {
                'success': False,
                'chat_id': chat_id,
                'error': str(e),
                'message': 'Failed to get document information'
            }

    def get_all_chat_dbs(self) -> Dict[str, Any]:
        """
        Get information about all chat vector databases
        
        Returns:
            Dictionary with all chat databases information
        """
        try:
            # Get all collections from ChromaDB
            all_collections = self.chroma_client.list_collections()
            
            chat_dbs = []
            total_collections = 0
            
            for collection in all_collections:
                collection_name = collection.name
                
                # Filter collections that end with '_docs' (our chat collections)
                if collection_name.endswith('_docs'):
                    # Extract chat_id from collection name
                    chat_id = collection_name.replace('_docs', '').replace('_', '/')
                    
                    try:
                        # Get collection metadata and stats
                        chroma_collection = self.chroma_client.get_collection(collection_name)
                        collection_data = chroma_collection.get()
                        
                        total_chunks = len(collection_data['ids']) if collection_data['ids'] else 0
                        
                        # Get document count from metadata
                        doc_ids = set()
                        if collection_data['metadatas']:
                            for metadata in collection_data['metadatas']:
                                doc_id = metadata.get('doc_id')
                                if doc_id:
                                    doc_ids.add(doc_id)
                        
                        # Get creation date from collection metadata
                        created_at = None
                        if hasattr(collection, 'metadata') and collection.metadata:
                            created_at = collection.metadata.get('created_at')
                        
                        chat_db_info = {
                            'chat_id': chat_id,
                            'collection_name': collection_name,
                            'total_chunks': total_chunks,
                            'total_documents': len(doc_ids),
                            'created_at': created_at,
                            'status': 'active'
                        }
                        
                        chat_dbs.append(chat_db_info)
                        total_collections += 1
                        
                    except Exception as e:
                        logger.warning(f"Error getting info for collection {collection_name}: {str(e)}")
                        # Still add basic info even if we can't get detailed stats
                        chat_dbs.append({
                            'chat_id': chat_id,
                            'collection_name': collection_name,
                            'total_chunks': 0,
                            'total_documents': 0,
                            'created_at': None,
                            'status': 'error',
                            'error': str(e)
                        })
                        total_collections += 1
            
            logger.info(f"Found {total_collections} chat vector databases")
            
            return {
                'success': True,
                'total_chat_dbs': total_collections,
                'chat_dbs': chat_dbs,
                'message': f'Found {total_collections} chat vector databases'
            }
            
        except Exception as e:
            logger.error(f"Error getting all chat databases: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get chat databases information'
            }

    def delete_chat_vector_db(self, chat_id: str) -> Dict[str, Any]:
        """
        Delete a chat's vector database and all associated documents
        
        Args:
            chat_id: Chat ID to delete vector database for
            
        Returns:
            Dictionary with deletion status
        """
        try:
            collection_name = f"{chat_id.replace('/', '_').replace('-', '_')}_docs"
            
            # Delete the collection
            try:
                self.chroma_client.delete_collection(collection_name)
                
                # Also remove document records from MongoDB
                docs_collection = get_mongodb_collection('documents')
                delete_result = docs_collection.delete_many({'chat_id': chat_id})
                
                logger.info(f"Deleted ChromaDB collection {collection_name} and {delete_result.deleted_count} MongoDB documents for chat {chat_id}")
                
                return {
                    'success': True,
                    'chat_id': chat_id,
                    'collection_name': collection_name,
                    'mongodb_deleted_count': delete_result.deleted_count,
                    'message': 'Vector database and documents deleted successfully'
                }
                
            except Exception:
                return {
                    'success': False,
                    'chat_id': chat_id,
                    'error': 'Collection not found',
                    'message': 'No vector database found for this chat'
                }
                
        except Exception as e:
            logger.error(f"Error deleting vector database for chat {chat_id}: {str(e)}")
            return {
                'success': False,
                'chat_id': chat_id,
                'error': str(e),
                'message': 'Failed to delete vector database'
            }


# Convenience functions for easy usage
def create_chat_db(chat_id: str) -> Dict[str, Any]:
    """
    Convenience function to create a chat vector database
    
    Args:
        chat_id: Chat ID to create database for
        
    Returns:
        Creation result dictionary
    """
    chroma_utils = ChromaUtils()
    return chroma_utils.create_chat_vector_db(chat_id)


def upload_document_to_chat(chat_id: str, temp_file_path: str, filename: str, 
                          user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to upload and process a document
    
    Args:
        chat_id: Chat ID to upload document to
        temp_file_path: Path to temporary file
        filename: Original filename
        user_id: Optional user ID
        
    Returns:
        Upload result dictionary
    """
    chroma_utils = ChromaUtils()
    return chroma_utils.upload_document(chat_id, temp_file_path, filename, user_id)


def query_documents(chat_id: str, query: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Convenience function to query chat documents
    
    Args:
        chat_id: Chat ID to query
        query: Search query
        n_results: Number of results to return
        
    Returns:
        Query result dictionary
    """
    chroma_utils = ChromaUtils()
    return chroma_utils.query_chat_docs(chat_id, query, n_results)


def get_all_chat_databases() -> Dict[str, Any]:
    """
    Convenience function to get all chat vector databases
    
    Returns:
        Dictionary with all chat databases information
    """
    chroma_utils = ChromaUtils()
    return chroma_utils.get_all_chat_dbs()


# Example usage
if __name__ == "__main__":
    # Example usage of the ChromaUtils
    
    # Initialize utils
    chroma_utils = ChromaUtils()
    
    # Example 1: Create a chat vector database
    chat_id = "test_chat_123"
    result = chroma_utils.create_chat_vector_db(chat_id)
    print("Create DB Result:", result)
    
    # Example 2: Upload a document (assuming you have a PDF file)
    # temp_file_path = "path/to/your/document.pdf"
    # filename = "sample_document.pdf"
    # upload_result = chroma_utils.upload_document(chat_id, temp_file_path, filename)
    # print("Upload Result:", upload_result)
    
    # Example 3: Query documents
    # query = "What are the main legal principles?"
    # query_result = chroma_utils.query_chat_docs(chat_id, query, n_results=3)
    # print("Query Result:", query_result)
    
    # Example 4: Get document info
    # info_result = chroma_utils.get_chat_documents_info(chat_id)
    # print("Document Info:", info_result)