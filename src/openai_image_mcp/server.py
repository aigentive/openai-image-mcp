"""Main MCP server implementation for OpenAI image generation using FastMCP."""

import asyncio
import logging
import os
from typing import Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

from .image_agent import OpenAIImageAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global agent instance
agent: Optional[OpenAIImageAgent] = None


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[OpenAIImageAgent]:
    """Lifespan context manager for the MCP server."""
    global agent
    try:
        # Initialize the OpenAI image agent
        agent = OpenAIImageAgent()
        logger.info("OpenAI Image Agent initialized successfully")
        yield agent
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI Image Agent: {e}")
        raise
    finally:
        # Cleanup if needed
        if agent:
            logger.info("Shutting down OpenAI Image Agent")


# Create FastMCP server
mcp = FastMCP(
    "openai-image-mcp",
    dependencies=["openai", "python-dotenv", "httpx"],
    lifespan=lifespan
)


@mcp.tool()
async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high", 
    background: str = "auto",
    output_format: str = "png",
    n: int = 1,
    ctx: Optional[Context] = None
) -> str:
    """
    Generate images using OpenAI GPT-Image-1.
    
    Args:
        prompt: The image generation prompt describing what you want to create
        size: Image size - options: 1024x1024, 1536x1024, 1024x1536, auto (default: 1024x1024)
        quality: Image quality - options: low, medium, high, auto (default: high)  
        background: Background type - options: auto, transparent (default: auto)
        output_format: Output format - options: png, jpeg, webp (default: png)
        n: Number of images to generate, 1-10 (default: 1)
        
    Returns:
        Detailed information about the generated images including URLs and metadata
    """
    global agent
    if not agent:
        return "Error: OpenAI Image Agent not initialized"
    
    try:
        if ctx:
            ctx.info(f"Generating {n} image(s) with GPT-Image-1 for prompt: '{prompt}'")
            await ctx.report_progress(0, 1, "Starting image generation...")
        logger.info(f"SERVER: Starting image generation with prompt: '{prompt}'")
        
        # Validate parameters based on official documentation
        valid_sizes = ["1024x1024", "1536x1024", "1024x1536", "auto"]
        if size not in valid_sizes:
            return f"Error: Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
            
        valid_qualities = ["low", "medium", "high", "auto"]
        if quality not in valid_qualities:
            return f"Error: Invalid quality '{quality}'. Must be one of: {', '.join(valid_qualities)}"
            
        valid_backgrounds = ["auto", "transparent"]
        if background not in valid_backgrounds:
            return f"Error: Invalid background '{background}'. Must be one of: {', '.join(valid_backgrounds)}"
            
        valid_formats = ["png", "jpeg", "webp"]
        if output_format not in valid_formats:
            return f"Error: Invalid output_format '{output_format}'. Must be one of: {', '.join(valid_formats)}"
            
        if n < 1 or n > 10:
            return "Error: Number of images must be between 1 and 10"
        
        # Generate images
        logger.info(f"SERVER: Calling agent.generate_images with params: size={size}, quality={quality}")
        results = await agent.generate_images(
            prompt=prompt,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            n=n
        )
        logger.info(f"SERVER: Agent returned {len(results) if results else 0} results")
        
        if ctx:
            await ctx.report_progress(1, 1, "Image generation complete!")
        
        # Format response
        response_lines = [
            f"Successfully generated {len(results)} image(s) using GPT-Image-1",
            f"Original prompt: '{prompt}'",
            ""
        ]
        
        for i, result in enumerate(results, 1):
            response_lines.extend([
                f"Image {i}:",
                f"  • URL: {result['url']}",
                f"  • Revised prompt: {result['revised_prompt']}",
                f"  • Size: {result['size']}",
                f"  • Quality: {result['quality']}",
                f"  • Background: {result['background']}",
                f"  • Format: {result['output_format']}",
                ""
            ])
        
        return "\n".join(response_lines)
        
    except Exception as e:
        error_msg = f"Error generating image: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def generate_and_download_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    background: str = "auto",
    output_format: str = "png",
    ctx: Optional[Context] = None
) -> str:
    """
    Generate a single image using OpenAI GPT-Image-1 and download the image data.
    
    Args:
        prompt: The image generation prompt describing what you want to create
        size: Image size - options: 1024x1024, 1536x1024, 1024x1536 (default: 1024x1024)
        quality: Image quality - options: high, medium, low (default: high)
        background: Background type - options: auto, transparent (default: auto)
        output_format: Output format - options: png, jpeg, webp (default: png)
        
    Returns:
        Information about the generated image including metadata and download status
    """
    global agent
    if not agent:
        return "Error: OpenAI Image Agent not initialized"
        
    try:
        if ctx:
            ctx.info(f"Generating and downloading image for prompt: '{prompt}'")
            await ctx.report_progress(0, 2, "Starting image generation...")
        
        # Generate and download image
        results = await agent.generate_and_download_images(
            prompt=prompt,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            n=1
        )
        
        if ctx:
            await ctx.report_progress(1, 2, "Downloading image data...")
        
        if not results:
            return "Error: No images were generated"
            
        result = results[0]
        if ctx:
            await ctx.report_progress(2, 2, "Complete!")
        
        # Format response
        download_status = "✓ Downloaded" if result.get("data") else "✗ Download failed"
        size_info = f" ({result.get('size_bytes', 0)} bytes)" if result.get("size_bytes") else ""
        
        response = f"""Successfully generated and processed image using GPT-Image-1

Original prompt: '{prompt}'
Revised prompt: {result['revised_prompt']}

Image Details:
  • URL: {result['url']}
  • Size: {result['size']}
  • Quality: {result['quality']}
  • Background: {result['background']}
  • Format: {result['output_format']}
  • Download status: {download_status}{size_info}

Note: The image is available at the provided URL and can be accessed directly."""
        
        return response
        
    except Exception as e:
        error_msg = f"Error generating and downloading image: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def edit_image(
    image_url: str,
    prompt: str,
    mask_url: str = "",
    size: str = "1024x1024",
    quality: str = "high",
    output_format: str = "png",
    n: int = 1,
    ctx: Optional[Context] = None
) -> str:
    """
    Edit an existing image using OpenAI GPT-Image-1.
    
    Args:
        image_url: URL of the base image to edit (required)
        prompt: Description of the edits to make (required)
        mask_url: Optional URL of mask image for targeted editing (default: "")
        size: Image size - options: 1024x1024, 1536x1024, 1024x1536 (default: 1024x1024)
        quality: Image quality - options: high, medium, low (default: high)
        output_format: Output format - options: png, jpeg, webp (default: png)
        n: Number of edited images to generate, 1-10 (default: 1)
        
    Returns:
        Information about the edited images including URLs and metadata
    """
    global agent
    if not agent:
        return "Error: OpenAI Image Agent not initialized"
    
    try:
        if ctx:
            ctx.info(f"Editing image with GPT-Image-1 for prompt: '{prompt}'")
            await ctx.report_progress(0, 1, "Starting image editing...")
        
        # Validate parameters based on official documentation
        valid_sizes = ["1024x1024", "1536x1024", "1024x1536", "auto"]
        if size not in valid_sizes:
            return f"Error: Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
            
        valid_qualities = ["low", "medium", "high", "auto"]
        if quality not in valid_qualities:
            return f"Error: Invalid quality '{quality}'. Must be one of: {', '.join(valid_qualities)}"
            
        valid_formats = ["png", "jpeg", "webp"]
        if output_format not in valid_formats:
            return f"Error: Invalid output_format '{output_format}'. Must be one of: {', '.join(valid_formats)}"
            
        if n < 1 or n > 10:
            return "Error: Number of images must be between 1 and 10"
        
        # Convert empty string to None for mask_url
        mask_url_param = mask_url if mask_url else None
        
        # Edit image
        results = await agent.edit_image(
            image_url=image_url,
            prompt=prompt,
            mask_url=mask_url_param,
            size=size,
            quality=quality,
            output_format=output_format,
            n=n
        )
        
        if ctx:
            await ctx.report_progress(1, 1, "Image editing complete!")
        
        # Format response
        response_lines = [
            f"Successfully edited {len(results)} image(s) using GPT-Image-1",
            f"Original image: {image_url}",
            f"Edit prompt: '{prompt}'",
            ""
        ]
        
        if mask_url_param:
            response_lines.insert(-1, f"Mask image: {mask_url_param}")
        
        for i, result in enumerate(results, 1):
            response_lines.extend([
                f"Edited Image {i}:",
                f"  • URL: {result['url']}",
                f"  • Revised prompt: {result['revised_prompt']}",
                f"  • Size: {result['size']}",
                f"  • Quality: {result['quality']}",
                f"  • Format: {result['output_format']}",
                ""
            ])
        
        return "\n".join(response_lines)
        
    except Exception as e:
        error_msg = f"Error editing image: {str(e)}"
        logger.error(error_msg)
        return error_msg


def main():
    """Main entry point for running the MCP server."""
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        return
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()