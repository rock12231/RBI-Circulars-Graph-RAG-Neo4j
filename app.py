import streamlit as st
from src.retrieval.rag import query_rag
from src.utils import config
from src.ingestion.ingest import ingest_data
import subprocess
from qdrant_client import QdrantClient
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="RBI Circulars AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Title and Description ---
st.title("🤖 RBI Circulars AI Assistant")
st.markdown("Ask any question about the 2024 RBI circulars, and I will find the answer for you.")
st.markdown("---")

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

# --- Qdrant Connection Status ---
def check_qdrant_connection(max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        try:
            client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT,
                check_compatibility=False,
                timeout=10.0
            )
            # Test connection by getting collections
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            return True, collection_names
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return False, str(e)
    return False, "Max retries exceeded"

# Create three columns for the status indicator
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### System Status")
    
    # Display connection status with retry button
    qdrant_status, collections = check_qdrant_connection()
    
    if qdrant_status:
        st.success("✅ Qdrant Connection: Active")
        if collections:
            st.info(f"Available Collections: {', '.join(collections)}")
        else:
            st.warning("No collections found. Please create embeddings.")
    else:
        st.error("❌ Qdrant Connection: Failed")
        st.error(f"Error: {collections}")
        
        # Add retry button
        if st.button("🔄 Retry Connection"):
            st.rerun()

# --- Main Content ---
# Create three columns for the buttons
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Create Embeddings Button
    if st.button("🔄 Create Embeddings", use_container_width=True):
        with st.spinner("Creating embeddings..."):
            try:
                ingest_data()
                st.success("✅ Embeddings created successfully!")
                st.rerun()  # Refresh to show new collections
            except Exception as e:
                st.error(f"❌ Error creating embeddings: {str(e)}")
        
    # Chat with Data Button - Only show if collections exist
    if qdrant_status and collections:
        if st.button("💬 Chat with Data", use_container_width=True):
            st.session_state.show_chat = not st.session_state.show_chat
    elif qdrant_status and not collections:
        st.warning("⚠️ Please create embeddings before starting a chat")

# --- Chat Interface ---
if st.session_state.show_chat:
    st.markdown("---")
    st.markdown("### Chat Interface")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                st.markdown(message["sources"])

    # Chat input
    if prompt := st.chat_input("Ask a question about RBI circulars..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response, sources = query_rag(prompt)
                    st.markdown(response)
                    st.markdown(sources)
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Sorry, an error occurred: {e}"
                    }) 