"""
Chat API endpoints for managing chats and conversations
"""

import os
import tempfile
import asyncio
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from utils import ChatUtils, UserUtils
from utils.chroma_utils import ChromaUtils
from services.chatbot_service import get_chatbot_service
import logging

# Create a Blueprint for chat routes
chat_apis = Blueprint('chat_apis', __name__)
logger = logging.getLogger(__name__)

# Initialize ChromaUtils
chroma_utils = ChromaUtils()

# Allowed file extensions for document upload
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@chat_apis.route('/chats', methods=['POST'])
def create_chat():
    """Create a new chat for a user (userId in request body) and corresponding vector database"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'userId' not in data:
            return jsonify({'error': 'userId is required in request body'}), 400
        
        user_id = data['userId']
        
        # Validate user exists
        user = UserUtils.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get optional title
        title = data.get('title', 'New Chat')
        
        # Create chat (this will automatically update the user's chats list)
        chat_id = ChatUtils.create_chat(user_id, title)
        
        if chat_id:
            # Also create the ChromaDB vector database for this chat
            chroma_result = chroma_utils.create_chat_vector_db(chat_id)
            
            if chroma_result['success']:
                return jsonify({
                    'message': 'Chat and vector database created successfully',
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'title': title,
                    'vector_db': {
                        'collection_name': chroma_result['collection_name'],
                        'created': chroma_result['created']
                    }
                }), 201
            else:
                # If vector DB creation fails, we should still return success 
                # but warn about the vector DB issue
                logger.warning(f"Chat created but vector DB failed: {chroma_result.get('error', 'Unknown error')}")
                return jsonify({
                    'message': 'Chat created successfully, but vector database setup failed',
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'title': title,
                    'vector_db_warning': chroma_result.get('error', 'Vector DB creation failed')
                }), 201
        else:
            return jsonify({'error': 'Failed to create chat'}), 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error creating chat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>/prompt', methods=['POST'])
def add_prompt_to_chat(chat_id):
    """Add a user prompt to chat and process it with RAG + LLM"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'prompt' not in data:
            return jsonify({'error': 'Prompt is required'}), 400
        
        user_prompt = data['prompt'].strip()
        if not user_prompt:
            return jsonify({'error': 'Prompt cannot be empty'}), 400
        
        # Get optional user_id for additional validation
        user_id = data.get('userId')
        
        # Verify chat exists
        chat = ChatUtils.get_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Process prompt with chatbot service (RAG + LLM workflow)
        try:
            chatbot_service = get_chatbot_service()
            
            # Use asyncio to handle the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response_data = loop.run_until_complete(
                    chatbot_service.process_chat_prompt(chat_id, user_prompt, user_id)
                )
                
                return jsonify({
                    'message': 'Prompt processed successfully with RAG',
                    'chat_id': response_data['chatId'],
                    'prompt': user_prompt,
                    'response': response_data['response'],
                    'citations': response_data['citations'],
                    'context_items_used': response_data['contextUsed'],
                    'history_messages_used': response_data['historyUsed'],
                    'timestamp': response_data['timestamp']
                }), 200
                
            finally:
                loop.close()
                
        except Exception as chatbot_error:
            logger.error(f"[ChatAPI] Chatbot service error: {chatbot_error}")
            
            # Fallback to basic prompt addition without RAG
            logger.info("[ChatAPI] Falling back to basic prompt addition")
            success = ChatUtils.add_prompt_to_chat(chat_id, user_prompt)
            
            if success:
                return jsonify({
                    'message': 'Prompt added successfully (RAG service unavailable)',
                    'chat_id': chat_id,
                    'prompt': user_prompt,
                    'fallback_mode': True,
                    'error': str(chatbot_error)
                }), 200
            else:
                return jsonify({'error': 'Failed to add prompt to chat and RAG service unavailable'}), 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error processing prompt: {e}")
        return jsonify({'error': 'Internal server error'}), 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error adding prompt to chat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>/response', methods=['POST'])
def add_assistant_response(chat_id):
    """Add assistant response to the latest conversation entry in chat"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'response' not in data:
            return jsonify({'error': 'Response is required'}), 400
        
        response = data['response'].strip()
        if not response:
            return jsonify({'error': 'Response cannot be empty'}), 400
        
        # Get optional citations
        citations = data.get('citations', [])
        
        # Verify chat exists
        chat = ChatUtils.get_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Verify chat has conversation history
        if not chat.get('conversation_history'):
            return jsonify({'error': 'No conversation history found. Add a prompt first.'}), 400
        
        # Add assistant response to chat
        success = ChatUtils.add_assistant_response_to_chat(chat_id, response, citations)
        
        if success:
            return jsonify({
                'message': 'Assistant response added successfully',
                'chat_id': chat_id,
                'response': response,
                'citations_count': len(citations)
            }), 200
        else:
            return jsonify({'error': 'Failed to add assistant response to chat'}), 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error adding assistant response: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get chat by ID"""
    try:
        chat = ChatUtils.get_chat(chat_id)
        
        if chat:
            return jsonify({
                'message': 'Chat retrieved successfully',
                'chat': chat
            }), 200
        else:
            return jsonify({'error': 'Chat not found'}), 404
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error getting chat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat"""
    try:
        # Verify chat exists
        chat = ChatUtils.get_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Get user_id from chat to update user's chat list
        user_id = chat.get('userId')
        
        # Delete chat
        success = ChatUtils.delete_chat(chat_id)
        
        if success:
            # Also delete the vector database for this chat
            vector_delete_result = chroma_utils.delete_chat_vector_db(chat_id)
            if not vector_delete_result['success']:
                logger.warning(f"Chat deleted but vector DB cleanup failed: {vector_delete_result.get('error', 'Unknown error')}")
            
            # Remove chat from user's chat list
            if user_id:
                try:
                    from config.mongodb import get_mongodb_collection
                    from bson import ObjectId
                    from datetime import datetime
                    
                    users_collection = get_mongodb_collection('users')
                    users_collection.update_one(
                        {"_id": ObjectId(user_id)},
                        {
                            "$pull": {"chats": chat_id},
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
                except Exception as e:
                    logger.warning(f"[ChatAPI] Failed to update user's chat list after deletion: {e}")
            
            response_data = {
                'message': 'Chat and vector database deleted successfully',
                'chat_id': chat_id
            }
            
            # Add vector DB deletion info if available
            if vector_delete_result['success']:
                response_data['vector_db'] = {
                    'deleted': True,
                    'mongodb_documents_deleted': vector_delete_result.get('mongodb_deleted_count', 0)
                }
            else:
                response_data['vector_db'] = {
                    'deleted': False,
                    'error': vector_delete_result.get('error', 'Unknown error')
                }
            
            return jsonify(response_data), 200
        else:
            return jsonify({'error': 'Failed to delete chat'}), 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error deleting chat: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>/upload', methods=['POST'])
def upload_document_to_chat(chat_id):
    """Upload a document to a specific chat's vector database"""
    try:
        # Verify chat exists
        chat = ChatUtils.get_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed', 
                'allowed_types': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Ensure the uploads directory exists
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Create temporary file in the uploads directory to store the upload
        with tempfile.NamedTemporaryFile(delete=False, dir=uploads_dir, suffix=os.path.splitext(filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Get user_id from chat data for metadata
            user_id = chat.get('userId') if isinstance(chat, dict) else getattr(chat, 'userId', None)
            
            # Upload and process document using ChromaUtils
            upload_result = chroma_utils.upload_document(
                chat_id=chat_id,
                temp_file_path=temp_file_path,
                filename=filename,
                user_id=user_id
            )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            if upload_result['success']:
                return jsonify({
                    'message': 'Document uploaded and processed successfully',
                    'chat_id': chat_id,
                    'document': {
                        'doc_id': upload_result['doc_id'],
                        'filename': upload_result['filename'],
                        'chunks_count': upload_result['chunks_count'],
                        'collection_name': upload_result['collection_name']
                    }
                }), 201
            else:
                return jsonify({
                    'error': 'Failed to upload document',
                    'details': upload_result.get('error', 'Unknown error')
                }), 500
        
        except Exception as e:
            # Clean up temporary file in case of error
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise e
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error uploading document to chat {chat_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>/query', methods=['POST'])
def query_chat_documents(chat_id):
    """Query documents in a chat's vector database"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Get optional parameters
        n_results = data.get('n_results', 5)
        if not isinstance(n_results, int) or n_results < 1 or n_results > 20:
            return jsonify({'error': 'n_results must be an integer between 1 and 20'}), 400
        
        # Verify chat exists
        chat = ChatUtils.get_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Query documents using ChromaUtils
        query_result = chroma_utils.query_chat_docs(chat_id, query, n_results)
        
        if query_result['success']:
            return jsonify({
                'message': 'Query executed successfully',
                'chat_id': chat_id,
                'query': query,
                'results': {
                    'count': query_result['results_count'],
                    'chunks': query_result['relevant_chunks']
                }
            }), 200
        else:
            return jsonify({
                'error': 'Failed to query documents',
                'details': query_result.get('error', 'Unknown error')
            }), 404 if 'not found' in query_result.get('error', '').lower() else 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error querying documents for chat {chat_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/<chat_id>/documents', methods=['GET'])
def get_chat_documents_info(chat_id):
    """Get information about all documents in a chat"""
    try:
        # Verify chat exists
        chat = ChatUtils.get_chat(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Get document information using ChromaUtils
        info_result = chroma_utils.get_chat_documents_info(chat_id)
        
        if info_result['success']:
            return jsonify({
                'message': 'Document information retrieved successfully',
                'chat_id': chat_id,
                'documents_info': {
                    'total_documents': info_result['total_documents'],
                    'total_chunks': info_result['total_chunks'],
                    'documents': info_result['documents'],
                    'collection_name': info_result['collection_name']
                }
            }), 200
        else:
            return jsonify({
                'error': 'Failed to get document information',
                'details': info_result.get('error', 'Unknown error')
            }), 404 if 'not found' in info_result.get('error', '').lower() else 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error getting document info for chat {chat_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/vector-databases', methods=['GET'])
def get_all_chat_vector_databases():
    """Get information about all chat vector databases"""
    try:
        # Get all chat databases using ChromaUtils
        dbs_result = chroma_utils.get_all_chat_dbs()
        
        if dbs_result['success']:
            return jsonify({
                'message': 'Chat vector databases retrieved successfully',
                'total_chat_dbs': dbs_result['total_chat_dbs'],
                'chat_databases': dbs_result['chat_dbs']
            }), 200
        else:
            return jsonify({
                'error': 'Failed to get chat databases',
                'details': dbs_result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        logger.error(f"[ChatAPI] Error getting all chat vector databases: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@chat_apis.route('/chats/health', methods=['GET'])
def chat_health_check():
    """Health check endpoint for chat APIs"""
    return jsonify({
        'status': 'healthy',
        'service': 'chat_apis',
        'endpoints': [
            'POST /chats - Create chat with vector database (userId in body)',
            'POST /chats/{chat_id}/prompt - Add prompt with RAG processing',
            'POST /chats/{chat_id}/response - Add assistant response',
            'GET /chats/{chat_id} - Get chat',
            'DELETE /chats/{chat_id} - Delete chat',
            'POST /chats/{chat_id}/upload - Upload document to chat',
            'POST /chats/{chat_id}/query - Query chat documents',
            'GET /chats/{chat_id}/documents - Get chat documents info',
            'GET /chats/vector-databases - Get all chat vector databases',
            'GET /chats/health - Health check for chatbot service'
        ],
        'features': [
            'Automatic vector database creation',
            'Document upload with RAG processing',
            'Semantic document search',
            'Temporary file handling for uploads',
            'RAG-powered chat responses with LLM integration',
            'Context formatting and token optimization',
            'Automatic citation extraction'
        ]
    }), 200


@chat_apis.route('/chats/health', methods=['GET'])
def chatbot_health_check():
    """Health check for chatbot service components"""
    try:
        chatbot_service = get_chatbot_service()
        health_status = chatbot_service.health_check()
        
        # Determine overall health
        overall_healthy = all([
            health_status.get('chatbot_service', False),
            health_status.get('chroma_db', False),
            health_status.get('mongodb', False)
        ])
        
        status_code = 200 if overall_healthy else 503
        
        return jsonify({
            'message': 'Chatbot service health check',
            'overall_status': 'healthy' if overall_healthy else 'degraded',
            'components': health_status
        }), status_code
        
    except Exception as e:
        logger.error(f"[ChatAPI] Error during health check: {e}")
        return jsonify({
            'message': 'Health check failed',
            'overall_status': 'unhealthy',
            'error': str(e)
        }), 500