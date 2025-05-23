"""Tests for MCP server tools."""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai_image_mcp.server import generate_image, generate_and_download_image, edit_image
from openai_image_mcp.image_agent import OpenAIImageAgent


class TestMCPServerTools:
    """Test cases for MCP server tools."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock OpenAI Image Agent."""
        agent = MagicMock(spec=OpenAIImageAgent)
        return agent
    
    @pytest.mark.asyncio
    async def test_generate_image_success(self, mock_agent):
        """Test successful image generation via MCP tool."""
        # Mock agent response
        mock_results = [{
            "url": "https://example.com/image1.png",
            "revised_prompt": "A cute puppy in a park",
            "size": "1024x1024",
            "quality": "high",
            "format": "png"
        }]
        mock_agent.generate_images.return_value = mock_results
        
        # Patch the global agent
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image("a cute puppy")
            
            assert "✅ Generated 1 image(s) using GPT-Image-1" in result
            assert "📝 Prompt: 'a cute puppy'" in result
            assert "URL: https://example.com/image1.png" in result
            assert "Revised: A cute puppy in a park" in result
            
            # Verify agent was called correctly
            mock_agent.generate_images.assert_called_once_with(
                prompt="a cute puppy",
                size="1024x1024",
                quality="low",
                n=1
            )
    
    @pytest.mark.asyncio
    async def test_generate_image_custom_params(self, mock_agent):
        """Test image generation with custom parameters."""
        mock_results = [{
            "url": "https://example.com/image1.jpg",
            "revised_prompt": "A test image",
            "size": "1536x1024",
            "quality": "low",
            "format": "jpeg"
        }]
        mock_agent.generate_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image(
                prompt="test image",
                size="1536x1024",
                quality="low",
                n=1
            )
            
            assert "Successfully generated 1 image(s)" in result
            assert "Size: 1536x1024" in result
            assert "Quality: low" in result
    
    @pytest.mark.asyncio
    async def test_generate_image_multiple(self, mock_agent):
        """Test generating multiple images."""
        mock_results = [
            {
                "url": "https://example.com/image1.png",
                "revised_prompt": "A test image 1",
                "size": "1024x1024",
                "quality": "high",
                "format": "png"
            },
            {
                "url": "https://example.com/image2.png",
                "revised_prompt": "A test image 2",
                "size": "1024x1024",
                "quality": "high",
                "format": "png"
            }
        ]
        mock_agent.generate_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image("test images", n=2)
            
            assert "Successfully generated 2 image(s)" in result
            assert "Image 1:" in result
            assert "Image 2:" in result
            assert "https://example.com/image1.png" in result
            assert "https://example.com/image2.png" in result
    
    @pytest.mark.asyncio
    async def test_generate_image_agent_not_initialized(self):
        """Test error when agent is not initialized."""
        with patch('openai_image_mcp.server.agent', None):
            result = await generate_image("test prompt")
            
            assert result == "Error: OpenAI Image Agent not initialized"
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_size(self, mock_agent):
        """Test validation of invalid size parameter."""
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image("test prompt", size="invalid")
            
            assert "Error: Invalid size 'invalid'" in result
            assert "Must be one of:" in result
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_quality(self, mock_agent):
        """Test validation of invalid quality parameter."""
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image("test prompt", quality="invalid")
            
            assert "Error: Invalid quality 'invalid'" in result
    
    
    
    @pytest.mark.asyncio
    async def test_generate_image_invalid_n(self, mock_agent):
        """Test validation of invalid n parameter."""
        with patch('openai_image_mcp.server.agent', mock_agent):
            # Test n < 1
            result = await generate_image("test prompt", n=0)
            assert "Error: Number of images must be between 1 and 10" in result
            
            # Test n > 10
            result = await generate_image("test prompt", n=11)
            assert "Error: Number of images must be between 1 and 10" in result
    
    @pytest.mark.asyncio
    async def test_generate_image_agent_exception(self, mock_agent):
        """Test handling of agent exceptions."""
        mock_agent.generate_images.side_effect = Exception("API Error")
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image("test prompt")
            
            assert "Error generating image: API Error" in result
    
    @pytest.mark.asyncio
    async def test_generate_and_download_image_success(self, mock_agent):
        """Test successful image generation and download."""
        mock_results = [{
            "url": "https://example.com/image1.png",
            "revised_prompt": "A cute puppy in a park",
            "size": "1024x1024",
            "quality": "high",
            "format": "png",
            "data": b"fake image data",
            "size_bytes": 12345
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_and_download_image("a cute puppy")
            
            assert "Successfully generated and processed image" in result
            assert "Original prompt: 'a cute puppy'" in result
            assert "Revised prompt: A cute puppy in a park" in result
            assert "URL: https://example.com/image1.png" in result
            assert "Download status: ✓ Downloaded (12345 bytes)" in result
            
            # Verify agent was called correctly
            mock_agent.generate_and_download_images.assert_called_once_with(
                prompt="a cute puppy",
                size="1024x1024",
                quality="high",
                n=1
            )
    
    @pytest.mark.asyncio
    async def test_generate_and_download_image_download_failed(self, mock_agent):
        """Test when download fails."""
        mock_results = [{
            "url": "https://example.com/image1.png",
            "revised_prompt": "A cute puppy in a park",
            "size": "1024x1024",
            "quality": "high",
            "format": "png",
            "data": None,
            "size_bytes": 0
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_and_download_image("a cute puppy")
            
            assert "Download status: ✗ Download failed" in result
    
    @pytest.mark.asyncio
    async def test_generate_and_download_image_no_results(self, mock_agent):
        """Test when no images are generated."""
        mock_agent.generate_and_download_images.return_value = []
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_and_download_image("test prompt")
            
            assert result == "Error: No images were generated"
    
    @pytest.mark.asyncio
    async def test_edit_image_success(self, mock_agent):
        """Test successful image editing."""
        mock_results = [{
            "url": "https://example.com/edited_image.png",
            "revised_prompt": "A blue puppy in a park",
            "original_image": "https://example.com/original.png",
            "mask_image": None,
            "size": "1024x1024",
            "quality": "high",
            "format": "png"
        }]
        mock_agent.edit_image.return_value = mock_results
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await edit_image(
                image_url="https://example.com/original.png",
                prompt="make it blue"
            )
            
            assert "Successfully edited 1 image(s)" in result
            assert "Original image: https://example.com/original.png" in result
            assert "Edit prompt: 'make it blue'" in result
            assert "URL: https://example.com/edited_image.png" in result
            assert "Revised prompt: A blue puppy in a park" in result
            
            # Verify agent was called correctly
            mock_agent.edit_image.assert_called_once_with(
                image_url="https://example.com/original.png",
                prompt="make it blue",
                mask_url=None,
                size="1024x1024",
                quality="high",
                n=1
            )
    
    @pytest.mark.asyncio
    async def test_edit_image_with_mask(self, mock_agent):
        """Test image editing with mask."""
        mock_results = [{
            "url": "https://example.com/edited_image.png",
            "revised_prompt": "A blue puppy in a park",
            "original_image": "https://example.com/original.png",
            "mask_image": "https://example.com/mask.png",
            "size": "1024x1024",
            "quality": "high",
            "format": "png"
        }]
        mock_agent.edit_image.return_value = mock_results
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await edit_image(
                image_url="https://example.com/original.png",
                prompt="make it blue",
                mask_url="https://example.com/mask.png"
            )
            
            assert "Mask image: https://example.com/mask.png" in result
            
            # Verify mask was passed correctly
            call_args = mock_agent.edit_image.call_args[1]
            assert call_args["mask_url"] == "https://example.com/mask.png"
    
    @pytest.mark.asyncio
    async def test_edit_image_validation_errors(self, mock_agent):
        """Test validation errors in edit_image."""
        with patch('openai_image_mcp.server.agent', mock_agent):
            # Test invalid size
            result = await edit_image("url", "prompt", size="invalid")
            assert "Error: Invalid size 'invalid'" in result
            
            # Test invalid quality
            result = await edit_image("url", "prompt", quality="invalid")
            assert "Error: Invalid quality 'invalid'" in result
            
            
            # Test invalid n
            result = await edit_image("url", "prompt", n=0)
            assert "Error: Number of images must be between 1 and 10" in result
    
    @pytest.mark.asyncio
    async def test_edit_image_agent_exception(self, mock_agent):
        """Test handling of agent exceptions in edit_image."""
        mock_agent.edit_image.side_effect = Exception("Edit failed")
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await edit_image("url", "prompt")
            
            assert "Error editing image: Edit failed" in result