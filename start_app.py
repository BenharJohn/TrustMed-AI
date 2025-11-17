"""
Medical Knowledge Graph RAG - Application Startup Script
Starts Ollama server and Streamlit frontend automatically
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_status(text, status="INFO"):
    """Print status message"""
    symbols = {"INFO": "[*]", "SUCCESS": "[+]", "ERROR": "[-]", "WAIT": "[~]"}
    print(f"{symbols.get(status, '[*]')} {text}")

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(["ollama", "--version"],
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False

def check_ollama_running():
    """Check if Ollama server is already running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama server"""
    print_header("Starting Ollama Server")

    if not check_ollama_installed():
        print_status("Ollama is not installed!", "ERROR")
        print_status("Please install Ollama from: https://ollama.com", "INFO")
        return None

    if check_ollama_running():
        print_status("Ollama is already running", "SUCCESS")
        return None

    print_status("Starting Ollama server...", "WAIT")

    try:
        # Start Ollama in background
        if sys.platform == "win32":
            # Windows: Start in new console window
            process = subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Unix: Start in background
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Wait for Ollama to be ready
        print_status("Waiting for Ollama to start...", "WAIT")
        for i in range(10):
            time.sleep(1)
            if check_ollama_running():
                print_status("Ollama server started successfully!", "SUCCESS")
                return process
            print(f"  Attempt {i+1}/10...", end="\r")

        print_status("Ollama took too long to start", "ERROR")
        return None

    except Exception as e:
        print_status(f"Failed to start Ollama: {e}", "ERROR")
        return None

def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("Checking Dependencies")

    required_packages = {
        'streamlit': 'streamlit',
        'neo4j': 'neo4j',
        'openai': 'openai',
        'anthropic': 'anthropic',
        'dotenv': 'python-dotenv',
        'requests': 'requests',
        'pydantic': 'pydantic'
    }

    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print_status(f"{package_name}: installed", "SUCCESS")
        except ImportError:
            print_status(f"{package_name}: MISSING", "ERROR")
            missing.append(package_name)

    if missing:
        print_status(f"\nMissing packages: {', '.join(missing)}", "ERROR")
        print_status("Install with: pip install " + " ".join(missing), "INFO")
        return False

    print_status("All dependencies installed", "SUCCESS")
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    print_header("Checking Configuration")

    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        print_status(".env file not found!", "ERROR")
        print_status("Create .env with: NEO4J_URL, NEO4J_USERNAME, NEO4J_PASSWORD", "INFO")
        return False

    # Load and check env variables
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ["NEO4J_URL", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            display_value = value if var != "NEO4J_PASSWORD" else "*" * len(value)
            print_status(f"{var}: {display_value}", "SUCCESS")
        else:
            print_status(f"{var}: NOT SET", "ERROR")
            missing_vars.append(var)

    if missing_vars:
        print_status(f"\nMissing variables in .env: {', '.join(missing_vars)}", "ERROR")
        return False

    print_status("Configuration file is valid", "SUCCESS")
    return True

def start_streamlit():
    """Start Streamlit frontend"""
    print_header("Starting Streamlit Frontend")

    frontend_path = Path(__file__).parent / "frontend" / "official_frontend_ollama.py"

    if not frontend_path.exists():
        print_status(f"Frontend file not found: {frontend_path}", "ERROR")
        return None

    print_status(f"Starting Streamlit...", "WAIT")
    print_status(f"Frontend will open at: http://localhost:8501", "INFO")
    print("\n")

    try:
        # Start Streamlit
        process = subprocess.Popen(
            ["streamlit", "run", str(frontend_path)],
            cwd=str(frontend_path.parent.parent)
        )

        print_status("Streamlit started!", "SUCCESS")
        print_status("Press Ctrl+C to stop the application", "INFO")

        return process

    except Exception as e:
        print_status(f"Failed to start Streamlit: {e}", "ERROR")
        return None

def main():
    """Main startup sequence"""
    print_header("Medical Knowledge Graph RAG - Startup")
    print("  P0.1 CONTRA-CHECK: Contraindication Safety System")
    print("  Ollama-powered local LLM")

    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n")
        print_status("Please install missing dependencies first", "ERROR")
        sys.exit(1)

    # Step 2: Check configuration
    if not check_env_file():
        print("\n")
        print_status("Please configure .env file first", "ERROR")
        sys.exit(1)

    # Step 3: Start Ollama
    ollama_process = start_ollama()

    # Step 4: Start Streamlit
    streamlit_process = start_streamlit()

    if not streamlit_process:
        print("\n")
        print_status("Failed to start application", "ERROR")
        sys.exit(1)

    # Keep running until user stops
    try:
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n")
        print_header("Shutting Down")
        print_status("Stopping Streamlit...", "WAIT")
        streamlit_process.terminate()

        if ollama_process:
            print_status("Stopping Ollama...", "WAIT")
            ollama_process.terminate()

        print_status("Application stopped", "SUCCESS")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
