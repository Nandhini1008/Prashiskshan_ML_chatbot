"""
Initialize Qdrant collection for the chatbot.
Run this script before starting the chatbot service.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestion.qdrant_index import QdrantIndexer
from config.settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME, EMBEDDING_DIMENSION

def init_qdrant():
    """Initialize Qdrant collection."""
    print("=" * 60)
    print("Initializing Qdrant Collection")
    print("=" * 60)
    
    try:
        # Create indexer (this will create the collection if it doesn't exist)
        indexer = QdrantIndexer(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            collection_name=QDRANT_COLLECTION_NAME,
            vector_size=EMBEDDING_DIMENSION
        )
        
        # Get stats
        stats = indexer.get_collection_stats()
        
        print("\n✅ Qdrant collection initialized successfully!")
        print(f"\nCollection Stats:")
        print(f"  - Name: {stats['collection_name']}")
        print(f"  - Documents: {stats['document_count']}")
        print(f"  - Vector Size: {stats['vector_size']}")
        print(f"  - Distance Metric: {stats['distance_metric']}")
        print(f"  - Qdrant URL: {stats['qdrant_url']}")
        
        if stats['document_count'] == 0:
            print("\n⚠️  Collection is empty. You may want to ingest documents.")
            print("   Run: python ingestion/ingest_data.py")
        
        print("\n" + "=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing Qdrant: {e}")
        print("\nMake sure:")
        print("  1. Qdrant is running: docker-compose up -d qdrant")
        print("  2. QDRANT_URL is correct in .env")
        print("  3. Qdrant is accessible at the specified URL")
        return False

if __name__ == "__main__":
    success = init_qdrant()
    sys.exit(0 if success else 1)
