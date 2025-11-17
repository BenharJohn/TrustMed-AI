@echo off
echo Starting Medical Graph RAG Frontend...
echo.
echo Opening browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
conda run -n medgraphrag streamlit run frontend\app.py
