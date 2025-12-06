"""
Quick test script to verify Qdrant retrieval is working.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.retriever import Retriever
from config.settings import get_config

def test_retrieval():
    """Test Qdrant retrieval."""
    print("="*60)
    print("TESTING QDRANT RETRIEVAL")
    print("="*60)
    
    config = get_config()
    
    print("\n[1/2] Initializing retriever...")
    retriever = Retriever(
        url=config["qdrant_url"],
        api_key=config["qdrant_api_key"],
        collection_name=config["collection_name"],
        embedding_model=config["embedding_model"],
        top_k=3
    )
    
    print("\n[2/2] Testing semantic search...")
    test_queries = [
        "What is the Google internship stipend?",
        "How do I prepare for interviews?",
        "What companies offer internships?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        results = retriever.retrieve(query, top_k=3)
        
        if results:
            print(f"   ✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                score = result['similarity_score']
                company = result['metadata'].get('company', 'N/A')
                content_preview = result['content'][:80].replace('\n', ' ')
                print(f"   {i}. Score: {score:.3f} | Company: {company}")
                print(f"      Preview: {content_preview}...")
        else:
            print("   ❌ No results found")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        test_retrieval()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
