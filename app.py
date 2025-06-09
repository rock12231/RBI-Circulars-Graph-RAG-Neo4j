import streamlit as st
from src.retrieval.rag import query_rag
from src.utils import config
from src.ingestion.ingest import ingest_data
import subprocess
from qdrant_client import QdrantClient
import time
import json
from src.utils.neo4j_utils import Neo4jConnection, visualize_chat_graph

# --- Page Config ---
st.set_page_config(
    page_title="RBI Circulars AI Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for smooth UI ---
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --error-color: #d62728;
        --background-color: #f8f9fa;
        --sidebar-bg: #f0f2f6;
        --card-bg: #ffffff;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--sidebar-bg);
    }
    
    .sidebar .sidebar-content {
        background-color: var(--sidebar-bg);
    }
    
    /* Custom styling for buttons */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Status cards styling */
    .status-card {
        background: var(--card-bg);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Chat message styling */
    .chat-container {
        background: var(--card-bg);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Animated loading */
    .loading-animation {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    /* Gradient text */
    .gradient-text {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Info cards */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Footer styling */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Link styling */
    .link-card {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .link-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border-color: #667eea;
    }
    
    .link-card a {
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
    }
    
    .link-card a:hover {
        color: #764ba2;
    }
    
    /* System info styling */
    .system-info {
        background: var(--card-bg);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
    }
    
    .system-info-item {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
    }
    
    .system-info-item i {
        margin-right: 0.5rem;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

if "connection_status" not in st.session_state:
    st.session_state.connection_status = None

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"

# --- Header with gradient text ---
st.markdown('<h1 class="gradient-text">🏦 RBI Circulars AI Assistant</h1>', unsafe_allow_html=True)

# --- Info Card ---
st.markdown("""
<div class="info-card">
    <h3>🤖 Intelligent RBI Circular Assistant</h3>
    <p>Get instant answers to your questions about RBI regulations, circulars, and guidelines. 
    Powered by advanced AI and real-time data retrieval.</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar for System Information ---
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2>🔧 System Dashboard</h2>
        <p style="color: #666; font-size: 0.9rem;">Monitor system status and access quick actions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Connection Status in Sidebar
    def check_qdrant_connection():
        """Check Qdrant connection and return status with collections"""
        try:
            # Initialize Qdrant client with cloud configuration
            qdrant_client = QdrantClient(
                url=config.QDRANT_HOST,
                api_key=config.QDRANT_API_KEY,
                timeout=10.0
            )
            
            # Test connection by getting collections
            collections = qdrant_client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            return True, collection_names
        except Exception as e:
            return False, str(e)
    
    # Check connection with spinner
    with st.spinner("Checking system status..."):
        qdrant_status, collections = check_qdrant_connection()
    
    # Display status with colored indicators
    st.markdown("### 📊 System Status")
    if qdrant_status:
        st.success("🟢 Qdrant Connected")
        if collections:
            st.info(f"📚 Collections: {len(collections)}")
            for collection in collections:
                st.text(f"  • {collection}")
        else:
            st.warning("⚠️ No collections found")
    else:
        st.error("🔴 Qdrant Disconnected")
        st.error(f"Error: {collections}")
    
    st.markdown("---")
    
    # System Info
    st.markdown("### 📈 System Info")
    st.markdown("""
    <div class="system-info">
        <div class="system-info-item">
            <i>🌐</i> <span>Host: {}</span>
        </div>
        <div class="system-info-item">
            <i>🔌</i> <span>Port: {}</span>
        </div>
        <div class="system-info-item">
            <i>🔑</i> <span>API: {}</span>
        </div>
    </div>
    """.format(
        config.QDRANT_HOST,
        config.QDRANT_PORT,
        "✅" if config.GOOGLE_API_KEY else "❌"
    ), unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

# Initialize Neo4j connection
neo4j_conn = Neo4jConnection(
    config.NEO4J_URI,
    config.NEO4J_USERNAME,
    config.NEO4J_PASSWORD
)

# --- Main Content Area ---
# Create tabs for better organization
if st.session_state.active_tab == "Chat":
    tab1, tab2 = st.tabs(["🏠 Dashboard", "💬 Chat Interface"])
    selected_tab = tab2
else:
    tab1, tab2 = st.tabs(["🏠 Dashboard", "💬 Chat Interface"])
    selected_tab = tab1

with tab1:
    # Action Buttons in Dashboard
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🎯 Actions")
        
        # Create Embeddings Button with progress
        if st.button("🚀 Create Embeddings", use_container_width=True, type="primary"):
            # Create expander for progress
            with st.expander("📊 Embedding Creation Progress", expanded=True):
                # Create containers for progress display
                progress_container = st.container()
                status_container = st.container()
                log_container = st.container()
                
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                with log_container:
                    log_area = st.empty()
                    log_text = ""
                
                try:
                    # Initialize progress
                    status_text.text("🔄 Initializing...")
                    progress_bar.progress(25)
                    time.sleep(0.5)
                    
                    # Create a custom stream to capture output
                    class StreamToUI:
                        def __init__(self, container):
                            self.container = container
                            self.buffer = []
                        
                        def write(self, text):
                            self.buffer.append(text)
                            if len(self.buffer) > 10:  # Keep last 10 lines
                                self.buffer.pop(0)
                            self.container.text("\n".join(self.buffer))
                        
                        def flush(self):
                            pass
                    
                    # Redirect stdout to our custom stream
                    import sys
                    original_stdout = sys.stdout
                    sys.stdout = StreamToUI(log_area)
                    
                    try:
                        status_text.text("🔍 Processing data...")
                        progress_bar.progress(50)
                        
                        # Run the ingestion process
                        ingest_data()
                        
                        progress_bar.progress(75)
                        status_text.text("✅ Finalizing...")
                        time.sleep(0.5)
                        
                        progress_bar.progress(100)
                        st.success("🎉 Embeddings created successfully!")
                        
                        # Show completion message
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                        
                    finally:
                        # Restore stdout
                        sys.stdout = original_stdout
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    log_area.empty()
        
        # Chat Button (conditional)
        if qdrant_status and collections:
            if st.button("💬 Start Chatting", use_container_width=True, type="secondary"):
                st.session_state.active_tab = "Chat"
                st.rerun()
        elif qdrant_status and not collections:
            st.warning("⚠️ Create embeddings first to enable chat")
        else:
            st.error("❌ Fix Qdrant connection to continue")

with tab2:
    if not qdrant_status or not collections:
        st.warning("⚠️ Please ensure Qdrant is connected and embeddings are created before using chat.")
    else:
        st.markdown("### 💬 Chat with RBI Circulars")
        
        # Show visualization at the top
        st.markdown("### 📊 Chat Visualization")
        try:
            # Get chat data from Neo4j
            chat_data = neo4j_conn.get_chat_graph()
            
            # Add clear visualization button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🗑️ Clear Visualization", use_container_width=True):
                    try:
                        with neo4j_conn.driver.session() as session:
                            # Delete all nodes and relationships
                            session.run("MATCH (n) DETACH DELETE n")
                        st.success("✅ Visualization cleared successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error clearing visualization: {str(e)}")
            
            if chat_data:
                # Create and display visualization
                visualize_chat_graph(chat_data)
            else:
                st.info("No chat interactions to visualize yet. Start chatting to see the graph!")
        except Exception as e:
            st.error(f"Could not load visualization: {str(e)}")
            st.info("Make sure Neo4j is running and properly configured.")
        
        # Create containers for chat interface
        chat_container = st.container()
        input_container = st.container()
        
        # Display chat messages
        with chat_container:
            # Display messages in reverse order (newest at bottom)
            for message in st.session_state.messages:
                if message["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**You:** {message['content']}")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(f"**Assistant:** {message['content']}")
                        if "sources" in message and message["sources"]:
                            with st.expander("📚 View Sources", expanded=False):
                                # Try to parse sources as JSON
                                try:
                                    sources = json.loads(message["sources"])
                                    if isinstance(sources, list):
                                        for i, source in enumerate(sources, 1):
                                            st.markdown(f"**Source {i}:**")
                                            st.markdown(source.get("content", str(source)))
                                            st.markdown("---")
                                    else:
                                        st.markdown(sources)
                                except:
                                    st.markdown(message["sources"])
        
        # Chat input at the bottom with clear button inline
        with input_container:
            st.markdown("---")  # Add a separator
            
            # Create two columns for clear button and chat input
            clear_col, input_col = st.columns([1, 4])
            
            with clear_col:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.messages = []
                    st.rerun()
            
            with input_col:
                if prompt := st.chat_input("💭 Ask about RBI circulars, regulations, or guidelines..."):
                    # Add user message
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    
                    # Display user message immediately
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**You:** {prompt}")
                    
                    # Generate response with animated loading
                    with st.chat_message("assistant", avatar="🤖"):
                        with st.spinner("🧠 Thinking..."):
                            try:
                                response, sources = query_rag(prompt)
                                
                                # Display response with typing effect simulation
                                st.markdown(f"**Assistant:** {response}")
                                
                                if sources:
                                    with st.expander("📚 View Sources", expanded=False):
                                        # Try to parse sources as JSON
                                        try:
                                            sources_json = json.loads(sources)
                                            if isinstance(sources_json, list):
                                                for i, source in enumerate(sources_json, 1):
                                                    st.markdown(f"**Source {i}:**")
                                                    st.markdown(source.get("content", str(source)))
                                                    st.markdown("---")
                                            else:
                                                st.markdown(sources)
                                        except:
                                            st.markdown(sources)
                                
                                # Store in Neo4j
                                try:
                                    neo4j_conn.create_chat_interaction(prompt, response, sources)
                                except Exception as e:
                                    st.warning(f"Could not store chat in Neo4j: {str(e)}")
                                
                                # Add to session state
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response,
                                    "sources": sources
                                })
                                
                            except Exception as e:
                                error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                                st.error(error_msg)
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": error_msg
                                })

# --- Footer ---
st.markdown("""
<div class="footer">
    <div style="display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto;">
        <div>
            <p style="margin: 0;">🏦 Powered by Advanced AI • Built with Streamlit</p>
        </div>
        <div>
            <a href="https://www.rbi.org.in" target="_blank" style="color: white; text-decoration: none; margin: 0 1rem;">
                RBI Official Website
            </a>
            <a href="https://github.com/your-repo" target="_blank" style="color: white; text-decoration: none; margin: 0 1rem;">
                GitHub
            </a>
            <a href="https://streamlit.io" target="_blank" style="color: white; text-decoration: none; margin: 0 1rem;">
                Streamlit
            </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True) 