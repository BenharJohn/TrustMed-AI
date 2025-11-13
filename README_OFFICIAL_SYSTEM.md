# Official Three-Layer Medical Graph RAG with Ollama

## 🎉 Complete Implementation

This is the **complete official three-layer architecture** from the research paper, adapted to use **Ollama** (local LLM) instead of OpenAI. You now have a fully functional medical knowledge graph system with entity-relationship extraction, Summary-based retrieval, and multi-layer reasoning.

## 📋 What You Have Now

### ✅ Core System Components:

1. **`creat_graph_ollama.py`** - Entity & relationship extraction
2. **`three_layer_import_ollama.py`** - Three-layer graph builder
3. **`retrieve_ollama.py`** - Summary-based retrieval (seq_ret)
4. **`utils_ollama.py`** - Answer generation (get_response)
5. **`frontend/official_frontend_ollama.py`** - Web UI for queries

### ✅ Features:

- **Entity-Relationship Graphs**: Extracts diseases, medications, symptoms, procedures with typed relationships (CAUSES, TREATS, HAS_SYMPTOM, etc.)
- **Summary Nodes**: Each subgraph has an LLM-generated summary for semantic matching
- **Ollama Embeddings**: All entities have embeddings for similarity computation
- **Three Layers**:
  - **Bottom (UMLS)**: Medical terminology & definitions
  - **Middle (MedC-K)**: Clinical guidelines & protocols
  - **Top (MIMIC-IV)**: Patient medical records
- **Cross-Layer REFERENCE Links**: Trinity architecture connects concepts across layers
- **Two-Pass Answer Generation**: First uses matched subgraph, then refines with cross-layer references

## 🚀 How to Use

### Step 1: Build the Three-Layer Graph

```bash
# Full build with all data files
python three_layer_import_ollama.py \
  --clear \
  --bottom dataset/umls \
  --middle dataset/medc_k \
  --top dataset/mimic_ex/dataset \
  --trinity \
  --model llama3
```

**What this does:**
- Clears existing database
- Processes Bottom layer (UMLS medical terms)
- Processes Middle layer (MedC-K clinical guidelines)
- Processes Top layer (MIMIC-IV patient cases)
- Creates cross-layer REFERENCE links using embedding similarity
- Saves layer GIDs to `layer_gids.txt`

**Expected time:** 10-30 minutes depending on data size (embedding generation is slow but accurate)

### Step 2: Launch the Official Frontend

```bash
streamlit run frontend/official_frontend_ollama.py
```

Open http://localhost:8501

### Step 3: Ask Questions

**Example queries:**
- "What is cardiac arrest?"
- "How is atrial fibrillation treated?"
- "What are the symptoms of heart failure?"
- "Treatment guidelines for myocardial infarction"

**How it works:**
1. System creates summary of your question
2. Compares with all Summary nodes in database using LLM
3. Finds best matching subgraph (GID)
4. Retrieves entities & relationships from that GID
5. Follows REFERENCE links to get cross-layer context
6. Generates comprehensive answer using both contexts

## 📊 Architecture Explained

### Build Phase:

```
Medical Text File
    ↓
[Ollama Entity Extraction]
    ↓
Entities: Disease, Medication, Symptom, Procedure
Relationships: CAUSES, TREATS, HAS_SYMPTOM, etc.
    ↓
[Create Summary Node]
    ↓
[Generate Embeddings for All Entities]
    ↓
Neo4j Knowledge Graph (one subgraph with GID)
```

Repeat for all files → Multiple subgraphs

Then:
```
[Cross-Layer Linking]
    ↓
Compare embeddings between layers
    ↓
Create REFERENCE relationships (similarity > 0.6)
    ↓
Complete Three-Layer Graph
```

### Query Phase:

```
User Question
    ↓
[Create Summary]
    ↓
[Compare with all Summary Nodes using LLM]
    ↓
Find Best Match (GID)
    ↓
[Retrieve Context from Matched GID]
    ↓
[Retrieve Linked Context via REFERENCE relationships]
    ↓
[Generate Answer - Pass 1: Self Context]
    ↓
[Generate Answer - Pass 2: With Cross-Layer Context]
    ↓
Final Answer
```

## 🔧 Configuration

### Ollama Models:

The system supports any Ollama model:
- **llama3** (recommended - best quality, 4.7GB)
- **mistral** (faster, 4.1GB)
- **phi3** (smallest, 2.3GB)

Change model:
```bash
python three_layer_import_ollama.py --model mistral ...
```

Or in frontend sidebar.

### Neo4j Configuration:

Edit `.env` file:
```
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

## 📁 File Structure

```
Medical-Graph-RAG/
├── creat_graph_ollama.py          # Entity extraction with Ollama
├── three_layer_import_ollama.py   # Graph builder
├── retrieve_ollama.py              # Summary-based retrieval
├── utils_ollama.py                 # Answer generation
├── frontend/
│   └── official_frontend_ollama.py  # Web UI
├── dataset/
│   ├── umls/                       # Bottom layer data
│   ├── medc_k/                     # Middle layer data
│   └── mimic_ex/dataset/           # Top layer data
└── layer_gids.txt                  # Layer identifiers
```

## 🆚 vs Simple Text Search System

| Feature | Simple System | Official System (This) |
|---------|--------------|----------------------|
| **Storage** | Full text in nodes | Entities & relationships |
| **Retrieval** | Keyword search | LLM summary comparison |
| **Structure** | Flat text | Graph with typed relationships |
| **Cross-layer** | None | REFERENCE links with embeddings |
| **Reasoning** | Single-hop | Multi-hop through relationships |
| **Answer Quality** | Basic | Comprehensive with cross-layer context |

## 🧪 Testing

### Quick Test (Command Line):

```python
from dotenv import load_dotenv
import os
from camel.storages import Neo4jGraph
from retrieve_ollama import seq_ret_ollama
from utils_ollama import get_response_ollama

load_dotenv()

n4j = Neo4jGraph(
    url=os.getenv('NEO4J_URL'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

question = "What is cardiac arrest?"
gid = seq_ret_ollama(n4j, question, "llama3")
answer = get_response_ollama(n4j, gid, question, "llama3")
print(answer)
```

### Verify Graph Structure:

```python
# Check Summary nodes
result = n4j.query("MATCH (s:Summary) RETURN count(s) as count")
print(f"Summary nodes: {result[0]['count']}")

# Check entities
result = n4j.query("MATCH (n) WHERE NOT n:Summary RETURN count(n) as count")
print(f"Entity nodes: {result[0]['count']}")

# Check REFERENCE links
result = n4j.query("MATCH ()-[r:REFERENCE]->() RETURN count(r) as count")
print(f"Cross-layer links: {result[0]['count']}")

# Check entity types
result = n4j.query("""
    MATCH (n) WHERE NOT n:Summary
    RETURN labels(n)[0] as type, count(*) as count
    ORDER BY count DESC
""")
for r in result:
    print(f"{r['type']}: {r['count']}")
```

## 🐛 Troubleshooting

### "No Summary nodes found"
- Build hasn't completed or failed
- Check `build_log.txt` for errors
- Re-run build command

### "Ollama not running"
- Start Ollama: `ollama serve`
- Pull model: `ollama pull llama3`

### Slow performance
- Use smaller model: `--model phi3`
- Reduce data: Process fewer files
- Embeddings take time (unavoidable for quality)

### "Cannot invoke java.util.List.size() because vector1 is null"
- Some entities don't have embeddings
- Normal for first build
- Embeddings generated now, rebuild fixes this

## 📈 Next Steps

1. **Add More Data**: Put medical texts in dataset folders
2. **Experiment with Models**: Try different Ollama models
3. **Custom Queries**: Test with your specific medical questions
4. **Visualization**: Explore graph in Neo4j Browser
5. **Export Results**: Save answers for analysis

## 🎓 Understanding the System

**Key Concept**: This isn't just text search. It's a **knowledge graph** where:
- Medical concepts are **entities** (nodes)
- Medical facts are **relationships** (edges)
- Retrieval uses **semantic matching** (LLM compares summaries)
- Answers use **multi-hop reasoning** (follows relationships across layers)

**Example Flow:**
```
Question: "How to treat heart failure?"
    ↓
Summary: "Treatment for heart failure condition"
    ↓
Matches: MedC-K Clinical Guideline Summary
    ↓
Retrieves: HFrEF → REQUIRES → Beta-blockers
           HFrEF → REQUIRES → ACE-inhibitors
           (and 20 more relationships)
    ↓
Follow REFERENCE to UMLS:
           Beta-blockers → DEFINITION → (medical term)
    ↓
Follow REFERENCE to Patient Cases:
           Patient X → HAS_CONDITION → HFrEF
           Patient X → RECEIVED → Beta-blockers
    ↓
Generate Answer using all contexts:
"Heart failure treatment includes four pillars: ACE inhibitors,
beta-blockers, MRAs, and SGLT2 inhibitors. Evidence from patient
cases shows effectiveness..."
```

This is the **complete research paper implementation**. Congratulations! 🎉
