"""
Ollama-based Utils
get_response function using Ollama for answer generation
"""

from creat_graph_ollama import call_ollama
from contraindication_checker import check_contraindications, format_contraindication_rules
from citation_formatter import CitationTracker
import re


def enforce_warning_template(response, safety_check, question):
    """
    SafetyGate: Post-generation validation
    Ensure WARNING is present if contraindication rules exist
    Override LLM output if it contradicts safety rules

    Args:
        response: Generated answer from LLM
        safety_check: Dict from check_contraindications()
        question: Original user question

    Returns:
        Validated/corrected response
    """

    if not safety_check['has_warnings']:
        return response  # No rules, no enforcement needed

    rules = safety_check['rules']

    # Check 1: Response must start with WARNING
    if not response.strip().upper().startswith('WARNING'):
        print("[SAFETYGATE] WARNING: LLM did not start with WARNING - enforcing template")

        # Generate mandatory warning prefix
        rule_summary = ", and ".join([
            f"{r.get('drug_name', r.get('drug', 'medication'))} is {r.get('rule_type', 'contraindicated').replace('_', ' ').lower()} {r.get('condition_name', r.get('condition', 'your condition'))}"
            for r in rules
        ])

        response = f"WARNING: {rule_summary}.\n\n{response}"

    # Check 2: Detect negation patterns after WARNING
    negation_patterns = [
        (r'WARNING.*?(but|however|although|except|unless)', 'negation word after WARNING'),
        (r'WARNING.*?may be safe', 'contradicts warning with "may be safe"'),
        (r'WARNING.*?in some cases', 'suggests exceptions with "in some cases"'),
        (r'WARNING.*?could be considered', 'weakens warning with "could be considered"'),
        (r'WARNING.*?not always', 'contradicts with "not always"'),
    ]

    violations = []
    for pattern, description in negation_patterns:
        if re.search(pattern, response, re.IGNORECASE | re.DOTALL):
            violations.append(description)
            print(f"[SAFETYGATE] WARNING: Detected: {description}")

    # If violations found, log them (could also regenerate or strip violating text)
    if violations:
        print(f"[SAFETYGATE] Found {len(violations)} safety violations:")
        for v in violations:
            print(f"  - {v}")
        # For now, we log but don't modify (could be enhanced to remove violating sentences)

    # Check 3: Ensure rule is actually cited in the response
    for rule in rules:
        drug = rule.get('drug_name', rule.get('drug', '')).lower()
        condition = rule.get('condition_name', rule.get('condition', '')).lower()

        # Check if both drug and condition are mentioned
        if drug and condition:
            if drug not in response.lower() or condition not in response.lower():
                print(f"[SAFETYGATE] WARNING: Rule not cited: {drug} / {condition}")

    return response


def ret_context_ollama(n4j, gid):
    """
    Retrieve context from nodes within a GID subgraph
    Returns dict with context strings and source metadata
    """
    context = []
    source_metadata = {
        'source_layer': 'Unknown',
        'source_file': 'Medical Knowledge Graph'
    }

    # First, get source metadata from Summary node
    source_query = """
    MATCH (s:Summary {gid: $gid})
    RETURN s.source_layer AS source_layer, s.source_file AS source_file
    """

    try:
        source_result = n4j.query(source_query, {'gid': gid})
        if source_result and len(source_result) > 0:
            source_metadata['source_layer'] = source_result[0].get('source_layer', 'Unknown')
            source_metadata['source_file'] = source_result[0].get('source_file', 'Medical Knowledge Graph')
    except Exception as e:
        print(f"  [Warning] Could not retrieve source metadata for GID {gid[:8]}: {e}")

    # Get ALL patient diseases/conditions (CRITICAL for contraindication checking)
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

    return {
        'context': context,
        'source_layer': source_metadata['source_layer'],
        'source_file': source_metadata['source_file']
    }

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
        dict: {
            'answer': Generated answer string with inline citations,
            'citations': Formatted citation list
        }
    """

    print(f"\n[Response Generation] Retrieving context from GID {gid[:8]}...")

    # Initialize citation tracker
    citation_tracker = CitationTracker()

    # P0.1 CONTRA-CHECK: Check contraindication rules BEFORE generation
    safety_check = check_contraindications(n4j, gid, question)

    # Get context from matched subgraph (now returns dict with source metadata)
    context_data = ret_context_ollama(n4j, gid)
    self_context = context_data['context']
    source_layer = context_data['source_layer']
    source_file = context_data['source_file']

    print(f"[Context] Retrieved {len(self_context)} relationships from matched subgraph")
    print(f"[Source] {source_layer} - {source_file}")

    # Add citation for this source
    citation_marker = citation_tracker.add_citation(source_layer, source_file)
    print(f"[Citation] Added source {citation_marker}")

    # Inject contraindication rules at TOP of context if found
    if safety_check['has_warnings']:
        print(f"[SAFETY] {len(safety_check['rules'])} contraindication rules found - injecting into context")

        rule_text = format_contraindication_rules(safety_check['rules'])

        # Insert at very top (before patient conditions)
        self_context.insert(0, "=" * 70)
        self_context.insert(1, "** CONTRAINDICATION RULES (NON-NEGOTIABLE - MUST FOLLOW) **")
        self_context.insert(2, rule_text)
        self_context.insert(3, "=" * 70)
        self_context.insert(4, "")

    # Get linked context from cross-layer references
    linked_context = link_context_ollama(n4j, gid)
    print(f"[Linked Context] Retrieved {len(linked_context)} cross-layer relationships")

    # First pass: Answer using self context with patient-aware reasoning
    sys_prompt_one = """You are a medical assistant providing personalized advice based on a patient's specific conditions.

NON-NEGOTIABLE SAFETY RULES:
1. If you see "CONTRAINDICATION RULES" section, you MUST start your answer with "WARNING:"
2. NEVER suggest exceptions, workarounds, or "but in some cases" for contraindications
3. NEVER use negation words (but, however, although, except) after stating a WARNING
4. DO NOT suggest the medication might be safe despite contraindications

CRITICAL INSTRUCTIONS:
1. FIRST, check for CONTRAINDICATION RULES section - these override everything else
2. SECOND, identify ALL of the patient's medical conditions from the "PATIENT'S MEDICAL CONDITIONS" section
3. If the question is about medications or treatments, CHECK if they are safe or contraindicated for this specific patient
4. Use this format:
   - If CONTRAINDICATED or CONTRAINDICATION RULES exist: Start with "WARNING: [medication] is NOT recommended for you because you have [specific conditions]. [Explain why from rules]"
   - If SAFE: Start with "SAFE: This appears safe for your conditions. [Explain]"
   - If CAUTION NEEDED: Start with "CAUTION: [medication] requires careful monitoring because you have [conditions]. [Explain]"

5. Keep answer concise (2-3 paragraphs), use simple language, avoid medical jargon
6. Be specific about which patient conditions create the contraindication
7. If CONTRAINDICATION RULES are present, cite them directly in your answer"""

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

    # P0.1 SAFETYGATE: Post-generation validation
    # Enforce WARNING template if contraindication rules exist
    if safety_check['has_warnings']:
        print(f"\n[SAFETYGATE] Validating response for contraindication compliance...")
        final_response = enforce_warning_template(final_response, safety_check, question)

    # Append citation marker to the end of the response
    final_response_with_citation = final_response + f" {citation_marker}"

    # Format citations
    citations = citation_tracker.format_citations()

    print(f"[Complete] Answer generated successfully with {citation_tracker.get_citation_count()} citation(s)\n")

    return {
        'answer': final_response_with_citation,
        'citations': citations
    }
