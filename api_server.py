"""
API server for the RAG chatbot system.
Can be called from Node.js with proper argument handling.
"""

import sys
import json
import os
import contextlib
from io import StringIO

# Redirect stdout to stderr during initialization to prevent mixing with JSON output
@contextlib.contextmanager
def redirect_stdout_to_stderr():
    """Context manager to redirect stdout to stderr."""
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout

from main import RAGChatbot

def main():
    """Handle command-line invocation from Node.js."""
    if len(sys.argv) < 4:
        print(json.dumps({
            "error": "Usage: python api_server.py <action> <user_id> <session_id> [query]"
        }), file=sys.stderr)
        sys.exit(1)
    
    action = sys.argv[1]
    user_id = sys.argv[2]
    session_id = sys.argv[3]
    query = sys.argv[4] if len(sys.argv) > 4 else ""
    
    try:
        # Redirect initialization messages to stderr
        with redirect_stdout_to_stderr():
            chatbot = RAGChatbot()
        
        if action == "query":
            if not query:
                print(json.dumps({
                    "error": "Query is required for query action"
                }), file=sys.stderr)
                sys.exit(1)
            
            response = chatbot.query(query, user_id, session_id)
            print(json.dumps({
                "success": True,
                "response": response
            }))
        
        elif action == "clear":
            # Redirect clear session message to stderr
            with redirect_stdout_to_stderr():
                chatbot.clear_session(user_id, session_id)
            print(json.dumps({
                "success": True,
                "message": "Session cleared"
            }))
        
        else:
            print(json.dumps({
                "error": f"Unknown action: {action}"
            }), file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "error": str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

