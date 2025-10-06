import os
from flask import Flask
from flask_cors import CORS
from routes.main_router import main_router
from config.mongodb import mongodb_connection, ensure_mongodb_connection
import logging
import atexit

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB connection
try:
    ensure_mongodb_connection()
    logger.info("[App] MongoDB connection pool initialized successfully")
except Exception as e:
    logger.error(f"[App] Failed to initialize MongoDB: {e}")
    # You can choose to exit here or continue without MongoDB
    # raise SystemExit(f"Cannot start application without MongoDB: {e}")

# Register cleanup function
def cleanup():
    """Cleanup function to close MongoDB connection on app shutdown"""
    mongodb_connection.close_connection()
    logger.info("[App] Application cleanup completed")

atexit.register(cleanup)

@app.route('/')
def home():
  return "Hello, this is a Flask app hosted on local WiFi!"

app.register_blueprint(main_router, url_prefix='/api')

if __name__ == '__main__':
  # Use '0.0.0.0' to make the app accessible on the local network
  app.run(host='0.0.0.0', port=os.getenv("SERVER_PORT", 5000) )