# Chatbot Caching Mechanism

## Overview

The chatbot implements an intelligent caching system to avoid storing duplicate Q&A pairs in the vector database while ensuring fast retrieval of previously answered questions.

## Flow Diagram

```
User Query
    ↓
1. Normalize Query
    ↓
2. Search Vector DB (Qdrant)
    ↓
3. Check Similarity Scores
    ↓
    ├─→ High Similarity (≥0.95) → Return Cached Answer ✓
    │
    ├─→ Medium Similarity (≥0.50) → Use RAG with Retrieved Docs
    │
    └─→ Low Similarity (<0.50) → Generate with Gemini LLM
                                      ↓
                                  Check for Duplicates
                                      ↓
                                  Store in Vector DB (if unique)
```

## Key Components

### 1. Query Normalization

**Location:** `retrieval/retriever.py` - `retrieve()` method

**Process:**

- Converts query to lowercase
- Removes extra whitespace
- Extracts keywords for better matching

```python
def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
    # Normalize query
    normalized_query = query.lower().strip()
    keywords = self._extract_keywords(normalized_query)

    # Generate embedding and search
    ...
```

### 2. Similarity Thresholds

**Location:** `config/settings.py`

```python
SIMILARITY_THRESHOLD = 0.50      # Minimum for RAG retrieval
EXACT_MATCH_THRESHOLD = 0.95     # Cached answer threshold
DUPLICATE_THRESHOLD = 0.95       # Duplicate detection threshold
```

**Threshold Meanings:**

| Threshold       | Range     | Action                         |
| --------------- | --------- | ------------------------------ |
| Exact Match     | ≥0.95     | Return cached answer directly  |
| High Similarity | 0.50-0.94 | Use RAG with retrieved context |
| Low Similarity  | <0.50     | Generate new answer with LLM   |

### 3. Cached Answer Retrieval

**Location:** `graph/nodes.py` - `rag_answer_node()`

**Process:**

1. Check retrieved documents for "Generated Q&A" type
2. If similarity ≥ 0.95, return cached answer immediately
3. Otherwise, generate new answer with LLM

```python
def rag_answer_node(self, state: ChatbotState) -> ChatbotState:
    for doc in filtered_docs:
        similarity = doc.get('similarity_score', 0)
        doc_type = metadata.get('document_type', '')

        # Return cached answer if very similar
        if doc_type == 'Generated Q&A' and similarity >= EXACT_MATCH_THRESHOLD:
            cached_answer = metadata.get('answer', '')
            if cached_answer:
                print(f"✓ Using cached answer (similarity: {similarity:.4f})")
                state["answer"] = cached_answer
                return state

    # Generate new answer if no cache hit
    ...
```

### 4. Duplicate Prevention

**Location:** `retrieval/retriever.py` - `ingest_qa_pair()`

**Process:**

1. Generate embedding for new question
2. Search for similar "Generated Q&A" documents
3. If similarity ≥ 0.95, skip ingestion (duplicate detected)
4. Otherwise, store new Q&A pair

```python
def ingest_qa_pair(self, question: str, answer: str, similarity_threshold: float = 0.95) -> bool:
    # Generate embedding
    embedding = self.embedding_generator.generate_embedding(question)

    # Search for duplicates
    search_results = self.client.search(
        collection_name=self.collection_name,
        query_vector=embedding.tolist(),
        limit=5,
        query_filter=Filter(
            must=[FieldCondition(key="document_type", match=MatchValue(value="Generated Q&A"))]
        )
    )

    # Check for duplicates
    for result in search_results:
        if result.score >= similarity_threshold:
            print(f"⚠ Similar Q&A already exists (similarity: {result.score:.4f})")
            return True  # Skip ingestion

    # No duplicate found, proceed with ingestion
    ...
```

## Complete Flow Example

### Example 1: First Time Question

```
User: "What internships are available in Bangalore?"

1. Normalize: "what internships are available in bangalore"
2. Search Vector DB: No similar Q&A found (score < 0.50)
3. Route to: External Knowledge (Gemini LLM)
4. Generate Answer: "Here are internships in Bangalore..."
5. Check Duplicates: No similar Q&A exists
6. Store in DB: ✓ New Q&A pair stored
```

### Example 2: Similar Question (Cached)

```
User: "What are the internships in Bangalore?"

1. Normalize: "what are the internships in bangalore"
2. Search Vector DB: Found similar Q&A (score = 0.97)
3. Check Threshold: 0.97 ≥ 0.95 (EXACT_MATCH)
4. Return Cached: ✓ Return stored answer immediately
5. Skip LLM: No API call needed
6. Skip Storage: No duplicate storage
```

### Example 3: Slightly Different Question

```
User: "Tell me about Bangalore internship opportunities"

1. Normalize: "tell me about bangalore internship opportunities"
2. Search Vector DB: Found related docs (score = 0.75)
3. Check Threshold: 0.75 < 0.95 (not exact match)
4. Use RAG: Generate answer using retrieved context
5. Generate Answer: "Based on available information..."
6. Check Duplicates: Similar Q&A exists (score = 0.96)
7. Skip Storage: ⚠ Duplicate detected, skip ingestion
```

## Benefits

### 1. Performance Optimization

- **Cached answers:** ~50ms response time (no LLM call)
- **New answers:** ~2-3s response time (LLM generation)
- **Savings:** 98% faster for cached queries

### 2. Cost Reduction

- Avoid redundant Gemini API calls
- Reduce vector database storage
- Lower embedding generation costs

### 3. Consistency

- Same question → Same answer
- Prevents answer drift over time
- Maintains quality across sessions

### 4. Storage Efficiency

- No duplicate Q&A pairs
- Cleaner vector database
- Better search performance

## Configuration

### Adjusting Thresholds

**Location:** `config/settings.py`

```python
# For stricter caching (fewer cache hits, more LLM calls)
EXACT_MATCH_THRESHOLD = 0.98

# For looser caching (more cache hits, fewer LLM calls)
EXACT_MATCH_THRESHOLD = 0.90

# For stricter duplicate prevention
DUPLICATE_THRESHOLD = 0.98

# For looser duplicate prevention (allow more variations)
DUPLICATE_THRESHOLD = 0.90
```

### Recommendations

| Use Case     | EXACT_MATCH | DUPLICATE | Reasoning                    |
| ------------ | ----------- | --------- | ---------------------------- |
| FAQ Bot      | 0.90        | 0.95      | More caching, less variation |
| General Chat | 0.95        | 0.95      | Balanced approach            |
| Creative Bot | 0.98        | 0.90      | Less caching, more variation |

## Monitoring

### Debug Output

The system logs caching decisions to stderr:

```
=== AUTO-INGESTION ===
→ No duplicate found, ingesting new Q&A pair
✓ Q&A pair successfully ingested into Qdrant

=== NEXT QUERY ===
✓ Using cached answer (similarity: 0.9723)

=== SIMILAR QUERY ===
⚠ Similar Q&A already exists (similarity: 0.9612)
  Existing: What internships are available in Bangalore?
  New: Tell me about Bangalore internship opportunities
  → Skipping ingestion to avoid duplicate
```

### Metrics to Track

1. **Cache Hit Rate:** % of queries answered from cache
2. **Duplicate Prevention Rate:** % of ingestions skipped
3. **Average Response Time:** Cached vs New answers
4. **Storage Growth:** Rate of new Q&A pairs added

## Troubleshooting

### Issue: Too Many Cache Misses

**Symptom:** Similar questions not returning cached answers

**Solution:**

- Lower `EXACT_MATCH_THRESHOLD` (e.g., 0.90)
- Improve query normalization
- Check embedding model quality

### Issue: Too Many Duplicates

**Symptom:** Duplicate Q&A pairs in database

**Solution:**

- Increase `DUPLICATE_THRESHOLD` (e.g., 0.98)
- Run deduplication script
- Check similarity calculation

### Issue: Stale Cached Answers

**Symptom:** Outdated answers being returned

**Solution:**

- Add timestamp to Q&A pairs
- Implement cache expiration
- Periodically refresh cached answers

## Future Enhancements

1. **Semantic Clustering:** Group similar questions together
2. **Cache Expiration:** Auto-expire old Q&A pairs
3. **Answer Versioning:** Track answer updates over time
4. **User Feedback:** Update cache based on user ratings
5. **Multi-language Support:** Cache answers per language

## Code References

- **Main Flow:** `graph/build_graph.py`
- **Caching Logic:** `graph/nodes.py` - `rag_answer_node()`
- **Duplicate Check:** `retrieval/retriever.py` - `ingest_qa_pair()`
- **Configuration:** `config/settings.py`
- **Thresholds:** `retrieval/score_threshold.py`
