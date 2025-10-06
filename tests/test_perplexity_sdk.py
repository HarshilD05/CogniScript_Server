"""
Test script for the new Perplexity SDK implementation
Run this script to test if the SDK integration works correctly
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.perplexity_llm import PerplexityLLM

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_perplexity_sdk():
    """Test the Perplexity SDK implementation"""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Check if API key is available
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            print("❌ PERPLEXITY_API_KEY not found in environment variables")
            print("   Please add your API key to the .env file")
            print("   Get your key from: https://perplexity.ai/account/api")
            return False
        
        print("🔑 API key found, initializing PerplexityLLM...")
        
        # Initialize the LLM
        llm = PerplexityLLM()
        print("✅ PerplexityLLM initialized successfully")
        
        # Test health check
        print("🏥 Running health check...")
        health = llm.health_check()
        print(f"   Health status: {health.get('status', 'unknown')}")
        print(f"   API accessible: {health.get('api_accessible', False)}")
        print(f"   Available models: {health.get('available_models', [])}")
        
        if health.get('status') != 'healthy':
            print(f"❌ Health check failed: {health.get('error', 'Unknown error')}")
            return False
        
        # Test basic generation
        print("🤖 Testing basic generation...")
        basic_response = llm.generate(
            prompt="What is artificial intelligence?",
            max_tokens=100
        )
        print(f"✅ Basic generation successful!")
        print(f"   Response length: {len(basic_response)} characters")
        print(f"   Response preview: {basic_response[:100]}...")
        
        # Test context-based generation
        print("🔍 Testing RAG context generation...")
        test_context = [
            {
                "document": "AI_Guide.pdf",
                "text": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans."
            }
        ]
        
        test_history = [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is a subset of AI that focuses on algorithms that can learn from data."}
        ]
        
        context_response = llm.generate_with_context(
            prompt="Based on the context, explain the difference between AI and machine learning.",
            context=test_context,
            history=test_history,
            max_tokens=150
        )
        
        print(f"✅ Context generation successful!")
        print(f"   Response length: {len(context_response)} characters")
        print(f"   Response preview: {context_response[:100]}...")
        
        # Test streaming (if needed)
        print("🌊 Testing streaming generation...")
        stream_chunks = []
        for chunk in llm.generate_stream(
            prompt="Briefly explain quantum computing.",
            max_tokens=50
        ):
            stream_chunks.append(chunk)
            if len(''.join(stream_chunks)) > 50:  # Limit for testing
                break
        
        streamed_response = ''.join(stream_chunks)
        print(f"✅ Streaming generation successful!")
        print(f"   Streamed {len(stream_chunks)} chunks")
        print(f"   Response preview: {streamed_response}...")
        
        print("\n🎉 All tests passed! The Perplexity SDK implementation is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure to install the perplexityai package:")
        print("   pip install perplexityai")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Perplexity SDK Integration")
    print("=" * 50)
    
    success = test_perplexity_sdk()
    
    if success:
        print("\n✅ Integration test completed successfully!")
        print("Your LawLibra RAG Server is ready to use the official Perplexity SDK.")
    else:
        print("\n❌ Integration test failed.")
        print("Please check the error messages above and fix any issues.")
    
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set your PERPLEXITY_API_KEY in the .env file")
    print("3. Run the server: python app.py")
    print("4. Test the chat endpoint: POST /chats/{chat_id}/prompt")