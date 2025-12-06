"""
Redis checkpoint adapter for LangGraph.
Integrates LangGraph checkpointing with our Redis-based memory system.
Uses LangGraph's MemorySaver pattern but stores in Redis.
"""

import json
import sys
from typing import Optional, Dict, Any
from graph.memory import ConversationMemory

# For now, we'll use MemorySaver and rely on our ConversationMemory for Redis persistence
# LangGraph's checkpoint system can be extended later if needed
# The main state persistence is handled by ConversationMemory in the memory_node

