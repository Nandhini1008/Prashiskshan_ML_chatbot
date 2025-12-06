"""
Score threshold module for validating retrieval confidence.
Filters retrieved documents based on similarity scores.
"""

from typing import List, Dict, Any

class ScoreThreshold:
    """Validates retrieval results based on similarity scores."""
    
    def __init__(self, threshold: float = 0.55):
        """
        Initialize the score threshold validator.
        
        Args:
            threshold: Minimum similarity score for valid results
        """
        self.threshold = threshold
    
    def filter_by_threshold(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter documents that meet the similarity threshold.
        
        Args:
            retrieved_docs: List of retrieved documents with similarity scores
            
        Returns:
            Filtered list of documents above threshold
        """
        if not retrieved_docs:
            return []
        
        filtered_docs = [
            doc for doc in retrieved_docs
            if doc.get('similarity_score', 0) >= self.threshold
        ]
        
        return filtered_docs
    
    def validate_retrieval(self, retrieved_docs: List[Dict[str, Any]]) -> bool:
        """
        Check if any retrieved document meets the threshold.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            True if at least one document meets threshold, False otherwise
        """
        filtered_docs = self.filter_by_threshold(retrieved_docs)
        return len(filtered_docs) > 0
    
    def get_best_match(self, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get the document with the highest similarity score above threshold.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Best matching document or empty dict if none meet threshold
        """
        filtered_docs = self.filter_by_threshold(retrieved_docs)
        
        if not filtered_docs:
            return {}
        
        # Sort by similarity score in descending order
        sorted_docs = sorted(
            filtered_docs,
            key=lambda x: x.get('similarity_score', 0),
            reverse=True
        )
        
        return sorted_docs[0]
    
    def get_confidence_level(self, similarity_score: float) -> str:
        """
        Get confidence level description based on similarity score.
        
        Args:
            similarity_score: Similarity score between 0 and 1
            
        Returns:
            Confidence level as string
        """
        if similarity_score >= 0.9:
            return "very_high"
        elif similarity_score >= 0.8:
            return "high"
        elif similarity_score >= 0.7:
            return "medium"
        elif similarity_score >= self.threshold:
            return "low"
        else:
            return "below_threshold"
