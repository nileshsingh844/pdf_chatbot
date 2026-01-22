from groq import Groq
import asyncio
import json
import time
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


class GroqClient:
    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile",
                 temperature: float = 0.2, max_tokens: int = 4096,
                 max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize Groq client for LLM interactions.
        
        Args:
            api_key: Groq API key
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize client
        self.client = Groq(api_key=api_key)
        
        logger.info(f"Initialized Groq client with model: {model}")
    
    async def stream_chat(self, messages: list, 
                        system_prompt: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat completion from Groq.
        
        Args:
            messages: List of chat messages
            system_prompt: Optional system prompt
            
        Yields:
            Dictionary with streaming response data
        """
        # Prepare messages
        chat_messages = []
        
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            if isinstance(msg, dict):
                chat_messages.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                chat_messages.append({"role": msg.role, "content": msg.content})
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Create chat completion with streaming
                stream = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=chat_messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True
                )
                
                # Stream response
                full_content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        
                        yield {
                            "type": "content",
                            "content": content,
                            "full_content": full_content
                        }
                
                # Send completion signal
                yield {
                    "type": "done",
                    "content": "",
                    "full_content": full_content
                }
                
                return  # Success, exit retry loop
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Groq API error (attempt {attempt + 1}/{self.max_retries}): {error_msg}")
                
                # Check for rate limit
                if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                elif attempt == self.max_retries - 1:
                    # Last attempt failed
                    yield {
                        "type": "error",
                        "content": f"Error generating response: {error_msg}",
                        "full_content": ""
                    }
                    return
                else:
                    await asyncio.sleep(self.retry_delay)
    
    async def chat_completion(self, messages: list, 
                           system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Get complete chat completion (non-streaming).
        
        Args:
            messages: List of chat messages
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with response data
        """
        # Prepare messages
        chat_messages = []
        
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            if isinstance(msg, dict):
                chat_messages.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                chat_messages.append({"role": msg.role, "content": msg.content})
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=chat_messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=False
                )
                
                return {
                    "type": "success",
                    "content": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Groq API error (attempt {attempt + 1}/{self.max_retries}): {error_msg}")
                
                # Check for rate limit
                if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                elif attempt == self.max_retries - 1:
                    # Last attempt failed
                    return {
                        "type": "error",
                        "content": f"Error generating response: {error_msg}",
                        "usage": None
                    }
                else:
                    await asyncio.sleep(self.retry_delay)
    
    def create_rag_prompt(self, context: str, question: str) -> str:
        """
        Create a RAG (Retrieval-Augmented Generation) prompt.
        
        Args:
            context: Retrieved context from documents
            question: User's question
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a technical assistant for device specifications and documentation. Answer the user's question based ONLY on the provided context.

Context from document:
{context}

User Question: {question}

Instructions:
- Answer ONLY using information from the provided context
- If the information is not available in the context, state "I cannot find this information in the provided document"
- Include page citations in the format (Page X) when referencing specific information
- Be concise and accurate
- Focus on technical specifications and factual information

Answer:"""
        
        return prompt
    
    def extract_citations(self, text: str) -> list:
        """
        Extract page citations from text.
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of page numbers cited
        """
        import re
        
        # Find all occurrences of (Page X) pattern
        citations = re.findall(r'\(Page (\d+)\)', text)
        
        # Convert to integers and remove duplicates
        unique_pages = sorted(list(set(int(page) for page in citations)))
        
        return unique_pages
    
    def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate the API key by checking models list.
        
        Returns:
            Dictionary with validation result and reason
        """
        try:
            # Use models list endpoint instead of chat completion
            self.client.models.list()
            return {"ok": True, "reason": "Key and network OK"}
        except Exception as e:
            msg = str(e).lower()
            if "401" in msg or "unauthorized" in msg or "invalid_api_key" in msg:
                return {"ok": False, "reason": "Invalid API key"}
            if "connection" in msg or "timeout" in msg or "dns" in msg:
                return {"ok": False, "reason": "Network issue - cannot reach Groq"}
            return {"ok": False, "reason": f"Unknown error: {e}"}
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "api_key_configured": bool(self.api_key)
        }
    
    def update_settings(self, **kwargs):
        """
        Update client settings.
        
        Args:
            **kwargs: Settings to update
        """
        valid_settings = ['temperature', 'max_tokens', 'max_retries', 'retry_delay']
        
        for key, value in kwargs.items():
            if key in valid_settings:
                setattr(self, key, value)
                logger.info(f"Updated {key} to {value}")
            else:
                logger.warning(f"Invalid setting: {key}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Groq API.
        
        Returns:
            Dictionary with test results
        """
        try:
            start_time = time.time()
            
            # Make a simple request
            response = await self.chat_completion([
                {"role": "user", "content": "Respond with 'Connection successful'"}
            ])
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response["type"] == "success":
                return {
                    "status": "success",
                    "response_time": response_time,
                    "model": self.model,
                    "message": "Connection to Groq API is working"
                }
            else:
                return {
                    "status": "error",
                    "error": response["content"],
                    "message": "Failed to connect to Groq API"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to connect to Groq API"
            }
