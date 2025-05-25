"""Conversation context building for Responses API."""

import logging
from typing import Dict, List, Optional, Any
import base64
import os

logger = logging.getLogger(__name__)


class ConversationBuilder:
    """Builds conversation context for Responses API calls."""
    
    @staticmethod
    def add_user_text_input(content: List[Dict[str, Any]], text: str) -> None:
        """Add text input to content list.
        
        Args:
            content: Content list to modify
            text: Text content to add
        """
        content.append({
            "type": "input_text",
            "text": text
        })
        logger.debug(f"Added text input: {text[:100]}...")
    
    @staticmethod
    def add_user_image_input(
        content: List[Dict[str, Any]], 
        image_path: str, 
        input_type: str = "file_path"
    ) -> None:
        """Add image input to content list.
        
        Args:
            content: Content list to modify
            image_path: Path to image file or base64 data
            input_type: Type of input ('file_path', 'base64', 'file_id')
        """
        if input_type == "file_path":
            # Convert file path to base64 data URL
            data_url = ConversationBuilder._encode_image_to_data_url(image_path)
            content.append({
                "type": "input_image",
                "image_url": data_url
            })
        elif input_type == "base64":
            content.append({
                "type": "input_image", 
                "image_url": image_path  # Assume already formatted data URL
            })
        elif input_type == "file_id":
            content.append({
                "type": "input_image",
                "file_id": image_path  # Actually file_id in this case
            })
        else:
            raise ValueError(f"Invalid input_type: {input_type}")
        
        logger.debug(f"Added image input: {input_type} - {image_path}")
    
    @staticmethod
    def add_image_generation_reference(
        content: List[Dict[str, Any]], 
        generation_call_id: str
    ) -> None:
        """Reference previous generation in new input.
        
        Args:
            content: Content list to modify
            generation_call_id: ID of previous generation call
        """
        content.append({
            "type": "image_generation_call",
            "id": generation_call_id
        })
        logger.debug(f"Added generation reference: {generation_call_id}")
    
    @staticmethod
    def build_tools_specification(
        quality: str = "auto",
        size: str = "auto", 
        background: str = "auto",
        format: str = "auto",
        mask_file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Build tools array for API call.
        
        Args:
            quality: Image quality (low, medium, high, auto)
            size: Image size (1024x1024, 1536x1024, 1024x1536, auto)
            background: Background type (transparent, auto)
            format: Output format (png, jpeg, webp, auto)
            mask_file_id: File ID for mask image (for inpainting)
            
        Returns:
            Tools specification list
        """
        tools_spec = {
            "type": "image_generation"
        }
        
        # Add parameters only if not auto
        if quality != "auto":
            tools_spec["quality"] = quality
        
        if size != "auto":
            tools_spec["size"] = size
        
        if background != "auto":
            tools_spec["background"] = background
        
        if format != "auto":
            tools_spec["format"] = format
        
        # Add mask for inpainting
        if mask_file_id:
            tools_spec["input_image_mask"] = {
                "file_id": mask_file_id
            }
        
        logger.debug(f"Built tools specification: {tools_spec}")
        return [tools_spec]
    
    @staticmethod
    def build_user_input_from_params(
        prompt: str,
        reference_image_path: Optional[str] = None,
        mask_image_path: Optional[str] = None,
        reference_generation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Build complete user input from parameters.
        
        Args:
            prompt: Text prompt for generation
            reference_image_path: Path to reference image
            mask_image_path: Path to mask image  
            reference_generation_id: ID of previous generation to reference
            
        Returns:
            User input content list
        """
        content = []
        
        # Add text prompt
        ConversationBuilder.add_user_text_input(content, prompt)
        
        # Add reference image if provided
        if reference_image_path:
            ConversationBuilder.add_user_image_input(content, reference_image_path)
        
        # Add generation reference if provided
        if reference_generation_id:
            ConversationBuilder.add_image_generation_reference(content, reference_generation_id)
        
        logger.info(f"Built user input with {len(content)} content items")
        return content
    
    @staticmethod
    def format_assistant_response(generation_calls: List[Any]) -> List[Dict[str, Any]]:
        """Format assistant response from generation calls.
        
        Args:
            generation_calls: List of ImageGenerationCall objects
            
        Returns:
            Assistant response content list
        """
        content = []
        
        for call in generation_calls:
            content.append({
                "type": "image_generation_call",
                "id": call.id,
                "status": "completed",
                "image_path": call.image_path,
                "revised_prompt": call.revised_prompt
            })
        
        logger.debug(f"Formatted assistant response with {len(content)} generation calls")
        return content
    
    @staticmethod
    def _encode_image_to_data_url(file_path: str) -> str:
        """Encode image file to base64 data URL.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Base64 data URL string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format not supported
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
        }.get(ext)
        
        if not mime_type:
            raise ValueError(f"Unsupported image format: {ext}")
        
        try:
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            return f"data:{mime_type};base64,{image_data}"
            
        except Exception as e:
            logger.error(f"Failed to encode image {file_path}: {e}")
            raise
    
    @staticmethod
    def validate_conversation_input(input_data: List[Dict[str, Any]]) -> bool:
        """Validate conversation input format.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(input_data, list):
            logger.error("Conversation input must be a list")
            return False
        
        for item in input_data:
            if not isinstance(item, dict):
                logger.error("Each conversation item must be a dictionary")
                return False
            
            if "role" not in item or "content" not in item:
                logger.error("Each conversation item must have 'role' and 'content' keys")
                return False
            
            if item["role"] not in ["user", "assistant", "system"]:
                logger.error(f"Invalid role: {item['role']}")
                return False
            
            if not isinstance(item["content"], list):
                logger.error("Content must be a list")
                return False
        
        return True
    
    @staticmethod
    def trim_conversation_history(
        conversation: List[Dict[str, Any]], 
        max_length: int = 50,
        preserve_system: bool = True
    ) -> List[Dict[str, Any]]:
        """Trim conversation history to maximum length.
        
        Args:
            conversation: Full conversation history
            max_length: Maximum number of turns to keep
            preserve_system: Whether to always keep system messages
            
        Returns:
            Trimmed conversation history
        """
        if len(conversation) <= max_length:
            return conversation
        
        if preserve_system:
            # Separate system messages and other messages
            system_messages = [msg for msg in conversation if msg.get("role") == "system"]
            other_messages = [msg for msg in conversation if msg.get("role") != "system"]
            
            # Keep recent non-system messages
            keep_count = max_length - len(system_messages)
            if keep_count > 0:
                recent_messages = other_messages[-keep_count:]
                result = system_messages + recent_messages
            else:
                # If too many system messages, just keep the most recent ones
                result = system_messages[-max_length:]
        else:
            # Just keep the most recent messages
            result = conversation[-max_length:]
        
        if len(result) < len(conversation):
            logger.info(f"Trimmed conversation from {len(conversation)} to {len(result)} turns")
        
        return result