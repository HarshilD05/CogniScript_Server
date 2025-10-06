import os
import re
import fitz # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

from langchain_huggingface import HuggingFaceEndpointEmbeddings
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

CHUNK_INFO = {
  'chunk_size': 500,
  'chunk_overlap': 50
}


def extract_text_from_pdf(pdf_path: str) -> str:
  """Extracts all text from a PDF file using PyMuPDF."""
  text = ""
  with fitz.open(pdf_path) as doc:
    for page in doc:
      text += page.get_text()
  return text


def clean_text(text: str) -> str:
  """Cleans text by removing multiple spaces, newlines, and repeated punctuation patterns."""
  # Remove lines with only dots, dashes, or underscores
  text = re.sub(r'\n[\.\-_ ]{5,}\n', '\n', text)
  # Remove all occurrences of long runs of dots, dashes, underscores
  text = re.sub(r'[.\-_]{2,}', ' ', text)
  # Replace multiple newlines with a single newline
  text = re.sub(r'\n+', '\n', text)
  # Replace multiple spaces with a single space
  text = re.sub(r' +', ' ', text)
  return text.strip()


def chunk_text(text: str, chunk_size: int = CHUNK_INFO.get('chunk_size'), chunk_overlap: int = CHUNK_INFO.get('chunk_overlap') ) -> list:
  """Splits text into chunks with overlap using langchain's RecursiveCharacterTextSplitter (token-based)."""
  # Use Pretrained tokenizer for token counting
  tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

  splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    tokenizer=tokenizer,
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
    separators=["\n\n", "\n", ". ", " ", ""],
    keep_separator=False
  )
  return splitter.split_text(text)


class DocProcessor : 
  def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    self._embedding_model = embedding_model
    self._embedder = HuggingFaceEndpointEmbeddings(
      model=self._embedding_model
    )

  def embed_text(self, text: str) -> list:
    embedding = self._embedder.embed_query(text)
    if not embedding:
      raise ValueError("Embedding failed, check the model and API key.")
    return embedding


if __name__ == "__main__":
  # Example usage and test
  upload_folder = os.path.join(os.path.dirname(__file__), "..", "uploads")
  file_name = "Constitution_Of_India.pdf"  # Change to your test PDF file
  pdf_path = os.path.join(upload_folder, file_name)
  
  # print(f"Extracting text from: {pdf_path}")
  # text = extract_text_from_pdf(pdf_path)

  # # Store extracted text in a File
  txt_file_path = pdf_path.replace('.pdf', '.txt')
  
  # with open(txt_file_path, 'w', encoding='utf-8') as f :
  #     f.write(text)

  # print("Text extraction complete. File saved at:", txt_file_path)
    
  
  clean_path = txt_file_path.replace('.txt', '_cleaned.txt')
  # cleaned = clean_text(text)
  # with open(clean_path, 'w', encoding='utf-8') as f : 
  #   f.write(cleaned)
  
  # with open(clean_path, 'r', encoding='utf-8') as f:
  #   cleaned = f.read()

  chunks_path = txt_file_path.replace('.txt', '_chunks.txt')
  # chunks = recursive_text_chunking(cleaned, chunk_size=230, chunk_overlap=23)
  # with open(chunks_path, 'w', encoding='utf-8') as f : 
  #   for i, chunk in enumerate(chunks):
  #     f.write(f"Chunk {i+1}:\n{chunk}\n\n")
  # print(f"Text cleaned and chunked. Chunks saved at: {chunks_path}")
      
  with open(chunks_path, 'r', encoding='utf-8') as f:
    chunk_text = f.read()

  chunks = re.split(r'Chunk \d+:', chunk_text)  # Splitting at "Chunk $:" where $ is a number
  chunks = [chunk.strip() for chunk in chunks]  # Remove empty chunks and strip whitespace

  # Embedding test (requires OpenAI API key)
  try:
    processor = DocProcessor()
    emb = processor.embed_text(chunks[0])
    print(f"\n--- Embedding Vector Length: {len(emb)} ---\n", emb[:10], "...")
  except Exception as e:
    print("\n[Embedding Error]", e)
