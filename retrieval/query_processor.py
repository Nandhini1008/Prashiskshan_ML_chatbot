"""
Query preprocessing module for normalizing and analyzing user queries.
Handles different question formats and extracts important keywords.
"""

import re
from typing import List, Dict, Any

class QueryProcessor:
    """Processes and normalizes user queries for better retrieval."""
    
    # Stop words to remove (common words that don't help retrieval)
    STOP_WORDS = {
        'what', 'how', 'when', 'where', 'why', 'who', 'which', 'whom',
        'is', 'are', 'was', 'were', 'am', 'be', 'been', 'being',
        'do', 'does', 'did', 'doing', 'done',
        'have', 'has', 'had', 'having',
        'a', 'an', 'the',
        'and', 'or', 'but', 'if', 'then', 'else',
        'in', 'on', 'at', 'to', 'for', 'with', 'about', 'from', 'of', 'by',
        'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'this', 'that', 'these', 'those',
        'can', 'could', 'will', 'would', 'should', 'may', 'might', 'must',
        'tell', 'please', 'give', 'show', 'provide', 'want', 'need', 'like'
    }
    
    # Domain-specific keywords to always keep
    DOMAIN_KEYWORDS = {
        'internship', 'intern', 'fellowship', 'apprenticeship',
        'salary', 'stipend', 'pay', 'compensation', 'wage', 'benefits', 'perks',
        'housing', 'relocation', 'travel', 'insurance', 'health',
        'eligibility', 'requirements', 'criteria', 'qualifications',
        'application', 'apply', 'deadline', 'process', 'interview',
        'python', 'java', 'javascript', 'c++', 'programming', 'coding', 'software',
        'engineer', 'developer', 'data', 'analyst', 'scientist', 'designer',
        'google', 'microsoft', 'amazon', 'meta', 'apple', 'netflix', 'uber',
        'learn', 'study', 'prepare', 'practice', 'tutorial', 'course',
        'project', 'experience', 'skills', 'technical', 'resume', 'portfolio'
    }
    
    # Common abbreviations and their expansions
    ABBREVIATIONS = {
        'swe': 'software engineer',
        'msft': 'microsoft',
        'amzn': 'amazon',
        'fb': 'meta',
        'faang': 'facebook amazon apple netflix google',
        'cs': 'computer science',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'ds': 'data science',
        'r': 'are',
        'u': 'you',
        'ur': 'your',
        '4': 'for',
        '2': 'to',
        '@': 'at'
    }
    
    def __init__(self, min_keyword_length: int = 2):
        """
        Initialize query processor.
        
        Args:
            min_keyword_length: Minimum length for keywords to keep
        """
        self.min_keyword_length = min_keyword_length
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query text.
        
        Args:
            query: Raw user query
            
        Returns:
            Normalized query string
        """
        if not query:
            return ""
        
        # Convert to lowercase
        normalized = query.lower()
        
        # Expand common abbreviations
        for abbr, expansion in self.ABBREVIATIONS.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbr) + r'\b'
            normalized = re.sub(pattern, expansion, normalized)
        
        # Remove special characters except spaces and alphanumeric
        # Keep + and # as they're used in programming (C++, C#)
        normalized = re.sub(r'[^\w\s+#-]', ' ', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query.
        
        Args:
            query: Normalized query string
            
        Returns:
            List of important keywords
        """
        if not query:
            return []
        
        # Split into words
        words = query.lower().split()
        
        keywords = []
        for word in words:
            # Skip if too short
            if len(word) < self.min_keyword_length:
                continue
            
            # Keep if it's a domain keyword
            if word in self.DOMAIN_KEYWORDS:
                keywords.append(word)
                continue
            
            # Skip if it's a stop word (unless it's a domain keyword)
            if word in self.STOP_WORDS:
                continue
            
            # Keep other words
            keywords.append(word)
        
        return keywords
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query with normalization and keyword extraction.
        
        Args:
            query: Raw user query
            
        Returns:
            Dictionary with processed query information
        """
        # Normalize
        normalized = self.normalize_query(query)
        
        # Extract keywords
        keywords = self.extract_keywords(normalized)
        
        # Create keyword query (space-separated keywords)
        keyword_query = ' '.join(keywords)
        
        return {
            'original': query,
            'normalized': normalized,
            'keywords': keywords,
            'keyword_query': keyword_query
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to extract intent and entities.
        
        Args:
            query: User query
            
        Returns:
            Analysis results with intent and entities
        """
        processed = self.process_query(query)
        normalized = processed['normalized']
        keywords = processed['keywords']
        
        # Detect entities (companies)
        companies = []
        company_names = ['google', 'microsoft', 'amazon', 'meta', 'apple', 
                        'netflix', 'uber', 'facebook', 'tesla', 'nvidia']
        for company in company_names:
            if company in normalized:
                companies.append(company)
        
        # Detect intent
        intent = 'general'
        if any(word in keywords for word in ['internship', 'intern', 'fellowship']):
            intent = 'internship_info'
        elif any(word in keywords for word in ['salary', 'stipend', 'pay', 'compensation']):
            intent = 'compensation'
        elif any(word in keywords for word in ['eligibility', 'requirements', 'criteria']):
            intent = 'eligibility'
        elif any(word in keywords for word in ['application', 'apply', 'deadline']):
            intent = 'application'
        elif any(word in keywords for word in ['learn', 'study', 'tutorial', 'course']):
            intent = 'learning'
        elif any(word in keywords for word in ['interview', 'prepare', 'practice']):
            intent = 'interview_prep'
        
        return {
            **processed,
            'intent': intent,
            'companies': companies
        }
