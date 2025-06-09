import os
from dotenv import load_dotenv

load_dotenv()

# --- Environment Variables ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Qdrant Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")  # Use the Docker service name
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION_NAME = "rbi_circulars"

# --- Gemini Configuration ---
GEMINI_GENERATION_MODEL = "gemini-1.5-flash"

# --- Data Configuration ---
DATA_PATH = "data/rbi_circulars.json" 