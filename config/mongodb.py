import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# MongoDB Configuration
CONFIG = {
    "MONGODB_USERNAME": quote_plus(os.getenv('MONGODB_USERNAME', '') ),
    "MONGODB_PASSWORD": quote_plus(os.getenv('MONGODB_PASSWORD', '') ),
    "MONGODB_CLUSTER_NAME": os.getenv('MONGODB_CLUSTER_NAME'),
    "MONGODB_CLUSTER_ID": os.getenv('MONGODB_CLUSTER_ID'),
    "MONGODB_DATABASE": os.getenv('MONGODB_DATABASE'),
}

for param, value in CONFIG.items():
    if value is None or value == '':
        raise ValueError(f"[MongoDB] Environment variable '{param}' is missing or empty. Please provide a correct field value.")


MONGODB_URL = f"mongodb+srv://{CONFIG['MONGODB_USERNAME']}:{CONFIG['MONGODB_PASSWORD']}@{CONFIG['MONGODB_CLUSTER_NAME'].lower()}.{CONFIG['MONGODB_CLUSTER_ID']}.mongodb.net/?retryWrites=true&w=majority&appName={CONFIG['MONGODB_CLUSTER_NAME']}"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 

class MongoDBConnection:
    """MongoDB Connection Pool Manager"""
    
    _instance = None
    _client = None
    _database = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one connection pool"""
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB connection pool"""
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB with connection pooling"""
        try:
            self._client = MongoClient(
                MONGODB_URL,
                retryWrites=True,
                w='majority'  # Write concern
            )
            
            # Test the connection
            self._client.admin.command('ping')
            logger.info(f"[MongoDB] Successfully connected to MongoDB !")
            
            # Set database
            self._database = self._client[CONFIG['MONGODB_DATABASE'] ]
            logger.info(f"[MongoDB] Using database: {CONFIG['MONGODB_DATABASE']}")
            
        except ConnectionFailure as e:
            logger.error(f"[MongoDB] Failed to connect to MongoDB: {e}")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"[MongoDB] Server selection timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"[MongoDB] Unexpected error during connection: {e}")
            raise
    
    def get_client(self):
        """Get MongoDB client"""
        if self._client is None:
            self._connect()
        return self._client
    
    def get_database(self):
        """Get MongoDB database"""
        if self._database is None:
            self._connect()
        return self._database
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        return self.get_database()[collection_name]
    
    def test_connection(self):
        """Test MongoDB connection"""
        try:
            self.get_client().admin.command('ping')
            return True, "MongoDB connection is healthy"
        except Exception as e:
            return False, str(e)
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("[MongoDB] Connection closed")
    
    def get_server_info(self):
        """Get MongoDB server information"""
        try:
            return self.get_client().server_info()
        except Exception as e:
            logger.error(f"[MongoDB] Error getting server info: {e}")
            return None
    
    def list_collections(self):
        """List all collections in the database"""
        try:
            return self.get_database().list_collection_names()
        except Exception as e:
            logger.error(f"[MongoDB] Error listing collections: {e}")
            return []

# Global MongoDB connection instance
mongodb_connection = MongoDBConnection()

def get_mongodb_client():
    """Get MongoDB client instance"""
    return mongodb_connection.get_client()

def get_mongodb_database():
    """Get MongoDB database instance"""
    return mongodb_connection.get_database()

def get_mongodb_collection(collection_name):
    """Get MongoDB collection instance"""
    return mongodb_connection.get_collection(collection_name)

def ensure_mongodb_connection():
    """Ensure MongoDB connection is established"""
    try:
        is_healthy, message = mongodb_connection.test_connection()
        if is_healthy:
            logger.info(f"[MongoDB] Connection verified: {message}")
        else:
            logger.error(f"[MongoDB] Connection failed: {message}")
            raise ConnectionError(message)
    except Exception as e:
        logger.error(f"[MongoDB] Error ensuring connection: {e}")
        raise

# Initialize connection when module is imported
try:
    ensure_mongodb_connection()
except Exception as e:
    logger.warning(f"[MongoDB] Failed to initialize connection on import: {e}")
    logger.warning("[MongoDB] Connection will be retried when needed")