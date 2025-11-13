"""
Ollama-based Utils
get_response function using Ollama for answer generation
"""

from creat_graph_ollama import call_ollama

def ret_context_ollama(n4j, gid):
    """
    Retrieve context from nodes within a GID subgraph
    Returns list of context strings with patient conditions highlighted
    """
    context = []

    # First, get ALL patient diseases/conditions (CRITICAL for contraindication checking)
    disease_query = """
    MATCH (n)
    WHERE n.gid = $gid AND NOT n:Summary
    AND (n:Disease OR n:Condition OR 'Disease' IN labels(n))
    RETURN DISTINCT n.id AS disease_name, n.name AS alt_name
    """

    try:
        diseases = n4j.query(disease_query, {'gid': gid})
        disease_list = []
        for d in diseases:
            disease_name = d.get('alt_name') or d.get('disease_name', 'Unknown')
            disease_list.append(disease_name)

        # Add patient conditions at the TOP of context (critical for reasoning)
        if disease_list:
            context.append("=" * 50)
            context.append("PATIENT'S MEDICAL CONDITIONS (CHECK CONTRAINDICATIONS!):")
            for disease in disease_list:
                context.append(f"  - {disease}")
            context.append("=" * 50)

    except Exception as e:
        print(f"  [Warning] Could not retrieve diseases for GID {gid[:8]}: {e}")

    # Then get all relationships
    ret_query = """
    // Match all nodes with specific gid (not Summary)
    MATCH (n)
    WHERE n.gid = $gid AND NOT n:Summary
    WITH collect(n) AS nodes

    // Get relationships between nodes in this subgraph
    UNWIND nodes AS n
    UNWIND nodes AS m
    MATCH (n)-[r]-(m)
    WHERE id(n) < id(m)  // Avoid duplicates

    RETURN n.id AS source, type(r) AS rel_type, m.id AS target
    LIMIT 100
    """

    try:
        results = n4j.query(ret_query, {'gid': gid})

        for r in results:
            source = r.get('source', 'Unknown')
            rel_type = r.get('rel_type', 'RELATED_TO')
            target = r.get('target', 'Unknown')
            context.append(f"{source} {rel_type} {target}")

    except Exception as e:
        print(f"  [Warning] Could not retrieve context for GID {gid[:8]}: {e}")

    return context

def link_context_ollama(n4j, gid):
    """
    Retrieve linked context from cross-layer REFERENCE relationships
    Returns list of context strings from connected subgraphs
    """
    context = []
    
    retrieve_query = """
    // Find nodes in this GID
    MATCH (n)
    WHERE n.gid = $gid AND NOT n:Summary
    
    // Find referenced nodes in other GIDs
    MATCH (n)-[r:REFERENCE]->(m)
    WHERE NOT m:Summary
    
    // Get relationships involving referenced nodes
    MATCH (m)-[s]-(o)
    WHERE NOT o:Summary AND type(s) <> 'REFERENCE'
    
    RETURN n.id AS source_node,
           m.id AS ref_node,
           type(r) AS ref_type,
           collect(DISTINCT {rel_type: type(s), target: o.id}) AS connections
    LIMIT 50
    """
    
    try:
        results = n4j.query(retrieve_query, {'gid': gid})
        
        for r in results:
            source = r.get('source_node', 'Unknown')
            ref_node = r.get('ref_node', 'Unknown')
            
            # Add reference relationship
            context.append(f"REFERENCE: {source} -> {ref_node}")
            
            # Add connections from referenced node
            connections = r.get('connections', [])
            for conn in connections[:5]:  # Limit connections
                rel_type = conn.get('rel_type', 'RELATED_TO')
                target = conn.get('target', 'Unknown')
                context.append(f"{ref_node} {rel_type} {target}")
                
    except Exception as e:
        print(f"  [Warning] Could not retrieve linked context for GID {gid[:8]}: {e}")
    
    return context

def get_response_ollama(n4j, gid, question, model="llama3"):
    """
    Official get_response: Generate answer using context from matched GID
    
    Args:
        n4j: Neo4jGraph instance
        gid: Graph ID of matched subgraph
        question: User's question
        model: Ollama model name
        
    Returns:
        answer: Generated answer string
    """
    
    print(f"\n[Response Generation] Retrieving context from GID {gid[:8]}...")
    
    # Get context from matched subgraph
    self_context = ret_context_ollama(n4j, gid)
    print(f"[Context] Retrieved {len(self_context)} relationships from matched subgraph")
    
    # Get linked context from cross-layer references
    linked_context = link_context_ollama(n4j, gid)
    print(f"[Linked Context] Retrieved {len(linked_context)} cross-layer relationships")
    
    # First pass: Answer using self context with patient-aware reasoning
    sys_prompt_one = """You are a medical assistant providing personalized advice based on a patient's specific conditions.

CRITICAL INSTRUCTIONS:
1. FIRST, identify ALL of the patient's medical conditions from the "PATIENT'S MEDICAL CONDITIONS" section
2. If the question is about medications or treatments, CHECK if they are safe or contraindicated for this specific patient
3. Use this format:
   - If CONTRAINDICATED: Start with "WARNING: [medication] is NOT recommended for you because you have [specific conditions]. [Explain why]"
   - If SAFE: Start with "SAFE: This appears safe for your conditions. [Explain]"
   - If CAUTION NEEDED: Start with "CAUTION: [medication] requires careful monitoring because you have [conditions]. [Explain]"

4. Keep answer concise (2-3 paragraphs), use simple language, avoid medical jargon
5. Be specific about which patient conditions create the contraindication"""

    self_context_text = "\n".join(self_context[:50])  # Increased limit to include patient conditions
    user_one = f"Question: {question}\n\nPatient Information and Medical Knowledge Graph:\n{self_context_text}"

    print(f"\n[Pass 1] Generating patient-aware answer...")
    first_response = call_ollama(sys_prompt_one + "\n\n" + user_one, model)

    # Second pass: Refine using linked context (guidelines, drug interactions, etc.)
    sys_prompt_two = """You are a medical assistant. Review your previous answer and enhance it using additional clinical guidelines and drug information.

CRITICAL:
- Maintain any warnings or contraindications from your previous answer
- Add supporting information from clinical guidelines if available
- Keep it concise (2-3 paragraphs) and easy to understand
- Ensure the answer is personalized to the patient's specific conditions"""

    linked_context_text = "\n".join(linked_context[:50])  # Increased limit
    user_two = f"Question: {question}\n\nYour previous answer: {first_response}\n\nAdditional Clinical Guidelines and References:\n{linked_context_text}"
    
    print(f"[Pass 2] Refining answer with cross-layer context...")
    final_response = call_ollama(sys_prompt_two + "\n\n" + user_two, model)
    
    print(f"[Complete] Answer generated successfully\n")
    
    return final_response
