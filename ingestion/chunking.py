"""
Text chunking module for splitting documents into smaller segments.
Implements overlapping chunking strategy for better context preservation.
"""

from typing import List, Dict, Any

class TextChunker:
    """Splits text into overlapping chunks."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                search_start = max(start, end - 100)
                search_text = text[search_start:end + 50]
                
                # Find the last sentence ending
                last_period = search_text.rfind('.')
                last_question = search_text.rfind('?')
                last_exclamation = search_text.rfind('!')
                
                sentence_end = max(last_period, last_question, last_exclamation)
                
                if sentence_end != -1:
                    # Adjust end to sentence boundary
                    end = search_start + sentence_end + 1
            
            # Extract chunk
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start <= end - self.chunk_size:
                start = end
        
        return chunks
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a document into chunks while preserving metadata.
        
        Args:
            document: Document with 'content' and 'metadata' keys
            
        Returns:
            List of chunk documents with metadata
        """
        text = document.get('content', '')
        metadata = document.get('metadata', {})
        
        chunks = self.split_text(text)
        
        chunked_documents = []
        for idx, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_id'] = idx
            chunk_metadata['total_chunks'] = len(chunks)
            
            chunked_documents.append({
                'content': chunk,
                'metadata': chunk_metadata
            })
        
        return chunked_documents
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        for document in documents:
            chunks = self.chunk_document(document)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks
