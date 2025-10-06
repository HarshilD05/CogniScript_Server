from flask import Blueprint, request, jsonify
import os
import tempfile
from utils.doc_utils import (
    extract_text_from_pdf,
    clean_text,
    chunk_text,
    DocProcessor
)

# Create a Blueprint for the routes
doc_apis = Blueprint('doc_apis', __name__)

# Initialize the document processor
doc_processor = DocProcessor()

ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@doc_apis.route('/extract-text', methods=['POST'])
def extract_text():
    """Extract text from uploaded PDF file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                file.save(temp_file.name)

                # Extract text
                extracted_text = extract_text_from_pdf(temp_file.name)

                # Clean up temporary file
                os.unlink(temp_file.name)

                return jsonify({
                    'message': 'Text extracted successfully',
                    'text': extracted_text,
                    'filename': file.filename,
                    'text_length': len(extracted_text)
                }), 200
        else:
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doc_apis.route('/clean-text', methods=['POST'])
def clean_text_endpoint():
    """Clean text by removing multiple spaces, newlines, and repeated punctuation"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']
        cleaned_text = clean_text(text)

        return jsonify({
            'message' : 'Text cleaned successfully',
            'original_text': text,
            'cleaned_text': cleaned_text,
            'original_length': len(text),
            'cleaned_length': len(cleaned_text)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doc_apis.route('/chunk-text', methods=['POST'])
def chunk_text_endpoint():
    """Split text into chunks with overlap using recursive character text splitter"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']
        chunk_size = data.get('chunk_size', 500)
        chunk_overlap = data.get('chunk_overlap', 50)

        chunks = chunk_text(text, chunk_size, chunk_overlap)

        return jsonify({
            'chunks': chunks,
            'total_chunks': len(chunks),
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'original_text_length': len(text)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doc_apis.route('/embed-text', methods=['POST'])
def embed_text():
    """Generate embeddings for text using HuggingFace model"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']

        # Generate embedding
        embedding = doc_processor.embed_text(text)

        return jsonify({
            'text': text,
            'embedding': embedding,
            'embedding_length': len(embedding)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doc_apis.route('/embed-chunks', methods=['POST'])
def embed_chunks():
    """Generate embeddings for multiple text chunks"""
    try:
        data = request.get_json()
        if not data or 'chunks' not in data:
            return jsonify({'error': 'No chunks provided'}), 400

        chunks = data['chunks']
        if not isinstance(chunks, list):
            return jsonify({'error': 'Chunks must be a list'}), 400

        embeddings = []
        for i, chunk in enumerate(chunks):
            try:
                embedding = doc_processor.embed_text(chunk)
                embeddings.append({
                    'chunk_index': i,
                    'text': chunk,
                    'embedding': embedding
                })
            except Exception as e:
                embeddings.append({
                    'chunk_index': i,
                    'text': chunk,
                    'embedding': None,
                    'error': str(e)
                })

        return jsonify({
            'embeddings': embeddings,
            'total_chunks': len(chunks),
            'successful_embeddings': len([e for e in embeddings if 'embedding' in e])
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
