# Updated src/openai_image_mcp/image_agent.py
import os
import logging
from typing import Dict, List, Optional, Any
import requests
from openai import OpenAI # type: ignore[import-untyped]
from dotenv import load_dotenv
import base64
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIImageAgent:
    """Agent for generating and editing images using OpenAI DALL-E models."""

    def __init__(self) -> None:
        """Initialize the OpenAI image agent."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable is not set.")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=180.0  # Increased timeout for API calls
        )
        logger.info("OpenAIImageAgent initialized with API key.")

    def generate_images(
        self,
        prompt: str,
        model: str = "dall-e-3", 
        size: str = "1024x1024", 
        quality: str = "standard", 
        n: int = 1,
        response_format: str = "b64_json", 
        style: Optional[str] = "vivid" 
    ) -> List[Dict[str, Any]]:
        """
        Generate images using OpenAI DALL-E.
        Returns metadata including b64_json or URL.
        """
        try:
            logger.info(f"Generating {n} image(s) with {model} for prompt: '{prompt}'")
            logger.debug(f"Generation Params: model={model}, size={size}, quality={quality}, n={n}, response_format={response_format}, style={style}")
            
            api_params: Dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "n": n,
                "response_format": response_format,
            }
            if style and model == "dall-e-3":
                 api_params["style"] = style
            
            logger.debug(f"Calling OpenAI images.generate with params: {api_params}")
            response = self.client.images.generate(**api_params)
            logger.info(f"OpenAI API call successful for image generation. Received {len(response.data)} items.")
            
            results = []
            for i, image_data_obj in enumerate(response.data):
                url = getattr(image_data_obj, 'url', None)
                b64_json = getattr(image_data_obj, 'b64_json', None)
                revised_prompt = getattr(image_data_obj, 'revised_prompt', prompt)

                # Determine a format primarily for consistent metadata, actual saving format can differ.
                determined_format = "png" # Default if b64_json is primary
                if response_format == 'url' and url:
                    try:
                        filename_from_url = url.split('/')[-1].split('?')[0]
                        if '.' in filename_from_url:
                            ext = filename_from_url.split('.')[-1].lower()
                            if ext in ["png", "jpeg", "jpg", "webp"]:
                                determined_format = ext
                        logger.debug(f"Inferred format from URL {url} as {determined_format}")
                    except Exception as e_fmt:
                        logger.warning(f"Could not infer format from URL {url}: {e_fmt}. Defaulting to png.")
                
                result = {
                    "url": url,
                    "b64_json": b64_json,
                    "revised_prompt": revised_prompt,
                    "requested_model": model,
                    "requested_size": size, 
                    "requested_quality": quality, 
                    "requested_response_format": response_format,
                    "determined_format": determined_format, 
                    "requested_style": style if model == "dall-e-3" else None,
                    "index": i,
                }
                results.append(result)
                logger.debug(f"Image {i+1} metadata: URL {bool(url)}, b64_json {bool(b64_json)}, revised_prompt {bool(revised_prompt)}")
            
            logger.info(f"Returning {len(results)} metadata results from generate_images.")
            return results
            
        except Exception as e:
            logger.error(f"Error in generate_images for prompt '{prompt}': {e}", exc_info=True)
            raise
    
    def _get_image_data_from_metadata(
        self, 
        image_metadata: Dict[str, Any]
    ) -> Optional[bytes]:
        """
        Internal helper to get image bytes from metadata (b64_json or URL).
        """
        image_data_content: Optional[bytes] = None
        index = image_metadata.get('index', 'N/A')
        b64_json = image_metadata.get("b64_json")
        url = image_metadata.get("url")

        if b64_json:
            logger.info(f"Decoding b64_json for image index {index}")
            try:
                image_data_content = base64.b64decode(b64_json)
            except Exception as e_b64_decode:
                logger.error(f"Error decoding b64_json for image index {index}: {e_b64_decode}", exc_info=True)
                return None # Failed to decode
        
        elif url and url.startswith("data:"):
            logger.info(f"Decoding data URI for image index {index}: {url[:100]}...")
            try:
                header, encoded_data = url.split(",", 1)
                if ";base64" not in header:
                    logger.error(f"Data URI for image index {index} is not base64 encoded.")
                    raise ValueError("Data URI is not base64 encoded")
                image_data_content = base64.b64decode(encoded_data)
            except Exception as e_data_uri:
                logger.error(f"Could not decode data URI for image index {index}: {e_data_uri}", exc_info=True)
                return None # Failed to decode
        
        elif url: # External URL
            logger.info(f"Downloading image from external URL for index {index}: {url[:100]}...")
            try:
                response = requests.get(url, timeout=90) # Increased timeout for downloads
                response.raise_for_status()
                image_data_content = response.content
                logger.info(f"Successfully downloaded image from {url[:100]}. Size: {len(image_data_content)} bytes.")
            except Exception as e_download:
                logger.error(f"Error downloading image from {url}: {e_download}", exc_info=True)
                return None # Download failed
        
        else:
            logger.warning(f"No b64_json or valid URL provided for image index {index} to get data.")
            
        return image_data_content

    def generate_and_download_images(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
        style: Optional[str] = "vivid",
        output_file_format: str = "png", # Desired format for the *saved file*
        save_paths: Optional[List[str]] = None, # List of organized save paths
        file_organizer: Optional[Any] = None # FileOrganizer instance for metadata saving
    ) -> List[Dict[str, Any]]:
        """
        Generates images, gets their data, and saves them to files.
        If save_paths is provided, uses organized paths. Otherwise falls back to default location.
        Returns a list of result dictionaries, each including the 'filepath' if successfully saved.
        """
        # Fallback to default location if no organized paths provided
        if save_paths is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # src/openai_image_mcp -> src -> workspace_root
            workspace_root = os.path.dirname(os.path.dirname(script_dir)) 
            save_dir = os.path.join(workspace_root, "generated_images")
            
            try:
                os.makedirs(save_dir, exist_ok=True)
                logger.info(f"Ensured 'generated_images' directory exists: {save_dir}")
            except OSError as e_mkdir:
                logger.error(f"Could not create/access directory {save_dir}: {e_mkdir}. Images may not be saved.", exc_info=True)

        # Always request b64_json from generate_images for easier data handling.
        # The actual content type of b64_json from DALL-E is typically PNG.
        image_metadata_list = self.generate_images(
            prompt=prompt, model=model, size=size, quality=quality, n=n, 
            response_format="b64_json", style=style
        )
        
        final_results = []
        for i, metadata in enumerate(image_metadata_list):
            # Initialize fields for this specific result dictionary
            metadata["filepath"] = None 
            metadata["saved_image_data_bytes"] = 0 
            metadata["output_file_format"] = output_file_format # Record what we intended to save as

            try:
                image_data_bytes = self._get_image_data_from_metadata(metadata)

                if image_data_bytes:
                    metadata["saved_image_data_bytes"] = len(image_data_bytes)
                    
                    # Use organized save path if provided, otherwise generate default filename
                    if save_paths and i < len(save_paths):
                        filepath = save_paths[i]
                        # Ensure directory exists for organized path
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    else:
                        # Fallback to default naming in save_dir
                        file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                        filename = f"image_{file_timestamp}_{metadata.get('index', 0)}.{output_file_format.lower()}"
                        filepath = os.path.join(save_dir, filename)
                    
                    try:
                        with open(filepath, "wb") as f:
                            f.write(image_data_bytes)
                        metadata["filepath"] = filepath 
                        logger.info(f"Successfully saved image for index {metadata.get('index')} to: {filepath}")
                        
                        # Save metadata if file_organizer is provided
                        if file_organizer:
                            try:
                                image_metadata = {
                                    "original_prompt": prompt,
                                    "revised_prompt": metadata.get("revised_prompt", prompt),
                                    "model": model,
                                    "size": size,
                                    "quality": quality,
                                    "style": style,
                                    "output_format": output_file_format,
                                    "file_size_bytes": len(image_data_bytes)
                                }
                                file_organizer.save_image_metadata(filepath, image_metadata)
                            except Exception as e_meta:
                                logger.warning(f"Failed to save metadata for {filepath}: {e_meta}")
                                
                    except IOError as e_io:
                        logger.error(f"Failed to save image for index {metadata.get('index')} to {filepath}: {e_io}", exc_info=True)
                else: 
                    logger.warning(f"No image data content obtained for index {metadata.get('index', 'N/A')}, cannot save file.")

            except Exception as e_proc:
                logger.error(f"Error processing image for saving (index {metadata.get('index', 'N/A')}): {e_proc}", exc_info=True)
            
            final_results.append(metadata)
        
        return final_results
    
    def edit_image(
        self,
        image_path: str, 
        prompt: str,
        mask_path: Optional[str] = None, 
        model: str = "dall-e-2", # DALL-E 2 is typically used for edits
        size: str = "1024x1024", 
        n: int = 1,
        response_format: str = "b64_json"
    ) -> List[Dict[str, Any]]:
        """
        Edit an existing image using a local image file and an optional local mask file.
        OpenAI's edit endpoint (typically DALL-E 2) requires image and mask as files/bytes.
        Returns metadata including b64_json or URL from OpenAI.
        This method does NOT currently save the edited image back to a new file automatically.
        """
        try:
            logger.info(f"Editing image at '{image_path}' with prompt: '{prompt}' using model {model}")

            if not os.path.exists(image_path):
                logger.error(f"Image file not found for editing: {image_path}")
                raise FileNotFoundError(f"Image file not found: {image_path}")

            image_file_rb = None
            mask_file_rb = None
            try:
                image_file_rb = open(image_path, "rb")
                
                if mask_path:
                    if not os.path.exists(mask_path):
                        logger.error(f"Mask file not found for editing: {mask_path}")
                        raise FileNotFoundError(f"Mask file not found: {mask_path}")
                    mask_file_rb = open(mask_path, "rb")

                api_params: Dict[str, Any] = {
                    "model": model,
                    "image": image_file_rb, 
                    "prompt": prompt,
                    "size": size,
                    "n": n,
                    "response_format": response_format,
                }
                if mask_file_rb:
                    api_params["mask"] = mask_file_rb
                
                logger.debug(f"Calling OpenAI images.edit with params: size={size}, n={n}, model={model}")
                response = self.client.images.edit(**api_params) # type: ignore[arg-type]
                logger.info("OpenAI image edit API call completed.")

            finally: 
                if image_file_rb:
                    image_file_rb.close()
                if mask_file_rb:
                    mask_file_rb.close()
                logger.debug("Closed image/mask files for edit operation.")

            results = []
            for i, image_data_obj in enumerate(response.data):
                url = getattr(image_data_obj, 'url', None)
                b64_json = getattr(image_data_obj, 'b64_json', None)
                revised_prompt = getattr(image_data_obj, 'revised_prompt', None)

                determined_format = "png"
                if response_format == 'url' and url:
                    try:
                        filename_from_url = url.split('/')[-1].split('?')[0]
                        if '.' in filename_from_url:
                            ext = filename_from_url.split('.')[-1].lower()
                            if ext in ["png", "jpeg", "jpg", "webp"]:
                                determined_format = ext
                    except Exception:
                        pass # Keep default png if inference fails

                result = {
                    "url": url,
                    "b64_json": b64_json,
                    "revised_prompt": revised_prompt,
                    "original_image_path": image_path,
                    "mask_image_path": mask_path,
                    "requested_model": model,
                    "requested_size": size, 
                    "requested_response_format": response_format,
                    "determined_format": determined_format,
                    "index": i,
                }
                results.append(result)
                logger.debug(f"Edited image {i+1} metadata: URL {bool(url)}, b64_json {bool(b64_json)}")
            
            logger.info(f"Returning {len(results)} metadata results from edit_image.")
            return results
            
        except Exception as e:
            logger.error(f"Error in edit_image for '{image_path}': {e}", exc_info=True)
            raise 