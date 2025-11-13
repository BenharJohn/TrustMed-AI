# Ollama Setup Guide for Medical Graph RAG

## What is Ollama?

Ollama allows you to run large language models locally on your computer. This means:
- **100% Free** - No API costs
- **Unlimited usage** - No rate limits
- **Private** - Your data never leaves your computer
- **Fast** - Once models are downloaded

## Step 1: Install Ollama

### Windows:
1. Go to https://ollama.com/download
2. Click "Download for Windows"
3. Run the installer (`OllamaSetup.exe`)
4. Follow the installation wizard

### Verify Installation:
Open Command Prompt or PowerShell and run:
```bash
ollama --version
```

You should see something like: `ollama version is 0.1.23`

## Step 2: Pull a Model

You need to download an LLM model. I recommend starting with **Llama 3** (best quality) or **Phi-3** (faster, smaller):

### Option A: Llama 3 (Recommended - Best Quality)
```bash
ollama pull llama3
```
- Size: ~4.7GB
- RAM needed: ~8GB
- Best for medical entity extraction

### Option B: Phi-3 (Faster Alternative)
```bash
ollama pull phi3
```
- Size: ~2.3GB
- RAM needed: ~4GB
- Good balance of speed and quality

### Option C: Mistral (Another Good Option)
```bash
ollama pull mistral
```
- Size: ~4.1GB
- RAM needed: ~8GB
- Great for structured output

**Note**: The first download will take 5-15 minutes depending on your internet speed. The model is saved locally and you only need to download it once.

## Step 3: Verify Ollama is Running

After pulling a model, test it:

```bash
ollama run llama3 "What is cardiac arrest?"
```

You should see a response from the model. Press Ctrl+C to exit the chat.

## Step 4: Build Your Three-Layer Graph

Now you're ready to build the three-layer medical knowledge graph!

### Basic Build (5 patients, Llama 3):
```bash
cd f:\Medgraph\Medical-Graph-RAG
python build_three_layer_ollama.py --num_patients 5 --model llama3
```

### With Phi-3 (faster):
```bash
python build_three_layer_ollama.py --num_patients 5 --model phi3
```

### More patients:
```bash
python build_three_layer_ollama.py --num_patients 10 --model llama3
```

### Clear database first:
```bash
python build_three_layer_ollama.py --num_patients 5 --model llama3 --clear_db
```

## Expected Build Time

| Model | Patients | Estimated Time |
|-------|----------|----------------|
| Llama 3 | 5 | 10-15 minutes |
| Llama 3 | 10 | 20-30 minutes |
| Phi-3 | 5 | 7-10 minutes |
| Phi-3 | 10 | 15-20 minutes |

**Note**: Times vary based on your CPU/GPU. First run may be slower as Ollama loads the model into memory.

## What the Script Does

1. **Connects to Neo4j** - Uses your Aura DB credentials
2. **Connects to Ollama** - Uses local LLM at `http://localhost:11434`
3. **Processes Bottom Layer** (UMLS):
   - Reads medical terminology from `dataset/umls/cardiac_terms.txt`
   - Extracts entities and relationships with Ollama
   - Stores in Neo4j with graph ID
4. **Processes Middle Layer** (MedC-K):
   - Reads clinical guidelines from `dataset/medc_k/cardiac_guidelines.txt`
   - Extracts entities and relationships
   - Stores in Neo4j
5. **Processes Top Layer** (MIMIC-IV):
   - Reads patient reports from `dataset/mimic_ex/dataset/`
   - Extracts patient-specific entities
   - Stores in Neo4j
6. **Creates Cross-Layer Links**:
   - Finds similar entities across layers
   - Creates REFERENCE relationships (similarity > 0.6)
7. **Saves layer IDs** to `layer_gids.txt`

## Troubleshooting

### Error: "Cannot connect to Ollama"

**Solution**: Make sure Ollama is running. After installation, it should start automatically. If not:

Windows:
- Look for Ollama in your system tray (bottom-right corner)
- If not there, search for "Ollama" in Start Menu and run it

Check if running:
```bash
curl http://localhost:11434/api/tags
```

Should return JSON with available models.

### Error: "Model 'llama3' not found"

**Solution**: You haven't pulled the model yet:
```bash
ollama pull llama3
```

### Ollama is Too Slow

**Solutions**:
1. Use a smaller model:
   ```bash
   ollama pull phi3
   python build_three_layer_ollama.py --model phi3
   ```

2. Process fewer patients:
   ```bash
   python build_three_layer_ollama.py --num_patients 2
   ```

3. Skip cross-layer linking (faster, but less connected graph):
   ```bash
   python build_three_layer_ollama.py --skip_linking
   ```

### Out of Memory

**Solution**: Use a smaller model or close other applications:
```bash
ollama pull phi3  # Smaller model
python build_three_layer_ollama.py --model phi3 --num_patients 3
```

## Comparing Models

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| **Llama 3** | 4.7GB | 8GB | Medium | Excellent | Best results |
| **Phi-3** | 2.3GB | 4GB | Fast | Good | Quick testing |
| **Mistral** | 4.1GB | 8GB | Medium | Very Good | Structured output |

## After Building

Once the build completes:

1. **Check the statistics**:
   ```
   Bottom Layer (UMLS): X nodes
   Middle Layer (MedC-K): Y nodes
   Top Layer (MIMIC-IV): Z nodes
   Cross-Layer Links: N REFERENCE relationships
   ```

2. **Launch the frontend**:
   ```bash
   launch_frontend.bat
   ```

3. **Test queries** at http://localhost:8501:
   - "What is cardiac arrest and how is it managed?"
   - "Is there any issue if I take creatine?"
   - "What treatments are recommended for heart failure?"

## Next Steps

- **Add more patient data**: Increase `--num_patients`
- **Try different models**: `--model mistral` or `--model phi3`
- **Query your graph**: Use the Streamlit frontend or query Neo4j directly
- **Customize data**: Add your own UMLS terms or clinical guidelines to the dataset folders

## Resources

- Ollama Website: https://ollama.com/
- Available Models: https://ollama.com/library
- Ollama GitHub: https://github.com/ollama/ollama
- Neo4j Browser: Log into your Aura DB to visualize the graph

## Quick Command Reference

```bash
# Install model
ollama pull llama3

# Test model
ollama run llama3 "Test question"

# Build graph
python build_three_layer_ollama.py --num_patients 5 --model llama3

# Launch frontend
launch_frontend.bat

# Check Ollama status
curl http://localhost:11434/api/tags
```
