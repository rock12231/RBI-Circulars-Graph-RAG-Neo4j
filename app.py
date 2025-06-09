import streamlit as st
from src.retrieval.rag import query_rag
from src.utils import config
from src.ingestion.ingest import ingest_data
import subprocess
from qdrant_client import QdrantClient
import time
import json

# --- Page Config ---
st.set_page_config(
    page_title="RBI Circulars AI Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced Custom CSS for Modern UI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --warning-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        --error-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        --glass-bg: rgba(255, 255, 255, 0.25);
        --glass-border: rgba(255, 255, 255, 0.18);
        --text-primary: #2d3748;
        --text-secondary: #4a5568;
        --shadow-light: 0 4px 6px rgba(0, 0, 0, 0.07);
        --shadow-medium: 0 10px 25px rgba(0, 0, 0, 0.1);
        --shadow-heavy: 0 20px 40px rgba(0, 0, 0, 0.15);
        --border-radius: 16px;
        --border-radius-sm: 8px;
        --border-radius-lg: 24px;
    }
    
    /* Reset and base styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Glassmorphism container */
    .glass-container {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: var(--border-radius);
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-medium);
    }
    
    /* Enhanced button styling */
    .stButton > button {
        background: var(--primary-gradient);
        color: white;
        border: none;
        border-radius: var(--border-radius-lg);
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.025em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-medium);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-heavy);
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Primary button variant */
    .stButton > button[kind="primary"] {
        background: var(--success-gradient);
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3182ce 0%, #00d4ff 100%);
        box-shadow: 0 8px 25px rgba(79, 172, 254, 0.6);
    }
    
    /* Secondary button variant */
    .stButton > button[kind="secondary"] {
        background: var(--secondary-gradient);
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #ed64a6 0%, #f56565 100%);
        box-shadow: 0 8px 25px rgba(240, 147, 251, 0.6);
    }
    
    /* Modern card styling */
    .modern-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-light);
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .modern-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--primary-gradient);
    }
    
    .modern-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-medium);
    }
    
    /* Enhanced gradient text */
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    /* Hero section */
    .hero-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.8) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: var(--border-radius-lg);
        padding: 3rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: var(--shadow-heavy);
        position: relative;
        overflow: hidden;
    }
    
    .hero-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(transparent, rgba(255, 255, 255, 0.3), transparent 30%);
        animation: rotate 4s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .hero-content {
        position: relative;
        z-index: 1;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: var(--border-radius-lg);
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.25rem;
        transition: all 0.3s ease;
    }
    
    .status-connected {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
    }
    
    .status-disconnected {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(245, 101, 101, 0.4);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(237, 137, 54, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: var(--border-radius);
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        border-radius: var(--border-radius-sm);
        color: rgba(255, 255, 255, 0.7);
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: var(--text-primary);
        box-shadow: var(--shadow-light);
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: var(--border-radius);
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: var(--primary-gradient);
        border-radius: var(--border-radius-sm);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: var(--border-radius-sm);
        border: 2px solid rgba(255, 255, 255, 0.2);
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--glass-bg);
        border-radius: var(--border-radius-sm);
        backdrop-filter: blur(10px);
    }
    
    /* Success/Error/Warning messages */
    .stAlert {
        border-radius: var(--border-radius);
        backdrop-filter: blur(10px);
    }
    
    /* Metric styling */
    .metric-card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
        box-shadow: var(--shadow-light);
        transition: all 0.3s ease;
        border-left: 4px solid;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }
    
    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.6s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .gradient-text {
            font-size: 2.5rem;
        }
        
        .hero-card {
            padding: 2rem;
            margin: 1rem 0;
        }
        
        .modern-card {
            padding: 1.5rem;
        }
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

# --- Header with Enhanced Gradient Text ---
st.markdown('<h1 class="gradient-text fade-in">🏦 RBI Circulars AI Assistant</h1>', unsafe_allow_html=True)

# --- Enhanced Hero Section ---
st.markdown("""
<div class="hero-card fade-in">
    <div class="hero-content">
        <h2 style="color: #2d3748; margin-bottom: 1rem; font-weight: 600;">🤖 Intelligent RBI Circular Assistant</h2>
        <p style="color: #4a5568; font-size: 1.1rem; line-height: 1.6; margin-bottom: 1.5rem;">
            Get instant, accurate answers to your questions about RBI regulations, circulars, and guidelines. 
            Powered by advanced AI and real-time data retrieval for comprehensive financial insights.
        </p>
        <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
            <span style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 0.5rem 1rem; border-radius: 25px; font-size: 0.875rem; font-weight: 600;">🚀 AI-Powered</span>
            <span style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; padding: 0.5rem 1rem; border-radius: 25px; font-size: 0.875rem; font-weight: 600;">⚡ Real-time</span>
            <span style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 0.5rem 1rem; border-radius: 25px; font-size: 0.875rem; font-weight: 600;">🔒 Secure</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Enhanced Sidebar ---
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0; font-weight: 600;">🔧 System Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Connection Status Function
    def check_qdrant_connection():
        try:
            client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT,
                timeout=5.0
            )
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            return True, collection_names
        except Exception as e:
            return False, str(e)
    
    # Check connection with enhanced spinner
    with st.spinner("🔍 Checking system status..."):
        qdrant_status, collections = check_qdrant_connection()
    
    # Enhanced Status Display
    if qdrant_status:
        st.markdown('<div class="status-indicator status-connected">🟢 Qdrant Connected</div>', unsafe_allow_html=True)
        if collections:
            st.markdown(f'<div class="status-indicator status-connected">📊 Collections: {len(collections)}</div>', unsafe_allow_html=True)
            for collection in collections:
                st.markdown(f"<div style='color: white; padding: 0.25rem 0; margin-left: 1rem;'>• {collection}</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-indicator status-warning">⚠️ No Collections</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-disconnected">🔴 Qdrant Disconnected</div>', unsafe_allow_html=True)
        st.error(f"Error: {collections}")
    
    st.markdown("---")
    
    # Enhanced System Info
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1rem; margin: 1rem 0;">
        <h4 style="color: white; margin-bottom: 0.5rem;">📈 System Info</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='color: white; font-size: 0.875rem;'><strong>Host:</strong><br>{config.QDRANT_HOST}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='color: white; font-size: 0.875rem;'><strong>Port:</strong><br>{config.QDRANT_PORT}</div>", unsafe_allow_html=True)
    
    api_status = "✅ Active" if config.GOOGLE_API_KEY else "❌ Missing"
    st.markdown(f"<div style='color: white; font-size: 0.875rem; margin-top: 0.5rem;'><strong>API Status:</strong> {api_status}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1rem; margin: 1rem 0;">
        <h4 style="color: white; margin-bottom: 1rem;">⚡ Quick Actions</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

# --- Enhanced Main Content with Tabs ---
if st.session_state.active_tab == "Chat":
    tab1, tab2 = st.tabs(["🏠 Dashboard", "💬 Chat Interface"])
    selected_tab = tab2
else:
    tab1, tab2 = st.tabs(["🏠 Dashboard", "💬 Chat Interface"])
    selected_tab = tab1

with tab1:
    st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
    
    # Enhanced Action Section
    st.markdown("### 🎯 Control Center")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Create Embeddings with Enhanced Progress
        if st.button("🚀 Create Embeddings", use_container_width=True, type="primary", key="create_embeddings"):
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Enhanced progress tracking
                    steps = [
                        ("🔄 Initializing system...", 20),
                        ("📊 Loading data files...", 40),
                        ("🧠 Generating embeddings...", 70),
                        ("💾 Storing in database...", 90),
                        ("✅ Finalizing process...", 100)
                    ]
                    
                    for step_text, progress_val in steps:
                        status_text.markdown(f"<div style='text-align: center; color: #4a5568; font-weight: 500;'>{step_text}</div>", unsafe_allow_html=True)
                        progress_bar.progress(progress_val)
                        time.sleep(0.8)
                        
                        if progress_val == 70:  # Run actual ingestion
                            ingest_data()
                    
                    st.success("🎉 Embeddings created successfully! You can now start chatting.")
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    progress_bar.empty()
                    status_text.empty()
        
        # Enhanced Chat Button
        if qdrant_status and collections:
            if st.button("💬 Start Intelligent Chat", use_container_width=True, type="secondary", key="start_chat"):
                st.session_state.active_tab = "Chat"
                st.rerun()
        elif qdrant_status and not collections:
            st.warning("⚠️ Please create embeddings first to enable the chat feature")
        else:
            st.error("❌ Please fix the Qdrant connection to continue")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Metrics Section
    if qdrant_status and collections:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 📊 System Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #4facfe;">
                <h3 style="color: #4facfe; margin: 0;">🔗</h3>
                <p style="margin: 0.5rem 0 0 0; color: #2d3748; font-weight: 600;">Connected</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #43e97b;">
                <h3 style="color: #43e97b; margin: 0;">{len(collections)}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #2d3748; font-weight: 600;">Collections</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #fa709a;">
                <h3 style="color: #fa709a; margin: 0;">🤖</h3>
                <p style="margin: 0.5rem 0 0 0; color: #2d3748; font-weight: 600;">AI Ready</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card" style="border-left-color: #667eea;">
                <h3 style="color: #667eea; margin: 0;">⚡</h3>
                <p style="margin: 0.5rem 0 0 0; color: #2d3748; font-weight: 600;">Real-time</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    if not qdrant_status or not collections:
        st.markdown("""
        <div class="modern-card" style="text-align: center;">
            <h3 style="color: #ed8936;">⚠️ Setup Required</h3>
            <p style="color: #4a5568;">Please ensure Qdrant is connected and embeddings are created before using the chat feature.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        
        # Enhanced Chat Header
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h2 style="color: #2d3748; margin-bottom: 0.5rem;">💬 Intelligent Chat Assistant</h2>
                <p style="color: #4a5568;">Ask questions about RBI regulations, circulars, and guidelines</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ Clear Chat History", use_container_width=True, key="clear_chat"):
                st.session_state.messages = []
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Enhanced Chat Container
        chat_container = st.container()
        
        with chat_container:
            # Display chat messages with enhanced styling
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**You:** {message['content']}")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(f"**RBI Assistant:** {message['content']}")
                        if "sources" in message and message["sources"]:
                            with st.expander("📚 View Sources & References"):
                                st.markdown(message["sources"])
        
        # Enhanced Chat Input
        if prompt := st.chat_input("💭 Ask about RBI circulars, regulations, or guidelines... (e.g., 'What are the latest KYC guidelines?')"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**You:** {prompt}")
            
            # Generate response with enhanced loading
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("🧠 Analyzing RBI data and generating response..."):
                    try:
                        response, sources = query_rag(prompt)
                        
                        # Display response
                        st.markdown(f"**RBI Assistant:** {response}")
                        
                        if sources:
                            with st.expander("📚 View Sources & References"):
                                st.markdown(sources)
                        
                        # Add to session state
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "sources": sources
                        })
                        
                    except Exception as e:
                        error_msg = f"❌ I apologize, but I encountered an error while processing your request: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })

# --- Enhanced Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: rgba(255, 255, 255, 0.1); border-radius: 16px; margin-top: 2rem; backdrop-filter: blur(10px);">
    <h4 style="color: white; margin-bottom: 1rem; font-weight: 600;">🏦 RBI Circulars AI Assistant</h4>
    <p style="color: rgba(255, 255, 255, 0.8); margin: 0; font-size: 0.875rem;">
        Powered by Advanced AI • Built with Streamlit • Real-time RBI Data Processing
    </p>
    <div style="margin-top: 1rem;">
        <span style="color: rgba(255, 255, 255, 0.6); font-size: 0.75rem;">© 2024 • Secure • Reliable • Intelligent</span>
    </div>
</div>
""", unsafe_allow_html=True) 