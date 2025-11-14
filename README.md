# Medical Graph RAG with Ollama

**A local, free, and privacy-preserving medical knowledge graph RAG system powered by Ollama**

[![Paper](https://img.shields.io/badge/arXiv-2408.04187-b31b1b.svg)](https://arxiv.org/abs/2408.04187)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> This is an Ollama-optimized implementation of Medical Graph RAG that runs 100% locally with no API costs or external dependencies.

## 🌟 Key Features

- **100% Local & Free**: Uses Ollama for local LLM inference - no API keys, no costs, no external dependencies
- **Privacy-First**: All data and processing stays on your machine
- **Three-Layer Architecture**: Hierarchical knowledge graph (UMLS → MedC-K → MIMIC-IV)
- **Smart Retrieval**: Vector-based semantic search with cross-layer linking
- **Patient-Aware**: Checks contraindications and patient-specific conditions
- **Two-Pass Generation**: First generates patient-specific answer, then refines with clinical guidelines

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Building the Knowledge Graph](#building-the-knowledge-graph)
- [Running the System](#running-the-system)
- [Usage Guide](#usage-guide)
- [System Components](#system-components)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Citation](#citation)

---

## 📖 Overview

Medical Graph RAG is a specialized retrieval-augmented generation system for medical knowledge. This implementation uses:

- **Ollama** for local LLM inference (llama3, mistral, phi3, etc.)
- **Neo4j** for graph database storage
- **Streamlit** for the web interface
- **CAMEL** framework for graph storage utilities

### What Makes This Different?

Traditional RAG systems use simple vector similarity. Medical Graph RAG:
1. Extracts **entities and relationships** from medical texts
2. Builds a **hierarchical three-layer knowledge graph**
3. Links similar concepts **across layers** using semantic embeddings
4. Retrieves context by **graph traversal** and cross-layer references
5. Generates answers using **two-pass refinement** (local + global context)

---

## 🏗️ Architecture

### Three-Layer Hierarchical Structure

```
┌─────────────────────────────────────────────────────┐
│   Top Layer: MIMIC-IV Patient Records              │
│   - De-identified patient cases                    │
│   - Real-world medical scenarios                   │
│   - Treatment outcomes                             │
└───────────────────┬─────────────────────────────────┘
                    │
          REFERENCE relationships
          (semantic similarity > 0.6)
                    │
┌───────────────────┴─────────────────────────────────┐
│   Middle Layer: MedC-K Clinical Guidelines         │
│   - Evidence-based treatment protocols             │
│   - Clinical decision rules                        │
│   - Drug interactions                              │
└───────────────────┬─────────────────────────────────┘
                    │
          REFERENCE relationships
          (semantic similarity > 0.6)
                    │
┌───────────────────┴─────────────────────────────────┐
│   Bottom Layer: UMLS Medical Terminology           │
│   - Standardized medical definitions              │
│   - Disease taxonomy                               │
│   - Drug classifications                           │
└─────────────────────────────────────────────────────┘
```

### Entity-Relationship Graph

Each layer contains:
- **Entities**: Disease, Medication, Symptom, Procedure, BodyPart, etc.
- **Relationships**: CAUSES, TREATS, HAS_SYMPTOM, CONTRAINDICATED_IN, etc.
- **Summary Node**: 2-3 sentence summary of each document/subgraph
- **Embeddings**: 768-dimensional vectors for semantic matching

### Query Workflow

```
User Question
    ↓
1. Generate Summary (Ollama)
    ↓
2. Vector Search → Find Best Matching Subgraph (GID)
    ↓
3. Retrieve Self Context (entities/relationships in matched GID)
    ↓
4. [PASS 1] Generate Patient-Aware Answer
    ↓
5. Retrieve Linked Context (follow REFERENCE links)
    ↓
6. [PASS 2] Refine with Cross-Layer Knowledge
    ↓
Final Answer
```

---

## ✅ Prerequisites

### Required Software

- **Python 3.10+** (Python 3.10.9+ recommended)
- **Conda** (Anaconda or Miniconda)
- **Ollama** ([Download here](https://ollama.ai))
- **Neo4j** (Aura DB cloud or local instance)

### Hardware Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB+ for models and data
- **GPU**: Optional (Ollama can use CPU, but GPU is faster)

### Operating Systems

- ✅ Windows 10/11
- ✅ macOS 12+
- ✅ Linux (Ubuntu 20.04+, Debian, etc.)

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/BenharJohn/TrustMed-AI.git
cd TrustMed-AI
```

### Step 2: Create Conda Environment

The project includes a pre-configured environment with all dependencies:

```bash
# Create environment from yml file (includes all packages)
conda env create -f medgraphrag.yml

# Activate the environment
conda activate medgraphrag
```

**Alternative:** Manual installation with pip:

```bash
# Create new environment
conda create -n medgraphrag python=3.10 -y
conda activate medgraphrag

# Install dependencies
pip install -r requirements_windows.txt
```

### Step 3: Install Ollama

**Windows/macOS:**
- Download from [ollama.ai](https://ollama.ai)
- Run the installer

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 4: Download Ollama Models

```bash
# Download llama3 (recommended, 4.7GB)
ollama pull llama3

# Optional: Download other models
ollama pull mistral      # 4.1GB
ollama pull phi3         # 2.3GB
ollama pull llama2       # 3.8GB
```

### Step 5: Verify Installation

```bash
# Check Ollama is running
ollama list

# Check Python environment
python --version  # Should show Python 3.10+
```

---

## ⚙️ Configuration

### Neo4j Setup

You can use either **Neo4j Aura** (cloud, free tier) or **local Neo4j**.

#### Option A: Neo4j Aura (Recommended for Beginners)

1. Go to [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura)
2. Create a free account
3. Create a new database instance
4. Save your credentials (URL, username, password)

#### Option B: Local Neo4j

1. Download from [neo4j.com/download](https://neo4j.com/download)
2. Install and start Neo4j Desktop
3. Create a new database
4. Note your credentials (default username: `neo4j`)

### Environment Variables

Create a `.env` file in the project root:

```bash
# Neo4j Configuration
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Optional: Ollama Configuration (defaults shown)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

**Example `.env` file:**

```
NEO4J_URL=neo4j+s://91cdd753.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=6xE8xaDVlNLCQphT4UmbZWygnP6YhExozHToAl6yvhQ
```

---

## 🔨 Building the Knowledge Graph

### Quick Start (5 Patients)

For testing and development, build a small graph with 5 patient records:

```bash
cd Medical-Graph-RAG
conda activate medgraphrag
python build_three_layer_ollama.py --num_patients 5 --model llama3
```

**Build time:** ~15-30 minutes (depends on your hardware)

### Full Build (All Data)

For production use with the complete dataset:

```bash
python three_layer_import_ollama.py \
  --clear \
  --bottom dataset/umls \
  --middle dataset/medc_k \
  --top dataset/mimic_ex/dataset \
  --trinity \
  --model llama3
```

**Build time:** ~2-4 hours for full MIMIC-IV dataset (89,830 patient reports)

### Build Options

| Option | Description | Default |
|--------|-------------|---------|
| `--num_patients` | Number of patient records to process | 5 |
| `--model` | Ollama model to use | llama3 |
| `--clear` | Clear database before building | False |
| `--skip_linking` | Skip cross-layer reference links (faster) | False |
| `--bottom` | Path to UMLS data | dataset/umls |
| `--middle` | Path to MedC-K data | dataset/medc_k |
| `--top` | Path to MIMIC-IV data | dataset/mimic_ex/dataset |
| `--trinity` | Enable three-layer linking | False |

### What Gets Built

1. **Bottom Layer (UMLS)**:
   - Medical terminology definitions
   - Disease classifications
   - Drug taxonomies

2. **Middle Layer (MedC-K)**:
   - Clinical guidelines
   - Treatment protocols
   - Evidence-based recommendations

3. **Top Layer (MIMIC-IV)**:
   - De-identified patient cases
   - Medical histories
   - Treatment outcomes

4. **Cross-Layer Links (Trinity)**:
   - REFERENCE relationships between similar entities
   - Semantic similarity threshold: 0.6
   - Enables multi-hop reasoning

---

## 🎯 Running the System

### Start Ollama (if not already running)

```bash
# Start Ollama server
ollama serve
```

**Keep this terminal open** - Ollama needs to keep running.

### Launch the Frontend

Open a **new terminal** and run:

```bash
cd Medical-Graph-RAG
conda activate medgraphrag
streamlit run frontend/official_frontend_ollama.py
```

### Access the Web Interface

The app will start on: **http://localhost:8501**

Open this URL in your browser to use the Medical Knowledge Assistant.

### Using the Command Line (Optional)

For programmatic access:

```python
from neo4j import GraphDatabase
from vector_retrieve_ollama import vector_ret_ollama
from utils_ollama import get_response_ollama

# Connect to Neo4j
driver = GraphDatabase.driver(
    "neo4j+s://your-url",
    auth=("neo4j", "your-password")
)

# Query the system
question = "What is cardiac arrest?"
gid = vector_ret_ollama(driver, question, model="llama3")
answer = get_response_ollama(driver, gid, question, model="llama3")

print(answer)
```

---

## 📚 Usage Guide

### Example Questions

**General Medical Questions:**
- "What is cardiac arrest?"
- "What are symptoms of myocardial infarction?"
- "How is diabetes diagnosed?"

**Patient-Specific Questions:**
- "Can I take NSAIDs if I have heart failure?"
- "Is ibuprofen safe with chronic kidney disease?"
- "What pain relievers are safe for patients with liver problems?"

**Treatment Questions:**
- "What is the treatment for atrial fibrillation?"
- "How is pneumonia managed in elderly patients?"
- "What are alternatives to NSAIDs for pain relief?"

### Understanding the Results

Each answer includes:

1. **Answer Text**: Two-pass generated response
   - Pass 1: Patient-aware answer with contraindication checking
   - Pass 2: Refined with clinical guidelines

2. **Graph Info Panel**: Shows the source
   - **GID**: Graph ID of the matched subgraph
   - **Layers Used**: Which layers contributed to the answer
   - **Match Quality**: How well the question matched

3. **Warnings** (if applicable):
   - Drug contraindications
   - Patient-specific risks
   - Safety considerations

### Best Practices

✅ **DO:**
- Ask specific medical questions
- Mention patient conditions for personalized answers
- Use the system as a research/educational tool

❌ **DON'T:**
- Use for emergency medical decisions
- Replace professional medical advice
- Assume answers are 100% accurate (always verify)

---

## 🔧 System Components

### Core Files

| File | Purpose | Size |
|------|---------|------|
| `build_three_layer_ollama.py` | Main graph builder | 8.2 KB |
| `three_layer_import_ollama.py` | Three-layer importer | 7.5 KB |
| `creat_graph_ollama.py` | Entity extraction from text | 10.5 KB |
| `retrieve_ollama.py` | Summary-based retrieval | 5.2 KB |
| `vector_retrieve_ollama.py` | Vector-based retrieval (faster) | 8.8 KB |
| `utils_ollama.py` | Two-pass answer generation | 6.3 KB |
| `frontend/official_frontend_ollama.py` | Streamlit web interface | 24.6 KB |

### Directory Structure

```
Medical-Graph-RAG/
├── frontend/
│   └── official_frontend_ollama.py  # Streamlit UI
├── camel/                           # CAMEL framework
│   └── storages/                    # Neo4j graph utilities
├── dataset/
│   ├── umls/                        # Bottom layer data
│   ├── medc_k/                      # Middle layer data
│   └── mimic_ex/                    # Top layer data
├── build_three_layer_ollama.py      # Graph builder
├── three_layer_import_ollama.py     # Three-layer importer
├── creat_graph_ollama.py            # Entity extraction
├── retrieve_ollama.py               # Sequential retrieval
├── vector_retrieve_ollama.py        # Vector retrieval
├── utils_ollama.py                  # Answer generation
├── requirements_windows.txt         # Dependencies
├── medgraphrag.yml                  # Conda environment
├── .env                             # Configuration
└── README.md                        # This file
```

### File Workflow

**Graph Building:**
```
Medical Text → creat_graph_ollama.py → Entities + Relationships
    ↓
build_three_layer_ollama.py → Summary Nodes + Embeddings
    ↓
three_layer_import_ollama.py → Cross-Layer Links (Trinity)
    ↓
Neo4j Database
```

**Query Processing:**
```
Question → vector_retrieve_ollama.py → Best Matching GID
    ↓
utils_ollama.py (ret_context) → Self Context
    ↓
utils_ollama.py (link_context) → Cross-Layer Context
    ↓
utils_ollama.py (get_response) → Two-Pass Answer
    ↓
Frontend Display
```

---

## 🐛 Troubleshooting

### Ollama Connection Issues

**Problem:** "Cannot connect to Ollama"

**Solutions:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Check which models are available
ollama list

# Pull llama3 if missing
ollama pull llama3
```

### Neo4j Connection Issues

**Problem:** "Failed to connect to Neo4j"

**Solutions:**
1. Verify credentials in `.env` file
2. Check Neo4j instance is running (Aura or local)
3. Test connection:
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    "neo4j+s://your-url",
    auth=("neo4j", "your-password")
)
with driver.session() as session:
    result = session.run("RETURN 1")
    print(result.single()[0])  # Should print 1
```

### Out of Memory Errors

**Problem:** "Out of memory" during graph building

**Solutions:**
1. Reduce `--num_patients` (start with 5)
2. Use a smaller Ollama model (`phi3` instead of `llama3`)
3. Close other applications
4. Build in batches:
```bash
# Build bottom + middle first
python three_layer_import_ollama.py --bottom dataset/umls --middle dataset/medc_k

# Then add top layer in batches
python build_three_layer_ollama.py --num_patients 10
```

### Slow Performance

**Problem:** Queries take >60 seconds

**Solutions:**
1. Use `vector_retrieve_ollama.py` instead of `retrieve_ollama.py` (20x faster)
2. Use a faster model (`phi3` vs `llama3`)
3. Reduce context limits in `utils_ollama.py`:
   - Change `limit 50` to `limit 25` in queries
4. Enable GPU acceleration for Ollama (if you have a GPU)

### No Results Returned

**Problem:** System returns "No matching subgraph found"

**Solutions:**
1. Check if graph is built:
```python
# Count nodes in Neo4j
MATCH (n) RETURN count(n)
```
2. Rebuild Summary embeddings:
```bash
python vector_retrieve_ollama.py --regenerate-embeddings
```
3. Lower similarity threshold in `vector_retrieve_ollama.py` (line 195)

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'X'`

**Solutions:**
```bash
# Reinstall dependencies
conda activate medgraphrag
pip install -r requirements_windows.txt

# Or recreate environment
conda env remove -n medgraphrag
conda env create -f medgraphrag.yml
```

---

## ⚡ Performance

### Query Time Breakdown

| Stage | Time (Sequential) | Time (Vector) |
|-------|------------------|---------------|
| Embedding Generation | 2-3s | 2-3s |
| Subgraph Matching | 20-40s | 3-5s |
| Context Retrieval | <1s | <1s |
| Answer Generation (2-pass) | 25-40s | 25-40s |
| **Total** | **50-85s** | **30-50s** |

### Optimization Tips

**Use Vector Retrieval:**
```python
# 20x faster than sequential
from vector_retrieve_ollama import vector_ret_ollama
gid = vector_ret_ollama(n4j, question, model="llama3")
```

**Choose Faster Models:**
- `phi3`: Fastest (2.3GB), good quality
- `llama3`: Balanced (4.7GB), best quality
- `mistral`: Alternative (4.1GB)

**Adjust Context Limits:**
In `utils_ollama.py`, reduce `LIMIT 50` to `LIMIT 25` for faster retrieval.

**Use GPU:**
Ollama automatically uses GPU if available (NVIDIA, AMD, or Apple Silicon).

---

## 📖 Citation

If you use this system in your research, please cite:

```bibtex
@article{wu2024medical,
  title={Medical Graph RAG: Towards Safe Medical Large Language Model via Graph Retrieval-Augmented Generation},
  author={Wu, Junde and Zhu, Jiayuan and Qi, Yunli},
  journal={arXiv preprint arXiv:2408.04187},
  year={2024}
}
```

**Original Paper:** [https://arxiv.org/abs/2408.04187](https://arxiv.org/abs/2408.04187)

---

## 🙏 Acknowledgments

- **CAMEL Framework**: [github.com/camel-ai/camel](https://github.com/camel-ai/camel)
- **Ollama**: [ollama.ai](https://ollama.ai)
- **Neo4j**: [neo4j.com](https://neo4j.com)
- **MIMIC-IV**: [physionet.org/content/mimiciv](https://physionet.org/content/mimiciv/3.0/)
- **UMLS**: [nlm.nih.gov/research/umls](https://www.nlm.nih.gov/research/umls/index.html)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

**Areas for contribution:**
- Adding support for more Ollama models
- Performance optimizations
- UI improvements
- Documentation enhancements
- Bug fixes

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/BenharJohn/TrustMed-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/BenharJohn/TrustMed-AI/discussions)
- **Original Paper**: [arXiv:2408.04187](https://arxiv.org/abs/2408.04187)

---

**Made with ❤️ for the medical AI community**

*Disclaimer: This system is for research and educational purposes only. Always consult qualified healthcare professionals for medical advice.*
