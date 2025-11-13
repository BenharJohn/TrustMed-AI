# Quick Start Guide - Official Three-Layer Medical Graph RAG

## ✅ System Verified and Ready

The official research paper implementation using Ollama has been fully tested and verified. See [TEST_RESULTS.md](TEST_RESULTS.md) for detailed test results.

## Prerequisites

1. **Ollama** installed with llama3 model
   ```bash
   ollama pull llama3
   ```

2. **Neo4j Aura DB** account and credentials in `.env` file

3. **Python environment** with dependencies installed
   ```bash
   pip install -r requirements.txt
   ```

## Quick Test (5 minutes)

Test the system with existing data:

```bash
cd Medical-Graph-RAG
python -c "
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

question = 'What is cardiac arrest?'
print(f'Question: {question}')

gid = seq_ret_ollama(n4j, question, 'llama3')
answer = get_response_ollama(n4j, gid, question, 'llama3')

print('\nAnswer:')
print(answer)
"
```

Expected: Comprehensive medical answer about cardiac arrest in ~30-45 seconds.

## Full Setup (30-60 minutes)

### Step 1: Build Complete Three-Layer Graph

```bash
python three_layer_import_ollama.py \
  --clear \
  --bottom dataset/umls \
  --middle dataset/medc_k \
  --top dataset/mimic_ex/dataset \
  --trinity \
  --model llama3
```

**What this does:**
- Processes all medical texts in three layers (UMLS, MedC-K, MIMIC-IV)
- Extracts entities and relationships with Ollama
- Creates Summary nodes for each document
- Generates embeddings for all entities
- Creates cross-layer REFERENCE links (Trinity architecture)
- Saves GIDs to `layer_gids.txt`

**Expected time:** 30-60 minutes (depending on data size and Ollama processing speed)

**Monitor progress:**
```bash
tail -f build_log.txt
```

### Step 2: Verify Graph Structure

```bash
python -c "
from dotenv import load_dotenv
import os
from camel.storages import Neo4jGraph

load_dotenv()

n4j = Neo4jGraph(
    url=os.getenv('NEO4J_URL'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# Summary nodes
result = n4j.query('MATCH (s:Summary) RETURN count(s) as count')
print(f'Summary nodes: {result[0][\"count\"]}')

# Total entities
result = n4j.query('MATCH (n) WHERE NOT n:Summary RETURN count(n) as count')
print(f'Entity nodes: {result[0][\"count\"]}')

# REFERENCE links
result = n4j.query('MATCH ()-[r:REFERENCE]->() RETURN count(r) as count')
print(f'Cross-layer links: {result[0][\"count\"]}')

# Entity types
result = n4j.query('''
    MATCH (n) WHERE NOT n:Summary
    RETURN labels(n)[0] as type, count(*) as count
    ORDER BY count DESC
    LIMIT 10
''')
print('\nEntity types:')
for r in result:
    print(f'  {r[\"type\"]}: {r[\"count\"]}')
"
```

Expected output:
```
Summary nodes: [number of documents processed]
Entity nodes: [hundreds to thousands depending on data]
Cross-layer links: [semantic relationships between layers]

Entity types:
  Disease: ...
  Medication: ...
  Symptom: ...
  Procedure: ...
```

### Step 3: Launch Frontend

```bash
streamlit run frontend/official_frontend_ollama.py
```

Open browser to http://localhost:8501

### Step 4: Ask Questions

Try these test questions:

**Medical Definitions (Bottom Layer - UMLS):**
- "What is cardiac arrest?"
- "Define myocardial infarction"
- "What is atrial fibrillation?"

**Treatment Guidelines (Middle Layer - MedC-K):**
- "How to treat heart failure?"
- "Treatment for acute coronary syndrome"
- "Management of arrhythmias"

**Patient Cases (Top Layer - MIMIC-IV):**
- "Tell me about patient with chest pain"
- "Cases of cardiac arrest treatment"

**Cross-Layer Questions (Tests Trinity Links):**
- "What is heart failure and how is it treated?"
- "Explain atrial fibrillation from definition to treatment to patient outcomes"

## Understanding the Results

### System Process Flow

When you ask a question, the system:

1. **Creates Question Summary** (Ollama)
   - Summarizes your question in 2-3 sentences

2. **Finds Best Match** (Summary-based Retrieval)
   - Compares question summary with all Summary nodes in database
   - Uses Ollama to rate similarity: "very similar", "similar", "general", "not similar", "totally not similar"
   - Returns GID of best matching subgraph

3. **Retrieves Context** (Graph Traversal)
   - **Self Context**: Gets entities and relationships from matched GID
   - **Linked Context**: Follows REFERENCE links to other layers
   - Collects comprehensive multi-layer context

4. **Generates Answer** (Two-Pass Method)
   - **Pass 1**: Generates initial answer using self context
   - **Pass 2**: Refines answer with cross-layer linked context
   - Returns comprehensive, multi-layer answer

### Quality Indicators

Good answer should include:
- ✅ Medical definitions and terminology
- ✅ Relevant symptoms and causes
- ✅ Treatment approaches
- ✅ Clinical guidelines
- ✅ References to medical standards (e.g., AHA guidelines)
- ✅ Structured, clear presentation

## Performance Tips

### For Faster Processing:

1. **Use smaller model**: `--model phi3` (faster but slightly lower quality)
2. **Process fewer files**: Select subset of most important documents
3. **Limit data size**: Start with smaller dataset for testing

### For Better Quality:

1. **Use llama3**: Best balance of quality and speed
2. **Add more data**: More documents = more comprehensive knowledge
3. **Create more REFERENCE links**: Richer cross-layer connections

### Typical Processing Times (llama3):

- **Entity extraction**: ~10-30 seconds per document
- **Embedding generation**: ~1-2 seconds per entity
- **Cross-layer linking**: ~30-60 seconds for full graph
- **Query processing**: ~30-45 seconds per question

## Troubleshooting

### "No Summary nodes found"
- Build hasn't completed
- Check `build_log.txt` for errors
- Re-run build command

### "Ollama not running"
```bash
# Check Ollama status
ollama list

# Start Ollama if needed
ollama serve
```

### Slow performance
- Use smaller model: `--model phi3`
- Reduce data: Process fewer files
- Check Ollama is using GPU if available

### Connection errors
- Verify `.env` has correct Neo4j credentials
- Test Neo4j connection in web browser
- Check network connectivity

## File Structure

```
Medical-Graph-RAG/
├── creat_graph_ollama.py          # Entity extraction
├── three_layer_import_ollama.py   # Graph builder
├── retrieve_ollama.py              # Summary-based retrieval
├── utils_ollama.py                 # Answer generation
├── frontend/
│   └── official_frontend_ollama.py # Web UI
├── dataset/
│   ├── umls/                       # Bottom layer data
│   ├── medc_k/                     # Middle layer data
│   └── mimic_ex/dataset/           # Top layer data
├── TEST_RESULTS.md                 # Verification results
├── VERIFICATION_CHECKLIST.md       # Architecture comparison
├── README_OFFICIAL_SYSTEM.md       # Detailed documentation
└── QUICK_START.md                  # This file
```

## What Makes This "Official"?

This implementation matches the research paper methodology exactly:

1. ✅ **Entity-Relationship Graphs** (not just text storage)
2. ✅ **Summary Nodes** for semantic retrieval
3. ✅ **Three-Layer Architecture** (Bottom/Middle/Top)
4. ✅ **Cross-Layer REFERENCE Links** (Trinity connections)
5. ✅ **Summary-Based Retrieval** (LLM comparison, not keywords)
6. ✅ **Two-Pass Answer Generation** (self + linked context)
7. ✅ **Multi-Hop Reasoning** (follows relationships across layers)

The only difference: **Ollama instead of OpenAI** (free, unlimited, private)

## Next Steps

1. ✅ Quick test with existing data
2. ✅ Build full graph with all your medical texts
3. ✅ Launch frontend and ask questions
4. ✅ Verify cross-layer reasoning works
5. ✅ Add more data to expand knowledge base

## Support

- **Issues**: See [TEST_RESULTS.md](TEST_RESULTS.md) for known issues
- **Architecture**: See [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) for detailed comparison
- **Documentation**: See [README_OFFICIAL_SYSTEM.md](README_OFFICIAL_SYSTEM.md) for complete guide

Congratulations! You have the complete official research paper system working with Ollama! 🎉
