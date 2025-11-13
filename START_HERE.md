# Medical Graph RAG - Quick Start Guide

## Current Status

Your Medical Graph RAG system is set up with:
- ✅ Neo4j Aura DB configured and connected
- ✅ Gemini API configured (quota exhausted for today)
- ✅ Sample data created (UMLS, MedC-K, MIMIC-IV)
- ✅ Streamlit frontend ready
- ✅ Three build options available

## Three Ways to Build Your Knowledge Graph

### Option 1: Ollama (Local LLM) - **RECOMMENDED**
**Free, unlimited, runs on your computer**

1. **Install Ollama**: https://ollama.com/download
2. **Pull a model**:
   ```bash
   ollama pull llama3
   ```
3. **Build the graph**:
   ```bash
   python build_three_layer_ollama.py --num_patients 5 --model llama3
   ```

**Time**: 10-15 minutes for 5 patients
**Guide**: See [OLLAMA_SETUP.md](OLLAMA_SETUP.md)

### Option 2: OpenAI API
**Costs ~$1-2, works immediately**

1. **Get API key**: https://platform.openai.com/api-keys
2. **Add to `.env`**:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. **Build the graph**:
   ```bash
   python build_three_layer_graph.py --num_patients 5
   ```

**Time**: 5-10 minutes for 5 patients

### Option 3: Gemini API (Wait 24 hours)
**Free but daily quota exhausted**

- Your Gemini API quota will reset tomorrow
- Then run:
  ```bash
  python build_three_layer_gemini.py --num_patients 5
  ```

## What You'll Get

After building, your three-layer knowledge graph will contain:

**Bottom Layer (UMLS Medical Terminology)**
- Medical terms: Cardiac Arrest, Myocardial Infarction, Creatine, etc.
- Definitions and relationships
- Located in: `dataset/umls/cardiac_terms.txt`

**Middle Layer (MedC-K Clinical Guidelines)**
- Treatment protocols: ACLS, Acute MI management, Heart Failure therapy
- Safety guidelines: Creatine supplementation, medication protocols
- Located in: `dataset/medc_k/cardiac_guidelines.txt`

**Top Layer (MIMIC-IV Patient Records)**
- Real patient cases and outcomes
- Located in: `dataset/mimic_ex/dataset/`
- 89,830 reports available (you'll import 5-10 for testing)

**Cross-Layer Links**
- Semantic REFERENCE relationships connect related concepts across layers
- Enables multi-hop reasoning (e.g., patient symptom → clinical guideline → medical term)

## After Building

### 1. Launch the Frontend
```bash
launch_frontend.bat
```

Or:
```bash
streamlit run frontend\app.py
```

### 2. Open Browser
Navigate to: http://localhost:8501

### 3. Test Queries

Enable "Show Process Flow" in the sidebar to see how queries flow through layers.

**Try these questions**:

✅ **"What is cardiac arrest and how is it managed?"**
- Uses Bottom Layer for definition
- Uses Middle Layer for ACLS guidelines
- Uses Top Layer for patient outcomes

✅ **"Is there any issue if I take creatine?"**
- Uses Bottom Layer for creatine definition
- Uses Middle Layer for safety guidelines
- Provides evidence-based answer

✅ **"What treatments are recommended for heart failure with reduced ejection fraction?"**
- Uses Bottom Layer for HFrEF/LVEF definitions
- Uses Middle Layer for 4-pillar therapy
- Uses Top Layer for patient responses

## Why Your Current Answers Are Limited

You're currently running in **simple mode** which only has:
- ❌ One patient report
- ❌ No medical dictionary
- ❌ No clinical guidelines

This is why queries like "is there any issue if i take creatine" return:
> "Sorry, I'm not able to provide an answer to that question"

After building the three-layer graph, you'll have:
- ✅ Medical terminology (UMLS)
- ✅ Clinical guidelines (MedC-K)
- ✅ Multiple patient records
- ✅ Cross-layer semantic linking

## Files Created

```
Medical-Graph-RAG/
├── build_three_layer_ollama.py      # Ollama version (recommended)
├── build_three_layer_gemini.py      # Gemini version
├── build_three_layer_graph.py       # OpenAI version
├── OLLAMA_SETUP.md                  # Detailed Ollama setup guide
├── START_HERE.md                    # This file
├── dataset/
│   ├── umls/
│   │   └── cardiac_terms.txt        # Medical terminology
│   ├── medc_k/
│   │   └── cardiac_guidelines.txt   # Clinical guidelines
│   └── mimic_ex/
│       └── dataset/                 # Patient records
│           ├── report_0.txt
│           ├── report_1.txt
│           └── ... (89,830 total)
├── frontend/
│   └── app.py                       # Streamlit UI with visualization
└── .env                             # Your API keys and credentials
```

## Recommended Next Steps

1. **Install Ollama** (10 minutes)
   - Download from https://ollama.com/download
   - Pull llama3: `ollama pull llama3`

2. **Build your three-layer graph** (15 minutes)
   ```bash
   python build_three_layer_ollama.py --num_patients 5 --model llama3
   ```

3. **Launch the frontend**
   ```bash
   launch_frontend.bat
   ```

4. **Test queries** with process flow visualization enabled

5. **Scale up** if results are good:
   ```bash
   python build_three_layer_ollama.py --num_patients 20 --model llama3
   ```

## Troubleshooting

### "Cannot connect to Ollama"
- Install Ollama from https://ollama.com/download
- Pull a model: `ollama pull llama3`
- Verify it's running: `ollama list`

### "Gemini quota exceeded"
- Wait 24 hours for quota reset, or
- Use Ollama (free, unlimited), or
- Use OpenAI ($1-2)

### "Neo4j connection failed"
- Check `.env` file has correct credentials
- Verify Neo4j Aura DB is running at https://console.neo4j.io/

### Frontend won't start
- Make sure conda environment is activated
- Run: `conda activate medgraphrag`
- Then: `streamlit run frontend\app.py`

## Documentation

- **Ollama Setup**: [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
- **Three-Layer Architecture**: [THREE_LAYER_SETUP.md](THREE_LAYER_SETUP.md)
- **Quick Start**: [QUICK_START_THREE_LAYER.md](QUICK_START_THREE_LAYER.md)

## Support

If you have issues:
1. Check the documentation files above
2. Verify all prerequisites are installed
3. Check console output for specific error messages
4. Make sure API keys in `.env` are correct

## Summary

**Current State**: Simple mode with one patient report
**Goal**: Three-layer graph with UMLS + MedC-K + multiple patients
**Recommended**: Use Ollama (free, unlimited, works locally)
**Time**: 10-15 minutes setup + 15 minutes build
**Result**: Much better answers with medical terminology and clinical guidelines

Ready to start? Follow the Ollama setup in [OLLAMA_SETUP.md](OLLAMA_SETUP.md)!
