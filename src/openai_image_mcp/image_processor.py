"""Image input/output processing for conversational image generation."""

import base64
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from .session_manager import ImageSession, ImageGenerationCall

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image input/output operations and integration with file organizer."""
    
    def __init__(self, file_organizer, responses_client):
        """Initialize image processor.
        
        Args:
            file_organizer: FileOrganizer instance for organized storage
            responses_client: ResponsesAPIClient for file uploads
        """
        self.organizer = file_organizer
        self.responses_client = responses_client
        logger.info("ImageProcessor initialized")
    
    def prepare_image_input(
        self, 
        image_path: str, 
        input_method: str = "auto"
    ) -> Dict[str, Any]:
        """Convert local image to API input format.
        
        Args:
            image_path: Path to local image file
            input_method: Method to use ('auto', 'base64', 'file_id')
            
        Returns:
            Dictionary with input format details
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If input method is invalid
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Get file size to help decide method
        file_size = os.path.getsize(image_path)
        
        # Auto-select method based on file size
        if input_method == "auto":
            # Use file_id for larger files (>5MB), base64 for smaller
            input_method = "file_id" if file_size > 5 * 1024 * 1024 else "base64"
        
        if input_method == "base64":
            data_url = self.responses_client.encode_image_base64(image_path)
            return {
                "method": "base64",
                "data": data_url,
                "file_size": file_size
            }
        elif input_method == "file_id":
            file_id = self.responses_client.create_file_from_path(image_path)
            return {
                "method": "file_id", 
                "data": file_id,
                "file_size": file_size
            }
        else:
            raise ValueError(f"Invalid input method: {input_method}")
    
    def save_generated_image(
        self, 
        image_data: str, 
        session: ImageSession,
        use_case: str = "general",
        filename_prefix: str = "generated"
    ) -> str:
        """Save generated image using file organizer.
        
        Args:
            image_data: Base64 encoded image data
            session: Current session for context
            use_case: Use case for file organization
            filename_prefix: Prefix for generated filename
            
        Returns:
            Path to saved image file
            
        Raises:
            ValueError: If image data is invalid
            OSError: If file cannot be saved
        """
        try:
            # Decode base64 image data
            if image_data.startswith('data:'):
                # Remove data URL prefix if present
                header, image_data = image_data.split(',', 1)
            
            image_bytes = base64.b64decode(image_data)
            
            # Generate organized save path
            save_path = self.organizer.get_save_path(
                use_case=use_case,
                filename_prefix=filename_prefix,
                file_format="png"  # Default format
            )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save image file
            with open(save_path, "wb") as f:
                f.write(image_bytes)
            
            logger.info(f"Saved generated image to: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Failed to save generated image: {e}")
            raise
    
    def save_image_with_metadata(
        self,
        generation_call: ImageGenerationCall,
        session: ImageSession,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Save image metadata using file organizer.
        
        Args:
            generation_call: Image generation call with metadata
            session: Session context
            additional_metadata: Additional metadata to include
            
        Returns:
            Path to metadata file if successful, None if failed
        """
        try:
            # Prepare metadata
            metadata = {
                "session_id": session.session_id,
                "session_name": session.session_name,
                "generation_call_id": generation_call.id,
                "original_prompt": generation_call.prompt,
                "revised_prompt": generation_call.revised_prompt,
                "model": session.model,
                "generation_params": generation_call.generation_params,
                "created_at": generation_call.created_at.isoformat(),
                "conversation_length": len(session.conversation_history)
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)
            
            # Save metadata using file organizer
            metadata_path = self.organizer.save_image_metadata(
                generation_call.image_path, 
                metadata
            )
            
            logger.debug(f"Saved metadata to: {metadata_path}")
            return metadata_path
            
        except Exception as e:
            logger.error(f"Failed to save image metadata: {e}")
            return None
    
    def process_generation_result(
        self,
        generation_call: ImageGenerationCall,
        session: ImageSession,
        use_case: str = "general"
    ) -> ImageGenerationCall:
        """Process complete generation result including saving and metadata.
        
        Args:
            generation_call: Generation call with image data
            session: Current session
            use_case: Use case for file organization
            
        Returns:
            Updated generation call with image path
        """
        try:
            # Save the generated image
            if generation_call.image_data:
                image_path = self.save_generated_image(
                    generation_call.image_data,
                    session,
                    use_case=use_case,
                    filename_prefix=f"session_{session.session_id[:8]}"
                )
                generation_call.image_path = image_path
                
                # Save metadata
                self.save_image_with_metadata(generation_call, session)
                
                logger.info(f"Processed generation result: {generation_call.id}")
            else:
                logger.warning(f"No image data for generation call: {generation_call.id}")
            
            return generation_call
            
        except Exception as e:
            logger.error(f"Failed to process generation result: {e}")
            # Return the call even if processing failed
            return generation_call
    
    def validate_image_file(self, file_path: str) -> Dict[str, Any]:
        """Validate image file for input use.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Validation results dictionary
        """
        result = {
            "valid": False,
            "file_exists": False,
            "file_size": 0,
            "format": None,
            "dimensions": None,
            "errors": []
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result["errors"].append("File does not exist")
                return result
            
            result["file_exists"] = True
            result["file_size"] = os.path.getsize(file_path)
            
            # Check file size (25MB limit for OpenAI)
            max_size = 25 * 1024 * 1024  # 25MB
            if result["file_size"] > max_size:
                result["errors"].append(f"File too large: {result['file_size']} bytes (max: {max_size})")
            
            # Check file format
            ext = os.path.splitext(file_path)[1].lower()
            supported_formats = ['.png', '.jpg', '.jpeg', '.webp', '.gif']
            if ext not in supported_formats:
                result["errors"].append(f"Unsupported format: {ext}")
            else:
                result["format"] = ext
            
            # If no errors so far, file is valid
            if not result["errors"]:
                result["valid"] = True
            
            logger.debug(f"Validated image file {file_path}: valid={result['valid']}")
            return result
            
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
            logger.error(f"Image validation failed for {file_path}: {e}")
            return result
    
    def cleanup_temp_files(self, session: ImageSession) -> int:
        """Clean up temporary files for a session.
        
        Args:
            session: Session to clean up
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        
        try:
            # This would implement cleanup logic for temporary files
            # For now, we'll just log the operation
            logger.info(f"Cleanup requested for session {session.session_id}")
            
            # In a full implementation, this would:
            # 1. Remove temporary uploaded files
            # 2. Clean up any cached image data  
            # 3. Remove orphaned metadata files
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cleanup failed for session {session.session_id}: {e}")
            return 0
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Get information about an image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image information dictionary
        """
        info = {
            "path": image_path,
            "exists": False,
            "size_bytes": 0,
            "format": None,
            "created": None,
            "modified": None
        }
        
        try:
            if os.path.exists(image_path):
                info["exists"] = True
                stat = os.stat(image_path)
                info["size_bytes"] = stat.st_size
                info["created"] = datetime.fromtimestamp(stat.st_ctime)
                info["modified"] = datetime.fromtimestamp(stat.st_mtime)
                info["format"] = os.path.splitext(image_path)[1].lower()
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get image info for {image_path}: {e}")
            return info