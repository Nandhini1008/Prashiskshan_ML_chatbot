"""
Gemini LLM integration using direct REST API.
Handles educational and interview-related questions.
"""

import os
import requests
import json
from llm.prompts import GEMINI_SYSTEM_PROMPT

class GeminiLLM:
    """Handles interactions with Google Gemini API via REST."""
    
    def __init__(self,
                 api_key: str,
                 model: str = "gemini-2.5-flash",
                 temperature: float = 0.4,
                 max_tokens: int = 2048):
        """
        Initialize Gemini LLM client.
        
        Args:
            api_key: Gemini API key
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"
        print(f"Gemini LLM initialized: {self.model_name}")
    
    def _call_api(self, prompt: str) -> str:
        """
        Call Gemini REST API with prompt.
        
        Args:
            prompt: Full prompt text
            
        Returns:
            Generated response text
        """
        try:
            url = f"{self.base_url}/{self.model_name}:generateContent"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens
                }
            }
            
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                data=json.dumps(payload),
                timeout=30
            )
            
            # Check HTTP status
            if response.status_code != 200:
                print(f"Gemini API HTTP Error {response.status_code}: {response.text}")
                return "Oops! I'm having trouble connecting to my knowledge base right now. 🤔 Could you try asking again in a moment?"
            
            result = response.json()
            
            # Validate response structure before accessing 'parts'
            if not result:
                print("Gemini API returned empty response")
                return "Hmm, I got a blank response. Let me try to help you differently - could you rephrase your question?"
            
            if 'candidates' not in result or not result['candidates']:
                print(f"Gemini API missing 'candidates': {result}")
                return "I'm having a bit of trouble processing that right now. 😅 Mind trying a different question?"
            
            candidate = result['candidates'][0]
            
            # Check if content exists and has the right structure
            if 'content' not in candidate:
                print(f"Gemini API missing 'content' in candidate: {candidate}")
                # Check for finish_reason to understand why
                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                print(f"Finish reason: {finish_reason}")
                return "I encountered an issue processing that. Could you try rephrasing your question?"
            
            content = candidate['content']
            
            # Check if parts exists in content
            if 'parts' not in content:
                print(f"Gemini API content missing 'parts': {content}")
                # This often happens with safety filters or blocked content
                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                print(f"Finish reason: {finish_reason}")
                
                # Handle specific finish reasons
                if finish_reason == 'MAX_TOKENS':
                    # The response was cut off due to token limit
                    return "The response was too long. Could you ask a more specific question?"
                elif finish_reason == 'SAFETY':
                    return "I cannot provide that information due to safety guidelines. Please rephrase your question."
                else:
                    # Return a helpful fallback for other cases
                    return "I encountered an issue generating a response. Could you try rephrasing your question?"
            
            if not content['parts']:
                print(f"Gemini API returned empty 'parts' list")
                return "I got your question but couldn't generate a response. Could you try asking differently?"
            
            text = content['parts'][0].get('text', '').strip()
            
            if not text:
                print("Gemini API returned empty text")
                return "I got your question but couldn't generate a good answer. 🤷 Want to try asking something else?"
            
            return text
            
        except requests.exceptions.Timeout:
            print("Gemini API request timed out")
            return "Whoa, that's taking too long! ⏰ The connection timed out. Mind trying again?"
        except requests.exceptions.RequestException as e:
            print(f"Gemini API request error: {e}")
            return "I'm having network issues connecting to my brain! 🌐 Try again in a sec?"
        except KeyError as e:
            print(f"Gemini API response structure error - missing key: {e}")
            print(f"Full response: {response.text if 'response' in locals() else 'No response'}")
            return "Got a weird response format! 🤨 Let me know if this keeps happening, but for now, try another question?"
        except Exception as e:
            print(f"Unexpected error in Gemini API: {type(e).__name__}: {e}")
            return "Something unexpected happened! 😬 But don't worry - try asking me something else!"
    
    def generate_response(self, question: str, conversation_history: str = "") -> str:
        """
        Generate response for a question.
        
        Args:
            question: User question
            conversation_history: Optional formatted conversation history
            
        Returns:
            Generated response
        """
        if conversation_history:
            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\n{conversation_history}\n\nUser Question: {question}\n\nAssistant:"
        else:
            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\nUser Question: {question}\n\nAssistant:"
        return self._call_api(prompt)
    
    def generate_with_context(self, question: str, context: str) -> str:
        """
        Generate response with additional context.
        
        Args:
            question: User question
            context: Additional context
            
        Returns:
            Generated response
        """
        prompt = f"{context}\n\nQuestion: {question}"
        return self.generate_response(prompt)
    
    def generate_rag_answer(self, context: str, question: str, conversation_history: str = "") -> str:
        """
        Generate RAG answer with retrieved context and conversation history.
        
        Args:
            context: Retrieved context from vector database
            question: User question
            conversation_history: Optional formatted conversation history
            
        Returns:
            Generated response
        """
        if conversation_history:
            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\n{conversation_history}\n\nRelevant Context:\n{context}\n\nUser Question: {question}\n\nAssistant:"
        else:
            prompt = f"{GEMINI_SYSTEM_PROMPT}\n\nRelevant Context:\n{context}\n\nUser Question: {question}\n\nAssistant:"
        return self._call_api(prompt)

