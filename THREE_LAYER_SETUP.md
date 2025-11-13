# Three-Layer Medical Knowledge Graph Setup Guide

## Overview

This guide explains how to build and query the complete three-layer medical knowledge graph architecture:

- **Bottom Layer (UMLS)**: Medical terminology and definitions
- **Middle Layer (MedC-K)**: Clinical guidelines and reference knowledge
- **Top Layer (MIMIC-IV)**: Patient medical records

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Top Layer: MIMIC-IV Patient Records     │
│         (Specific patient cases & outcomes)     │
└───────────────────┬─────────────────────────────┘
                    │ REFERENCE relationships
                    │ (semantic similarity > 0.6)
┌───────────────────┴─────────────────────────────┐
│      Middle Layer: MedC-K Clinical Guidelines   │
│      (Evidence-based treatment protocols)       │
└───────────────────┬─────────────────────────────┘
                    │ REFERENCE relationships
                    │ (semantic similarity > 0.6)
┌───────────────────┴─────────────────────────────┐
│       Bottom Layer: UMLS Medical Terminology    │
│       (Standardized medical definitions)        │
└─────────────────────────────────────────────────┘
```

## Prerequisites

1. **Neo4j Aura DB** account (free tier available)
   - Already configured in your `.env` file
   - URL: `neo4j+s://91cdd753.databases.neo4j.io`

2. **Google Gemini API** key
   - Already configured in your `.env` file
   - Using Gemini Flash for text generation (15 RPM)
   - Using embedding-001 for vector embeddings (768-dim)

3. **Conda environment** `medgraphrag`
   - Already created and configured

## Data Sources

### Bottom Layer: UMLS Medical Terminology
- **Location**: `dataset/umls/cardiac_terms.txt`
- **Content**: Medical terminology definitions
- **Examples**: Cardiac Arrest, Myocardial Infarction, Atrial Fibrillation, Creatine, etc.
- **Purpose**: Provides standardized medical vocabulary

### Middle Layer: MedC-K Clinical Guidelines
- **Location**: `dataset/medc_k/cardiac_guidelines.txt`
- **Content**: Evidence-based clinical guidelines
- **Examples**:
  - ACLS Cardiac Arrest Management
  - Acute MI Treatment Protocols
  - Heart Failure Management (4-pillar therapy)
  - Atrial Fibrillation Management
  - Creatine Supplementation Safety Guidelines
- **Purpose**: Provides clinical context and treatment protocols

### Top Layer: MIMIC-IV Patient Records
- **Location**: `dataset/mimic_ex/dataset/`
- **Content**: De-identified patient medical records
- **Size**: 89,830 reports total (subset used for demo)
- **Purpose**: Real-world patient cases and outcomes

## Step-by-Step Build Process

### Step 1: Build the Three-Layer Graph

Run the build script to import all layers into Neo4j:

```bash
# Import 10 patient records (default, faster for testing)
conda run -n medgraphrag python build_three_layer_graph.py

# Import more patient records
conda run -n medgraphrag python build_three_layer_graph.py --num_patients 50

# Import all patient records (takes longer)
conda run -n medgraphrag python build_three_layer_graph.py --num_patients 89830

# Clear existing database first (WARNING: deletes all data)
conda run -n medgraphrag python build_three_layer_graph.py --clear_db

# Skip cross-layer linking (faster for testing)
conda run -n medgraphrag python build_three_layer_graph.py --skip_linking

# Skip entity merging (faster for testing)
conda run -n medgraphrag python build_three_layer_graph.py --skip_merging
```

### What the Build Script Does

1. **Connects to Neo4j Aura DB** using credentials from `.env`

2. **Imports Bottom Layer (UMLS)**:
   - Loads `dataset/umls/cardiac_terms.txt`
   - Extracts medical entities using Gemini
   - Creates knowledge graph with unique GID
   - Stores in Neo4j

3. **Imports Middle Layer (MedC-K)**:
   - Loads `dataset/medc_k/cardiac_guidelines.txt`
   - Extracts clinical guidelines and protocols
   - Creates knowledge graph with unique GID
   - Stores in Neo4j

4. **Imports Top Layer (MIMIC-IV)**:
   - Loads patient reports from `dataset/mimic_ex/dataset/`
   - Processes each patient record
   - Creates individual patient knowledge graphs
   - Stores in Neo4j with unique GIDs

5. **Creates Cross-Layer Semantic Links**:
   - Links Bottom ↔ Middle (UMLS terms to clinical guidelines)
   - Links Middle ↔ Top (clinical guidelines to patient cases)
   - Links Bottom ↔ Top (medical terms to patient records)
   - Uses cosine similarity > 0.6 threshold
   - Creates REFERENCE relationships in Neo4j

6. **Merges Similar Entities**:
   - Identifies duplicate entities across layers
   - Merges nodes with high similarity
   - Consolidates knowledge graph

7. **Saves Layer GIDs**:
   - Writes `layer_gids.txt` with all graph IDs
   - Frontend uses this to query specific layers

### Step 2: Verify the Build

Check the console output for statistics:

```
📊 GRAPH STATISTICS
============================================================

🔵 Bottom Layer (UMLS):
   Subgraphs: 1
   Nodes: 125

🟢 Middle Layer (MedC-K):
   Subgraphs: 1
   Nodes: 267

🔴 Top Layer (MIMIC-IV):
   Subgraphs: 10
   Nodes: 1,432

🔗 Cross-Layer Links:
   REFERENCE relationships: 847
```

### Step 3: Launch the Frontend

```bash
launch_frontend.bat
```

Or manually:

```bash
conda run -n medgraphrag streamlit run frontend/app.py
```

### Step 4: Query the Three-Layer Graph

1. **Open browser**: http://localhost:8501

2. **Enable Process Flow Visualization**:
   - Check "Show Process Flow" in sidebar
   - See real-time processing through layers

3. **Select Query Mode**:
   - **Global**: Uses community reports (best for broad questions)
   - **Local**: Uses entity embeddings (best for specific questions)

4. **Ask Questions**:

   **Example queries that use multiple layers**:

   - "What is cardiac arrest and how is it managed?"
     - Uses Bottom Layer: Definition of cardiac arrest
     - Uses Middle Layer: ACLS management guidelines
     - Uses Top Layer: Patient cases with cardiac arrest

   - "Is there any issue if I take creatine?"
     - Uses Bottom Layer: Creatine vs creatinine distinction
     - Uses Middle Layer: Creatine supplementation safety guidelines
     - Provides evidence-based answer

   - "What treatments are recommended for heart failure with reduced ejection fraction?"
     - Uses Bottom Layer: HFrEF, LVEF definitions
     - Uses Middle Layer: 4-pillar therapy guidelines
     - Uses Top Layer: Patient outcomes with HFrEF

## Understanding the Process Flow Visualization

When enabled, you'll see:

### Layer Diagram
```
┌─────────────────────────────────┐
│  🔝 Top Layer                   │
│  Patient Records (MIMIC-IV)     │
│  Current active data            │
└─────────────────────────────────┘
         ↕ REFERENCE
┌─────────────────────────────────┐
│  🟢 Middle Layer                │
│  Clinical Guidelines (MedC-K)   │
│  Treatment protocols            │
└─────────────────────────────────┘
         ↕ REFERENCE
┌─────────────────────────────────┐
│  🔵 Bottom Layer                │
│  Medical Terminology (UMLS)     │
│  Standardized definitions       │
└─────────────────────────────────┘
```

### Processing Steps

For each query, you'll see:

1. ⏳ **Query Initialization** - Setting up query parameters
2. ⏳ **Entity Extraction** - Identifying medical entities
3. ⏳ **Bottom Layer Search** - Searching UMLS for definitions
4. ⏳ **Middle Layer Search** - Searching clinical guidelines
5. ⏳ **Top Layer Search** - Searching patient records
6. ⏳ **Cross-Layer Integration** - Following REFERENCE relationships
7. ⏳ **Answer Generation** - Synthesizing final answer
8. ✅ **Complete** - Answer ready

## Querying with Python

You can also query the graph programmatically:

```python
from camel.storages import Neo4jGraph
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Connect to Neo4j
n4j = Neo4jGraph(
    url=os.getenv("NEO4J_URL"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# Load layer GIDs
with open("layer_gids.txt") as f:
    for line in f:
        if line.startswith("TOP_LAYER_GIDS="):
            top_gids = line.split("=")[1].strip().split(",")

# Query a specific patient graph
gid = top_gids[0]  # First patient
result = n4j.query("""
    MATCH (n) WHERE n.gid = $gid
    RETURN n.name, labels(n)
    LIMIT 10
""", {'gid': gid})

for record in result:
    print(f"{record['n.name']}: {record['labels(n)']}")

# Query with cross-layer following
result = n4j.query("""
    MATCH (patient) WHERE patient.gid = $gid
    MATCH (patient)-[:REFERENCE*1..2]-(related)
    WHERE related.gid <> $gid
    RETURN patient.name, related.name, labels(related)
    LIMIT 10
""", {'gid': gid})
```

## Comparison: Simple Mode vs Three-Layer Mode

### Simple Mode (Previous)
- ❌ Single patient report
- ❌ No medical terminology reference
- ❌ No clinical guidelines
- ❌ Limited knowledge base
- ❌ Cannot answer questions outside patient record
- ✅ Fast setup
- ✅ Low API usage

### Three-Layer Mode (Current)
- ✅ Multiple patient records
- ✅ UMLS medical terminology (standardized definitions)
- ✅ MedC-K clinical guidelines (evidence-based protocols)
- ✅ Comprehensive knowledge base
- ✅ Can answer general medical questions
- ✅ Cross-layer semantic linking
- ⚠️ Longer build time
- ⚠️ Higher API usage during build

## Troubleshooting

### Issue: API Rate Limit Errors

**Solution**: The script uses `best_model_max_async=2` to limit concurrent requests. If you still hit rate limits:

```python
# Edit build_three_layer_graph.py
# Reduce concurrent requests in creat_metagraph calls
```

### Issue: Neo4j Connection Failed

**Solution**: Verify credentials in `.env`:

```bash
NEO4J_URL=neo4j+s://91cdd753.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=6xE8xaDVlNLCQphT4UmbZWygnP6YhExozHToAl6yvhQ
```

### Issue: Out of Memory

**Solution**: Import fewer patients:

```bash
conda run -n medgraphrag python build_three_layer_graph.py --num_patients 5
```

### Issue: Cross-Layer Links Not Created

**Solution**: Check similarity threshold in `utils.py`:

```python
# Reduce threshold from 0.6 to 0.5 for more links
WHERE similarity > 0.5  # instead of 0.6
```

## Next Steps

1. **Build the graph** with 10 patients to test
2. **Query and evaluate** answer quality
3. **Import more patients** if results are good
4. **Customize layers** with your own data sources

## File Structure

```
Medical-Graph-RAG/
├── build_three_layer_graph.py    # Main build script
├── layer_gids.txt                 # Generated layer IDs
├── dataset/
│   ├── umls/
│   │   └── cardiac_terms.txt      # Medical terminology
│   ├── medc_k/
│   │   └── cardiac_guidelines.txt # Clinical guidelines
│   └── mimic_ex/
│       └── dataset/               # Patient records
│           ├── report_0.txt
│           ├── report_1.txt
│           └── ...
├── frontend/
│   └── app.py                     # Streamlit UI
└── .env                           # API keys & credentials
```

## Technical Details

### Knowledge Graph Creation

Each layer uses the CAMEL Knowledge Graph Agent to:

1. **Extract entities** from text using Gemini
2. **Identify relationships** between entities
3. **Generate embeddings** for semantic search
4. **Store in Neo4j** with unique graph ID (GID)

### Cross-Layer Linking

The `ref_link()` function:

1. Matches nodes with **same labels** across different GIDs
2. Computes **cosine similarity** on embeddings
3. Creates **REFERENCE relationship** if similarity > 0.6
4. Enables multi-hop queries across layers

### Query Processing

When you ask a question:

1. **Entity extraction**: Identifies medical terms in query
2. **Bottom layer lookup**: Finds definitions in UMLS
3. **Middle layer lookup**: Finds relevant guidelines in MedC-K
4. **Top layer lookup**: Finds relevant patient cases
5. **Cross-layer traversal**: Follows REFERENCE relationships
6. **Answer synthesis**: Combines information using Gemini

## Resources

- **CAMEL Documentation**: https://docs.camel-ai.org/
- **Neo4j Cypher Query Language**: https://neo4j.com/docs/cypher-manual/
- **Google Gemini API**: https://ai.google.dev/docs
- **MIMIC-IV Dataset**: https://physionet.org/content/mimiciv/

## Support

For issues or questions:
1. Check this guide first
2. Review console output for error messages
3. Check Neo4j Aura DB console for graph status
4. Verify API keys and credentials in `.env`
