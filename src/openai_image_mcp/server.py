"""Main MCP server implementation for OpenAI image generation using FastMCP."""

import logging
import os
from typing import Optional

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from dotenv import load_dotenv

from .image_agent import OpenAIImageAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("openai-image-mcp")

# Global agent instance - will be initialized on first use
agent: Optional[OpenAIImageAgent] = None


def get_agent() -> OpenAIImageAgent:
    """Get or initialize the agent instance."""
    global agent
    if agent is None:
        agent = OpenAIImageAgent()
        logger.info("OpenAI Image Agent initialized")
    return agent


@mcp.tool()
async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "low",
    n: int = 1
) -> str:
    """
    Generate images using OpenAI GPT-Image-1.
    
    Args:
        prompt: The image generation prompt describing what you want to create
        size: Image size - options: 1024x1024, 1536x1024, 1024x1536 (default: 1024x1024)
        quality: Image quality - options: low, medium, high (default: low for speed)
        n: Number of images to generate, 1-10 (default: 1)
        
    Returns:
        Detailed information about the generated images including URLs and metadata
    """
    try:
        logger.info(f"Generating {n} image(s) with prompt: '{prompt}', quality: {quality}")
        
        # Validate parameters
        valid_sizes = ["1024x1024", "1536x1024", "1024x1536"]
        if size not in valid_sizes:
            return f"Error: Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
            
        valid_qualities = ["low", "medium", "high"]
        if quality not in valid_qualities:
            return f"Error: Invalid quality '{quality}'. Must be one of: {', '.join(valid_qualities)}"
            
        if n < 1 or n > 10:
            return "Error: Number of images must be between 1 and 10"
        
        # Get agent and generate images
        agent = get_agent()
        results = await agent.generate_images(
            prompt=prompt,
            size=size,
            quality=quality,
            n=n
        )
        
        logger.info(f"Generated {len(results)} images successfully")
        
        # Format response
        response_lines = [
            f"✅ Generated {len(results)} image(s) using GPT-Image-1",
            f"📝 Prompt: '{prompt}'",
            f"⚙️  Settings: {size}, {quality} quality",
            ""
        ]
        
        for i, result in enumerate(results, 1):
            url = result.get('url', 'No URL')
            revised_prompt = result.get('revised_prompt', prompt)
            
            response_lines.extend([
                f"🖼️  Image {i}:",
                f"   URL: {url}",
                f"   Revised: {revised_prompt}",
                ""
            ])
        
        return "\n".join(response_lines)
        
    except Exception as e:
        error_msg = f"❌ Error generating image: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def generate_and_download_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "low"
) -> str:
    """
    Generate and download a single image using OpenAI GPT-Image-1.
    
    Args:
        prompt: The image generation prompt
        size: Image size (default: 1024x1024)
        quality: Image quality (default: low for speed)
        
    Returns:
        Information about the generated image with download status
    """
    try:
        logger.info(f"Generating and downloading image: '{prompt}'")
        
        agent = get_agent()
        results = await agent.generate_and_download_images(
            prompt=prompt,
            size=size,
            quality=quality,
            n=1
        )
        
        if not results:
            return "❌ No images were generated"
            
        result = results[0]
        download_status = "✅ Downloaded" if result.get("data") else "❌ Download failed"
        size_info = f" ({result.get('size_bytes', 0)} bytes)" if result.get("size_bytes") else ""
        
        response = f"""✅ Generated and processed image
        
📝 Prompt: '{prompt}'
🔄 Revised: {result.get('revised_prompt', prompt)}
🖼️  URL: {result.get('url', 'No URL')}
📊 Size: {result.get('size', size)}
⚙️  Quality: {result.get('quality', quality)}
💾 Download: {download_status}{size_info}"""
        
        return response
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def edit_image(
    image_url: str,
    prompt: str,
    mask_url: str = "",
    size: str = "1024x1024",
    quality: str = "low",
    n: int = 1
) -> str:
    """
    Edit an existing image using OpenAI GPT-Image-1.
    
    Args:
        image_url: URL of the base image to edit (required)
        prompt: Description of the edits to make (required)
        mask_url: Optional URL of mask image for targeted editing (default: "")
        size: Image size - options: 1024x1024, 1536x1024, 1024x1536 (default: 1024x1024)
        quality: Image quality - options: low, medium, high (default: low for speed)
        n: Number of edited images to generate, 1-10 (default: 1)
        
    Returns:
        Information about the edited images including URLs and metadata
    """
    try:
        logger.info(f"Editing image with prompt: '{prompt}', quality: {quality}")
        
        # Validate parameters
        valid_sizes = ["1024x1024", "1536x1024", "1024x1536"]
        if size not in valid_sizes:
            return f"Error: Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
            
        valid_qualities = ["low", "medium", "high"]
        if quality not in valid_qualities:
            return f"Error: Invalid quality '{quality}'. Must be one of: {', '.join(valid_qualities)}"
            
        if n < 1 or n > 10:
            return "Error: Number of images must be between 1 and 10"
        
        # Convert empty string to None for mask_url
        mask_url_param = mask_url if mask_url else None
        
        # Get agent and edit image
        agent = get_agent()
        results = await agent.edit_image(
            image_url=image_url,
            prompt=prompt,
            mask_url=mask_url_param,
            size=size,
            quality=quality,
            n=n
        )
        
        logger.info(f"Edited {len(results)} images successfully")
        
        # Format response
        response_lines = [
            f"✅ Edited {len(results)} image(s) using GPT-Image-1",
            f"🖼️  Original: {image_url}",
            f"📝 Edit prompt: '{prompt}'",
            f"⚙️  Settings: {size}, {quality} quality",
            ""
        ]
        
        if mask_url_param:
            response_lines.insert(-1, f"🎭 Mask: {mask_url_param}")
        
        for i, result in enumerate(results, 1):
            url = result.get('url', 'No URL')
            revised_prompt = result.get('revised_prompt', prompt)
            
            response_lines.extend([
                f"🖼️  Edited Image {i}:",
                f"   URL: {url}",
                f"   Revised: {revised_prompt}",
                ""
            ])
        
        return "\n".join(response_lines)
        
    except Exception as e:
        error_msg = f"❌ Error editing image: {str(e)}"
        logger.error(error_msg)
        return error_msg


def main():
    """Main entry point for running the MCP server."""
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is required")
        return
    
    logger.info("Starting OpenAI Image MCP Server...")
    
    # Run the server with stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()