"""
Data ingestion script for indexing documents into ChromaDB.
Run this script to prepare the vector store before using the chatbot.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.load_data import DataLoader
from ingestion.clean_text import TextCleaner
from ingestion.chunking import TextChunker
from ingestion.embeddings import EmbeddingGenerator
from ingestion.qdrant_index import QdrantIndexer
from config.settings import get_config

def run_ingestion():
    """Run the complete data ingestion pipeline."""
    print("=" * 60)
    print("RAG CHATBOT - DATA INGESTION PIPELINE")
    print("=" * 60)
    
    # Load configuration
    config = get_config()
    
    print("\n[1/5] Loading documents...")
    loader = DataLoader(config.get("data_dir", "data"))
    documents = loader.load_all_documents()
    
    if not documents:
        print("No documents found. Please add documents to the data/ directory.")
        return
    
    print(f"Loaded {len(documents)} documents")
    
    print("\n[2/5] Cleaning documents...")
    cleaner = TextCleaner()
    cleaned_docs = [cleaner.clean_document(doc) for doc in documents]
    print(f"Cleaned {len(cleaned_docs)} documents")
    
    print("\n[3/5] Chunking documents...")
    chunker = TextChunker(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"]
    )
    chunks = chunker.chunk_documents(cleaned_docs)
    print(f"Created {len(chunks)} chunks")
    
    print("\n[4/5] Generating embeddings...")
    embedder = EmbeddingGenerator(config["embedding_model"])
    texts = [chunk["content"] for chunk in chunks]
    embeddings = embedder.generate_embeddings(texts)
    print(f"Generated {len(embeddings)} embeddings")
    
    print("\n[5/5] Indexing in Qdrant...")
    indexer = QdrantIndexer(
        url=config["qdrant_url"],
        api_key=config["qdrant_api_key"],
        collection_name=config["collection_name"],
        vector_size=config.get("embedding_dimension", 384)
    )
    
    # Ask if user wants to reset existing collection
    if indexer.collection.count() > 0:
        print(f"\nWarning: Collection already contains {indexer.collection.count()} documents.")
        response = input("Do you want to reset and re-index? (yes/no): ").strip().lower()
        if response == 'yes':
            indexer.reset_collection()
    
    indexer.add_documents(chunks, embeddings)
    
    # Print statistics
    stats = indexer.get_collection_stats()
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Collection: {stats['collection_name']}")
    print(f"Total documents: {stats['document_count']}")
    print(f"Qdrant URL: {stats['qdrant_url']}")
    print("\nYou can now run the chatbot using: python main.py")


if __name__ == "__main__":
    try:
        run_ingestion()
    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
