# Official Three-Layer Medical Graph RAG Setup with Ollama

## Overview
This document explains the complete official three-layer architecture implementation using Ollama instead of OpenAI.

## Architecture

### Three Layers:
1. **Bottom Layer (UMLS)**: Medical terminology and definitions
2. **Middle Layer (MedC-K)**: Clinical guidelines and protocols
3. **Top Layer (MIMIC-IV)**: Patient medical records

### Key Components:
- **Entity-Relationship Graphs**: Each layer contains medical entities (diseases, medications, symptoms, etc.) with relationships
- **Summary Nodes**: Each subgraph has a Summary node containing a text summary
- **Cross-Layer REFERENCE Links**: Trinity links connect related concepts across layers using embedding similarity
- **Embeddings**: All entities have Ollama-generated embeddings for semantic matching

## Files Created

### 1. `creat_graph_ollama.py`
- Extracts entities and relationships using Ollama
- Creates Summary nodes
- Generates embeddings for all entities
- Handles large files by chunking

Key functions:
- `creat_metagraph_ollama(content, gid, n4j, model)`: Main graph creation
- `extract_entities_and_relations(text, model)`: Entity extraction
- `get_ollama_embedding(text, model)`: Embedding generation

### 2. `three_layer_import_ollama.py`
- Imports all three layers
- Creates cross-layer REFERENCE links
- Official importer using Ollama

Usage:
```bash
python three_layer_import_ollama.py \
  --clear \
  --bottom dataset/umls \
  --middle dataset/medc_k \
  --top dataset/mimic_ex/dataset \
  --trinity \
  --model llama3
```

### 3. Next Steps to Complete

#### A. Complete `retrieve_ollama.py`
Need to implement:
- `seq_ret_ollama(n4j, question, model)`: Matches question to best Summary node
- Uses Ollama to compare question summary with all Summary nodes
- Returns the matching GID

#### B. Complete `utils_ollama.py`
Need to implement:
- `get_response_ollama(n4j, gid, question, model)`: Generates answer
- Retrieves context from matched GID
- Retrieves linked context from REFERENCE relationships
- Uses Ollama to generate final answer

#### C. Create Official Frontend
- Use Summary-based retrieval (not direct text search)
- Query flow:
  1. User asks question
  2. Create summary of question
  3. Find best matching Summary node using `seq_ret_ollama`
  4. Retrieve context from matched GID + linked GIDs
  5. Generate answer using Ollama

## Current Status

✅ **Completed:**
- Ollama-based entity extraction
- Embedding generation
- Summary node creation
- Three-layer import structure
- Large file handling (chunking)

⚠️ **In Progress:**
- ref_link function needs updating for Ollama embeddings
- Complete retrieval system

❌ **To Do:**
- Finish `retrieve_ollama.py`
- Create `utils_ollama.py`
- Build complete graph with all data
- Create official frontend
- End-to-end testing

## How It Works (Official Flow)

### Build Phase:
1. Read medical text file
2. Extract entities/relationships with Ollama
3. Create Summary node
4. Generate embeddings for all entities
5. Create entity nodes and relationship edges
6. Repeat for all files in each layer
7. Create cross-layer REFERENCE links using embedding similarity

### Query Phase:
1. User asks: "What is cardiac arrest?"
2. Create summary: "Question about cardiac arrest definition and management"
3. Compare with all Summary nodes in database
4. Find best match (e.g., Bottom layer UMLS cardiac_terms Summary)
5. Retrieve all entities/relationships from that GID
6. Follow REFERENCE links to Middle/Top layers
7. Collect context from all layers
8. Generate comprehensive answer using Ollama

## Differences from Our Simple System

**Simple System (what we did initially):**
- Stored full text in nodes
- Direct keyword search
- No entity extraction
- No Summary nodes
- Simple text matching

**Official System (what we're building now):**
- Entity-relationship graphs
- Summary-based retrieval using LLM comparison
- Structured knowledge representation
- Cross-layer semantic linking
- Multi-hop reasoning through REFERENCE relationships

## Next Commands to Run

Once complete, the full workflow will be:

```bash
# 1. Build the graph
python three_layer_import_ollama.py \
  --clear \
  --bottom dataset/umls \
  --middle dataset/medc_k \
  --top dataset/mimic_ex/dataset \
  --trinity \
  --model llama3

# 2. Run queries (after completing utils_ollama.py)
python -c "
from retrieve_ollama import seq_ret_ollama
from utils_ollama import get_response_ollama
from camel.storages import Neo4jGraph
import os

n4j = Neo4jGraph(
    url=os.getenv('NEO4J_URL'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

question = 'What is cardiac arrest?'
gid = seq_ret_ollama(n4j, question, 'llama3')
answer = get_response_ollama(n4j, gid, question, 'llama3')
print(answer)
"

# 3. Launch frontend
streamlit run frontend/official_frontend_ollama.py
```

## Why This Is Better

1. **Structured Knowledge**: Entities and relationships, not just text
2. **Multi-Layer Reasoning**: Can traverse from definitions → guidelines → patient cases
3. **Semantic Matching**: LLM-based summary comparison, not just keywords
4. **Explainable**: Can show which entities and relationships led to the answer
5. **Scalable**: Graph structure allows complex queries and reasoning

This is the complete official architecture from the research paper, adapted to use Ollama instead of OpenAI.
