from qdrant_client import QdrantClient
import google.generativeai as genai
from src.utils import config

# --- Initialize Clients (globally for efficiency) ---
qdrant_client = QdrantClient(
    host=config.QDRANT_HOST or "localhost",
    port=config.QDRANT_PORT,
    check_compatibility=False
)
genai.configure(api_key=config.GOOGLE_API_KEY)
generation_model = genai.GenerativeModel(config.GEMINI_GENERATION_MODEL)

def query_rag(query: str) -> tuple[str, str]:
    """
    Queries the RAG system.
    1. Embeds the query.
    2. Searches Qdrant for relevant context.
    3. Generates a response using Gemini.
    """
    # 1. Embed the query
    embedding_result = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )
    query_embedding = embedding_result["embedding"]

    # 2. Search Qdrant
    search_results = qdrant_client.search(
        collection_name=config.QDRANT_COLLECTION_NAME,
        query_vector=query_embedding,
        limit=3,  # Retrieve top 3 most relevant chunks
        with_payload=True
    )

    # 3. Construct Context and Sources
    context = ""
    sources = []
    for result in search_results:
        context += result.payload['text'] + "\n\n---\n\n"
        sources.append({
            "subject": result.payload['metadata']['subject'],
            "link": result.payload['metadata']['source_link']
        })

    # Deduplicate sources
    unique_sources = [dict(t) for t in {tuple(d.items()) for d in sources}]

    # 4. Generate Response using a detailed prompt
    prompt = f"""
    You are an expert financial analyst specializing in RBI regulations.
    Your task is to answer the user's question based *only* on the provided context.
    Do not use any external knowledge. If the context does not contain the answer,
    clearly state that the information is not available in the provided documents.

    CONTEXT:
    {context}

    QUESTION:
    {query}

    ANSWER:
    """

    response = generation_model.generate_content(prompt)
    
    # Format sources for display
    sources_text = "\n\n**Sources:**\n"
    for src in unique_sources:
        sources_text += f"- [{src['subject']}]({src['link']})\n"

    return response.text, sources_text 