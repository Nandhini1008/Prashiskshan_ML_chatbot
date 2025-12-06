"""
Qdrant indexing module for storing and managing vector embeddings.
Supports both local Docker and cloud deployments.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import uuid

class QdrantIndexer:
    """Manages Qdrant vector store for document embeddings."""
    
    def __init__(self, 
                 url: str = "http://localhost:6333",
                 api_key: str = None,
                 collection_name: str = "internship_education_db",
                 vector_size: int = 384):
        """
        Initialize the Qdrant indexer.
        
        Args:
            url: Qdrant server URL (e.g., http://localhost:6333 or cloud URL)
            api_key: API key for Qdrant Cloud (None for local)
            collection_name: Name of the collection
            vector_size: Dimension of embedding vectors
        """
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client and create collection if needed."""
        try:
            # Initialize client
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=60
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created new collection: {self.collection_name}")
            else:
                print(f"Using existing collection: {self.collection_name}")
            
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            print(f"Collection size: {collection_info.points_count} vectors")
            
        except Exception as e:
            print(f"Error initializing Qdrant client: {e}")
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
            # Prepare points for Qdrant
            points = []
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point_id = str(uuid.uuid4())  # Generate unique ID
                
                # Prepare payload (metadata + content)
                payload = {
                    "content": doc['content'],
                    **doc['metadata']  # Include all metadata fields
                }
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upload in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} vectors")
            
            print(f"Successfully added {len(documents)} documents to collection")
            
            # Get updated count
            collection_info = self.client.get_collection(self.collection_name)
            print(f"Total collection size: {collection_info.points_count} vectors")
            
        except Exception as e:
            print(f"Error adding documents to Qdrant: {e}")
            raise
    
    def reset_collection(self):
        """Reset the collection by deleting and recreating it."""
        try:
            # Delete collection
            self.client.delete_collection(collection_name=self.collection_name)
            print(f"Deleted collection: {self.collection_name}")
            
            # Recreate collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Created new collection: {self.collection_name}")
            
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
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "document_count": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "qdrant_url": self.url
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {}
    
    @property
    def collection(self):
        """Property for compatibility with ChromaDB interface."""
        class CollectionProxy:
            def __init__(self, client, collection_name):
                self._client = client
                self._collection_name = collection_name
            
            def count(self):
                info = self._client.get_collection(self._collection_name)
                return info.points_count
        
        return CollectionProxy(self.client, self.collection_name)
