import json
import uuid
from qdrant_client import QdrantClient, models
import google.generativeai as genai
from src.utils import config
import time
import sys

def ingest_data():
    """
    Reads data, creates embeddings, and upserts them into Qdrant.
    """
    print("--- Starting Data Ingestion ---")
    print(f"Python version: {sys.version}")
    print(f"Environment variables:")
    print(f"QDRANT_HOST: {config.QDRANT_HOST}")
    print(f"QDRANT_PORT: {config.QDRANT_PORT}")
    print(f"GOOGLE_API_KEY: {'Set' if config.GOOGLE_API_KEY else 'Not Set'}")

    # --- 1. Initialize Clients ---
    try:
        print(f"\nConnecting to Qdrant at {config.QDRANT_HOST}:{config.QDRANT_PORT}...")
        qdrant_client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT,
            timeout=10.0  # Add timeout
        )
        
        # Test connection
        try:
            collections = qdrant_client.get_collections()
            print("Successfully connected to Qdrant")
            print(f"Available collections: {[c.name for c in collections.collections]}")
        except Exception as e:
            print(f"Error testing Qdrant connection: {e}")
            raise
        
        if not config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in environment variables")
            
        genai.configure(api_key=config.GOOGLE_API_KEY)
        print("Successfully configured Gemini API")
    except Exception as e:
        print(f"Error initializing clients: {e}")
        return

    # --- 2. Create Qdrant Collection ---
    try:
        print(f"\nCreating collection '{config.QDRANT_COLLECTION_NAME}'...")
        
        # Check if collection exists
        try:
            collections = qdrant_client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            print(f"Existing collections: {collection_names}")
        except Exception as e:
            print(f"Error getting collections: {e}")
            raise
        
        if config.QDRANT_COLLECTION_NAME in collection_names:
            print(f"Collection '{config.QDRANT_COLLECTION_NAME}' already exists. Recreating...")
            try:
                qdrant_client.delete_collection(collection_name=config.QDRANT_COLLECTION_NAME)
                print("Successfully deleted existing collection")
                time.sleep(1)  # Wait for deletion to complete
            except Exception as e:
                print(f"Error deleting collection: {e}")
                raise
        
        # Create new collection
        try:
            qdrant_client.create_collection(
                collection_name=config.QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
            )
            print(f"Collection '{config.QDRANT_COLLECTION_NAME}' created successfully")
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
        
        # Verify collection was created
        try:
            collections = qdrant_client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            if config.QDRANT_COLLECTION_NAME not in collection_names:
                raise Exception(f"Collection '{config.QDRANT_COLLECTION_NAME}' was not created successfully")
            print(f"Verified collection exists: {config.QDRANT_COLLECTION_NAME}")
        except Exception as e:
            print(f"Error verifying collection: {e}")
            raise
            
    except Exception as e:
        print(f"Error in collection creation process: {e}")
        return

    # --- 3. Load and Process Data ---
    print(f"\nLoading data from {config.DATA_PATH}...")
    try:
        with open(config.DATA_PATH, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded data file with {len(data.get('circulars', []))} circulars")
    except Exception as e:
        print(f"Error loading data file: {e}")
        return

    points_to_upsert = []
    for circular in data['circulars']:
        for section in circular['details']['circular']['contentSections']:
            content = section.get('content', '').strip()
            if not content:
                continue

            # Create a meaningful document chunk with metadata
            document_chunk = (
                f"Circular Number: {circular['Circular Number']}\n"
                f"Subject: {circular['Subject']}\n"
                f"Section: {section.get('title', 'N/A')}\n\n"
                f"{content}"
            )
            
            points_to_upsert.append({
                "chunk": document_chunk,
                "metadata": {
                    "circular_number": circular['Circular Number'],
                    "subject": circular['Subject'],
                    "date_of_issue": circular['Date Of Issue'],
                    "source_link": circular['link']
                }
            })
    
    print(f"Processed {len(points_to_upsert)} text chunks.")

    # --- 4. Generate Embeddings and Upsert to Qdrant ---
    print("\nGenerating embeddings and upserting to Qdrant...")
    try:
        # Get embeddings in a batch
        text_chunks = [p['chunk'] for p in points_to_upsert]
        embeddings = []
        
        # Process embeddings in smaller batches to avoid rate limits
        batch_size = 5  # Reduced batch size for better error handling
        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1} of {(len(text_chunks) + batch_size - 1)//batch_size}")
            
            for j, text in enumerate(batch):
                try:
                    print(f"Generating embedding for chunk {i + j + 1} of {len(text_chunks)}")
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=text,
                        task_type="retrieval_document"
                    )
                    
                    if not result or "embedding" not in result:
                        raise ValueError(f"Invalid embedding result for chunk {i + j + 1}")
                        
                    embedding = result["embedding"]
                    if not isinstance(embedding, list) or len(embedding) != 768:
                        raise ValueError(f"Invalid embedding format for chunk {i + j + 1}")
                        
                    embeddings.append(embedding)
                    print(f"Successfully generated embedding for chunk {i + j + 1}")
                    
                except Exception as e:
                    print(f"Error generating embedding for chunk {i + j + 1}: {e}")
                    raise  # Re-raise to stop the process

        print(f"\nSuccessfully generated {len(embeddings)} embeddings")

        # Verify we have embeddings for all chunks
        if len(embeddings) != len(points_to_upsert):
            raise ValueError(f"Number of embeddings ({len(embeddings)}) doesn't match number of chunks ({len(points_to_upsert)})")

        # Upsert points with embeddings
        print(f"\nUpserting {len(embeddings)} points to Qdrant...")
        points = []
        for point, embedding in zip(points_to_upsert, embeddings):
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": point["chunk"],
                        "metadata": point["metadata"]
                    }
                )
            )

        # Upsert in smaller batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            print(f"Upserting batch {i//batch_size + 1} of {(len(points) + batch_size - 1)//batch_size}")
            try:
                qdrant_client.upsert(
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    points=batch,
                    wait=True
                )
                print(f"Successfully upserted batch {i//batch_size + 1}")
            except Exception as e:
                print(f"Error upserting batch {i//batch_size + 1}: {e}")
                raise
        
        # Verify points were added
        try:
            collection_info = qdrant_client.get_collection(config.QDRANT_COLLECTION_NAME)
            print(f"\nCollection info: {collection_info}")
            print("--- Ingestion Complete ---")
        except Exception as e:
            print(f"Error getting collection info: {e}")
            raise

    except Exception as e:
        print(f"An error occurred during embedding or upserting: {e}")
        raise  # Re-raise to see the full traceback

if __name__ == "__main__":
    ingest_data() 