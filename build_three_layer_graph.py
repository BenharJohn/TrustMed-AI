"""
Three-Layer Medical Knowledge Graph Builder

This script builds the complete three-layer medical knowledge graph:
- Bottom Layer: UMLS medical terminology
- Middle Layer: MedC-K clinical guidelines
- Top Layer: MIMIC-IV patient records

Usage:
    python build_three_layer_graph.py --num_patients 10
"""

import os
import argparse
from dotenv import load_dotenv
from camel.storages import Neo4jGraph
from utils import str_uuid, ref_link, merge_similar_nodes
from creat_graph import creat_metagraph
from dataloader import load_high

# Load environment variables
load_dotenv()

class ThreeLayerGraphBuilder:
    def __init__(self):
        """Initialize connection to Neo4j Aura DB"""
        self.url = os.getenv("NEO4J_URL")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        print(f"🔗 Connecting to Neo4j Aura DB...")
        print(f"   URL: {self.url}")

        self.n4j = Neo4jGraph(
            url=self.url,
            username=self.username,
            password=self.password
        )

        self.layer_gids = {
            'bottom': [],
            'middle': [],
            'top': []
        }

        print("✅ Connected to Neo4j Aura DB\n")

    def clear_database(self):
        """Clear all existing data (optional - use with caution)"""
        print("⚠️  Clearing existing database...")
        self.n4j.query("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared\n")

    def import_bottom_layer(self):
        """Import UMLS medical terminology (Bottom Layer)"""
        print("=" * 60)
        print("📚 BOTTOM LAYER: UMLS Medical Terminology")
        print("=" * 60)

        umls_path = "./dataset/umls/cardiac_terms.txt"

        if not os.path.exists(umls_path):
            print(f"❌ Error: UMLS data not found at {umls_path}")
            return

        print(f"📖 Loading: {umls_path}")
        content = load_high(umls_path)

        # Generate unique GID for bottom layer
        gid = str_uuid()
        self.layer_gids['bottom'].append(gid)

        print(f"🔑 Graph ID: {gid}")
        print("🔄 Building knowledge graph from UMLS terms...")

        # Create graph using creat_metagraph
        args = argparse.Namespace(
            ingraphmerge=False,
            grained_chunk=False
        )
        self.n4j = creat_metagraph(args, content, gid, self.n4j)

        print(f"✅ Bottom layer imported successfully (GID: {gid})\n")

    def import_middle_layer(self):
        """Import MedC-K clinical guidelines (Middle Layer)"""
        print("=" * 60)
        print("📋 MIDDLE LAYER: MedC-K Clinical Guidelines")
        print("=" * 60)

        medc_k_path = "./dataset/medc_k/cardiac_guidelines.txt"

        if not os.path.exists(medc_k_path):
            print(f"❌ Error: MedC-K data not found at {medc_k_path}")
            return

        print(f"📖 Loading: {medc_k_path}")
        content = load_high(medc_k_path)

        # Generate unique GID for middle layer
        gid = str_uuid()
        self.layer_gids['middle'].append(gid)

        print(f"🔑 Graph ID: {gid}")
        print("🔄 Building knowledge graph from clinical guidelines...")

        # Create graph using creat_metagraph
        args = argparse.Namespace(
            ingraphmerge=False,
            grained_chunk=False
        )
        self.n4j = creat_metagraph(args, content, gid, self.n4j)

        print(f"✅ Middle layer imported successfully (GID: {gid})\n")

    def import_top_layer(self, num_patients=None):
        """Import MIMIC-IV patient records (Top Layer)"""
        print("=" * 60)
        print("🏥 TOP LAYER: MIMIC-IV Patient Records")
        print("=" * 60)

        data_path = "./dataset/mimic_ex/dataset"

        if not os.path.exists(data_path):
            print(f"❌ Error: Patient data not found at {data_path}")
            return

        # Get list of patient report files
        files = [f for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))]

        if num_patients:
            files = files[:num_patients]

        print(f"📊 Found {len(files)} patient reports to import")
        print(f"📂 Source: {data_path}\n")

        args = argparse.Namespace(
            ingraphmerge=False,
            grained_chunk=False
        )

        for i, file_name in enumerate(files, 1):
            file_path = os.path.join(data_path, file_name)

            print(f"[{i}/{len(files)}] Processing: {file_name}")

            # Load patient report
            content = load_high(file_path)

            # Generate unique GID for this patient
            gid = str_uuid()
            self.layer_gids['top'].append(gid)

            print(f"   🔑 Graph ID: {gid}")
            print(f"   🔄 Building patient knowledge graph...")

            # Create graph
            self.n4j = creat_metagraph(args, content, gid, self.n4j)

            print(f"   ✅ Patient {i} imported\n")

        print(f"✅ Top layer: {len(files)} patient records imported\n")

    def create_cross_layer_links(self):
        """Create semantic links between layers"""
        print("=" * 60)
        print("🔗 CROSS-LAYER SEMANTIC LINKING")
        print("=" * 60)

        total_links = 0

        # Link Bottom → Middle
        print("\n📊 Linking Bottom (UMLS) ↔ Middle (MedC-K)...")
        for bottom_gid in self.layer_gids['bottom']:
            for middle_gid in self.layer_gids['middle']:
                print(f"   🔄 {bottom_gid[:8]}... ↔ {middle_gid[:8]}...")
                result = ref_link(self.n4j, bottom_gid, middle_gid)
                total_links += len(result) if result else 0

        # Link Middle → Top
        print("\n📊 Linking Middle (MedC-K) ↔ Top (Patient Records)...")
        for middle_gid in self.layer_gids['middle']:
            for top_gid in self.layer_gids['top'][:5]:  # Link first 5 patients to middle
                print(f"   🔄 {middle_gid[:8]}... ↔ {top_gid[:8]}...")
                result = ref_link(self.n4j, middle_gid, top_gid)
                total_links += len(result) if result else 0

        # Link Bottom → Top
        print("\n📊 Linking Bottom (UMLS) ↔ Top (Patient Records)...")
        for bottom_gid in self.layer_gids['bottom']:
            for top_gid in self.layer_gids['top'][:5]:  # Link first 5 patients to bottom
                print(f"   🔄 {bottom_gid[:8]}... ↔ {top_gid[:8]}...")
                result = ref_link(self.n4j, bottom_gid, top_gid)
                total_links += len(result) if result else 0

        print(f"\n✅ Cross-layer linking complete: {total_links} REFERENCE relationships created\n")

    def merge_similar_entities(self):
        """Merge similar nodes across all layers"""
        print("=" * 60)
        print("🔄 MERGING SIMILAR ENTITIES")
        print("=" * 60)

        print("🔄 Running similarity-based entity merging...")
        merge_similar_nodes(self.n4j, None)
        print("✅ Entity merging complete\n")

    def display_statistics(self):
        """Display graph statistics"""
        print("=" * 60)
        print("📊 GRAPH STATISTICS")
        print("=" * 60)

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

        print(f"\n🔵 Bottom Layer (UMLS):")
        print(f"   Subgraphs: {stats['bottom']['subgraphs']}")
        print(f"   Nodes: {stats['bottom']['nodes']}")

        print(f"\n🟢 Middle Layer (MedC-K):")
        print(f"   Subgraphs: {stats['middle']['subgraphs']}")
        print(f"   Nodes: {stats['middle']['nodes']}")

        print(f"\n🔴 Top Layer (MIMIC-IV):")
        print(f"   Subgraphs: {stats['top']['subgraphs']}")
        print(f"   Nodes: {stats['top']['nodes']}")

        print(f"\n🔗 Cross-Layer Links:")
        print(f"   REFERENCE relationships: {ref_count}")

        print("\n" + "=" * 60)

    def save_gids(self):
        """Save layer GIDs to file for frontend use"""
        print("\n💾 Saving layer GIDs for frontend...")

        with open("layer_gids.txt", "w") as f:
            f.write("# Three-Layer Graph IDs\n")
            f.write("# Generated by build_three_layer_graph.py\n\n")
            f.write(f"BOTTOM_LAYER_GIDS={','.join(self.layer_gids['bottom'])}\n")
            f.write(f"MIDDLE_LAYER_GIDS={','.join(self.layer_gids['middle'])}\n")
            f.write(f"TOP_LAYER_GIDS={','.join(self.layer_gids['top'])}\n")

        print("✅ Layer GIDs saved to layer_gids.txt\n")


def main():
    parser = argparse.ArgumentParser(description="Build Three-Layer Medical Knowledge Graph")
    parser.add_argument('--num_patients', type=int, default=10,
                        help='Number of patient reports to import (default: 10)')
    parser.add_argument('--clear_db', action='store_true',
                        help='Clear existing database before import (WARNING: deletes all data)')
    parser.add_argument('--skip_linking', action='store_true',
                        help='Skip cross-layer linking (faster for testing)')
    parser.add_argument('--skip_merging', action='store_true',
                        help='Skip entity merging (faster for testing)')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🏗️  THREE-LAYER MEDICAL KNOWLEDGE GRAPH BUILDER")
    print("=" * 60)
    print()

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

    # Merge similar entities
    if not args.skip_merging:
        builder.merge_similar_entities()

    # Display statistics
    builder.display_statistics()

    # Save GIDs for frontend
    builder.save_gids()

    print("\n✅ Three-layer graph build complete!")
    print("🚀 You can now run the frontend: python launch_frontend.bat")
    print()


if __name__ == "__main__":
    main()
