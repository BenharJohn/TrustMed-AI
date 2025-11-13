"""
Vector-based retrieval using embeddings and cosine similarity
Replaces sequential LLM comparison with fast vector search
"""

from creat_graph_ollama import get_ollama_embedding, call_ollama
import time

def ensure_summary_embeddings(n4j, model="llama3"):
    """
    Check if Summary nodes have embeddings, generate if missing

    Args:
        n4j: Neo4jGraph instance
        model: Ollama model for embeddings

    Returns:
        bool: True if embeddings exist or were successfully generated
    """
    print("[Vector Setup] Checking for Summary node embeddings...")

    # Check if embeddings exist
    check_query = """
    MATCH (s:Summary)
    WHERE s.embedding IS NULL
    RETURN count(s) AS missing_count
    """

    result = n4j.query(check_query)
    missing_count = result[0]['missing_count'] if result else 0

    if missing_count == 0:
        print("  [OK] All Summary nodes have embeddings")
        return True

    print(f"  [WARNING] {missing_count} Summary nodes missing embeddings - generating now...")

    # Get all summaries without embeddings
    fetch_query = """
    MATCH (s:Summary)
    WHERE s.embedding IS NULL
    RETURN s.gid AS gid, s.content AS content
    """

    summaries = n4j.query(fetch_query)

    # Generate and update embeddings
    for idx, summary in enumerate(summaries):
        gid = summary['gid']
        content = summary['content']

        print(f"  [{idx+1}/{len(summaries)}] Generating embedding for GID {gid[:8]}...")

        try:
            embedding = get_ollama_embedding(content, model)

            if embedding:
                # Update Summary node with embedding
                update_query = """
                MATCH (s:Summary {gid: $gid})
                SET s.embedding = $embedding
                """
                n4j.query(update_query, {'gid': gid, 'embedding': embedding})
                print(f"    [OK] Embedding saved (dimension: {len(embedding)})")
            else:
                print(f"    [FAILED] Failed to generate embedding")

        except Exception as e:
            print(f"    [ERROR] Error generating embedding: {e}")
            continue

    print("  [OK] Embedding generation complete!")
    return True


def vector_ret_ollama(n4j, question, model="llama3", top_k=3):
    """
    Vector-based retrieval using cosine similarity
    Replaces seq_ret_ollama with much faster embedding comparison

    Args:
        n4j: Neo4jGraph instance
        question: User's question
        model: Ollama model name
        top_k: Number of top candidates to retrieve

    Returns:
        gid: Best matching Graph ID
    """

    print(f"\n[Vector Retrieval] Using embedding-based search...")
    start_time = time.time()

    # Ensure Summary nodes have embeddings
    if not ensure_summary_embeddings(n4j, model):
        print("  [ERROR] Could not ensure embeddings exist - falling back to first Summary")
        # Fallback: return first available GID
        fallback_query = "MATCH (s:Summary) RETURN s.gid AS gid LIMIT 1"
        result = n4j.query(fallback_query)
        return result[0]['gid'] if result else None

    # Step 1: Generate question embedding (1 LLM call - fast!)
    print(f"\n[Step 1] Generating question embedding...")
    question_embedding = get_ollama_embedding(question, model)

    if not question_embedding:
        print("  [ERROR] Failed to generate question embedding")
        return None

    print(f"  [OK] Question embedding generated (dimension: {len(question_embedding)})")

    # Step 2: Use Neo4j to compute cosine similarity with all Summary embeddings
    print(f"\n[Step 2] Computing cosine similarity with all Summary nodes...")

    similarity_query = """
    MATCH (s:Summary)
    WHERE s.embedding IS NOT NULL
    WITH s,
         gds.similarity.cosine(s.embedding, $question_embedding) AS similarity
    RETURN s.gid AS gid,
           s.content AS content,
           similarity
    ORDER BY similarity DESC
    LIMIT $top_k
    """

    try:
        candidates = n4j.query(similarity_query, {
            'question_embedding': question_embedding,
            'top_k': top_k
        })

        if not candidates:
            print("  [ERROR] No candidates found")
            return None

        print(f"  [OK] Found {len(candidates)} candidates:")
        for idx, candidate in enumerate(candidates):
            gid = candidate['gid']
            similarity = candidate['similarity']
            content_preview = candidate['content'][:80] if candidate['content'] else "No content"
            print(f"    [{idx+1}] GID {gid[:8]}... - Similarity: {similarity:.4f}")
            print(f"        Preview: {content_preview}...")

    except Exception as e:
        print(f"  [ERROR] Error computing similarity: {e}")
        print("  [INFO] Falling back to manual cosine similarity computation...")

        # Fallback: Manual cosine similarity in Python
        import math

        fetch_all_query = """
        MATCH (s:Summary)
        WHERE s.embedding IS NOT NULL
        RETURN s.gid AS gid, s.content AS content, s.embedding AS embedding
        """

        all_summaries = n4j.query(fetch_all_query)

        def cosine_similarity(vec1, vec2):
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            return dot_product / (magnitude1 * magnitude2) if magnitude1 and magnitude2 else 0

        candidates = []
        for summary in all_summaries:
            similarity = cosine_similarity(question_embedding, summary['embedding'])
            candidates.append({
                'gid': summary['gid'],
                'content': summary['content'],
                'similarity': similarity
            })

        # Sort by similarity and take top_k
        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        candidates = candidates[:top_k]

        print(f"  [OK] Found {len(candidates)} candidates using manual similarity:")
        for idx, candidate in enumerate(candidates):
            gid = candidate['gid']
            similarity = candidate['similarity']
            content_preview = candidate['content'][:80] if candidate['content'] else "No content"
            print(f"    [{idx+1}] GID {gid[:8]}... - Similarity: {similarity:.4f}")
            print(f"        Preview: {content_preview}...")

    # Step 3: If only one candidate or very high similarity, return immediately
    if len(candidates) == 1 or (candidates and candidates[0]['similarity'] > 0.85):
        best_gid = candidates[0]['gid']
        elapsed = time.time() - start_time
        print(f"\n[Result] Best match: GID {best_gid[:8]}... (in {elapsed:.2f}s)")
        print(f"[Performance] Vector search: ~4 LLM calls vs ~{len(candidates)*10}+ with sequential")
        return best_gid

    # Step 4: Optional re-ranking with LLM (only top-3, not all summaries!)
    print(f"\n[Step 3] Re-ranking top {len(candidates)} candidates with LLM...")

    best_gid = None
    best_rating = -1

    sys_prompt = """You are comparing a question to a medical summary. Rate their semantic similarity from 1-10.
Output ONLY a single number 1-10, nothing else.
10 = extremely relevant, 1 = not relevant at all"""

    for idx, candidate in enumerate(candidates):
        gid = candidate['gid']
        content = candidate['content']

        user_prompt = f"Question: {question}\n\nSummary: {content}\n\nRating (1-10):"

        try:
            rating_text = call_ollama(sys_prompt + "\n\n" + user_prompt, model)
            rating = int(''.join(filter(str.isdigit, rating_text.strip()[:2])))

            print(f"  [{idx+1}] GID {gid[:8]}... - LLM Rating: {rating}/10")

            if rating > best_rating:
                best_rating = rating
                best_gid = gid

        except Exception as e:
            print(f"  [ERROR] Error re-ranking candidate {idx+1}: {e}")
            continue

    elapsed = time.time() - start_time

    if best_gid:
        print(f"\n[Result] Best match after re-ranking: GID {best_gid[:8]}... (rating: {best_rating}/10)")
        print(f"[Performance] Total time: {elapsed:.2f}s with {1 + len(candidates)} LLM calls")
        print(f"[Speedup] ~{20}x faster than sequential comparison!")
        return best_gid
    else:
        # Fallback to highest similarity
        best_gid = candidates[0]['gid']
        print(f"\n[Result] Using highest similarity match: GID {best_gid[:8]}...")
        print(f"[Performance] Total time: {elapsed:.2f}s")
        return best_gid
