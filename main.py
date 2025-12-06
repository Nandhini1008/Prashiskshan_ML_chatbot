"""
Main entry point for the RAG chatbot system.
Handles user query intake and orchestrates the pipeline.
"""

import os
from config.settings import get_config, validate_config
from retrieval.retriever import Retriever
from retrieval.score_threshold import ScoreThreshold
from llm.gemini_llm import GeminiLLM
from routing.route_rules import RouteRules
from graph.memory import ConversationMemory
from graph.build_graph import ChatbotGraph

class RAGChatbot:
    """Main chatbot class orchestrating all components."""
    
    def __init__(self):
        """Initialize the RAG chatbot with all components."""
        # Load configuration
        self.config = get_config()
        
        # Validate configuration
        if not validate_config():
            raise RuntimeError("Invalid configuration: Missing API keys")
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all chatbot components."""
        print("Initializing RAG Chatbot components...")
        
        # Initialize retriever
        self.retriever = Retriever(
            url=self.config["qdrant_url"],
            api_key=self.config["qdrant_api_key"],
            collection_name=self.config["collection_name"],
            embedding_model=self.config["embedding_model"],
            top_k=self.config["top_k"]
        )
        
        # Initialize score threshold
        self.score_threshold = ScoreThreshold(
            threshold=self.config["similarity_threshold"]
        )
        
        # Initialize Gemini LLM
        self.gemini_llm = GeminiLLM(
            api_key=self.config["gemini_api_key"],
            model=self.config["gemini_model"],
            temperature=self.config["gemini_temperature"],
            max_tokens=self.config["gemini_max_tokens"]
        )
        
        # Initialize routing
        self.route_rules = RouteRules()
        
        # Initialize memory
        self.memory = ConversationMemory(
            max_history=self.config["max_conversation_history"]
        )
        
        # Build graph
        self.graph = ChatbotGraph(
            retriever=self.retriever,
            score_threshold=self.score_threshold,
            gemini_llm=self.gemini_llm,
            route_rules=self.route_rules,
            memory=self.memory
        )
        
        print("RAG Chatbot initialized successfully!")
    
    def query(self, user_query: str, user_id: str, session_id: str) -> str:
        """
        Process a user query and return the response.
        
        Args:
            user_query: The user's question
            user_id: Unique user identifier
            session_id: User session identifier
            
        Returns:
            Chatbot response
        """
        if not user_query or not user_query.strip():
            return "Please provide a valid question."
        
        if not user_id or not session_id:
            return "User ID and session ID are required."
        
        # Execute the graph
        response = self.graph.execute(user_query, user_id, session_id)
        
        return response
    
    def clear_session(self, user_id: str, session_id: str):
        """
        Clear conversation history for a session.
        
        Args:
            user_id: Unique user identifier
            session_id: User session identifier
        """
        self.memory.clear_session(user_id, session_id)
        print(f"Session {user_id}:{session_id} cleared.")


def main():
    """Main function for testing the chatbot."""
    print("=" * 60)
    print("RAG CHATBOT - Student Internship & Education Support")
    print("=" * 60)
    
    try:
        # Initialize chatbot
        chatbot = RAGChatbot()
        
        # Interactive loop
        print("\nChatbot ready! Type 'quit' to exit, 'clear' to clear history.\n")
        
        user_id = "test_user"
        session_id = "test_session"
        
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                chatbot.clear_session(user_id, session_id)
                print("Conversation history cleared.\n")
                continue
            
            # Get response
            try:
                response = chatbot.query(user_input, user_id, session_id)
                print(f"\nAssistant: {response}\n")
            except Exception as e:
                print(f"\nError: {e}\n")
    
    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")
        return


if __name__ == "__main__":
    main()
