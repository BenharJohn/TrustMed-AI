"""
Simple Three-Layer Text-Based Graph Builder
Stores full text chunks instead of extracting entities
This ensures all information is preserved for retrieval
"""

import os
from dotenv import load_dotenv
from camel.storages import Neo4jGraph
import hashlib
import argparse

load_dotenv()

def generate_simple_embedding(text):
    """Generate a simple hash-based embedding for text"""
    # Use first 128 characters for hash
    text_sample = text[:128].lower()
    hash_obj = hashlib.sha256(text_sample.encode())
    hash_bytes = hash_obj.digest()

    # Convert to list of floats in range [-1, 1]
    embedding = [(b / 127.5) - 1.0 for b in hash_bytes[:64]]
    return embedding

def add_text_node(n4j, text, node_type, gid, source_file):
    """Add a text node to Neo4j"""
    # Create a short name from first line or first 50 chars
    name = text.split('\n')[0][:100].strip()
    if not name:
        name = text[:50].strip()

    # Generate embedding
    embedding = generate_simple_embedding(text)

    # Create Cypher query to add node
    query = """
    CREATE (n:TextChunk)
    SET n.name = $name,
        n.full_text = $full_text,
        n.node_type = $node_type,
        n.gid = $gid,
        n.source = $source_file,
        n.embedding = $embedding
    RETURN n.name as name
    """

    result = n4j.query(query, {
        'name': name,
        'full_text': text,
        'node_type': node_type,
        'gid': gid,
        'source_file': source_file,
        'embedding': embedding
    })

    return result[0]['name'] if result else None

def build_text_graph(clear_db=False):
    """Build a simple text-based three-layer graph"""

    # Connect to Neo4j
    url = os.getenv("NEO4J_URL")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    print(f"Connecting to Neo4j at {url}...")
    n4j = Neo4jGraph(url=url, username=username, password=password)

    if clear_db:
        print("Clearing existing database...")
        n4j.query("MATCH (n) DETACH DELETE n")
        print("Database cleared!")

    # Generate layer IDs
    import uuid
    bottom_gid = str(uuid.uuid4())
    middle_gid = str(uuid.uuid4())
    top_gid = str(uuid.uuid4())

    # Layer 1: UMLS - Medical Terminology
    print("\nProcessing Bottom Layer (UMLS)...")
    umls_file = "dataset/umls/cardiac_terms.txt"
    if os.path.exists(umls_file):
        with open(umls_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by paragraph (double newline)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        # Skip header (first paragraph)
        terms = [p for p in paragraphs[1:] if ':' in p.split('\n')[0]]
        print(f"Found {len(terms)} UMLS terms")

        for i, term_text in enumerate(terms, 1):
            name = add_text_node(n4j, term_text, 'UMLS', bottom_gid, umls_file)
            print(f"  {i}. Added: {name}")

    # Layer 2: MedC-K - Clinical Guidelines
    print("\nProcessing Middle Layer (MedC-K)...")
    medc_file = "dataset/medc_k/cardiac_guidelines.txt"
    if os.path.exists(medc_file):
        with open(medc_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by guidelines
        guidelines = content.split('GUIDELINE ')[1:]  # Skip header
        print(f"Found {len(guidelines)} clinical guidelines")

        for i, guideline_text in enumerate(guidelines, 1):
            guideline_text = 'GUIDELINE ' + guideline_text.strip()
            name = add_text_node(n4j, guideline_text, 'MedC-K', middle_gid, medc_file)
            print(f"  {i}. Added: {name}")

    # Layer 3: MIMIC-IV - Patient Reports
    print("\nProcessing Top Layer (MIMIC-IV)...")
    mimic_dir = "dataset/mimic_ex/dataset"
    patient_files = sorted([f for f in os.listdir(mimic_dir) if f.startswith('report_')])[:5]
    print(f"Processing {len(patient_files)} patient reports")

    for i, filename in enumerate(patient_files, 1):
        filepath = os.path.join(mimic_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        name = add_text_node(n4j, content, 'MIMIC-IV', top_gid, filename)
        print(f"  {i}. Added: {name}")

    # Create semantic links between layers
    print("\nCreating cross-layer semantic links...")
    link_query = """
    MATCH (a:TextChunk), (b:TextChunk)
    WHERE a.gid <> b.gid
      AND a.embedding IS NOT NULL
      AND b.embedding IS NOT NULL
    WITH a, b,
         reduce(dot = 0.0, i IN range(0, size(a.embedding)-1) |
                dot + a.embedding[i] * b.embedding[i]) AS dot_product,
         sqrt(reduce(sum = 0.0, x IN a.embedding | sum + x*x)) AS norm_a,
         sqrt(reduce(sum = 0.0, x IN b.embedding | sum + x*x)) AS norm_b
    WITH a, b, dot_product / (norm_a * norm_b) AS similarity
    WHERE similarity > 0.6
    MERGE (a)-[r:REFERENCE {similarity: similarity}]->(b)
    RETURN count(r) as links_created
    """

    result = n4j.query(link_query)
    links_count = result[0]['links_created'] if result else 0
    print(f"Created {links_count} REFERENCE relationships")

    # Save layer GIDs
    with open('layer_gids.txt', 'w') as f:
        f.write("# Three-Layer Graph IDs\n")
        f.write(f"# Generated by build_simple_text_graph.py\n\n")
        f.write(f"BOTTOM_LAYER_GIDS={bottom_gid}\n")
        f.write(f"MIDDLE_LAYER_GIDS={middle_gid}\n")
        f.write(f"TOP_LAYER_GIDS={top_gid}\n")

    print(f"\nLayer GIDs saved to layer_gids.txt")
    print(f"\nBuild complete!")
    print(f"  Bottom Layer (UMLS): {len(terms)} nodes")
    print(f"  Middle Layer (MedC-K): {len(guidelines)} nodes")
    print(f"  Top Layer (MIMIC-IV): {len(patient_files)} nodes")
    print(f"  Cross-layer links: {links_count} REFERENCE relationships")

    return n4j

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build simple text-based three-layer graph')
    parser.add_argument('--clear_db', action='store_true', help='Clear database before building')
    args = parser.parse_args()

    build_text_graph(clear_db=args.clear_db)
    print("\nYou can now launch the frontend with: streamlit run frontend\\neo4j_app.py")
