"""OpenAI image generation agent using the GPT-Image-1 model."""

import os
import logging
from typing import Dict, List, Optional, Any
import asyncio
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIImageAgent:
    """Agent for generating images using OpenAI GPT-Image-1."""
    
    def __init__(self) -> None:
        """Initialize the OpenAI image agent."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create client with more conservative timeout settings
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=120.0  # 2 minutes timeout
        )
    
    async def generate_images(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate images using OpenAI GPT-Image-1.
        
        Args:
            prompt: The image generation prompt
            size: Image size (1024x1024, 1536x1024, 1024x1536)
            quality: Image quality (high, medium, low)
            n: Number of images to generate (1-10)
        
        Returns:
            List of image results with URLs and metadata (PNG format)
        """
        try:
            logger.info(f"Generating {n} image(s) with GPT-Image-1 for prompt: '{prompt}'")
            logger.info(f"Parameters: size={size}, quality={quality}")
            
            # Use basic parameters for gpt-image-1
            params = {
                "model": "gpt-image-1",
                "prompt": prompt,
                "size": size,
                "quality": quality,
                "n": n
            }
            
            logger.info(f"API call parameters: {params}")
            
            # Call with timeout - the client already has a timeout but this adds extra protection
            response = await asyncio.wait_for(
                self.client.images.generate(**params),
                timeout=120.0  # 2 minutes
            )
            
            logger.info("Received response from OpenAI API")
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response data length: {len(response.data) if hasattr(response, 'data') else 'No data attr'}")
            
            results = []
            for i, image_data in enumerate(response.data):
                # Debug logging to see what we get from the API
                logger.info(f"Processing image {i+1}")
                logger.info(f"Image data type: {type(image_data)}")
                logger.info(f"Image data attributes: {dir(image_data)}")
                logger.info(f"Image data: {image_data}")
                
                # Handle both URL and base64 responses
                url = getattr(image_data, 'url', None)
                b64_json = getattr(image_data, 'b64_json', None)
                
                # If we have base64 data, create a data URL
                if b64_json and not url:
                    url = f"data:image/png;base64,{b64_json}"
                
                result = {
                    "url": url,
                    "revised_prompt": getattr(image_data, 'revised_prompt', prompt),
                    "size": size,
                    "quality": quality,
                    "format": "png",
                    "index": i,
                    "b64_json": b64_json  # Include base64 data if available
                }
                results.append(result)
                logger.info(f"Generated image {i+1}: {result['url']}")
            
            logger.info(f"Returning {len(results)} results")
            return results
            
        except asyncio.TimeoutError:
            logger.error("Image generation timed out after 2 minutes")
            raise Exception("Image generation timed out - gpt-image-1 can take up to 2 minutes for complex prompts")
        except Exception as e:
            logger.error(f"Error generating images: {e}")
            logger.error(f"Error type: {type(e)}")
            raise
    
    async def download_image(self, url: str) -> bytes:
        """
        Download image from URL.
        
        Args:
            url: Image URL
            
        Returns:
            Image data as bytes
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            raise
    
    async def generate_and_download_images(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate images and download them as bytes.
        
        Args:
            prompt: The image generation prompt
            size: Image size
            quality: Image quality
            n: Number of images to generate
            
        Returns:
            List of image results with URLs, metadata, and image data (PNG format)
        """
        results = await self.generate_images(prompt, size, quality, n)
        
        # Download image data
        for result in results:
            try:
                image_data = await self.download_image(result["url"])
                result["data"] = image_data
                result["size_bytes"] = len(image_data)
            except Exception as e:
                logger.warning(f"Failed to download image: {e}")
                result["data"] = None
                result["size_bytes"] = 0
        
        return results
    
    async def edit_image(
        self,
        image_url: str,
        prompt: str,
        mask_url: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "high",
        n: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Edit an existing image using OpenAI GPT-Image-1.
        
        Args:
            image_url: URL of the base image to edit
            prompt: Description of the edits to make
            mask_url: Optional URL of mask image for targeted editing
            size: Image size (1024x1024, 1536x1024, 1024x1536)
            quality: Image quality (high, medium, low)
            n: Number of edited images to generate (1-10)
        
        Returns:
            List of edited image results with URLs and metadata (PNG format)
        """
        try:
            logger.info(f"Editing image with GPT-Image-1 for prompt: '{prompt}'")
            
            # Download the base image
            base_image_data = await self.download_image(image_url)
            
            # Download mask if provided
            mask_data = None
            if mask_url:
                mask_data = await self.download_image(mask_url)
            
            response = await self.client.images.edit(
                model="gpt-image-1",
                image=base_image_data,
                mask=mask_data,
                prompt=prompt,
                size=size,
                quality=quality,
                n=n
            )
            
            results = []
            for i, image_data in enumerate(response.data):
                # Handle both URL and base64 responses
                url = getattr(image_data, 'url', None)
                b64_json = getattr(image_data, 'b64_json', None)
                
                # If we have base64 data, create a data URL
                if b64_json and not url:
                    url = f"data:image/png;base64,{b64_json}"
                
                result = {
                    "url": url,
                    "revised_prompt": getattr(image_data, 'revised_prompt', prompt),
                    "original_image": image_url,
                    "mask_image": mask_url,
                    "size": size,
                    "quality": quality,
                    "format": "png",
                    "index": i,
                    "b64_json": b64_json
                }
                results.append(result)
                logger.info(f"Edited image {i+1}: {result['url']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error editing image: {e}")
            raise