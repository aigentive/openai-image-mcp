"""OpenAI Responses API client for conversational image generation."""

import base64
import logging
import os
import time
from typing import Dict, List, Optional, Any, Iterator
import openai
from openai import OpenAI

from .session_manager import ImageSession, ImageGenerationCall

logger = logging.getLogger(__name__)


class ResponsesAPIClient:
    """Wrapper for OpenAI Responses API with conversation support."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Responses API client.
        
        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY environment variable.
            
        Raises:
            ValueError: If no API key provided
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(
            api_key=api_key,
            timeout=180.0  # 3 minutes timeout for image generation
        )
        
        # Rate limiting and retry configuration
        self._max_retries = 3
        self._base_delay = 1.0
        
        logger.info("ResponsesAPIClient initialized")
    
    def generate_with_conversation(
        self, 
        session: ImageSession, 
        user_input: List[Dict[str, Any]],
        tools_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate image using full conversation context.
        
        Args:
            session: Current session with conversation history
            user_input: New user input to add to conversation
            tools_config: Image generation tool configuration
            
        Returns:
            Dictionary with generation results and metadata
            
        Raises:
            openai.APIError: If API call fails
            ValueError: If response format is invalid
        """
        try:
            # Build conversation context from session history
            conversation_context = self.build_conversation_context(session)
            
            # Add new user input
            conversation_context.append({
                "role": "user",
                "content": user_input
            })
            
            # Prepare tools specification
            tools = self._build_tools_specification(tools_config or {})
            
            logger.info(f"Making Responses API call for session {session.session_id}")
            logger.debug(f"Conversation context length: {len(conversation_context)}")
            
            # Make API call with retry logic
            response = self._make_api_call_with_retry(
                model=session.model,
                input=conversation_context,
                tools=tools
            )
            
            # Parse response and extract generation calls
            generation_calls = self.parse_generation_response(response)
            
            return {
                "success": True,
                "generation_calls": generation_calls,
                "raw_response": response,
                "conversation_length": len(conversation_context)
            }
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error in session {session.session_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_error",
                "retryable": self._is_retryable_error(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in session {session.session_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unknown_error",
                "retryable": False
            }
    
    def build_conversation_context(self, session: ImageSession) -> List[Dict[str, Any]]:
        """Build API input from session conversation history.
        
        Args:
            session: Session with conversation history
            
        Returns:
            List of conversation turns formatted for Responses API
        """
        api_context = []
        
        for turn in session.conversation_history:
            role = turn["role"]
            content = turn["content"]
            
            if role == "system":
                # System context becomes part of the conversation flow
                # We'll integrate it into the first user message or handle separately
                continue
            elif role == "user":
                api_context.append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant":
                # Convert assistant generation calls to references for next input
                for content_item in content:
                    if content_item.get("type") == "image_generation_call":
                        # Reference the generation in conversation flow
                        api_context.append({
                            "type": "image_generation_call",
                            "id": content_item["id"]
                        })
        
        logger.debug(f"Built conversation context with {len(api_context)} turns")
        return api_context
    
    def parse_generation_response(self, response: Any) -> List[ImageGenerationCall]:
        """Parse API response to extract generation calls.
        
        Args:
            response: Raw response from Responses API
            
        Returns:
            List of ImageGenerationCall objects
            
        Raises:
            ValueError: If response format is invalid
        """
        generation_calls = []
        
        try:
            # The response should have an 'output' attribute with generation calls
            if not hasattr(response, 'output'):
                raise ValueError("Response missing 'output' attribute")
            
            for output_item in response.output:
                if output_item.type == "image_generation_call":
                    # Extract generation call details
                    call = ImageGenerationCall(
                        id=output_item.id,
                        prompt=getattr(output_item, 'prompt', ''),
                        revised_prompt=getattr(output_item, 'revised_prompt', ''),
                        image_path='',  # Will be set when saving
                        generation_params=self._extract_generation_params(output_item),
                        created_at=datetime.now(),
                        image_data=getattr(output_item, 'result', '')  # Base64 image data
                    )
                    
                    generation_calls.append(call)
                    logger.debug(f"Parsed generation call {call.id}")
            
            logger.info(f"Parsed {len(generation_calls)} generation calls from response")
            return generation_calls
            
        except Exception as e:
            logger.error(f"Failed to parse generation response: {e}")
            raise ValueError(f"Invalid response format: {e}")
    
    def _make_api_call_with_retry(
        self, 
        model: str, 
        input: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]]
    ) -> Any:
        """Make API call with exponential backoff retry.
        
        Args:
            model: Model name to use
            input: Conversation input
            tools: Tools specification
            
        Returns:
            API response
            
        Raises:
            openai.APIError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self._max_retries):
            try:
                response = self.client.responses.create(
                    model=model,
                    input=input,
                    tools=tools
                )
                
                logger.debug(f"API call succeeded on attempt {attempt + 1}")
                return response
                
            except openai.RateLimitError as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error("Max retries reached for rate limiting")
                    raise
            
            except openai.APITimeoutError as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(f"API timeout, retrying in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error("Max retries reached for timeout")
                    raise
            
            except openai.APIError as e:
                # Don't retry on client errors (4xx) except rate limits
                if self._is_retryable_error(e) and attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(f"Retryable API error, retrying in {delay}s: {e}")
                    time.sleep(delay)
                    last_exception = e
                    continue
                else:
                    logger.error(f"Non-retryable API error: {e}")
                    raise
        
        # If we get here, all retries failed
        raise last_exception
    
    def _build_tools_specification(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build tools array for API call.
        
        Args:
            config: Tool configuration parameters
            
        Returns:
            Tools specification for API
        """
        tools_spec = {
            "type": "image_generation"
        }
        
        # Add optional parameters
        if config.get("quality") and config["quality"] != "auto":
            tools_spec["quality"] = config["quality"]
        
        if config.get("size") and config["size"] != "auto":
            tools_spec["size"] = config["size"]
        
        if config.get("background") and config["background"] != "auto":
            tools_spec["background"] = config["background"]
        
        if config.get("format") and config["format"] != "auto":
            tools_spec["format"] = config["format"]
        
        # Handle mask for inpainting
        if config.get("mask_file_id"):
            tools_spec["input_image_mask"] = {
                "file_id": config["mask_file_id"]
            }
        
        return [tools_spec]
    
    def _extract_generation_params(self, output_item: Any) -> Dict[str, Any]:
        """Extract generation parameters from output item.
        
        Args:
            output_item: Output item from API response
            
        Returns:
            Dictionary of generation parameters
        """
        params = {}
        
        # Extract available parameters
        for attr in ["quality", "size", "background", "format", "model"]:
            if hasattr(output_item, attr):
                params[attr] = getattr(output_item, attr)
        
        return params
    
    def _is_retryable_error(self, error: openai.APIError) -> bool:
        """Check if an API error is retryable.
        
        Args:
            error: OpenAI API error
            
        Returns:
            True if error should be retried
        """
        # Retry on 5xx server errors and specific 4xx errors
        if isinstance(error, (openai.RateLimitError, openai.APITimeoutError)):
            return True
        
        if hasattr(error, 'status_code'):
            # Retry on server errors (5xx)
            if 500 <= error.status_code < 600:
                return True
            
            # Retry on specific client errors
            if error.status_code in [408, 429]:  # Timeout, Too Many Requests
                return True
        
        return False
    
    def create_file_from_path(self, file_path: str) -> str:
        """Upload local image file to OpenAI Files API.
        
        Args:
            file_path: Path to local image file
            
        Returns:
            OpenAI file ID
            
        Raises:
            FileNotFoundError: If file doesn't exist
            openai.APIError: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        try:
            with open(file_path, "rb") as f:
                file_response = self.client.files.create(
                    file=f,
                    purpose="vision"
                )
            
            logger.info(f"Uploaded file {file_path} as {file_response.id}")
            return file_response.id
            
        except openai.APIError as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    def encode_image_base64(self, file_path: str) -> str:
        """Encode local image file as base64 data URL.
        
        Args:
            file_path: Path to local image file
            
        Returns:
            Base64 data URL string
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        # Determine MIME type from extension
        ext = os.path.splitext(file_path)[1].lower()
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }.get(ext, 'image/png')
        
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        return f"data:{mime_type};base64,{image_data}"


# Import datetime here to avoid circular imports
from datetime import datetime