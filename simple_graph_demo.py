"""
Simple Graph Data Demo - No complex dependencies
Shows exactly how contraindication graph data is created
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment
load_dotenv()

class SimpleNeo4jDemo:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def create_sample_graph(self):
        """Create sample contraindication graph"""

        import uuid
        patient_gid = str(uuid.uuid4())

        print("\n" + "=" * 70)
        print("CREATING GRAPH DATA FOR CONTRAINDICATIONS")
        print("=" * 70)
        print(f"\nPatient GID: {patient_gid[:8]}...")

        # Clear any existing sample data
        print("\nClearing previous sample data...")
        self.run_query("MATCH (n) WHERE n.id STARTS WITH 'DEMO_' DETACH DELETE n")

        # STEP 1: Create Patient
        print("\n" + "-" * 70)
        print("STEP 1: Creating Patient with Conditions")
        print("-" * 70)

        patient_query = """
        CREATE (p:Patient {
            id: 'DEMO_Patient_001',
            name: 'John Doe',
            age: 65,
            gender: 'M',
            gid: $gid
        })
        RETURN p.id AS patient_id
        """
        self.run_query(patient_query, {'gid': patient_gid})
        print("Created: Patient_001 (age 65, male)")

        # Create diseases
        diseases_query = """
        CREATE (d1:Disease {
            id: 'DEMO_heart_failure',
            name: 'Congestive Heart Failure',
            gid: $gid
        })
        CREATE (d2:Disease {
            id: 'DEMO_chronic_kidney_disease',
            name: 'Chronic Kidney Disease',
            gid: $gid
        })
        CREATE (d3:Disease {
            id: 'DEMO_hypertension',
            name: 'Hypertension',
            gid: $gid
        })
        RETURN count(*) AS count
        """
        self.run_query(diseases_query, {'gid': patient_gid})
        print("Created: Heart Failure")
        print("Created: Chronic Kidney Disease")
        print("Created: Hypertension")

        # Link patient to diseases
        link_query = """
        MATCH (p:Patient {id: 'DEMO_Patient_001', gid: $gid})
        MATCH (d:Disease {gid: $gid})
        CREATE (p)-[:HAS_CONDITION]->(d)
        """
        self.run_query(link_query, {'gid': patient_gid})
        print("Linked patient to 3 conditions")

        # STEP 2: Create Medications
        print("\n" + "-" * 70)
        print("STEP 2: Creating Medications")
        print("-" * 70)

        meds_query = """
        CREATE (m1:Medication {id: 'DEMO_ibuprofen', name: 'Ibuprofen', class: 'NSAID'})
        CREATE (m2:Medication {id: 'DEMO_naproxen', name: 'Naproxen', class: 'NSAID'})
        CREATE (m3:Medication {id: 'DEMO_acetaminophen', name: 'Acetaminophen', class: 'Analgesic'})
        CREATE (m4:Medication {id: 'DEMO_lisinopril', name: 'Lisinopril', class: 'ACE Inhibitor'})
        RETURN count(*) AS count
        """
        self.run_query(meds_query)
        print("Created: Ibuprofen (NSAID)")
        print("Created: Naproxen (NSAID)")
        print("Created: Acetaminophen (Analgesic)")
        print("Created: Lisinopril (ACE Inhibitor)")

        # STEP 3: Create CONTRAINDICATION relationships
        print("\n" + "-" * 70)
        print("STEP 3: Creating CONTRAINDICATION Relationships")
        print("-" * 70)
        print("THIS IS THE KEY - linking drugs to conditions they're contraindicated in!")

        contra_query = """
        MATCH (m1:Medication {id: 'DEMO_ibuprofen'})
        MATCH (d1:Disease {id: 'DEMO_heart_failure'})
        CREATE (m1)-[:CONTRAINDICATED_IN {
            reason: 'NSAIDs cause sodium and water retention, worsening heart failure'
        }]->(d1)

        WITH m1
        MATCH (d2:Disease {id: 'DEMO_chronic_kidney_disease'})
        CREATE (m1)-[:CONTRAINDICATED_IN {
            reason: 'NSAIDs reduce renal blood flow and can cause acute kidney injury'
        }]->(d2)

        WITH m1
        MATCH (d3:Disease {id: 'DEMO_hypertension'})
        CREATE (m1)-[:WORSENS {
            reason: 'NSAIDs can elevate blood pressure by causing fluid retention'
        }]->(d3)

        WITH 1 AS dummy
        MATCH (m2:Medication {id: 'DEMO_naproxen'})
        MATCH (d1:Disease {id: 'DEMO_heart_failure'})
        CREATE (m2)-[:CONTRAINDICATED_IN {
            reason: 'NSAIDs cause sodium and water retention, worsening heart failure'
        }]->(d1)

        WITH m2
        MATCH (d2:Disease {id: 'DEMO_chronic_kidney_disease'})
        CREATE (m2)-[:CONTRAINDICATED_IN {
            reason: 'NSAIDs reduce renal blood flow and can cause acute kidney injury'
        }]->(d2)

        RETURN count(*) AS contraindications_created
        """
        result = self.run_query(contra_query)
        print("  Ibuprofen --[CONTRAINDICATED_IN]--> Heart Failure")
        print("  Ibuprofen --[CONTRAINDICATED_IN]--> Chronic Kidney Disease")
        print("  Ibuprofen --[WORSENS]--> Hypertension")
        print("  Naproxen --[CONTRAINDICATED_IN]--> Heart Failure")
        print("  Naproxen --[CONTRAINDICATED_IN]--> Chronic Kidney Disease")
        print(f"\nCreated 5 contraindication rules")

        # STEP 4: Create safe alternatives
        print("\n" + "-" * 70)
        print("STEP 4: Creating Safe Alternatives")
        print("-" * 70)

        safe_query = """
        MATCH (m:Medication {id: 'DEMO_acetaminophen'})
        MATCH (d1:Disease {id: 'DEMO_heart_failure'})
        CREATE (m)-[:SAFE_FOR]->(d1)

        WITH m
        MATCH (d2:Disease {id: 'DEMO_chronic_kidney_disease'})
        CREATE (m)-[:SAFE_FOR]->(d2)

        RETURN count(*) AS safe_relationships
        """
        self.run_query(safe_query)
        print("  Acetaminophen --[SAFE_FOR]--> Heart Failure")
        print("  Acetaminophen --[SAFE_FOR]--> Chronic Kidney Disease")

        # STEP 5: Verify the graph
        print("\n" + "-" * 70)
        print("STEP 5: QUERYING THE GRAPH (How P0.1 Works)")
        print("-" * 70)

        # Query contraindications for patient
        verify_query = """
        MATCH (p:Patient {id: 'DEMO_Patient_001', gid: $gid})-[:HAS_CONDITION]->(d:Disease)
        MATCH (m:Medication)-[r:CONTRAINDICATED_IN|WORSENS]->(d)
        RETURN m.name AS drug, type(r) AS relationship, d.name AS condition, r.reason AS reason
        """

        print("\nQuery: Find contraindications for Patient_001")
        results = self.run_query(verify_query, {'gid': patient_gid})

        print(f"\nFound {len(results)} contraindication rules:")
        for r in results:
            print(f"\n  WARNING: {r['drug']} is {r['relationship'].replace('_', ' ').lower()} {r['condition']}")
            print(f"    Reason: {r['reason']}")

        # Query safe alternatives
        safe_verify_query = """
        MATCH (p:Patient {id: 'DEMO_Patient_001', gid: $gid})-[:HAS_CONDITION]->(d:Disease)
        MATCH (m:Medication)-[:SAFE_FOR]->(d)
        RETURN DISTINCT m.name AS drug, m.class AS drug_class
        """

        print("\n" + "-" * 70)
        print("Query: Find safe pain relievers for Patient_001")
        results = self.run_query(safe_verify_query, {'gid': patient_gid})

        print(f"\nFound {len(results)} safe alternatives:")
        for r in results:
            print(f"  SAFE: {r['drug']} ({r['drug_class']})")

        # DEMONSTRATION: How P0.1 uses this
        print("\n" + "=" * 70)
        print("HOW P0.1 CONTRA-CHECK USES THIS GRAPH DATA")
        print("=" * 70)

        print("""
USER ASKS: "Can I take ibuprofen?"

1. contraindication_checker.py extracts:
   - Drugs mentioned: ['ibuprofen', 'nsaid', 'nsaids', 'advil', 'motrin']

2. contraindication_checker.py gets patient conditions:
   - Patient GID: """ + patient_gid[:8] + """...
   - Conditions: ['heart failure', 'hf', 'chf', 'chronic kidney disease', 'ckd', ...]

3. Runs Cypher query (similar to what we just did):

   MATCH (d:Medication)-[r:CONTRAINDICATED_IN|WORSENS]->(c:Disease)
   WHERE toLower(d.id) IN ['ibuprofen', 'nsaid', ...]
     AND toLower(c.id) IN ['heart failure', 'hf', ...]
   RETURN d.name, type(r), c.name, r.reason

4. Graph returns contraindication rules (EXACTLY like we saw above)

5. utils_ollama.py injects rules into context:
   ======================================================================
   ** CONTRAINDICATION RULES (NON-NEGOTIABLE - MUST FOLLOW) **
   WARNING: IBUPROFEN is contraindicated in HEART FAILURE
   WARNING: IBUPROFEN is contraindicated in CHRONIC KIDNEY DISEASE
   WARNING: IBUPROFEN worsens HYPERTENSION
   ======================================================================

6. LLM generates answer starting with WARNING (enforced by SafetyGate)

7. FINAL ANSWER:
   "WARNING: Ibuprofen is NOT recommended for you because you have
   heart failure and chronic kidney disease. NSAIDs like ibuprofen cause
   sodium and water retention, which worsens heart failure, and they
   reduce renal blood flow which can cause acute kidney injury in
   patients with kidney disease. Consider acetaminophen as a safer
   alternative for pain relief."
""")

        print("\n" + "=" * 70)
        print("GRAPH DATA SUCCESSFULLY CREATED!")
        print("=" * 70)
        print(f"""
Summary:
- Patient GID: {patient_gid}
- Nodes: 1 patient + 3 diseases + 4 medications = 8 nodes
- Relationships: 3 HAS_CONDITION + 5 contraindications + 2 safe alternatives

You can view this in Neo4j Browser:
1. Open http://localhost:7474
2. Run: MATCH (n) WHERE n.id STARTS WITH 'DEMO_' RETURN n

To delete this demo data:
MATCH (n) WHERE n.id STARTS WITH 'DEMO_' DETACH DELETE n
""")

        return patient_gid


def main():
    # Get credentials
    url = os.getenv("NEO4J_URL")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([url, username, password]):
        print("\nError: Neo4j credentials not found in .env")
        print("Please set: NEO4J_URL, NEO4J_USERNAME, NEO4J_PASSWORD")
        return

    print(f"\nConnecting to Neo4j: {url}")

    try:
        demo = SimpleNeo4jDemo(url, username, password)
        demo.create_sample_graph()
        demo.close()

        print("\nConnection closed successfully")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Neo4j is running:")
        print("- Check if Neo4j Desktop is running")
        print("- Or if using Docker: docker ps")


if __name__ == "__main__":
    main()
