"""
Persistent HTTP service for the RAG chatbot.
Keeps chatbot instance in memory for fast responses.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import RAGChatbot

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global chatbot instance (initialized once at startup)
chatbot = None

def initialize_chatbot():
    """Initialize the chatbot instance (called once at startup)."""
    global chatbot
    if chatbot is None:
        print("Initializing chatbot service...", file=sys.stderr)
        chatbot = RAGChatbot()
        print("Chatbot service ready!", file=sys.stderr)
    return chatbot

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "chatbot_initialized": chatbot is not None})

@app.route('/query', methods=['POST'])
def query():
    """Handle chatbot query."""
    try:
        data = request.json
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        query_text = data.get('query')
        
        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id are required"}), 400
        
        if not query_text or not query_text.strip():
            return jsonify({"error": "query is required"}), 400
        
        # Ensure chatbot is initialized
        bot = initialize_chatbot()
        
        # Process query
        response = bot.query(query_text, user_id, session_id)
        
        return jsonify({
            "success": True,
            "response": response,
            "sessionId": session_id
        })
    
    except Exception as e:
        print(f"Error in query endpoint: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_session():
    """Clear conversation session."""
    try:
        data = request.json
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id are required"}), 400
        
        # Ensure chatbot is initialized
        bot = initialize_chatbot()
        
        # Clear session
        bot.clear_session(user_id, session_id)
        
        return jsonify({
            "success": True,
            "message": "Session cleared"
        })
    
    except Exception as e:
        print(f"Error in clear endpoint: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize chatbot at startup
    initialize_chatbot()
    
    # Get port from environment or default to 5001
    port = int(os.getenv('CHATBOT_SERVICE_PORT', 5001))
    host = os.getenv('CHATBOT_SERVICE_HOST', 'localhost')
    
    print(f"Starting chatbot service on {host}:{port}", file=sys.stderr)
    app.run(host=host, port=port, debug=False, threaded=True)

