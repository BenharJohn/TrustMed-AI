"""Quick check of embedding dimension"""
import os
from dotenv import load_dotenv
from camel.storages import Neo4jGraph

load_dotenv()

url = os.getenv("NEO4J_URL")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

n4j = Neo4jGraph(url=url, username=username, password=password)

query = """
MATCH (s:Summary)
WHERE s.embedding IS NOT NULL
RETURN size(s.embedding) AS dimension
LIMIT 1
"""

result = n4j.query(query)
if result:
    print(f"Existing embedding dimension: {result[0]['dimension']}")
else:
    print("No embeddings found")
