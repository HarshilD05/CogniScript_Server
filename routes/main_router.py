from flask import Blueprint
from routes.doc_apis import doc_apis
from routes.chat_apis import chat_apis
from routes.user_apis import user_apis

main_router = Blueprint('main_router', __name__)

# Register blueprints without URL prefixes (routes defined in individual files)
main_router.register_blueprint(doc_apis)
main_router.register_blueprint(chat_apis)
main_router.register_blueprint(user_apis)