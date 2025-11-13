"""
Ollama-based Retrieval System
Replaces OpenAI-based seq_ret with Ollama for Summary matching
"""

from creat_graph_ollama import create_summary, call_ollama

def find_index_of_largest(lst):
    """Find index of largest value in list"""
    if not lst:
        return 0
    return lst.index(max(lst))

def seq_ret_ollama(n4j, question, model="llama3"):
    """
    Official retrieval: Compare question summary with all Summary nodes
    Returns GID of best matching subgraph
    
    Args:
        n4j: Neo4jGraph instance
        question: User's question
        model: Ollama model name
        
    Returns:
        gid: Graph ID of best matching subgraph
    """
    
    print(f"\n[Retrieval] Finding best matching subgraph for question...")
    
    # Create summary of question
    question_summary = create_summary(question, model)
    print(f"[Question Summary] {question_summary[:100]}...")
    
    # Get all Summary nodes
    sum_query = """
        MATCH (s:Summary)
        RETURN s.content as content, s.gid as gid
    """
    summaries = n4j.query(sum_query)
    
    if not summaries:
        print("[Warning] No Summary nodes found in database!")
        return None
    
    print(f"[Retrieved] {len(summaries)} Summary nodes from database")
    
    # Compare question summary with each Summary node
    rating_list = []
    gids = []
    
    sys_prompt = """Assess the similarity of the two provided summaries and return a rating from these options: 'very similar', 'similar', 'general', 'not similar', 'totally not similar'. Provide only the rating."""
    
    for idx, summary_node in enumerate(summaries):
        content = summary_node['content']
        gid = summary_node['gid']
        gids.append(gid)
        
        # Compare summaries
        user_prompt = f"The two summaries for comparison are:\nSummary 1: {content}\nSummary 2: {question_summary}"
        
        try:
            rating_text = call_ollama(sys_prompt + "\n\n" + user_prompt, model)
            
            # Parse rating
            if "totally not similar" in rating_text.lower():
                rating = 0
            elif "not similar" in rating_text.lower():
                rating = 1
            elif "general" in rating_text.lower():
                rating = 2
            elif "very similar" in rating_text.lower():
                rating = 4
            elif "similar" in rating_text.lower():
                rating = 3
            else:
                print(f"  [Warning] Unexpected rating: {rating_text}")
                rating = -1
                
            rating_list.append(rating)
            
            if (idx + 1) % 3 == 0:
                print(f"  Compared {idx + 1}/{len(summaries)} summaries...")
                
        except Exception as e:
            print(f"  [Error] Failed to compare summary {idx + 1}: {e}")
            rating_list.append(-1)
    
    # Find best match
    best_idx = find_index_of_largest(rating_list)
    best_gid = gids[best_idx]
    best_rating = rating_list[best_idx]
    
    print(f"\n[Best Match] GID: {best_gid[:8]}... (Rating: {best_rating})")
    
    return best_gid
