"""
Intent classification module for routing user queries.
Classifies queries into one of four intent categories.
"""

from typing import Dict, Any
import re

class IntentRouter:
    """Classifies user queries into intent categories."""
    
    # Intent categories
    COMPANY_INTERNSHIP = "COMPANY_INTERNSHIP"
    EDUCATION_CODING = "EDUCATION_CODING"
    INTERVIEW_PREPARATION = "INTERVIEW_PREPARATION"
    GENERAL_EDUCATION = "GENERAL_EDUCATION"
    
    def __init__(self):
        """Initialize the intent router with keyword patterns."""
        # Keywords for each intent category
        self.internship_keywords = [
            'internship', 'intern', 'company', 'companies', 'stipend', 
            'eligibility', 'apply', 'application', 'deadline', 'requirements',
            'hiring', 'recruitment', 'job', 'position', 'opening', 'opportunity'
        ]
        
        self.coding_keywords = [
            'programming', 'code', 'coding', 'algorithm', 'data structure',
            'dsa', 'python', 'java', 'javascript', 'c++', 'function',
            'class', 'variable', 'loop', 'array', 'list', 'dictionary',
            'recursion', 'sorting', 'searching', 'tree', 'graph', 'stack',
            'queue', 'linked list', 'hash', 'dynamic programming'
        ]
        
        self.interview_keywords = [
            'interview', 'hr', 'placement', 'behavioral', 'technical round',
            'resume', 'cv', 'cover letter', 'preparation', 'mock interview',
            'interview question', 'interview tip', 'how to prepare'
        ]
        
        self.education_keywords = [
            'learn', 'study', 'course', 'tutorial', 'concept', 'theory',
            'explain', 'what is', 'how does', 'definition', 'understand',
            'teach', 'education', 'knowledge', 'subject'
        ]
    
    def _count_keyword_matches(self, text: str, keywords: list) -> int:
        """
        Count how many keywords match in the text.
        
        Args:
            text: Input text to analyze
            keywords: List of keywords to match
            
        Returns:
            Number of keyword matches
        """
        text_lower = text.lower()
        count = 0
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                count += 1
        
        return count
    
    def classify_intent(self, query: str) -> str:
        """
        Classify the user query into an intent category.
        
        Args:
            query: User query text
            
        Returns:
            Intent category as string
        """
        if not query:
            return self.GENERAL_EDUCATION
        
        # Count matches for each category
        internship_score = self._count_keyword_matches(query, self.internship_keywords)
        coding_score = self._count_keyword_matches(query, self.coding_keywords)
        interview_score = self._count_keyword_matches(query, self.interview_keywords)
        education_score = self._count_keyword_matches(query, self.education_keywords)
        
        # Determine intent based on highest score
        scores = {
            self.COMPANY_INTERNSHIP: internship_score,
            self.EDUCATION_CODING: coding_score,
            self.INTERVIEW_PREPARATION: interview_score,
            self.GENERAL_EDUCATION: education_score
        }
        
        # Get intent with highest score
        intent = max(scores, key=scores.get)
        
        # If no clear match, default to general education
        if scores[intent] == 0:
            intent = self.GENERAL_EDUCATION
        
        return intent
    
    def get_intent_info(self, intent: str) -> Dict[str, Any]:
        """
        Get information about an intent category.
        
        Args:
            intent: Intent category
            
        Returns:
            Dictionary with intent information
        """
        intent_info = {
            self.COMPANY_INTERNSHIP: {
                "name": "Company Internship",
                "description": "Questions about internships, companies, and applications",
                "uses_rag": True
            },
            self.EDUCATION_CODING: {
                "name": "Education - Coding",
                "description": "Programming and computer science questions",
                "uses_rag": False
            },
            self.INTERVIEW_PREPARATION: {
                "name": "Interview Preparation",
                "description": "Interview tips and preparation guidance",
                "uses_rag": False
            },
            self.GENERAL_EDUCATION: {
                "name": "General Education",
                "description": "General learning and educational questions",
                "uses_rag": False
            }
        }
        
        return intent_info.get(intent, {})
