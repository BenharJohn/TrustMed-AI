"""
Medical Knowledge Graph Assistant - Chat Interface
Inspired by LittleAIBox design with official three-layer architecture
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from camel.storages import Neo4jGraph
from retrieve_ollama import seq_ret_ollama  # Old sequential retrieval (fallback)
from vector_retrieve_ollama import vector_ret_ollama  # New vector-based retrieval
from utils_ollama import get_response_ollama

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Medical Knowledge Assistant",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# LittleAIBox-inspired Clean Theme CSS
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* Root variables */
    :root {
        --bg-color: #fafafa;
        --text-primary: #333;
        --text-secondary: #666;
        --text-tertiary: #999;
        --border-color: #e5e5e5;
        --input-bg: #f5f5f5;
        --pill-bg: #f0f0f0;
        --pill-hover: #e8e8e8;
        --button-bg: #c0c0c0;
        --button-hover: #b0b0b0;
        --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Global styles */
    * {
        font-family: var(--font-family);
    }

    /* Hide Streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}

    /* Remove default padding */
    .main .block-container {
        padding: 0;
        max-width: 350px !important;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }

    /* Remove Streamlit element spacing */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Fix Streamlit wrapper interference */
    .row-widget.stHorizontal,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* Sidebar styling - force visible and prevent collapse */
    [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid var(--border-color);
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: none !important;
        min-width: 250px !important;
        max-width: 350px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background-color: white;
    }

    /* Hide the collapse button to prevent hiding sidebar */
    [data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
    }

    /* Sidebar text visibility */
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] label {
        color: var(--text-secondary) !important;
    }

    [data-testid="stSidebar"] .stMetric label,
    [data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
    }

    /* Style Streamlit's built-in collapse button to be more visible */
    [data-testid="collapsedControl"] {
        background-color: white !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.2s !important;
        top: 1rem !important;
        left: 1rem !important;
    }

    [data-testid="collapsedControl"]:hover {
        background-color: var(--pill-hover) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }

    [data-testid="collapsedControl"] svg {
        color: var(--text-primary) !important;
        width: 20px !important;
        height: 20px !important;
    }

    /* Body background */
    .stApp {
        background-color: var(--bg-color);
    }

    /* Welcome container - absolute positioning for guaranteed centering */
    .welcome-container {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        max-width: 350px;
        text-align: center;
    }

    .welcome-title {
        font-size: 2rem;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
    }

    .welcome-subtitle {
        font-size: 1rem;
        font-weight: 400;
        color: var(--text-secondary);
        margin-bottom: 3rem;
    }

    /* Suggestion pills */
    .suggestions-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        justify-content: center;
        max-width: 100%;
        margin: 0 auto 3rem auto;
    }

    .suggestion-pill {
        background: var(--pill-bg);
        border: none;
        border-radius: 20px;
        padding: 0.65rem 1.25rem;
        font-size: 0.875rem;
        font-weight: 400;
        color: var(--text-primary);
        cursor: pointer;
        transition: all 0.15s ease;
        white-space: nowrap;
    }

    .suggestion-pill:hover {
        background: var(--pill-hover);
        transform: translateY(-1px);
    }

    /* Input container - fixed bottom */
    .input-wrapper {
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        width: 350px !important;
        max-width: 350px !important;
        z-index: 1000;
    }

    .input-box {
        background: transparent;
        border: none;
        border-radius: 28px;
        padding: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    /* Hide Streamlit input styling */
    .stTextInput > div {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    .stTextInput > div > div {
        border: none !important;
        background: transparent !important;
    }

    .stTextInput input {
        border: 1px solid #d0d0d0 !important;
        border-radius: 20px !important;
        background: transparent !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9375rem !important;
        color: var(--text-primary) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input:focus {
        border: 1px solid #999 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        outline: none !important;
    }

    .stTextInput input::placeholder {
        color: var(--text-tertiary) !important;
    }

    /* Send button */
    .stButton > button {
        background: var(--button-bg) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
    }

    .stButton > button:hover {
        background: var(--button-hover) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    .stButton > button p {
        font-size: 1.25rem !important;
        margin: 0 !important;
        color: white !important;
    }

    /* Chat container */
    .chat-area {
        max-width: 350px !important;
        width: 100%;
        margin: 0 auto;
        padding: 2rem 1rem 8rem 1rem;
    }

    /* Message bubbles */
    .message-bubble {
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        animation: slideIn 0.2s ease;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .message-user {
        align-items: flex-end;
    }

    .message-assistant {
        align-items: flex-start;
    }

    .message-content {
        max-width: 75%;
        padding: 0.75rem 1rem;
        border-radius: 16px;
        font-size: 0.875rem;
        line-height: 1.4;
    }

    .message-user .message-content {
        background: var(--text-primary);
        color: white;
    }

    .message-assistant .message-content {
        background: white;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .message-time {
        font-size: 0.75rem;
        color: var(--text-tertiary);
        margin-top: 0.375rem;
        padding: 0 0.5rem;
    }

    /* Adjust spacing */
    .stTextInput {
        margin: 0 !important;
    }

    /* Column adjustments */
    [data-testid="column"] {
        padding: 0 !important;
    }

    /* Processing status */
    .processing-status {
        position: fixed;
        top: 1.5rem;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 24px;
        font-size: 0.875rem;
        font-weight: 500;
        z-index: 2000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }

    /* Graph info panel */
    .graph-info {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.75rem;
        font-size: 0.8125rem;
        color: #555;
    }

    .graph-info-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
    }

    .graph-info-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.375rem 0;
        font-size: 0.8125rem;
    }

    .graph-info-item .icon {
        color: #1a73e8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Initialize Neo4j connection
@st.cache_resource
def init_neo4j():
    try:
        url = os.getenv("NEO4J_URL")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([url, username, password]):
            return None

        n4j = Neo4jGraph(url=url, username=username, password=password)
        return n4j
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {e}")
        return None

# Check Ollama status
def check_ollama():
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

# Get graph statistics
def get_graph_stats(n4j):
    try:
        stats = {}
        result = n4j.query("MATCH (n) WHERE NOT n:Summary RETURN count(n) as count")
        stats['entities'] = result[0]['count'] if result else 0

        result = n4j.query("MATCH (s:Summary) RETURN count(s) as count")
        stats['summaries'] = result[0]['count'] if result else 0

        result = n4j.query("MATCH ()-[r]->() WHERE type(r) <> 'REFERENCE' RETURN count(r) as count")
        stats['relationships'] = result[0]['count'] if result else 0

        result = n4j.query("MATCH ()-[r:REFERENCE]->() RETURN count(r) as count")
        stats['references'] = result[0]['count'] if result else 0

        return stats
    except:
        return None

# Initialize connections
n4j = init_neo4j()
ollama_available = check_ollama()

# Store model selection in session state
if 'model' not in st.session_state:
    st.session_state.model = "llama3"

model = st.session_state.model

# Sidebar configuration
with st.sidebar:
    st.markdown("### AI Parameters")

    # Model selection
    model_option = st.selectbox(
        "Model",
        ["llama3", "llama2", "mistral"],
        index=0
    )
    st.session_state.model = model_option

    st.markdown("---")

    # Advanced settings (collapsible)
    with st.expander("Advanced Settings", expanded=False):
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
        max_tokens = st.slider("Max Tokens", 100, 2000, 512, 50)

    st.markdown("---")

    # Graph statistics
    st.markdown("### Knowledge Graph Stats")
    if n4j:
        stats = get_graph_stats(n4j)
        if stats:
            st.metric("Entities", stats.get('entities', 0))
            st.metric("Summaries", stats.get('summaries', 0))
            st.metric("Relationships", stats.get('relationships', 0))
            st.metric("Cross-layer Links", stats.get('references', 0))
    else:
        st.warning("Not connected to Neo4j")

    st.markdown("---")

    # System status
    st.markdown("### System Status")
    if n4j:
        st.success("Neo4j: Connected")
    else:
        st.error("Neo4j: Disconnected")

    if ollama_available:
        st.success("Ollama: Running")
    else:
        st.error("Ollama: Not running")

# Main content area
if len(st.session_state.messages) == 0:
    # Welcome screen - exactly like LittleAIBox
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">Welcome to Medical Knowledge Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-subtitle">You can start from here, or ask any question</div>', unsafe_allow_html=True)

    st.markdown('<div class="suggestions-container">', unsafe_allow_html=True)
    st.markdown('<button class="suggestion-pill">Can I take NSAIDs like ibuprofen if I have heart failure and kidney problems?</button>', unsafe_allow_html=True)
    st.markdown('<button class="suggestion-pill">Is it safe to take calcium channel blockers with my heart failure diagnosis?</button>', unsafe_allow_html=True)
    st.markdown('<button class="suggestion-pill">Can I use Flecainide for my atrial fibrillation if I had a heart attack?</button>', unsafe_allow_html=True)
    st.markdown('<button class="suggestion-pill">Should I be concerned about taking Spironolactone with acute kidney injury?</button>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
else:
    # Chat history view
    st.markdown('<div class="chat-area">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        role_class = "message-user" if message["role"] == "user" else "message-assistant"
        st.markdown(f"""
        <div class="message-bubble {role_class}">
            <div class="message-content">{message["content"]}</div>
            <div class="message-time">{message.get("timestamp", "")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Show graph info for assistant messages
        if message["role"] == "assistant" and message.get("gid"):
            graph_info = message.get("graph_info", {})
            st.markdown(f"""
            <div class="graph-info">
                <div class="graph-info-title">Knowledge Graph Source</div>
                <div class="graph-info-item"><span class="icon">Graph ID:</span> {message.get("gid", "Unknown")}</div>
                <div class="graph-info-item"><span class="icon">Retrieved from:</span> Three-layer medical knowledge graph</div>
                <div class="graph-info-item"><span class="icon">Architecture:</span> Official research paper implementation</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Fixed bottom input - LittleAIBox style
st.markdown('<div class="input-wrapper"><div class="input-box">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([0.5, 8, 0.5])

with col1:
    st.markdown('<span style="font-size: 1.25rem; color: #999;">+</span>', unsafe_allow_html=True)

with col2:
    user_input = st.text_input(
        "input",
        placeholder="Ask any question",
        label_visibility="collapsed",
        key="user_input"
    )

with col3:
    send_button = st.button("➤", key="send_btn")

st.markdown('</div></div>', unsafe_allow_html=True)

# Process input
if send_button and user_input:
    if not n4j:
        st.error("Error: Cannot connect to Neo4j database")
    elif not ollama_available:
        st.error("Error: Ollama is not running")
    else:
        # Add user message
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })

        # Processing with detailed stages
        try:
            import time
            status_placeholder = st.empty()

            # Stage 1: Vector search with embedding
            status_placeholder.markdown('<div class="processing-status">Generating question embedding...</div>', unsafe_allow_html=True)
            time.sleep(0.3)

            # Stage 2: Searching knowledge graph with vector similarity
            status_placeholder.markdown('<div class="processing-status">Using vector search to find matching Summary nodes (fast!)...</div>', unsafe_allow_html=True)
            gid = vector_ret_ollama(n4j, user_input, model)

            if gid:
                # Stage 3: Found match - show GID
                status_placeholder.markdown(f'<div class="processing-status">Found match: Graph ID {gid}</div>', unsafe_allow_html=True)
                time.sleep(0.5)

                # Stage 4: Retrieving context from graph
                status_placeholder.markdown('<div class="processing-status">Retrieving entities & relationships from matched subgraph...</div>', unsafe_allow_html=True)
                time.sleep(0.3)

                # Stage 5: Getting cross-layer references
                status_placeholder.markdown('<div class="processing-status">Following cross-layer REFERENCE links...</div>', unsafe_allow_html=True)
                time.sleep(0.3)

                # Stage 6: Generating answer with graph context
                status_placeholder.markdown('<div class="processing-status">Generating answer using graph context (2-pass approach)...</div>', unsafe_allow_html=True)
                answer = get_response_ollama(n4j, gid, user_input, model)

                # Add assistant message with graph info
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "gid": gid,
                    "graph_info": {
                        "matched": True,
                        "layers_used": "Three-layer architecture (UMLS→MedC-K→MIMIC-IV)"
                    }
                })

                status_placeholder.empty()
                st.rerun()
            else:
                status_placeholder.empty()
                st.warning("Warning: No matching Summary node found in knowledge graph")

        except Exception as e:
            if status_placeholder:
                status_placeholder.empty()

            # Better error messages
            error_msg = str(e)
            if "Ollama" in error_msg or "500" in error_msg:
                st.error(f"Ollama Error: {error_msg}\n\nTry: Restart Ollama or check if llama3 model is loaded")
            elif "Neo4j" in error_msg or "connection" in error_msg.lower():
                st.error(f"Neo4j Connection Error: {error_msg}\n\nCheck if Neo4j is running")
            else:
                st.error(f"Error: {error_msg}")
