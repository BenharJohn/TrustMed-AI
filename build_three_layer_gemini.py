"""
Three-Layer Medical Knowledge Graph Builder (Gemini-only version)

This script builds the complete three-layer medical knowledge graph using only Google Gemini:
- Bottom Layer: UMLS medical terminology
- Middle Layer: MedC-K clinical guidelines
- Top Layer: MIMIC-IV patient records

Usage:
    python build_three_layer_gemini.py --num_patients 5
"""

import os
import argparse
import re
from dotenv import load_dotenv
from camel.storages import Neo4jGraph
import google.generativeai as genai

# Load environment variables
load_dotenv()

class GeminiKnowledgeExtractor:
    """Simple knowledge graph extractor using Gemini"""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def extract_entities_and_relationships(self, text):
        """Extract medical entities and relationships from text using Gemini"""

        prompt = f"""You are a medical knowledge graph extractor. Analyze the following medical text and extract:
1. Medical entities (diseases, symptoms, medications, procedures, anatomical terms, etc.)
2. Relationships between entities

Format your response as:
ENTITIES:
- Entity1 (Type: disease/symptom/medication/procedure/anatomy/other)
- Entity2 (Type: ...)

RELATIONSHIPS:
- Entity1 -> RELATIONSHIP_TYPE -> Entity2
- Entity3 -> RELATIONSHIP_TYPE -> Entity4

Medical Text:
{text[:4000]}

Be precise and extract all significant medical entities and their relationships."""

        try:
            response = self.model.generate_content(prompt)
            return self._parse_gemini_response(response.text)
        except Exception as e:
            print(f"Warning: Gemini extraction failed: {e}")
            return {"entities": [], "relationships": []}

    def _parse_gemini_response(self, response_text):
        """Parse Gemini's response into structured format"""
        entities = []
        relationships = []

        lines = response_text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if 'ENTITIES:' in line.upper():
                current_section = 'entities'
                continue
            elif 'RELATIONSHIPS:' in line.upper():
                current_section = 'relationships'
                continue

            if current_section == 'entities' and line.startswith('-'):
                # Parse: - Entity1 (Type: disease)
                match = re.match(r'-\s*(.+?)\s*\(Type:\s*(\w+)\)', line)
                if match:
                    entity_name = match.group(1).strip()
                    entity_type = match.group(2).strip()
                    entities.append({
                        'name': entity_name,
                        'type': entity_type
                    })

            elif current_section == 'relationships' and '->' in line:
                # Parse: - Entity1 -> RELATIONSHIP_TYPE -> Entity2
                parts = [p.strip() for p in line.replace('-', '').split('->')]
                if len(parts) >= 3:
                    relationships.append({
                        'source': parts[0],
                        'relation': parts[1],
                        'target': parts[2]
                    })

        return {"entities": entities, "relationships": relationships}

    def get_embedding(self, text):
        """Get embedding for text using Gemini"""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text[:2000],  # Limit text length
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Warning: Embedding generation failed: {e}")
            # Return zero vector as fallback
            return [0.0] * 768


class ThreeLayerGraphBuilder:
    def __init__(self):
        """Initialize connection to Neo4j Aura DB"""
        self.url = os.getenv("NEO4J_URL")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        print("\n" + "=" * 60)
        print("THREE-LAYER MEDICAL KNOWLEDGE GRAPH BUILDER (Gemini)")
        print("=" * 60)
        print()
        print("Connecting to Neo4j Aura DB...")
        print(f"   URL: {self.url}")

        self.n4j = Neo4jGraph(
            url=self.url,
            username=self.username,
            password=self.password
        )

        print("Connected to Neo4j Aura DB")
        print()

        # Initialize Gemini extractor
        print("Initializing Gemini knowledge extractor...")
        self.extractor = GeminiKnowledgeExtractor()
        print("Gemini initialized")
        print()

        self.layer_gids = {
            'bottom': [],
            'middle': [],
            'top': []
        }

    def _generate_gid(self):
        """Generate unique graph ID"""
        import uuid
        return str(uuid.uuid4())

    def _add_to_neo4j(self, gid, entities, relationships, summary_text):
        """Add extracted knowledge to Neo4j"""

        # Create nodes
        for entity in entities:
            node_query = """
            MERGE (n:{label} {{name: $name, gid: $gid}})
            ON CREATE SET n.embedding = $embedding
            RETURN n
            """.format(label=entity['type'].capitalize())

            embedding = self.extractor.get_embedding(entity['name'])

            self.n4j.query(node_query, {
                'name': entity['name'],
                'gid': gid,
                'embedding': embedding
            })

        # Create relationships
        for rel in relationships:
            rel_query = """
            MATCH (a {{name: $source, gid: $gid}})
            MATCH (b {{name: $target, gid: $gid}})
            MERGE (a)-[r:{rel_type}]->(b)
            RETURN r
            """.format(rel_type=rel['relation'].upper().replace(' ', '_'))

            try:
                self.n4j.query(rel_query, {
                    'source': rel['source'],
                    'target': rel['target'],
                    'gid': gid
                })
            except Exception as e:
                # Relationship creation might fail if nodes don't exist
                pass

        # Add summary node
        summary_embedding = self.extractor.get_embedding(summary_text[:1000])
        summary_query = """
        CREATE (s:Summary {gid: $gid, content: $content, embedding: $embedding})
        RETURN s
        """
        self.n4j.query(summary_query, {
            'gid': gid,
            'content': summary_text[:1000],
            'embedding': summary_embedding
        })

    def clear_database(self):
        """Clear all existing data (optional - use with caution)"""
        print("WARNING: Clearing existing database...")
        self.n4j.query("MATCH (n) DETACH DELETE n")
        print("Database cleared")
        print()

    def import_bottom_layer(self):
        """Import UMLS medical terminology (Bottom Layer)"""
        print("=" * 60)
        print("BOTTOM LAYER: UMLS Medical Terminology")
        print("=" * 60)

        umls_path = "./dataset/umls/cardiac_terms.txt"

        if not os.path.exists(umls_path):
            print(f"Error: UMLS data not found at {umls_path}")
            return

        print(f"Loading: {umls_path}")

        with open(umls_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generate unique GID for bottom layer
        gid = self._generate_gid()
        self.layer_gids['bottom'].append(gid)

        print(f"Graph ID: {gid}")
        print("Extracting medical entities with Gemini...")

        # Extract knowledge using Gemini
        knowledge = self.extractor.extract_entities_and_relationships(content)

        print(f"   Found {len(knowledge['entities'])} entities")
        print(f"   Found {len(knowledge['relationships'])} relationships")

        print("Adding to Neo4j...")
        self._add_to_neo4j(gid, knowledge['entities'], knowledge['relationships'], content)

        print(f"Bottom layer imported successfully (GID: {gid})")
        print()

    def import_middle_layer(self):
        """Import MedC-K clinical guidelines (Middle Layer)"""
        print("=" * 60)
        print("MIDDLE LAYER: MedC-K Clinical Guidelines")
        print("=" * 60)

        medc_k_path = "./dataset/medc_k/cardiac_guidelines.txt"

        if not os.path.exists(medc_k_path):
            print(f"Error: MedC-K data not found at {medc_k_path}")
            return

        print(f"Loading: {medc_k_path}")

        with open(medc_k_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Generate unique GID for middle layer
        gid = self._generate_gid()
        self.layer_gids['middle'].append(gid)

        print(f"Graph ID: {gid}")
        print("Extracting clinical knowledge with Gemini...")

        # Extract knowledge using Gemini
        knowledge = self.extractor.extract_entities_and_relationships(content)

        print(f"   Found {len(knowledge['entities'])} entities")
        print(f"   Found {len(knowledge['relationships'])} relationships")

        print("Adding to Neo4j...")
        self._add_to_neo4j(gid, knowledge['entities'], knowledge['relationships'], content)

        print(f"Middle layer imported successfully (GID: {gid})")
        print()

    def import_top_layer(self, num_patients=None):
        """Import MIMIC-IV patient records (Top Layer)"""
        print("=" * 60)
        print("TOP LAYER: MIMIC-IV Patient Records")
        print("=" * 60)

        data_path = "./dataset/mimic_ex/dataset"

        if not os.path.exists(data_path):
            print(f"Error: Patient data not found at {data_path}")
            return

        # Get list of patient report files
        files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]

        if num_patients:
            files = files[:num_patients]

        print(f"Found {len(files)} patient reports to import")
        print(f"Source: {data_path}")
        print()

        for i, file_name in enumerate(files, 1):
            file_path = os.path.join(data_path, file_name)

            print(f"[{i}/{len(files)}] Processing: {file_name}")

            # Load patient report
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Generate unique GID for this patient
            gid = self._generate_gid()
            self.layer_gids['top'].append(gid)

            print(f"   Graph ID: {gid}")
            print(f"   Extracting patient data with Gemini...")

            # Extract knowledge using Gemini
            knowledge = self.extractor.extract_entities_and_relationships(content)

            print(f"   Found {len(knowledge['entities'])} entities, {len(knowledge['relationships'])} relationships")
            print(f"   Adding to Neo4j...")

            self._add_to_neo4j(gid, knowledge['entities'], knowledge['relationships'], content)

            print(f"   Patient {i} imported")
            print()

        print(f"Top layer: {len(files)} patient records imported")
        print()

    def create_cross_layer_links(self):
        """Create semantic links between layers using embeddings"""
        print("=" * 60)
        print("CROSS-LAYER SEMANTIC LINKING")
        print("=" * 60)
        print()

        total_links = 0

        # Link Bottom <-> Middle
        print("Linking Bottom (UMLS) <-> Middle (MedC-K)...")
        for bottom_gid in self.layer_gids['bottom']:
            for middle_gid in self.layer_gids['middle']:
                links = self._create_links_between_layers(bottom_gid, middle_gid)
                total_links += links
                print(f"   Created {links} links")

        # Link Middle <-> Top
        print()
        print("Linking Middle (MedC-K) <-> Top (Patient Records)...")
        for middle_gid in self.layer_gids['middle']:
            for top_gid in self.layer_gids['top'][:5]:  # Link first 5 patients
                links = self._create_links_between_layers(middle_gid, top_gid)
                total_links += links
                print(f"   Created {links} links")

        # Link Bottom <-> Top
        print()
        print("Linking Bottom (UMLS) <-> Top (Patient Records)...")
        for bottom_gid in self.layer_gids['bottom']:
            for top_gid in self.layer_gids['top'][:5]:  # Link first 5 patients
                links = self._create_links_between_layers(bottom_gid, top_gid)
                total_links += links
                print(f"   Created {links} links")

        print()
        print(f"Cross-layer linking complete: {total_links} REFERENCE relationships created")
        print()

    def _create_links_between_layers(self, gid1, gid2, threshold=0.6):
        """Create REFERENCE relationships between similar nodes in different layers"""

        link_query = """
        MATCH (a) WHERE a.gid = $gid1 AND NOT a:Summary AND EXISTS(a.embedding)
        WITH collect(a) AS GraphA
        MATCH (b) WHERE b.gid = $gid2 AND NOT b:Summary AND EXISTS(b.embedding)
        WITH GraphA, collect(b) AS GraphB
        UNWIND GraphA AS n
        UNWIND GraphB AS m
        WITH n, m, $threshold AS threshold
        WHERE n <> m AND EXISTS(n.embedding) AND EXISTS(m.embedding)
        WITH n, m, threshold,
            reduce(s = 0.0, i IN range(0, size(n.embedding)-1) |
                s + n.embedding[i] * m.embedding[i]) /
            (sqrt(reduce(s = 0.0, i IN range(0, size(n.embedding)-1) |
                s + n.embedding[i] * n.embedding[i])) *
             sqrt(reduce(s = 0.0, i IN range(0, size(m.embedding)-1) |
                s + m.embedding[i] * m.embedding[i]))) AS similarity
        WHERE similarity > threshold
        MERGE (m)-[:REFERENCE {similarity: similarity}]->(n)
        RETURN count(*) as link_count
        """

        try:
            result = self.n4j.query(link_query, {'gid1': gid1, 'gid2': gid2, 'threshold': threshold})
            return result[0]['link_count'] if result else 0
        except Exception as e:
            print(f"   Warning: Link creation failed: {e}")
            return 0

    def display_statistics(self):
        """Display graph statistics"""
        print("=" * 60)
        print("GRAPH STATISTICS")
        print("=" * 60)
        print()

        # Count nodes by layer
        stats = {}

        for layer_name, gids in self.layer_gids.items():
            total_nodes = 0
            for gid in gids:
                result = self.n4j.query(
                    "MATCH (n) WHERE n.gid = $gid RETURN count(n) as count",
                    {'gid': gid}
                )
                total_nodes += result[0]['count'] if result else 0
            stats[layer_name] = {
                'subgraphs': len(gids),
                'nodes': total_nodes
            }

        # Count relationships
        ref_rels = self.n4j.query("MATCH ()-[r:REFERENCE]->() RETURN count(r) as count")
        ref_count = ref_rels[0]['count'] if ref_rels else 0

        print(f"Bottom Layer (UMLS):")
        print(f"   Subgraphs: {stats['bottom']['subgraphs']}")
        print(f"   Nodes: {stats['bottom']['nodes']}")

        print(f"\nMiddle Layer (MedC-K):")
        print(f"   Subgraphs: {stats['middle']['subgraphs']}")
        print(f"   Nodes: {stats['middle']['nodes']}")

        print(f"\nTop Layer (MIMIC-IV):")
        print(f"   Subgraphs: {stats['top']['subgraphs']}")
        print(f"   Nodes: {stats['top']['nodes']}")

        print(f"\nCross-Layer Links:")
        print(f"   REFERENCE relationships: {ref_count}")

        print("\n" + "=" * 60)

    def save_gids(self):
        """Save layer GIDs to file for frontend use"""
        print()
        print("Saving layer GIDs for frontend...")

        with open("layer_gids.txt", "w") as f:
            f.write("# Three-Layer Graph IDs\n")
            f.write("# Generated by build_three_layer_gemini.py\n\n")
            f.write(f"BOTTOM_LAYER_GIDS={','.join(self.layer_gids['bottom'])}\n")
            f.write(f"MIDDLE_LAYER_GIDS={','.join(self.layer_gids['middle'])}\n")
            f.write(f"TOP_LAYER_GIDS={','.join(self.layer_gids['top'])}\n")

        print("Layer GIDs saved to layer_gids.txt")
        print()


def main():
    parser = argparse.ArgumentParser(description="Build Three-Layer Medical Knowledge Graph (Gemini-only)")
    parser.add_argument('--num_patients', type=int, default=10,
                        help='Number of patient reports to import (default: 10)')
    parser.add_argument('--clear_db', action='store_true',
                        help='Clear existing database before import (WARNING: deletes all data)')
    parser.add_argument('--skip_linking', action='store_true',
                        help='Skip cross-layer linking (faster for testing)')

    args = parser.parse_args()

    # Initialize builder
    builder = ThreeLayerGraphBuilder()

    # Optional: clear database
    if args.clear_db:
        builder.clear_database()

    # Import all three layers
    builder.import_bottom_layer()
    builder.import_middle_layer()
    builder.import_top_layer(num_patients=args.num_patients)

    # Create cross-layer semantic links
    if not args.skip_linking:
        builder.create_cross_layer_links()

    # Display statistics
    builder.display_statistics()

    # Save GIDs for frontend
    builder.save_gids()

    print()
    print("Three-layer graph build complete!")
    print("You can now run the frontend: launch_frontend.bat")
    print()


if __name__ == "__main__":
    main()
