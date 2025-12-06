"""
ChromaDB indexing module for storing and managing vector embeddings.
Uses FAISS as the similarity index backend.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import os

class ChromaIndexer:
    """Manages ChromaDB vector store with FAISS indexing."""
    
    def __init__(self, persist_directory: str = "vectorstore/chroma", 
                 collection_name: str = "internship_education_db"):
        """
        Initialize the ChromaDB indexer.
        
        Args:
            persist_directory: Directory to persist the vector store
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            print(f"ChromaDB initialized with collection: {self.collection_name}")
            print(f"Current collection size: {self.collection.count()}")
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Add documents with embeddings to the collection.
        
        Args:
            documents: List of documents with content and metadata
            embeddings: List of embedding vectors
        """
        if not documents or not embeddings:
            print("No documents or embeddings to add")
            return
        
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        try:
            # Prepare data for ChromaDB
            ids = [f"doc_{i}" for i in range(len(documents))]
            texts = [doc['content'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                
                self.collection.add(
                    ids=ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=texts[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
                
                print(f"Added batch {i//batch_size + 1}: {end_idx - i} documents")
            
            print(f"Successfully added {len(documents)} documents to collection")
            print(f"Total collection size: {self.collection.count()}")
            
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            raise
    
    def reset_collection(self):
        """Reset the collection by deleting and recreating it."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Collection {self.collection_name} reset successfully")
        except Exception as e:
            print(f"Error resetting collection: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {}
