"""
State definition for LangGraph using TypedDict (T-T pattern).
Defines the structure of the chatbot state.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal

class ChatbotState(TypedDict):
    """State schema for the chatbot graph using TypedDict."""
    
    # User and session information
    user_id: str
    session_id: str
    query: str
    
    # Conversation history
    conversation_history: List[Dict[str, str]]
    formatted_history: str
    
    # Routing information
    intent: Optional[str]
    pipeline: Optional[Literal["RAG", "EXTERNAL"]]
    
    # RAG pipeline state
    retrieved_docs: List[Dict[str, Any]]
    retrieval_valid: bool
    filtered_docs: List[Dict[str, Any]]
    
    # External pipeline state
    gemini_response: Optional[str]
    
    # Final output
    answer: Optional[str]

