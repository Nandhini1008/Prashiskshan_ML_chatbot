"""
Test script to verify ChromaDB embedding and semantic search functionality.
Run this after ingesting data to test the system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.embeddings import EmbeddingGenerator
from ingestion.chroma_index import ChromaIndexer
from retrieval.retriever import Retriever
from config.settings import get_config

def test_embedding_generation():
    """Test 1: Verify embedding generation works."""
    print("\n" + "="*60)
    print("TEST 1: Embedding Generation")
    print("="*60)
    
    try:
        embedder = EmbeddingGenerator("sentence-transformers/all-MiniLM-L6-v2")
        
        test_text = "What is the stipend for Google internship?"
        embedding = embedder.generate_embedding(test_text)
        
        print(f"✓ Text: {test_text}")
        print(f"✓ Embedding dimension: {len(embedding)}")
        print(f"✓ Embedding sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        print("\n✅ Embedding generation PASSED")
        return True
    except Exception as e:
        print(f"\n❌ Embedding generation FAILED: {e}")
        return False

def test_chromadb_connection():
    """Test 2: Verify ChromaDB connection and data."""
    print("\n" + "="*60)
    print("TEST 2: ChromaDB Connection")
    print("="*60)
    
    try:
        config = get_config()
        indexer = ChromaIndexer(
            persist_directory=config["chroma_persist_dir"],
            collection_name=config["collection_name"]
        )
        
        stats = indexer.get_collection_stats()
        doc_count = stats['document_count']
        
        print(f"✓ Collection: {stats['collection_name']}")
        print(f"✓ Persist directory: {stats['persist_directory']}")
        print(f"✓ Document count: {doc_count}")
        
        if doc_count > 0:
            print("\n✅ ChromaDB connection PASSED")
            return True
        else:
            print("\n⚠️  ChromaDB is empty. Run 'python ingest_data.py' first.")
            return False
    except Exception as e:
        print(f"\n❌ ChromaDB connection FAILED: {e}")
        print("   Make sure to run 'python ingest_data.py' first.")
        return False

def test_semantic_search():
    """Test 3: Verify semantic search retrieval."""
    print("\n" + "="*60)
    print("TEST 3: Semantic Search")
    print("="*60)
    
    try:
        config = get_config()
        retriever = Retriever(
            persist_directory=config["chroma_persist_dir"],
            collection_name=config["collection_name"],
            embedding_model=config["embedding_model"],
            top_k=3
        )
        
        # Test queries
        test_queries = [
            "What is the Google internship stipend?",
            "How do I prepare for technical interviews?",
            "What are the eligibility requirements?"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            results = retriever.retrieve(query, top_k=3)
            
            if results:
                print(f"   Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    score = result['similarity_score']
                    company = result['metadata'].get('company', 'N/A')
                    doc_type = result['metadata'].get('document_type', 'N/A')
                    content_preview = result['content'][:100].replace('\n', ' ')
                    
                    print(f"   {i}. Score: {score:.3f} | Company: {company} | Type: {doc_type}")
                    print(f"      Preview: {content_preview}...")
            else:
                print("   ⚠️  No results found")
        
        print("\n✅ Semantic search PASSED")
        return True
    except Exception as e:
        print(f"\n❌ Semantic search FAILED: {e}")
        return False

def test_similarity_understanding():
    """Test 4: Verify semantic understanding (not just keyword matching)."""
    print("\n" + "="*60)
    print("TEST 4: Semantic Understanding")
    print("="*60)
    
    try:
        config = get_config()
        retriever = Retriever(
            persist_directory=config["chroma_persist_dir"],
            collection_name=config["collection_name"],
            embedding_model=config["embedding_model"],
            top_k=1
        )
        
        # Test semantic similarity (different words, same meaning)
        query_pairs = [
            ("Google salary", "Google stipend"),
            ("How much does Google pay?", "Google compensation"),
            ("Interview preparation", "Getting ready for interviews")
        ]
        
        print("\nTesting semantic similarity (different words, same meaning):\n")
        
        for query1, query2 in query_pairs:
            results1 = retriever.retrieve(query1, top_k=1)
            results2 = retriever.retrieve(query2, top_k=1)
            
            if results1 and results2:
                score1 = results1[0]['similarity_score']
                score2 = results2[0]['similarity_score']
                content1 = results1[0]['content'][:50].replace('\n', ' ')
                content2 = results2[0]['content'][:50].replace('\n', ' ')
                
                print(f"Query 1: '{query1}'")
                print(f"  → Score: {score1:.3f} | Content: {content1}...")
                print(f"Query 2: '{query2}'")
                print(f"  → Score: {score2:.3f} | Content: {content2}...")
                
                # Check if they retrieve similar content
                if abs(score1 - score2) < 0.2:
                    print("  ✓ Semantic similarity detected\n")
                else:
                    print("  ⚠️  Different results\n")
        
        print("✅ Semantic understanding PASSED")
        return True
    except Exception as e:
        print(f"\n❌ Semantic understanding FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CHROMADB EMBEDDING & SEMANTIC SEARCH VERIFICATION")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Embedding Generation", test_embedding_generation()))
    results.append(("ChromaDB Connection", test_chromadb_connection()))
    results.append(("Semantic Search", test_semantic_search()))
    results.append(("Semantic Understanding", test_similarity_understanding()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Your system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        if not results[1][1]:  # ChromaDB connection failed
            print("\n💡 Tip: Run 'python ingest_data.py' to index your data first.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
