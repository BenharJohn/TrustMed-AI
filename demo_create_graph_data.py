"""
Demonstration: How to Create Graph Data for Contraindications
This script shows you exactly how graph data is created in Neo4j
"""

import os
from dotenv import load_dotenv
from camel.storages import Neo4jGraph

# Load environment variables
load_dotenv()

def create_sample_contraindication_graph():
    """
    Create sample graph data showing how contraindications are stored
    """

    print("\n" + "=" * 70)
    print("DEMONSTRATION: Creating Graph Data for Contraindications")
    print("=" * 70)

    # Connect to Neo4j
    url = os.getenv("NEO4J_URL")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([url, username, password]):
        print("\nError: Neo4j credentials not found in .env file")
        print("Please set NEO4J_URL, NEO4J_USERNAME, NEO4J_PASSWORD")
        return

    print(f"\nConnecting to Neo4j: {url}")
    n4j = Neo4jGraph(url=url, username=username, password=password)
    print("Connected successfully!")

    # Generate a sample patient GID
    import uuid
    patient_gid = str(uuid.uuid4())

    print(f"\nCreating sample patient graph with GID: {patient_gid[:8]}...")

    # ========================================================================
    # STEP 1: Create Patient Nodes
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 1: Creating Patient with Conditions")
    print("-" * 70)

    # Create patient node
    patient_query = """
    CREATE (p:Patient {
        id: 'Patient_001',
        name: 'John Doe',
        age: 65,
        gender: 'M',
        gid: $gid
    })
    RETURN p.id AS patient_id
    """

    result = n4j.query(patient_query, {'gid': patient_gid})
    print(f"Created: Patient_001 (age 65, male)")

    # Create disease nodes for this patient
    diseases = [
        {'id': 'heart failure', 'name': 'Congestive Heart Failure', 'severity': 'moderate'},
        {'id': 'chronic kidney disease', 'name': 'Chronic Kidney Disease', 'stage': 'Stage 3'},
        {'id': 'hypertension', 'name': 'Hypertension', 'severity': 'controlled'}
    ]

    for disease in diseases:
        disease_query = """
        CREATE (d:Disease {
            id: $id,
            name: $name,
            gid: $gid
        })
        RETURN d.id AS disease_id
        """
        n4j.query(disease_query, {
            'id': disease['id'],
            'name': disease['name'],
            'gid': patient_gid
        })
        print(f"Created: {disease['name']}")

    # Link patient to diseases
    link_query = """
    MATCH (p:Patient {id: 'Patient_001', gid: $gid})
    MATCH (d:Disease {gid: $gid})
    CREATE (p)-[r:HAS_CONDITION]->(d)
    RETURN count(r) AS links_created
    """
    n4j.query(link_query, {'gid': patient_gid})
    print(f"Linked patient to {len(diseases)} conditions")

    # ========================================================================
    # STEP 2: Create Drug Nodes
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 2: Creating Drug/Medication Nodes")
    print("-" * 70)

    drugs = [
        {'id': 'ibuprofen', 'name': 'Ibuprofen', 'class': 'NSAID'},
        {'id': 'naproxen', 'name': 'Naproxen', 'class': 'NSAID'},
        {'id': 'acetaminophen', 'name': 'Acetaminophen', 'class': 'Analgesic'},
        {'id': 'lisinopril', 'name': 'Lisinopril', 'class': 'ACE Inhibitor'}
    ]

    for drug in drugs:
        drug_query = """
        CREATE (m:Medication {
            id: $id,
            name: $name,
            class: $class
        })
        RETURN m.id AS drug_id
        """
        n4j.query(drug_query, {
            'id': drug['id'],
            'name': drug['name'],
            'class': drug['class']
        })
        print(f"Created: {drug['name']} ({drug['class']})")

    # ========================================================================
    # STEP 3: Create CONTRAINDICATION Relationships (THE KEY STEP!)
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 3: Creating CONTRAINDICATION Relationships")
    print("-" * 70)
    print("This is where the magic happens - connecting drugs to conditions!")

    contraindications = [
        {
            'drug': 'ibuprofen',
            'condition': 'heart failure',
            'type': 'CONTRAINDICATED_IN',
            'reason': 'NSAIDs cause sodium and water retention, worsening heart failure'
        },
        {
            'drug': 'ibuprofen',
            'condition': 'chronic kidney disease',
            'type': 'CONTRAINDICATED_IN',
            'reason': 'NSAIDs reduce renal blood flow and can cause acute kidney injury'
        },
        {
            'drug': 'naproxen',
            'condition': 'heart failure',
            'type': 'CONTRAINDICATED_IN',
            'reason': 'NSAIDs cause sodium and water retention, worsening heart failure'
        },
        {
            'drug': 'naproxen',
            'condition': 'chronic kidney disease',
            'type': 'CONTRAINDICATED_IN',
            'reason': 'NSAIDs reduce renal blood flow and can cause acute kidney injury'
        },
        {
            'drug': 'ibuprofen',
            'condition': 'hypertension',
            'type': 'WORSENS',
            'reason': 'NSAIDs can elevate blood pressure by causing fluid retention'
        }
    ]

    for contra in contraindications:
        contra_query = """
        MATCH (m:Medication {{id: $drug}})
        MATCH (d:Disease {{id: $condition}})
        CREATE (m)-[r:{rel_type} {{reason: $reason}}]->(d)
        RETURN type(r) AS relationship, m.name AS drug, d.name AS condition
        """.format(rel_type=contra['type'])

        result = n4j.query(contra_query, {
            'drug': contra['drug'],
            'condition': contra['condition'],
            'reason': contra['reason']
        })

        if result:
            print(f"  {contra['drug']} --[{contra['type']}]--> {contra['condition']}")

    print(f"\nCreated {len(contraindications)} contraindication rules")

    # ========================================================================
    # STEP 4: Create Safe Alternatives
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 4: Creating Safe Alternative Relationships")
    print("-" * 70)

    safe_alts = [
        {
            'drug': 'acetaminophen',
            'condition': 'heart failure',
            'type': 'SAFE_FOR'
        },
        {
            'drug': 'acetaminophen',
            'condition': 'chronic kidney disease',
            'type': 'SAFE_FOR'
        }
    ]

    for alt in safe_alts:
        alt_query = """
        MATCH (m:Medication {{id: $drug}})
        MATCH (d:Disease {{id: $condition}})
        CREATE (m)-[r:{rel_type}]->(d)
        RETURN type(r) AS relationship, m.name AS drug, d.name AS condition
        """.format(rel_type=alt['type'])

        result = n4j.query(alt_query, {
            'drug': alt['drug'],
            'condition': alt['condition']
        })

        if result:
            print(f"  {alt['drug']} --[{alt['type']}]--> {alt['condition']}")

    # ========================================================================
    # STEP 5: Verify the Graph
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 5: Verifying Graph Data")
    print("-" * 70)

    # Query 1: Find all contraindications for patient's conditions
    verify_query_1 = """
    MATCH (p:Patient {id: 'Patient_001', gid: $gid})-[:HAS_CONDITION]->(d:Disease)
    MATCH (m:Medication)-[r:CONTRAINDICATED_IN|WORSENS]->(d)
    RETURN m.name AS drug, type(r) AS relationship, d.name AS condition, r.reason AS reason
    """

    print("\nQuery: Find all contraindications for Patient_001's conditions")
    results = n4j.query(verify_query_1, {'gid': patient_gid})

    if results:
        print(f"\nFound {len(results)} contraindication rules:")
        for r in results:
            print(f"  WARNING: {r['drug']} is {r['relationship'].replace('_', ' ').lower()} {r['condition']}")
            print(f"    Reason: {r.get('reason', 'N/A')}")
    else:
        print("  No contraindications found (unexpected!)")

    # Query 2: Find safe alternatives
    verify_query_2 = """
    MATCH (p:Patient {id: 'Patient_001', gid: $gid})-[:HAS_CONDITION]->(d:Disease)
    MATCH (m:Medication)-[r:SAFE_FOR]->(d)
    RETURN DISTINCT m.name AS drug, m.class AS drug_class
    """

    print("\nQuery: Find safe pain relievers for Patient_001")
    results = n4j.query(verify_query_2, {'gid': patient_gid})

    if results:
        print(f"\nFound {len(results)} safe alternatives:")
        for r in results:
            print(f"  SAFE: {r['drug']} ({r['drug_class']})")
    else:
        print("  No safe alternatives found")

    # ========================================================================
    # STEP 6: Show How P0.1 CONTRA-CHECK Uses This Data
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 6: How P0.1 CONTRA-CHECK Uses This Graph Data")
    print("=" * 70)

    print("""
When a user asks: "Can I take ibuprofen?"

1. contraindication_checker.py extracts drug: ['ibuprofen', 'nsaid', ...]
2. contraindication_checker.py gets patient conditions from GID
3. Runs this Cypher query:

   MATCH (d:Medication)-[r:CONTRAINDICATED_IN|WORSENS]->(c:Disease)
   WHERE toLower(d.id) IN ['ibuprofen', 'nsaid', ...]
     AND toLower(c.id) IN ['heart failure', 'hf', 'chf', ...]
   RETURN d.name, type(r), c.name

4. If rules found:
   - Inject rules into context (utils_ollama.py line 215-225)
   - LLM MUST start answer with "WARNING:"
   - SafetyGate validates response (utils_ollama.py line 276-278)

5. Result: "WARNING: Ibuprofen is NOT recommended for you because you
   have heart failure. NSAIDs cause sodium and water retention..."
""")

    print("\n" + "=" * 70)
    print("Graph Data Created Successfully!")
    print("=" * 70)
    print(f"\nPatient GID: {patient_gid}")
    print(f"Nodes created: 1 patient + 3 diseases + 4 medications = 8 nodes")
    print(f"Relationships created: 3 HAS_CONDITION + {len(contraindications)} contraindications + {len(safe_alts)} safe alternatives")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. View your graph in Neo4j Browser:
   - Open http://localhost:7474
   - Run: MATCH (n) RETURN n LIMIT 50

2. Test contraindication checking:
   python test_contraindications.py

3. Query specific patient:
   MATCH (p:Patient {id: 'Patient_001'})-[:HAS_CONDITION]->(d)
   MATCH (m)-[r:CONTRAINDICATED_IN]->(d)
   RETURN m.name, type(r), d.name

4. Build full graph with real data:
   python build_three_layer_ollama.py --num_patients 10
""")

    return patient_gid


if __name__ == "__main__":
    create_sample_contraindication_graph()
