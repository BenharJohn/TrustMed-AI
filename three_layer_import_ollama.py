"""
Three-Layer Graph Import with Ollama
Official architecture: Bottom (UMLS) -> Middle (MedC-K) -> Top (MIMIC-IV)
Uses Ollama instead of OpenAI for entity extraction
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from camel.storages import Neo4jGraph
from creat_graph_ollama import creat_metagraph_ollama
from utils import str_uuid, ref_link

load_dotenv()

class ThreeLayerImporterOllama:
    """Three-layer graph importer using Ollama"""

    def __init__(self, neo4j_url, neo4j_username, neo4j_password, model="llama3"):
        """Initialize"""
        print("\n" + "="*80)
        print("Three-Layer Medical Knowledge Graph Importer (Ollama)")
        print("="*80)

        # Connect to Neo4j
        print("\n[Connecting to Neo4j]...")
        self.n4j = Neo4jGraph(
            url=neo4j_url,
            username=neo4j_username,
            password=neo4j_password
        )
        print(f"Connected to: {neo4j_url}")

        self.model = model
        print(f"Using Ollama model: {model}")

        # Store GIDs for each layer
        self.layer_gids = {
            'bottom': [],
            'middle': [],
            'top': []
        }

    def clear_database(self):
        """Clear database"""
        print("\n[Clearing database]...")
        result = self.n4j.query("MATCH (n) RETURN count(n) as count")
        count = result[0]['count'] if result else 0
        print(f"Current nodes: {count}")

        if count > 0:
            print("Deleting all nodes...")
            self.n4j.query("MATCH (n) DETACH DELETE n")
            print("Database cleared!")
        else:
            print("Database already empty")

    def import_layer(self, layer_name: str, data_path: str):
        """
        Import one layer of data

        Args:
            layer_name: Layer name (bottom/middle/top)
            data_path: Data path
        """
        print("\n" + "="*80)
        print(f"[{layer_name.upper()} LAYER] Starting import")
        print(f"Data path: {data_path}")
        print("="*80)

        data_path = Path(data_path)

        # Get all text files
        if data_path.is_file():
            files = [data_path]
        else:
            files = list(data_path.glob("*.txt"))
            files.extend(data_path.rglob("*/*.txt"))

        print(f"\nFound {len(files)} files")

        # Process each file
        for idx, file_path in enumerate(files, 1):
            print(f"\n{'-'*80}")
            print(f"[File {idx}/{len(files)}] {file_path.name}")
            print(f"{'-'*80}")

            try:
                # Read content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not content or len(content.strip()) < 50:
                    print(f"  Skipped: Content too short")
                    continue

                # Generate GID
                gid = str_uuid()
                self.layer_gids[layer_name].append(gid)

                # Create graph using Ollama
                self.n4j = creat_metagraph_ollama(
                    content, gid, self.n4j, self.model
                )

                print(f"  Completed: {file_path.name} (GID: {gid[:8]}...)")

            except Exception as e:
                print(f"  Error: {file_path.name} - {e}")
                continue

        print(f"\n{'='*80}")
        print(f"[{layer_name.upper()} LAYER] Import complete")
        print(f"Imported {len(self.layer_gids[layer_name])} subgraphs")
        print(f"{'='*80}")

    def create_trinity_links(self):
        """Create REFERENCE relationships between layers"""
        print("\n" + "="*80)
        print("[Trinity Links] Creating cross-layer relationships")
        print("="*80)

        total_links = 0

        # Bottom -> Middle
        print("\n[Linking] Bottom -> Middle")
        for bottom_gid in self.layer_gids['bottom']:
            for middle_gid in self.layer_gids['middle']:
                try:
                    result = ref_link(self.n4j, bottom_gid, middle_gid)
                    if result:
                        count = len(result)
                        total_links += count
                        if count > 0:
                            print(f"  {bottom_gid[:8]}... -> {middle_gid[:8]}...: {count} links")
                except Exception as e:
                    print(f"  Error: {e}")

        # Middle -> Top
        print("\n[Linking] Middle -> Top")
        for middle_gid in self.layer_gids['middle']:
            for top_gid in self.layer_gids['top']:
                try:
                    result = ref_link(self.n4j, middle_gid, top_gid)
                    if result:
                        count = len(result)
                        total_links += count
                        if count > 0:
                            print(f"  {middle_gid[:8]}... -> {top_gid[:8]}...: {count} links")
                except Exception as e:
                    print(f"  Error: {e}")

        # Bottom -> Top (direct links)
        print("\n[Linking] Bottom -> Top")
        for bottom_gid in self.layer_gids['bottom']:
            for top_gid in self.layer_gids['top']:
                try:
                    result = ref_link(self.n4j, bottom_gid, top_gid)
                    if result:
                        count = len(result)
                        total_links += count
                        if count > 0:
                            print(f"  {bottom_gid[:8]}... -> {top_gid[:8]}...: {count} links")
                except Exception as e:
                    print(f"  Error: {e}")

        print(f"\n{'='*80}")
        print(f"[Trinity Links] Complete")
        print(f"Created {total_links} REFERENCE relationships")
        print(f"{'='*80}")

    def print_statistics(self):
        """Print statistics"""
        print("\n" + "="*80)
        print("[Statistics]")
        print("="*80)

        # Node counts
        result = self.n4j.query("MATCH (n) WHERE NOT n:Summary RETURN count(n) as count")
        node_count = result[0]['count'] if result else 0

        # Summary counts
        result = self.n4j.query("MATCH (s:Summary) RETURN count(s) as count")
        summary_count = result[0]['count'] if result else 0

        # Relationship counts
        result = self.n4j.query("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result[0]['count'] if result else 0

        # REFERENCE counts
        result = self.n4j.query("MATCH ()-[r:REFERENCE]->() RETURN count(r) as count")
        ref_count = result[0]['count'] if result else 0

        # Entity type distribution
        result = self.n4j.query("""
            MATCH (n)
            WHERE NOT n:Summary
            RETURN labels(n)[0] as type, count(n) as count
            ORDER BY count DESC
            LIMIT 10
        """)

        print(f"\nOverall:")
        print(f"  - Entity nodes: {node_count}")
        print(f"  - Summary nodes: {summary_count}")
        print(f"  - Total relationships: {rel_count}")
        print(f"  - REFERENCE relationships: {ref_count}")

        print(f"\nLayers:")
        print(f"  - Bottom (UMLS): {len(self.layer_gids['bottom'])} subgraphs")
        print(f"  - Middle (MedC-K): {len(self.layer_gids['middle'])} subgraphs")
        print(f"  - Top (MIMIC-IV): {len(self.layer_gids['top'])} subgraphs")

        print(f"\nEntity types (top 10):")
        for item in result:
            print(f"  - {item['type']}: {item['count']}")

        # Save layer GIDs
        with open('layer_gids.txt', 'w') as f:
            f.write("# Three-Layer Graph IDs (Ollama)\n\n")
            f.write(f"BOTTOM_LAYER_GIDS={','.join(self.layer_gids['bottom'])}\n")
            f.write(f"MIDDLE_LAYER_GIDS={','.join(self.layer_gids['middle'])}\n")
            f.write(f"TOP_LAYER_GIDS={','.join(self.layer_gids['top'])}\n")

        print(f"\nGIDs saved to layer_gids.txt")
        print(f"\n{'='*80}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Three-Layer Graph Import with Ollama')

    # Data paths
    parser.add_argument('--bottom', type=str, help='Bottom layer path (UMLS medical dictionary)')
    parser.add_argument('--middle', type=str, help='Middle layer path (MedC-K clinical guidelines)')
    parser.add_argument('--top', type=str, help='Top layer path (MIMIC-IV patient cases)')

    # Options
    parser.add_argument('--clear', action='store_true', help='Clear database first')
    parser.add_argument('--trinity', action='store_true', help='Create Trinity cross-layer links')
    parser.add_argument('--model', type=str, default='llama3', help='Ollama model (default: llama3)')

    # Neo4j config
    parser.add_argument('--neo4j-url', type=str,
                       default=os.getenv('NEO4J_URL', 'bolt://localhost:7687'))
    parser.add_argument('--neo4j-username', type=str,
                       default=os.getenv('NEO4J_USERNAME', 'neo4j'))
    parser.add_argument('--neo4j-password', type=str,
                       default=os.getenv('NEO4J_PASSWORD'))

    args = parser.parse_args()

    # Check Neo4j password
    if not args.neo4j_password:
        print("Error: No Neo4j password provided")
        print("Set NEO4J_PASSWORD environment variable or use --neo4j-password")
        sys.exit(1)

    # Initialize importer
    importer = ThreeLayerImporterOllama(
        args.neo4j_url,
        args.neo4j_username,
        args.neo4j_password,
        args.model
    )

    # Clear database
    if args.clear:
        importer.clear_database()

    # Import layers
    if args.bottom:
        importer.import_layer('bottom', args.bottom)

    if args.middle:
        importer.import_layer('middle', args.middle)

    if args.top:
        importer.import_layer('top', args.top)

    # Create Trinity links
    if args.trinity:
        importer.create_trinity_links()

    # Print statistics
    importer.print_statistics()

    print("\nAll tasks complete!")


if __name__ == '__main__':
    main()
