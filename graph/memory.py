"""
Memory management module for conversation state using Redis.
Maintains per-user isolated conversation history with LangGraph state management.
Uses redis_key = "chatbot:{user_id}:{session_id}" for complete isolation.
"""

import os
import json
import redis
from typing import List, Dict, Any, Optional
from datetime import datetime

class ConversationMemory:
    """Manages conversation history for multiple users using Redis."""
    
    def __init__(self, max_history: int = 10, redis_host: Optional[str] = None, 
                 redis_port: Optional[int] = None, redis_password: Optional[str] = None):
        """
        Initialize conversation memory with Redis backend.
        
        Args:
            max_history: Maximum number of conversation turns to keep
            redis_host: Redis host (defaults to env or localhost)
            redis_port: Redis port (defaults to env or 6379)
            redis_password: Redis password (optional)
        """
        self.max_history = max_history
        
        # Redis connection configuration
        redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        redis_password = redis_password or os.getenv("REDIS_PASSWORD", None)
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}. Falling back to in-memory storage.")
            self.redis_client = None
            self._fallback_storage: Dict[str, List[Dict[str, str]]] = {}
    
    def _get_redis_key(self, user_id: str, session_id: str) -> str:
        """
        Generate Redis key for user session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Redis key string
        """
        return f"chatbot:{user_id}:{session_id}"
    
    def _load_state(self, redis_key: str) -> List[Dict[str, Any]]:
        """
        Load conversation state from Redis.
        
        Args:
            redis_key: Redis key for the session
            
        Returns:
            List of message dictionaries
        """
        if not self.redis_client:
            # Fallback to in-memory storage
            return self._fallback_storage.get(redis_key, [])
        
        try:
            data = self.redis_client.get(redis_key)
            if data:
                return json.loads(data)
            return []
        except Exception as e:
            print(f"Error loading state from Redis: {e}")
            return []
    
    def _save_state(self, redis_key: str, messages: List[Dict[str, Any]], ttl: int = 86400 * 7):
        """
        Save conversation state to Redis.
        
        Args:
            redis_key: Redis key for the session
            messages: List of message dictionaries
            ttl: Time to live in seconds (default: 7 days)
        """
        if not self.redis_client:
            # Fallback to in-memory storage
            self._fallback_storage[redis_key] = messages
            return
        
        try:
            data = json.dumps(messages)
            self.redis_client.setex(redis_key, ttl, data)
        except Exception as e:
            print(f"Error saving state to Redis: {e}")
    
    def add_message(self, user_id: str, session_id: str, role: str, content: str):
        """
        Add a message to conversation history.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        redis_key = self._get_redis_key(user_id, session_id)
        messages = self._load_state(redis_key)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        messages.append(message)
        
        # Trim history if it exceeds max_history
        if len(messages) > self.max_history * 2:
            # Keep only the last max_history exchanges (user + assistant pairs)
            messages = messages[-(self.max_history * 2):]
        
        self._save_state(redis_key, messages)
    
    def get_history(self, user_id: str, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            List of message dictionaries (role and content only)
        """
        redis_key = self._get_redis_key(user_id, session_id)
        messages = self._load_state(redis_key)
        
        # Return simplified format (role and content only)
        return [
            {"role": msg.get("role", ""), "content": msg.get("content", "")}
            for msg in messages
        ]
    
    def get_formatted_history(self, user_id: str, session_id: str) -> str:
        """
        Get formatted conversation history as string.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Formatted history string
        """
        history = self.get_history(user_id, session_id)
        
        if not history:
            return ""
        
        formatted_parts = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted_parts)
    
    def clear_session(self, user_id: str, session_id: str):
        """
        Clear conversation history for a session.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
        """
        redis_key = self._get_redis_key(user_id, session_id)
        
        if not self.redis_client:
            if redis_key in self._fallback_storage:
                del self._fallback_storage[redis_key]
            return
        
        try:
            self.redis_client.delete(redis_key)
        except Exception as e:
            print(f"Error clearing session from Redis: {e}")
    
    def get_last_exchange(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Get the last user-assistant exchange.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            Dictionary with last user and assistant messages
        """
        history = self.get_history(user_id, session_id)
        
        if len(history) < 2:
            return {}
        
        # Get last two messages (should be user then assistant)
        return {
            "user": history[-2].get("content", "") if len(history) >= 2 else "",
            "assistant": history[-1].get("content", "") if len(history) >= 1 else ""
        }
    
    def has_context(self, user_id: str, session_id: str) -> bool:
        """
        Check if session has conversation history.
        
        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            
        Returns:
            True if history exists, False otherwise
        """
        history = self.get_history(user_id, session_id)
        return len(history) > 0
