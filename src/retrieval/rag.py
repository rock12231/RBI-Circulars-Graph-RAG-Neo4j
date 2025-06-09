from qdrant_client import QdrantClient
import google.generativeai as genai
from src.utils import config

# --- Initialize Clients (globally for efficiency) ---
qdrant_client = QdrantClient(
    host=config.QDRANT_HOST,
    port=config.QDRANT_PORT,
    api_key=config.QDRANT_API_KEY
)
genai.configure(api_key=config.GOOGLE_API_KEY)
generation_model = genai.GenerativeModel(config.GEMINI_GENERATION_MODEL)

def format_sources(sources):
    """Format sources into a readable markdown string."""
    if not sources:
        return ""
    
    formatted = "\n\n**📚 Sources:**\n"
    for i, src in enumerate(sources, 1):
        formatted += f"{i}. [{src['subject']}]({src['link']})\n"
    return formatted

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
        limit=5,  # Increased to 5 for better context
        with_payload=True,
        score_threshold=0.7  # Only include highly relevant results
    )

    # 3. Construct Context and Sources
    context = ""
    sources = []
    seen_subjects = set()  # To avoid duplicate sources
    
    for result in search_results:
        # Add context with clear separation
        context += f"---\n{result.payload['text']}\n\n"
        
        # Add source if not already included
        subject = result.payload['metadata']['subject']
        if subject not in seen_subjects:
            sources.append({
                "subject": subject,
                "link": result.payload['metadata']['source_link']
            })
            seen_subjects.add(subject)

    # 4. Generate Response using a detailed prompt
    prompt = f"""
    You are an expert financial analyst specializing in RBI regulations and circulars.
    Your task is to provide a clear, accurate, and well-structured response based ONLY on the provided context.
    
    Guidelines:
    1. Use ONLY the information from the provided context
    2. If the context doesn't contain the answer, clearly state that
    3. Structure your response with clear sections and bullet points where appropriate
    4. Include relevant dates, circular numbers, and specific details
    5. Be precise and professional in your language
    6. If there are multiple relevant points, organize them clearly
    
    CONTEXT:
    {context}
    
    QUESTION:
    {query}
    
    Please provide a well-structured response that directly addresses the question.
    """

    response = generation_model.generate_content(prompt)
    
    # Format the response with sources
    formatted_response = response.text
    formatted_sources = format_sources(sources)
    
    return formatted_response, formatted_sources 