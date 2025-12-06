"""
LLM integration using Gemini REST API.
Handles answer generation and response refinement.
"""

import os
from typing import Optional
import requests
import json
from llm.prompts import (
    RAG_SYSTEM_PROMPT,
    REFINEMENT_SYSTEM_PROMPT,
    format_rag_prompt,
    format_refinement_prompt
)

class LlamaLLM:
    """Handles LLM interactions using Gemini REST API."""
    
    def __init__(self,
                 api_key: str,
                 model: str = "gemini-2.5-flash",
                 temperature: float = 0.3,
                 max_tokens: int = 1024):
        """
        Initialize LLM client using Gemini REST API.
        
        Args:
            api_key: Gemini API key (using GEMINI_API_KEY from env)
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        # Use Gemini API key from environment
        from config.settings import GEMINI_API_KEY
        self.api_key = GEMINI_API_KEY
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"
        print(f"LLM initialized with Gemini: {self.model_name}")
    
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
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return "Oops! Something went wrong on my end. 😓 Could you try asking again?"
    
    def generate_rag_answer(self, context: str, question: str, conversation_history: str = "") -> str:
        """
        Generate answer using RAG with retrieved context.
        
        Args:
            context: Retrieved context from documents
            question: User question
            conversation_history: Formatted conversation history
            
        Returns:
            Generated answer
        """
        from llm.prompts import RAG_SYSTEM_PROMPT, format_rag_prompt
        
        # Build the prompt with context
        user_prompt = format_rag_prompt(context=context, question=question)
        
        # Add conversation history if available
        if conversation_history:
            full_prompt = f"{RAG_SYSTEM_PROMPT}\n\n{conversation_history}\n\n{user_prompt}"
        else:
            full_prompt = f"{RAG_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        return self._call_api(full_prompt)
    
    def refine_response(self, original_response: str, question: str, conversation_history: str = "") -> str:
        """
        Refine a response for clarity and professionalism.
        
        Args:
            original_response: Original response to refine
            question: User question
            conversation_history: Formatted conversation history
            
        Returns:
            Refined response
        """
        from llm.prompts import REFINEMENT_SYSTEM_PROMPT, format_refinement_prompt
        
        # Build refinement prompt
        user_prompt = format_refinement_prompt(
            original_response=original_response,
            question=question
        )
        
        # Add conversation history if available
        if conversation_history:
            full_prompt = f"{REFINEMENT_SYSTEM_PROMPT}\n\n{conversation_history}\n\n{user_prompt}"
        else:
            full_prompt = f"{REFINEMENT_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        return self._call_api(full_prompt)

