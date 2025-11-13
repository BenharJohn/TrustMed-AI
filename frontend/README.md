# Medical Graph RAG Frontend

A Streamlit-based web interface for the Medical Graph RAG system.

## Features

- **Query Interface**: Ask questions about medical knowledge
  - Global mode: Uses community reports for comprehensive answers
  - Local mode: Uses entity embeddings (disabled due to API quota)

- **Document Management**: Upload and index medical documents
  - File upload (.txt files)
  - Direct text input
  - Track indexed documents

- **Query History**: View all previous queries and results

- **Statistics Dashboard**: Monitor system usage

## Quick Start

### Method 1: Using the Launch Script

```bash
# Simply double-click launch_frontend.bat
# OR run from command line:
launch_frontend.bat
```

### Method 2: Manual Launch

```bash
# Activate conda environment
conda activate medgraphrag

# Run Streamlit
streamlit run frontend/app.py
```

The frontend will open automatically in your browser at http://localhost:8501

## Usage Guide

### 1. Initialize GraphRAG

1. Open the sidebar
2. Click "Initialize GraphRAG" button
3. Wait for initialization to complete

### 2. Query the Knowledge Graph

1. Go to the "Query" tab
2. Enter your medical question
3. Select query mode (Global recommended)
4. Click "Execute Query"

Example questions:
- "What cardiac procedures or treatments were performed?"
- "What was the patient's diagnosis?"
- "Describe the patient's medical history"

### 3. Add Documents

1. Go to the "Documents" tab
2. Choose upload method:
   - **File Upload**: Select a .txt file
   - **Text Input**: Paste medical text directly
3. Click "Index Document" or "Index Text"

### 4. View History

1. Go to the "History" tab
2. Expand any previous query to see details
3. Use "Clear History" to reset

## System Architecture

```
Frontend (Streamlit)
    ↓
GraphRAG (nano_graphrag)
    ↓
┌─────────────┬──────────────┐
│   Storage   │   LLM API    │
├─────────────┼──────────────┤
│ NumPy (Win) │ Gemini Flash │
└─────────────┴──────────────┘
```

## Configuration

The frontend uses the same `.env` configuration as the main system:

```env
GOOGLE_API_KEY=your_gemini_api_key
NEO4J_URL=your_neo4j_url
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

## Current Limitations

- **Local query mode disabled**: Gemini embedding API quota exhausted
  - Only Global mode available
  - Global mode uses community reports (no embeddings needed)

- **Rate limits**: Free tier Gemini Flash has 15 RPM
  - System configured with max_async=2 to stay within limits
  - May see delays during heavy usage

## Troubleshooting

### Frontend won't start

```bash
# Check if port 8501 is in use
netstat -an | findstr :8501

# Kill existing Streamlit processes
taskkill /F /IM streamlit.exe
```

### GraphRAG initialization fails

1. Check `.env` file exists with GOOGLE_API_KEY
2. Verify conda environment is activated
3. Check working directory contains `./nanotest/`

### Queries return errors

1. Ensure GraphRAG is initialized first
2. Check API quota limits
3. Try Global mode instead of Local
4. Wait a minute if hitting rate limits

## Advanced Usage

### Using with Neo4j (Full Three-Layer System)

To use the full three-layer architecture with Neo4j instead of the simple mode:

1. Modify `frontend/app.py` to use Neo4j backend
2. Set `enable_local=True` if you have embedding quota
3. Use the full `run.py` instead of simple mode

### Customization

You can customize the frontend by editing:

- `frontend/app.py` - Main application logic
- CSS in the `st.markdown()` sections
- Add new tabs or components

## Files

```
frontend/
├── app.py           # Main Streamlit application
├── README.md        # This file
├── components/      # Future component modules
└── utils/           # Future utility functions

launch_frontend.bat  # Windows launch script
```

## Performance Tips

1. **First query is slow**: Graph building takes time on first document
2. **Subsequent queries are faster**: Uses cached community reports
3. **Large documents**: May take longer to index
4. **Concurrent requests**: Limited to 2 to avoid rate limits

## Support

For issues or questions:
1. Check the main project README
2. Review error messages in Streamlit interface
3. Check background process logs

## License

Same as main Medical-Graph-RAG project.
