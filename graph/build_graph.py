"""
Graph builder module using LangGraph library.
Builds and orchestrates the RAG pipeline using LangGraph StateGraph.
"""

import re
import sys
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import ChatbotState
from graph.nodes import GraphNodes
from graph.memory import ConversationMemory
from retrieval.retriever import Retriever
from retrieval.score_threshold import ScoreThreshold
from llm.gemini_llm import GeminiLLM
from routing.route_rules import RouteRules

class ChatbotGraph:
    """Orchestrates the chatbot pipeline execution using LangGraph."""
    
    def __init__(self,
                 retriever: Retriever,
                 score_threshold: ScoreThreshold,
                 gemini_llm: GeminiLLM,
                 route_rules: RouteRules,
                 memory: ConversationMemory):
        """
        Initialize the chatbot graph using LangGraph.
        
        Args:
            retriever: Document retriever
            score_threshold: Score validator
            gemini_llm: Gemini LLM client
            route_rules: Routing rules
            memory: Conversation memory
        """
        self.memory = memory
        
        # Initialize graph nodes
        self.nodes = GraphNodes(
            retriever=retriever,
            score_threshold=score_threshold,
            gemini_llm=gemini_llm,
            route_rules=route_rules,
            memory=memory
        )
        
        # Build LangGraph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled LangGraph workflow
        """
        # Create StateGraph with ChatbotState schema
        workflow = StateGraph(ChatbotState)
        
        # Add nodes
        workflow.add_node("route", self.nodes.route_node)
        workflow.add_node("retrieve", self.nodes.retrieve_node)
        workflow.add_node("validate", self.nodes.validate_node)
        workflow.add_node("rag_answer", self.nodes.rag_answer_node)
        workflow.add_node("external_knowledge", self.nodes.external_knowledge_node)
        workflow.add_node("memory", self.nodes.memory_node)
        
        # Define routing logic
        def should_use_rag(state: ChatbotState) -> Literal["rag_path", "external_path"]:
            """Route to RAG or external pipeline based on intent."""
            if state.get("pipeline") == "RAG":
                return "rag_path"
            return "external_path"
        
        # Add edges
        workflow.add_edge(START, "route")
        
        # Conditional routing after route node
        workflow.add_conditional_edges(
            "route",
            should_use_rag,
            {
                "rag_path": "retrieve",
                "external_path": "external_knowledge"
            }
        )
        
        # RAG pipeline edges
        workflow.add_edge("retrieve", "validate")
        workflow.add_edge("validate", "rag_answer")
        workflow.add_edge("rag_answer", "memory")
        
        # External pipeline edges - directly to memory (no refinement)
        workflow.add_edge("external_knowledge", "memory")
        
        # Memory node leads to END
        workflow.add_edge("memory", END)
        
        # Compile graph with checkpointing
        # Use MemorySaver for LangGraph's internal checkpointing
        # State persistence is handled by ConversationMemory (Redis) in memory_node
        try:
            memory_saver = MemorySaver()
            return workflow.compile(checkpointer=memory_saver)
        except Exception as e:
            # If checkpoint setup fails, compile without checkpointing
            print(f"Warning: Checkpoint setup failed, compiling without checkpoint: {e}", file=sys.stderr)
            return workflow.compile()
    
    def execute(self, query: str, user_id: str, session_id: str) -> str:
        """
        Execute the complete chatbot pipeline using LangGraph.
        
        Args:
            query: User query
            user_id: Unique user identifier
            session_id: User session identifier
            
        Returns:
            Final answer
        """
        # Retrieve conversation history for context
        conversation_history = self.memory.get_history(user_id, session_id)
        formatted_history = self.memory.get_formatted_history(user_id, session_id)
        
        # Initialize state with conversation history
        initial_state: ChatbotState = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id,
            "conversation_history": conversation_history,
            "formatted_history": formatted_history,
            "intent": None,
            "pipeline": None,
            "retrieved_docs": [],
            "retrieval_valid": False,
            "filtered_docs": [],
            "gemini_response": None,
            "answer": None
        }
        
        # Create config for this thread (user_id + session_id)
        config = {
            "configurable": {
                "thread_id": f"{user_id}:{session_id}"
            }
        }
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state, config)
        
        # Extract answer
        answer = final_state.get("answer", "I apologize, but I couldn't generate a response.")
        
        # Clean response: Remove intent/entity labels if they appear
        answer = self._clean_response(answer)
        
        return answer
    
    def _clean_response(self, response: str) -> str:
        """
        Clean response by removing intent/entity labels and other debug information.
        
        Args:
            response: Raw response text
            
        Returns:
            Cleaned response text
        """
        if not response:
            return response
        
        # Remove lines that start with "Intent:" or "Entity:"
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that are intent/entity labels
            if re.match(r'^\s*(Intent|Entity):\s*', line, re.IGNORECASE):
                continue
            cleaned_lines.append(line)
        
        # Join back and clean up extra whitespace
        cleaned = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining patterns like "Intent: ..." or "Entity: ..." anywhere in text
        cleaned = re.sub(r'\b(Intent|Entity):\s*[^\n]+\n?', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up multiple consecutive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
