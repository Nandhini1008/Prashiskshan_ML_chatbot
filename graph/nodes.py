"""
Graph nodes module defining processing stages using LangGraph.
Each node represents a stage in the RAG pipeline.
"""

from typing import Dict, Any
from graph.state import ChatbotState
from retrieval.retriever import Retriever
from retrieval.score_threshold import ScoreThreshold
from llm.gemini_llm import GeminiLLM
from routing.route_rules import RouteRules
from graph.memory import ConversationMemory
from config.settings import FALLBACK_RESPONSE

class GraphNodes:
    """Defines processing nodes for the chatbot graph."""
    
    def __init__(self,
                 retriever: Retriever,
                 score_threshold: ScoreThreshold,
                 gemini_llm: GeminiLLM,
                 route_rules: RouteRules,
                 memory: ConversationMemory):
        """
        Initialize graph nodes.
        
        Args:
            retriever: Document retriever
            score_threshold: Score validator
            gemini_llm: Gemini LLM client
            route_rules: Routing rules
            memory: Conversation memory
        """
        self.retriever = retriever
        self.score_threshold = score_threshold
        self.gemini_llm = gemini_llm
        self.route_rules = route_rules
        self.memory = memory
    
    def route_node(self, state: ChatbotState) -> ChatbotState:
        """
        Node: Route query to appropriate pipeline.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with routing information
        """
        query = state.get("query", "")
        routing_info = self.route_rules.route_query(query)
        
        state["intent"] = routing_info["intent"]
        state["pipeline"] = routing_info["pipeline"]
        
        return state
    
    def retrieve_node(self, state: ChatbotState) -> ChatbotState:
        """
        Node: Retrieve relevant documents (RAG path).
        
        Args:
            state: Current state
            
        Returns:
            Updated state with retrieved documents
        """
        query = state.get("query", "")
        
        # Retrieve documents
        retrieved_docs = self.retriever.retrieve(query)
        state["retrieved_docs"] = retrieved_docs
        
        return state
    
    def validate_node(self, state: ChatbotState) -> ChatbotState:
        """
        Node: Validate retrieval confidence.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with validation result
        """
        retrieved_docs = state.get("retrieved_docs", [])
        
        # Debug: Print similarity scores (to stderr to avoid mixing with output)
        import sys
        print("\n=== VALIDATION DEBUG ===", file=sys.stderr)
        for idx, doc in enumerate(retrieved_docs, 1):
            score = doc.get('similarity_score', 0)
            company = doc.get('metadata', {}).get('company', 'Unknown')
            print(f"Doc {idx}: Company={company}, Score={score:.4f}", file=sys.stderr)
        
        # Check if any document meets threshold
        is_valid = self.score_threshold.validate_retrieval(retrieved_docs)
        state["retrieval_valid"] = is_valid
        
        print(f"Threshold: {self.score_threshold.threshold}", file=sys.stderr)
        print(f"Validation Result: {is_valid}", file=sys.stderr)
        print("======================\n", file=sys.stderr)
        
        if is_valid:
            # Filter documents above threshold
            filtered_docs = self.score_threshold.filter_by_threshold(retrieved_docs)
            state["filtered_docs"] = filtered_docs
            print(f"Filtered {len(filtered_docs)} docs above threshold", file=sys.stderr)
        else:
            state["filtered_docs"] = []
            print("No documents passed threshold validation", file=sys.stderr)
        
        return state
    
    def rag_answer_node(self, state: ChatbotState) -> ChatbotState:
        """
        Node: Generate answer using RAG with Gemini.
        First checks for cached Q&A pairs with high similarity.
        If no good retrieval, falls back to external knowledge.
        
        Args:
            state: Current state
            
        Returns:
            Updated state with generated answer
        """
        import sys
        
        if not state.get("retrieval_valid", False):
            # No good retrieval results, fall back to external knowledge (Gemini)
            print("→ No good retrieval results, using external knowledge", file=sys.stderr)
            return self.external_knowledge_node(state)
        
        query = state.get("query", "")
        filtered_docs = state.get("filtered_docs", [])
        formatted_history = state.get("formatted_history", "")
        
        # Check for cached Q&A pairs with very high similarity (>0.95)
        from config.settings import EXACT_MATCH_THRESHOLD
        
        for doc in filtered_docs:
            similarity = doc.get('similarity_score', 0)
            metadata = doc.get('metadata', {})
            doc_type = metadata.get('document_type', '')
            
            # If this is a cached Q&A pair with very high similarity, return it directly
            if doc_type == 'Generated Q&A' and similarity >= EXACT_MATCH_THRESHOLD:
                cached_answer = metadata.get('answer', '')
                if cached_answer:
                    print(f"✓ Using cached answer (similarity: {similarity:.4f})", file=sys.stderr)
                    state["answer"] = cached_answer
                    return state
        
        # No cached answer found, generate new one
        print("→ Generating new answer with LLM", file=sys.stderr)
        
        # Format context
        context = self.retriever.format_retrieved_context(filtered_docs)
        
        # Generate answer with Gemini using conversation history
        answer = self.gemini_llm.generate_rag_answer(
            context=context,
            question=query,
            conversation_history=formatted_history
        )
        state["answer"] = answer
        
        return state
    
    def external_knowledge_node(self, state: ChatbotState) -> ChatbotState:
        """
        Node: Generate response using Gemini (external path).
        Auto-ingests the Q&A pair into Qdrant for future retrieval.
        Sets the answer directly (no refinement needed).
        
        Args:
            state: Current state
            
        Returns:
            Updated state with Gemini response as final answer
        """
        query = state.get("query", "")
        formatted_history = state.get("formatted_history", "")
        
        # Generate response using Gemini with conversation history
        gemini_response = self.gemini_llm.generate_response(
            question=query,
            conversation_history=formatted_history
        )
        
        # Set as final answer directly
        state["answer"] = gemini_response
        
        # Auto-ingest Q&A pair into Qdrant for future retrieval
        try:
            import sys
            print("\n=== AUTO-INGESTION ===" , file=sys.stderr)
            print(f"Ingesting Q&A pair into Qdrant...", file=sys.stderr)
            success = self.retriever.ingest_qa_pair(query, gemini_response)
            if success:
                print(f"✓ Q&A pair successfully ingested", file=sys.stderr)
            else:
                print(f"✗ Failed to ingest Q&A pair", file=sys.stderr)
            print("=====================\n", file=sys.stderr)
        except Exception as e:
            import sys
            print(f"Error during auto-ingestion: {e}", file=sys.stderr)
        
        return state
    
    def memory_node(self, state: ChatbotState) -> ChatbotState:
        """
        Node: Update conversation memory.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        user_id = state.get("user_id", "")
        session_id = state.get("session_id", "")
        query = state.get("query", "")
        answer = state.get("answer", "")
        
        # Add to memory with user_id and session_id for isolation
        if query and answer:
            self.memory.add_message(user_id, session_id, "user", query)
            self.memory.add_message(user_id, session_id, "assistant", answer)
        
        return state
