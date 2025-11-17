"""
Add source metadata to existing Neo4j Summary nodes
This script adds source_layer and source_file properties to Summary nodes
"""
import os
from dotenv import load_dotenv
from camel.storages import Neo4jGraph

load_dotenv()

# Connect to Neo4j
url = os.getenv("NEO4J_URL")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

print("[INFO] Connecting to Neo4j...")
n4j = Neo4jGraph(url=url, username=username, password=password)

print("\n[STEP 1] Analyzing existing Summary nodes...")

# Get all Summary nodes with their content
query = """
MATCH (s:Summary)
RETURN s.gid AS gid, s.content AS content, s.id AS id
"""

summaries = n4j.query(query)
print(f"  Found {len(summaries)} Summary nodes")

# Analyze and categorize each summary
layer_assignments = []

for summary in summaries:
    gid = summary['gid']
    content = summary['content'][:200] if summary['content'] else ""  # First 200 chars
    sid = summary['id']

    # Determine layer based on content patterns
    if any(keyword in content.lower() for keyword in ['umls', 'ontology', 'concept', 'cui', 'semantic type']):
        layer = 'UMLS'
        file_hint = 'cardiac_terms.txt'
    elif any(keyword in content.lower() for keyword in ['guideline', 'recommendation', 'clinical practice', 'evidence-based']):
        layer = 'MedC-K'
        file_hint = 'cardiac_guidelines.txt'
    else:
        # Default to MIMIC-IV for clinical notes
        layer = 'MIMIC-IV'
        file_hint = f'clinical_note_{gid[:8]}.txt'

    layer_assignments.append({
        'gid': gid,
        'layer': layer,
        'file': file_hint,
        'id': sid
    })

    print(f"  {sid[:30]}... -> {layer} ({file_hint})")

print(f"\n[STEP 2] Updating Neo4j with source metadata...")

# Update each Summary node with source metadata
update_query = """
MATCH (s:Summary {gid: $gid})
SET s.source_layer = $layer,
    s.source_file = $file
RETURN s.gid AS gid
"""

updated_count = 0
for assignment in layer_assignments:
    result = n4j.query(update_query, {
        'gid': assignment['gid'],
        'layer': assignment['layer'],
        'file': assignment['file']
    })
    if result:
        updated_count += 1
        print(f"  [OK] Updated {assignment['id'][:30]}... with {assignment['layer']}")

print(f"\n[DONE] Updated {updated_count} Summary nodes with source metadata!")

# Verify the updates
print("\n[VERIFICATION] Checking updated nodes...")
verify_query = """
MATCH (s:Summary)
RETURN s.source_layer AS layer, count(s) AS count
"""

results = n4j.query(verify_query)
print("\nSource Layer Distribution:")
for result in results:
    print(f"  {result['layer']}: {result['count']} nodes")

print("\n[SUCCESS] Source metadata added successfully!")
