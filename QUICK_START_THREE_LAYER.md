# Quick Start: Build Your Three-Layer Medical Knowledge Graph

## What You Have Now

✅ **Neo4j Aura DB** configured and connected
✅ **Google Gemini API** set up (Gemini Flash for text, embedding-001 for vectors)
✅ **Sample Data** ready:
   - Bottom Layer: UMLS medical terminology (`dataset/umls/cardiac_terms.txt`)
   - Middle Layer: Clinical guidelines (`dataset/medc_k/cardiac_guidelines.txt`)
   - Top Layer: Patient records (`dataset/mimic_ex/dataset/`)

## Current System (Simple Mode)

Your current system uses **simple mode** with:
- ❌ Only one patient report (report_0.txt)
- ❌ No medical dictionary (UMLS)
- ❌ No clinical guidelines (MedC-K)
- ❌ Limited answer quality

This is why queries like "is there any issue if i take creatine" couldn't be answered - the system only has data from one patient's record.

## New System (Three-Layer Mode)

The three-layer system will have:
- ✅ Multiple patient reports
- ✅ UMLS medical terminology (definitions for all medical terms)
- ✅ MedC-K clinical guidelines (treatment protocols, safety info)
- ✅ Cross-layer semantic linking (connects related information across layers)

## Build the Three-Layer Graph in 3 Steps

### Step 1: Build the Graph (5-10 minutes)

```bash
cd f:\Medgraph\Medical-Graph-RAG
conda run -n medgraphrag python build_three_layer_graph.py --num_patients 5
```

This will:
1. Connect to your Neo4j Aura DB
2. Import UMLS medical terminology
3. Import MedC-K clinical guidelines
4. Import 5 patient records
5. Create semantic links between all layers
6. Merge similar entities
7. Save layer IDs for the frontend

**Expected output:**
```
============================================================
🏗️  THREE-LAYER MEDICAL KNOWLEDGE GRAPH BUILDER
============================================================

🔗 Connecting to Neo4j Aura DB...
   URL: neo4j+s://91cdd753.databases.neo4j.io
✅ Connected to Neo4j Aura DB

============================================================
📚 BOTTOM LAYER: UMLS Medical Terminology
============================================================
📖 Loading: ./dataset/umls/cardiac_terms.txt
🔑 Graph ID: a1b2c3d4-...
🔄 Building knowledge graph from UMLS terms...
✅ Bottom layer imported successfully

[... continues for middle and top layers ...]

============================================================
📊 GRAPH STATISTICS
============================================================

🔵 Bottom Layer (UMLS):
   Subgraphs: 1
   Nodes: 125

🟢 Middle Layer (MedC-K):
   Subgraphs: 1
   Nodes: 267

🔴 Top Layer (MIMIC-IV):
   Subgraphs: 5
   Nodes: 732

🔗 Cross-Layer Links:
   REFERENCE relationships: 423

============================================================

✅ Three-layer graph build complete!
🚀 You can now run the frontend: python launch_frontend.bat
```

### Step 2: Launch the Frontend

```bash
launch_frontend.bat
```

Or:
```bash
conda run -n medgraphrag streamlit run frontend\app.py
```

### Step 3: Test Your Queries

Open http://localhost:8501 and try:

**1. Enable Process Flow Visualization**
   - Check "Show Process Flow" in the sidebar
   - See how your query flows through the three layers

**2. Ask Questions That Use Multiple Layers**

**Query 1: "What is cardiac arrest and how is it managed?"**
- Uses Bottom Layer: "Cardiac Arrest" definition from UMLS
- Uses Middle Layer: ACLS management protocol from MedC-K
- Uses Top Layer: Patient cases with cardiac arrest
- **Expected**: Comprehensive answer with definitions, guidelines, and real patient outcomes

**Query 2: "Is there any issue if I take creatine?"**
- Uses Bottom Layer: Creatine vs creatinine distinction from UMLS
- Uses Middle Layer: Creatine supplementation safety guidelines from MedC-K
- **Expected**: "Creatine supplementation is generally safe for healthy adults at 3-5g/day. The International Society of Sports Nutrition position states it's safe and effective when used appropriately. Contraindications include pre-existing kidney disease. Adequate hydration is recommended."

**Query 3: "What treatments are recommended for heart failure with reduced ejection fraction?"**
- Uses Bottom Layer: HFrEF, LVEF definitions
- Uses Middle Layer: 4-pillar therapy guidelines (ACE inhibitors, beta-blockers, MRAs, SGLT2 inhibitors)
- Uses Top Layer: Patient outcomes with HFrEF
- **Expected**: Detailed treatment protocol with medication specifics

## Understanding the Difference

### Before (Simple Mode):
```
Query: "is there any issue if i take creatine"
Answer: "Sorry, I'm not able to provide an answer to that question"
Reason: Only has one patient's cardiac record, no creatine information
```

### After (Three-Layer Mode):
```
Query: "is there any issue if i take creatine"
Answer: "Creatine supplementation is generally safe for healthy adults...
         [detailed safety information from clinical guidelines]"
Reason: Has access to medical terminology + clinical guidelines
```

## Options and Customization

### Import More Patients

```bash
# Import 10 patients (default)
conda run -n medgraphrag python build_three_layer_graph.py

# Import 50 patients (more data, takes longer)
conda run -n medgraphrag python build_three_layer_graph.py --num_patients 50

# Import all 89,830 patients (complete dataset, takes hours)
conda run -n medgraphrag python build_three_layer_graph.py --num_patients 89830
```

### Rebuild from Scratch

```bash
# Clear database and rebuild
conda run -n medgraphrag python build_three_layer_graph.py --clear_db --num_patients 5
```

### Fast Testing Mode

```bash
# Skip cross-layer linking and merging for faster builds
conda run -n medgraphrag python build_three_layer_graph.py --skip_linking --skip_merging --num_patients 2
```

## Troubleshooting

### "API quota exceeded"
- Gemini Flash has 15 requests/minute limit
- The script already limits concurrent requests to 2
- Wait 1 minute and try again
- Or reduce number of patients: `--num_patients 2`

### "Connection to Neo4j failed"
- Check `.env` file has correct credentials
- Verify Neo4j Aura DB is running (check web console)
- Check firewall/network connection

### "No module named 'langchain_google_genai'"
- This has been fixed by making imports conditional
- If you still see this, the script will skip grained chunking automatically

## Next Steps

1. **Build the graph** with 5 patients to start
2. **Test queries** with process flow visualization enabled
3. **Add more data** if you want:
   - More patient records (increase `--num_patients`)
   - Your own UMLS data (add to `dataset/umls/`)
   - Your own clinical guidelines (add to `dataset/medc_k/`)
4. **Monitor Neo4j** using the Aura DB web console to see your graph

## File Locations

- **Build script**: `build_three_layer_graph.py`
- **Bottom layer data**: `dataset/umls/cardiac_terms.txt`
- **Middle layer data**: `dataset/medc_k/cardiac_guidelines.txt`
- **Top layer data**: `dataset/mimic_ex/dataset/`
- **Frontend**: `frontend/app.py`
- **Layer IDs** (generated): `layer_gids.txt`
- **Detailed guide**: `THREE_LAYER_SETUP.md`

## Questions?

See [THREE_LAYER_SETUP.md](THREE_LAYER_SETUP.md) for comprehensive documentation including:
- Architecture details
- How cross-layer linking works
- Advanced querying with Python
- Customization options
- Full troubleshooting guide
