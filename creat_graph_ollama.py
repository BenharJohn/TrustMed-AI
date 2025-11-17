"""
Ollama-based Knowledge Graph Creation
Replaces OpenAI KnowledgeGraphAgent with Ollama for entity extraction
"""

import requests
import json
import re
from camel.storages import Neo4jGraph
from utils import str_uuid

def call_ollama(prompt, model="llama3"):
    """Call Ollama API for text generation"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=300  # Increased timeout to 5 minutes
    )

    if response.status_code == 200:
        return response.json()['response']
    else:
        raise Exception(f"Ollama API error: {response.status_code}")

def get_ollama_embedding(text, model="nomic-embed-text"):
    """Get embedding from Ollama using nomic-embed-text (proper embedding model)"""
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": model,  # Use nomic-embed-text for fast, proper embeddings
            "prompt": text[:2000]  # Nomic supports longer text
        },
        timeout=30  # Nomic is much faster than llama3
    )

    if response.status_code == 200:
        return response.json()['embedding']
    else:
        raise Exception(f"Ollama embedding error: {response.status_code}")

def extract_entities_and_relations(text, model="llama3"):
    """
    Extract medical entities and relationships from text using Ollama
    For long text, processes in chunks
    Returns: (entities, relationships)
    """

    # If text is too long, process in chunks
    max_chunk_size = 2000
    all_entities = []
    all_relationships = []

    if len(text) > max_chunk_size:
        # Split into chunks
        chunks = []
        for i in range(0, len(text), max_chunk_size):
            chunks.append(text[i:i+max_chunk_size])

        print(f"    Processing {len(chunks)} chunks...")

        for idx, chunk in enumerate(chunks[:5]):  # Limit to first 5 chunks to avoid timeout
            entities, relationships = _extract_from_chunk(chunk, model)
            all_entities.extend(entities)
            all_relationships.extend(relationships)

            if (idx + 1) % 2 == 0:
                print(f"    Processed chunk {idx + 1}/{min(5, len(chunks))}")
    else:
        all_entities, all_relationships = _extract_from_chunk(text, model)

    # Deduplicate entities
    seen_entities = {}
    for entity in all_entities:
        key = entity['name'].lower()
        if key not in seen_entities:
            seen_entities[key] = entity

    return list(seen_entities.values()), all_relationships

def _extract_from_chunk(text, model="llama3"):
    """Extract from a single chunk"""
    prompt = f"""You are a medical knowledge graph extractor. Extract entities and relationships from the following medical text.

Medical Text:
{text[:2000]}

Extract:
1. Medical entities (diseases, symptoms, medications, procedures, body parts, measurements)
2. Relationships between entities

CRITICAL: If the text mentions drug contraindications, conditions that worsen with medications,
or drug interactions, use CONTRAINDICATED_IN, WORSENS, or INTERACTS_WITH relationships.

Format your response EXACTLY as:

ENTITIES:
- EntityName1 (Type: disease)
- EntityName2 (Type: medication)
- EntityName3 (Type: symptom)

RELATIONSHIPS:
- Entity1 CAUSES Entity2
- Entity2 TREATS Entity3
- Entity4 HAS_SYMPTOM Entity5
- Medication1 CONTRAINDICATED_IN Disease1
- Medication2 WORSENS Condition1

Use relationship types: CAUSES, TREATS, HAS_SYMPTOM, CONTRAINDICATED_IN, WORSENS,
INTERACTS_WITH, RECOMMENDS, REQUIRES, INDICATES, ASSOCIATED_WITH, PART_OF

Extract now:"""

    response = call_ollama(prompt, model)

    # Parse response
    entities = []
    relationships = []

    lines = response.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if 'ENTITIES:' in line:
            current_section = 'entities'
            continue
        elif 'RELATIONSHIPS:' in line:
            current_section = 'relationships'
            continue

        if current_section == 'entities' and line.startswith('-'):
            # Parse: - EntityName (Type: disease)
            match = re.search(r'-\s*(.+?)\s*\(Type:\s*(.+?)\)', line)
            if match:
                entity_name = match.group(1).strip()
                entity_type = match.group(2).strip()
                entities.append({'name': entity_name, 'type': entity_type})

        elif current_section == 'relationships' and line.startswith('-'):
            # Parse: - Entity1 CAUSES Entity2
            parts = line[1:].strip().split()
            if len(parts) >= 3:
                source = parts[0]
                rel_type = parts[1]
                target = ' '.join(parts[2:])
                relationships.append({
                    'source': source,
                    'type': rel_type,
                    'target': target
                })

    return entities, relationships

def create_summary(text, model="llama3"):
    """Create a summary of the medical text"""
    prompt = f"""Summarize the following medical text in 2-3 sentences focusing on key medical concepts, diagnoses, and treatments:

{text[:1500]}

Summary:"""

    return call_ollama(prompt, model)

def creat_metagraph_ollama(content, gid, n4j, model="llama3"):
    """
    Create a knowledge graph from medical text using Ollama

    Args:
        content: Medical text content
        gid: Graph ID for this subgraph
        n4j: Neo4jGraph instance
        model: Ollama model name

    Returns:
        Updated Neo4jGraph instance
    """

    print(f"  [Ollama] Extracting entities and relationships...")

    # Extract entities and relationships
    entities, relationships = extract_entities_and_relations(content, model)

    print(f"  [Ollama] Found {len(entities)} entities, {len(relationships)} relationships")

    # Create Summary node
    summary_text = create_summary(content, model)

    summary_query = """
    CREATE (s:Summary {
        id: $id,
        content: $content,
        gid: $gid
    })
    """

    n4j.query(summary_query, {
        'id': f"summary_{gid[:8]}",
        'content': summary_text,
        'gid': gid
    })

    print(f"  [Summary] Created: {summary_text[:60]}...")

    # Create entity nodes with embeddings
    print(f"  [Embeddings] Generating embeddings for entities...")
    for i, entity in enumerate(entities):
        # Capitalize entity type for label
        label = entity['type'].capitalize()
        if label not in ['Disease', 'Medication', 'Symptom', 'Procedure', 'BodyPart', 'Measurement']:
            label = 'Entity'

        # Generate embedding for entity
        try:
            embedding = get_ollama_embedding(entity['name'], model)
        except Exception as e:
            print(f"    Warning: Could not generate embedding for '{entity['name']}': {e}")
            embedding = None

        if embedding:
            create_query = f"""
            MERGE (n:{label} {{id: $id, gid: $gid}})
            ON CREATE SET n.name = $name, n.embedding = $embedding
            ON MATCH SET n.embedding = $embedding
            """

            n4j.query(create_query, {
                'id': entity['name'],
                'name': entity['name'],
                'gid': gid,
                'embedding': embedding
            })
        else:
            create_query = f"""
            MERGE (n:{label} {{id: $id, gid: $gid}})
            ON CREATE SET n.name = $name
            """

            n4j.query(create_query, {
                'id': entity['name'],
                'name': entity['name'],
                'gid': gid
            })

        if (i + 1) % 5 == 0:
            print(f"    Generated embeddings for {i + 1}/{len(entities)} entities")

    # Create relationships
    for rel in relationships:
        rel_query = f"""
        MATCH (a {{id: $source, gid: $gid}})
        MATCH (b {{id: $target, gid: $gid}})
        MERGE (a)-[r:{rel['type']}]->(b)
        """

        try:
            n4j.query(rel_query, {
                'source': rel['source'],
                'target': rel['target'],
                'gid': gid
            })
        except Exception as e:
            # Skip if nodes don't exist
            pass

    print(f"  [Graph] Created {len(entities)} nodes and {len(relationships)} relationships")

    return n4j
