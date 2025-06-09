import os
from dotenv import load_dotenv

load_dotenv()

# --- Environment Variables ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Qdrant Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "fd98050b-4928-44e1-9536-66478313e9c5.us-west-1-0.aws.cloud.qdrant.io")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.3IUWpp8_yI-KDupXQzyBbkCnFDnP92hzWBO4uWqtq0M")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rbi_circulars")

# --- Gemini Configuration ---
GEMINI_GENERATION_MODEL = "gemini-2.0-flash"

# --- Data Configuration ---
DATA_PATH = os.getenv("DATA_PATH", "data/rbi_circulars.json")

# --- Neo4j Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://8f889fdf.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "BIcxg-LSb4Z9t8HGfJ6OJP1Ju1BzLrTfnGO4ZedDPjQ") 
