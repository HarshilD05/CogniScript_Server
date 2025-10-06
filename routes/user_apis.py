"""
User API endpoints for managing users
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from utils import UserUtils
from models import UserModel
import logging

# Create a Blueprint for user routes
user_apis = Blueprint('user_apis', __name__)
logger = logging.getLogger(__name__)


@user_apis.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'email' not in data or 'user_type' not in data:
            return jsonify({'error': 'email and user_type are required'}), 400
        
        # Validate data using Pydantic model
        try:
            user_model = UserModel(
                email=data['email'],
                user_type=data['user_type'],
                chats=[]
            )
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
        
        # Check if user already exists
        existing_user = UserUtils.get_user_by_email(data['email'])
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create user
        user_id = UserUtils.create_user(data['email'], data['user_type'])
        
        if user_id:
            return jsonify({
                'message': 'User created successfully',
                'user_id': user_id,
                'email': data['email'],
                'user_type': data['user_type']
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        logger.error(f"[UserAPI] Error creating user: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@user_apis.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    try:
        user = UserUtils.get_user(user_id)
        
        if user:
            return jsonify({
                'message': 'User retrieved successfully',
                'user': user
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"[UserAPI] Error getting user: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@user_apis.route('/users/<user_id>/chats', methods=['GET'])
def get_user_chats(user_id):
    """Get all chats for a user"""
    try:
        # Validate user exists
        user = UserUtils.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pagination parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        skip = int(request.args.get('skip', 0))
        
        from utils import ChatUtils
        chats = ChatUtils.get_user_chats(user_id, limit, skip)
        
        return jsonify({
            'message': 'User chats retrieved successfully',
            'user_id': user_id,
            'chats': chats,
            'count': len(chats),
            'limit': limit,
            'skip': skip
        }), 200
        
    except Exception as e:
        logger.error(f"[UserAPI] Error getting user chats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@user_apis.route('/users/email/<email>', methods=['GET'])
def get_user_by_email(email):
    """Get user by email"""
    try:
        user = UserUtils.get_user_by_email(email)
        
        if user:
            return jsonify({
                'message': 'User retrieved successfully',
                'user': user
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        logger.error(f"[UserAPI] Error getting user by email: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@user_apis.route('/users/health', methods=['GET'])
def user_health_check():
    """Health check endpoint for user APIs"""
    return jsonify({
        'status': 'healthy',
        'service': 'user_apis',
        'endpoints': [
            'POST /users - Create user',
            'GET /users/{user_id} - Get user by ID',
            'GET /users/{user_id}/chats - Get user chats',
            'GET /users/email/{email} - Get user by email'
        ]
    }), 200