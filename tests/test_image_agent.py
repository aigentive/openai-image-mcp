"""Comprehensive tests for the OpenAI Image Agent."""

import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai_image_mcp.image_agent import OpenAIImageAgent


class TestOpenAIImageAgent:
    """Test cases for OpenAI Image Agent."""
    
    def test_agent_initialization_without_api_key(self):
        """Test that agent raises error without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                OpenAIImageAgent()
    
    def test_agent_initialization_with_api_key(self):
        """Test that agent initializes correctly with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            assert agent.api_key == "test-key"
            assert agent.client is not None
    
    @pytest.mark.asyncio
    async def test_generate_images_basic(self):
        """Test basic image generation with mocked OpenAI client."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock the OpenAI client response
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/image1.png"
            mock_image_data.revised_prompt = "A cute puppy sitting in a park"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images("test prompt")
                
                assert len(results) == 1
                assert results[0]["url"] == "https://example.com/image1.png"
                assert results[0]["revised_prompt"] == "A cute puppy sitting in a park"
                assert results[0]["size"] == "1024x1024"
                assert results[0]["quality"] == "high"
                assert results[0]["format"] == "png"
                assert results[0]["index"] == 0
    
    @pytest.mark.asyncio
    async def test_generate_images_with_custom_params(self):
        """Test image generation with custom parameters."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/image1.jpg"
            mock_image_data.revised_prompt = "A test image"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response) as mock_generate:
                results = await agent.generate_images(
                    prompt="test prompt",
                    size="1536x1024",
                    quality="low",
                    n=1
                )
                
                # Verify API was called with correct parameters
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args[1]
                assert call_args["model"] == "gpt-image-1"
                assert call_args["prompt"] == "test prompt"
                assert call_args["size"] == "1536x1024"
                assert call_args["quality"] == "low"
                assert call_args["n"] == 1
                # Note: background and output_format are not passed to gpt-image-1 API
                assert "background" not in call_args
                assert "output_format" not in call_args
                
                assert len(results) == 1
                assert results[0]["size"] == "1536x1024"
                assert results[0]["quality"] == "low"
                assert results[0]["format"] == "png"
    
    @pytest.mark.asyncio
    async def test_generate_images_multiple(self):
        """Test generating multiple images."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_image_data_1 = MagicMock()
            mock_image_data_1.url = "https://example.com/image1.png"
            mock_image_data_1.revised_prompt = "A test image 1"
            mock_image_data_1.b64_json = None
            
            mock_image_data_2 = MagicMock()
            mock_image_data_2.url = "https://example.com/image2.png"
            mock_image_data_2.revised_prompt = "A test image 2"
            mock_image_data_2.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data_1, mock_image_data_2]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images("test prompt", n=2)
                
                assert len(results) == 2
                assert results[0]["url"] == "https://example.com/image1.png"
                assert results[1]["url"] == "https://example.com/image2.png"
                assert results[0]["index"] == 0
                assert results[1]["index"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_images_with_b64_response(self):
        """Test handling base64 response from OpenAI."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_image_data = MagicMock()
            mock_image_data.url = None
            mock_image_data.b64_json = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            mock_image_data.revised_prompt = "A test image"
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images("test prompt")
                
                assert len(results) == 1
                assert results[0]["url"].startswith("data:image/png;base64,")
                assert results[0]["b64_json"] == mock_image_data.b64_json
    
    @pytest.mark.asyncio
    async def test_generate_images_api_error(self):
        """Test handling of API errors."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            with patch.object(agent.client.images, 'generate', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    await agent.generate_images("test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_images_timeout(self):
        """Test handling of timeout errors."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            with patch.object(agent.client.images, 'generate', side_effect=asyncio.TimeoutError()):
                with pytest.raises(Exception, match="Image generation timed out"):
                    await agent.generate_images("test prompt")
    
    @pytest.mark.asyncio
    async def test_download_image_success(self):
        """Test successful image download."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_response = MagicMock()
            mock_response.content = b"fake image data"
            mock_response.raise_for_status = MagicMock()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await agent.download_image("https://example.com/image.png")
                
                assert result == b"fake image data"
    
    @pytest.mark.asyncio
    async def test_download_image_error(self):
        """Test image download error handling."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Download failed")
                
                with pytest.raises(Exception, match="Download failed"):
                    await agent.download_image("https://example.com/image.png")
    
    @pytest.mark.asyncio
    async def test_generate_and_download_images(self):
        """Test generate and download workflow."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock generate_images
            mock_results = [{
                "url": "https://example.com/image1.png",
                "revised_prompt": "A test image",
                "size": "1024x1024",
                "quality": "high",
                "background": "auto",
                "output_format": "png",
                "index": 0,
                "b64_json": None
            }]
            
            # Mock download_image
            mock_image_data = b"fake image data"
            
            with patch.object(agent, 'generate_images', return_value=mock_results):
                with patch.object(agent, 'download_image', return_value=mock_image_data):
                    results = await agent.generate_and_download_images("test prompt")
                    
                    assert len(results) == 1
                    assert results[0]["data"] == mock_image_data
                    assert results[0]["size_bytes"] == len(mock_image_data)
    
    @pytest.mark.asyncio
    async def test_generate_and_download_images_download_failure(self):
        """Test generate and download with download failure."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_results = [{
                "url": "https://example.com/image1.png",
                "revised_prompt": "A test image",
                "size": "1024x1024",
                "quality": "high",
                "background": "auto",
                "output_format": "png",
                "index": 0,
                "b64_json": None
            }]
            
            with patch.object(agent, 'generate_images', return_value=mock_results):
                with patch.object(agent, 'download_image', side_effect=Exception("Download failed")):
                    results = await agent.generate_and_download_images("test prompt")
                    
                    assert len(results) == 1
                    assert results[0]["data"] is None
                    assert results[0]["size_bytes"] == 0
    
    @pytest.mark.asyncio
    async def test_edit_image_basic(self):
        """Test basic image editing functionality."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock download_image for base image
            mock_image_data = b"fake image data"
            
            # Mock OpenAI edit response
            mock_edited_data = MagicMock()
            mock_edited_data.url = "https://example.com/edited_image.png"
            mock_edited_data.revised_prompt = "An edited test image"
            mock_edited_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_edited_data]
            
            with patch.object(agent, 'download_image', return_value=mock_image_data):
                with patch.object(agent.client.images, 'edit', return_value=mock_response) as mock_edit:
                    results = await agent.edit_image(
                        image_url="https://example.com/original.png",
                        prompt="make it blue"
                    )
                    
                    # Verify API was called correctly
                    mock_edit.assert_called_once()
                    call_args = mock_edit.call_args[1]
                    assert call_args["model"] == "gpt-image-1"
                    assert call_args["image"] == mock_image_data
                    assert call_args["mask"] is None
                    assert call_args["prompt"] == "make it blue"
                    
                    assert len(results) == 1
                    assert results[0]["url"] == "https://example.com/edited_image.png"
                    assert results[0]["original_image"] == "https://example.com/original.png"
                    assert results[0]["mask_image"] is None
    
    @pytest.mark.asyncio
    async def test_edit_image_with_mask(self):
        """Test image editing with mask."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_image_data = b"fake image data"
            mock_mask_data = b"fake mask data"
            
            mock_edited_data = MagicMock()
            mock_edited_data.url = "https://example.com/edited_image.png"
            mock_edited_data.revised_prompt = "An edited test image"
            mock_edited_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_edited_data]
            
            # Mock download_image to return different data based on URL
            def mock_download(url):
                if "mask" in url:
                    return mock_mask_data
                return mock_image_data
            
            with patch.object(agent, 'download_image', side_effect=mock_download):
                with patch.object(agent.client.images, 'edit', return_value=mock_response) as mock_edit:
                    results = await agent.edit_image(
                        image_url="https://example.com/original.png",
                        prompt="make it blue",
                        mask_url="https://example.com/mask.png"
                    )
                    
                    # Verify API was called with mask
                    call_args = mock_edit.call_args[1]
                    assert call_args["mask"] == mock_mask_data
                    
                    assert results[0]["mask_image"] == "https://example.com/mask.png"