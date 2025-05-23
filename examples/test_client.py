"""
Example client to test the OpenAI GPT-Image-1 MCP Server.

This script demonstrates how to interact with the MCP server directly
for testing purposes before integrating with Claude Desktop.
"""

import asyncio
import os
import json
from typing import Any, Dict
from pathlib import Path

# Add the src directory to the path
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from openai_image_mcp.server import mcp


async def test_generate_image():
    """Test the generate_image tool."""
    print("🎨 Testing GPT-Image-1 generation...")
    
    # Test basic image generation
    result = await mcp.call_tool(
        "generate_image",
        {
            "prompt": "A futuristic cityscape at sunset with flying cars",
            "size": "1024x1024",
            "quality": "high",
            "background": "auto",
            "output_format": "png",
            "n": 1
        }
    )
    
    print("Result:")
    print(result)
    print("\n" + "="*50 + "\n")


async def test_generate_and_download():
    """Test the generate_and_download_image tool."""
    print("📥 Testing image generation with download...")
    
    result = await mcp.call_tool(
        "generate_and_download_image",
        {
            "prompt": "A cute robot working on a computer with code on the screen",
            "size": "1024x1024",
            "quality": "high",
            "background": "transparent",
            "output_format": "png"
        }
    )
    
    print("Result:")
    print(result)
    print("\n" + "="*50 + "\n")


async def test_multiple_images():
    """Test generating multiple images."""
    print("🎨✨ Testing multiple image generation...")
    
    result = await mcp.call_tool(
        "generate_image",
        {
            "prompt": "A magical forest with glowing mushrooms and fairy lights",
            "size": "1536x1024",
            "quality": "high",
            "background": "auto",
            "output_format": "webp",
            "n": 2
        }
    )
    
    print("Result:")
    print(result)
    print("\n" + "="*50 + "\n")


async def test_transparent_background():
    """Test transparent background feature."""
    print("🎭 Testing transparent background generation...")
    
    result = await mcp.call_tool(
        "generate_image",
        {
            "prompt": "A colorful butterfly with detailed wings",
            "size": "1024x1024",
            "quality": "high",
            "background": "transparent",
            "output_format": "png",
            "n": 1
        }
    )
    
    print("Result:")
    print(result)
    print("\n" + "="*50 + "\n")


async def test_image_editing():
    """Test image editing functionality."""
    print("✏️ Testing image editing...")
    print("Note: This test requires a valid image URL to edit.")
    
    # You would need to provide a real image URL for this to work
    # For now, we'll show what the call would look like
    sample_image_url = "https://example.com/sample-image.png"
    
    print(f"Would edit image at: {sample_image_url}")
    print("Edit prompt: 'Add a blue sky background and make the image more colorful'")
    print("(Skipping actual API call in test - provide real image URL to test)")
    
    # Uncomment below to test with a real image URL:
    # result = await mcp.call_tool(
    #     "edit_image",
    #     {
    #         "image_url": sample_image_url,
    #         "prompt": "Add a blue sky background and make the image more colorful",
    #         "size": "1024x1024",
    #         "quality": "high",
    #         "output_format": "png"
    #     }
    # )
    # print("Result:")
    # print(result)
    
    print("\n" + "="*50 + "\n")


async def test_error_handling():
    """Test error handling with invalid parameters."""
    print("⚠️ Testing error handling...")
    
    # Test invalid size
    result = await mcp.call_tool(
        "generate_image",
        {
            "prompt": "A simple test image",
            "size": "invalid_size"
        }
    )
    
    print("Result (should show error):")
    print(result)
    print("\n" + "="*50 + "\n")


async def list_available_tools():
    """List all available tools."""
    print("🛠️ Available tools:")
    
    tools = await mcp.list_tools()
    
    for tool in tools:
        print(f"  • {tool.name}: {tool.description}")
        
    print("\n" + "="*50 + "\n")


async def main():
    """Run all tests."""
    print("🚀 Starting OpenAI GPT-Image-1 MCP Server Tests\n")
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is not set!")
        print("Please set it in your .env file or environment.")
        print("Note: GPT-Image-1 requires organization verification.")
        return
    
    try:
        # List available tools
        await list_available_tools()
        
        # Run tests
        await test_generate_image()
        await test_generate_and_download()
        await test_multiple_images()
        await test_transparent_background()
        await test_image_editing()
        await test_error_handling()
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())