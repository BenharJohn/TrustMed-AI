@echo off
echo ========================================
echo Medical Graph RAG - Citation System
echo ========================================
echo.
echo [1/2] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not running!
    echo Please start Ollama first.
    pause
    exit /b 1
)
echo [OK] Ollama is running

echo.
echo [2/2] Starting Streamlit frontend...
echo.
echo Frontend will open in your browser at http://localhost:8501
echo.
echo IMPORTANT: The citation system is now active!
echo All answers will include inline citations like [1], [2]
echo with sources listed below each response.
echo.

cd /d "F:\Medgraph\Medical-Graph-RAG"
"C:\Users\benha\anaconda3\python.exe" -m streamlit run "frontend\official_frontend_ollama.py"
