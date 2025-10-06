import os

CHROMA_DB_PATH = os.path.join(os.getcwd(), "chromaDB")

def ensure_chroma_db_folder():
	"""Ensure the ChromaDB folder exists."""
	if not os.path.exists(CHROMA_DB_PATH):
		os.makedirs(CHROMA_DB_PATH)
		print(f"[ChromaDB] Created ChromaDB folder at: {CHROMA_DB_PATH}")

	else:
		print(f"[ChromaDB] ChromaDB folder exists at: {CHROMA_DB_PATH}")

ensure_chroma_db_folder()