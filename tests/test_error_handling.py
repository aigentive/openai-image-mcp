"""Tests for error handling and edge cases."""

import pytest
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys
from pathlib import Path
import httpx

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai_image_mcp.image_agent import OpenAIImageAgent
from openai_image_mcp.server import generate_image


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_openai_api_timeout(self):
        """Test handling of OpenAI API timeouts."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            with patch.object(agent.client.images, 'generate', side_effect=asyncio.TimeoutError()):
                with pytest.raises(Exception, match="Image generation timed out"):
                    await agent.generate_images("test prompt")
    
    @pytest.mark.asyncio
    async def test_openai_api_rate_limit(self):
        """Test handling of rate limit errors."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            rate_limit_error = Exception("Rate limit exceeded")
            with patch.object(agent.client.images, 'generate', side_effect=rate_limit_error):
                with pytest.raises(Exception, match="Rate limit exceeded"):
                    await agent.generate_images("test prompt")
    
    @pytest.mark.asyncio
    async def test_openai_api_invalid_key(self):
        """Test handling of invalid API key errors."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            auth_error = Exception("Invalid API key")
            with patch.object(agent.client.images, 'generate', side_effect=auth_error):
                with pytest.raises(Exception, match="Invalid API key"):
                    await agent.generate_images("test prompt")
    
    @pytest.mark.asyncio
    async def test_openai_api_malformed_response(self):
        """Test handling of malformed API responses."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock response with missing data attribute
            mock_response = MagicMock()
            del mock_response.data  # Remove data attribute
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                with pytest.raises(AttributeError):
                    await agent.generate_images("test prompt")
    
    @pytest.mark.asyncio
    async def test_image_download_network_error(self):
        """Test handling of network errors during image download."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.ConnectError("Connection failed")
                
                with pytest.raises(Exception, match="Connection failed"):
                    await agent.download_image("https://example.com/image.png")
    
    @pytest.mark.asyncio
    async def test_image_download_http_error(self):
        """Test handling of HTTP errors during image download."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=None, response=None)
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                with pytest.raises(Exception):
                    await agent.download_image("https://example.com/nonexistent.png")
    
    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self):
        """Test handling of empty or whitespace-only prompts."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/image.png"
            mock_image_data.revised_prompt = "Enhanced empty prompt"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                # Empty string
                results = await agent.generate_images("")
                assert len(results) == 1
                
                # Whitespace only
                results = await agent.generate_images("   ")
                assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_very_long_prompt_handling(self):
        """Test handling of very long prompts."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Create a very long prompt (over typical limits)
            long_prompt = "a cute puppy " * 1000
            
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/image.png"
            mock_image_data.revised_prompt = "Revised long prompt"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images(long_prompt)
                assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_special_characters_in_prompt(self):
        """Test handling of special characters in prompts."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            special_prompt = "🐶 cute puppy with émojis & special chars: @#$%^&*()"
            
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/image.png"
            mock_image_data.revised_prompt = "Revised special prompt"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images(special_prompt)
                assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_missing_image_attributes(self):
        """Test handling of API responses with missing image attributes."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock image data with missing attributes
            mock_image_data = MagicMock()
            # Don't set url, revised_prompt, or b64_json attributes
            del mock_image_data.url
            del mock_image_data.revised_prompt
            del mock_image_data.b64_json
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images("test prompt")
                
                # Should handle missing attributes gracefully
                assert len(results) == 1
                assert results[0]["url"] is None  # getattr should return None for missing attributes
                assert results[0]["revised_prompt"] == "test prompt"  # should fall back to original prompt
    
    @pytest.mark.asyncio
    async def test_server_tool_with_context_none(self):
        """Test server tools with None context."""
        mock_agent = MagicMock()
        mock_agent.generate_images = AsyncMock(return_value=[{
            "url": "https://example.com/image.png",
            "revised_prompt": "Test prompt",
            "size": "1024x1024",
            "quality": "high",
            "background": "auto",
            "output_format": "png"
        }])
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            result = await generate_image("test prompt", ctx=None)
            assert "Successfully generated 1 image(s)" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of multiple concurrent requests."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/image.png"
            mock_image_data.revised_prompt = "Concurrent image"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                # Create multiple concurrent requests
                tasks = [
                    agent.generate_images(f"prompt {i}")
                    for i in range(5)
                ]
                
                results = await asyncio.gather(*tasks)
                
                # All requests should succeed
                assert len(results) == 5
                for result in results:
                    assert len(result) == 1
                    assert result[0]["url"] == "https://example.com/image.png"
    
    @pytest.mark.asyncio
    async def test_edge_case_boundary_values(self):
        """Test boundary values for parameters."""
        mock_agent = MagicMock()
        
        with patch('openai_image_mcp.server.agent', mock_agent):
            # Test minimum and maximum n values
            await generate_image("test", n=1)  # minimum valid
            await generate_image("test", n=10)  # maximum valid
            
            # Test invalid boundary values
            result = await generate_image("test", n=0)  # below minimum
            assert "Error: Number of images must be between 1 and 10" in result
            
            result = await generate_image("test", n=11)  # above maximum
            assert "Error: Number of images must be between 1 and 10" in result
    
    @pytest.mark.asyncio
    async def test_malformed_urls_in_edit_image(self):
        """Test edit_image with malformed URLs."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            malformed_urls = [
                "not-a-url",
                "ftp://invalid-protocol.com/image.png",
                "https://",
                "",
                None
            ]
            
            for url in malformed_urls:
                if url is None:
                    continue  # Skip None URL as it would cause TypeError
                
                with patch.object(agent, 'download_image', side_effect=Exception(f"Invalid URL: {url}")):
                    with pytest.raises(Exception):
                        await agent.edit_image(url, "edit prompt")
    
    @pytest.mark.asyncio
    async def test_memory_handling_large_images(self):
        """Test handling of large image downloads."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Simulate very large image data (10MB)
            large_image_data = b"x" * (10 * 1024 * 1024)
            
            with patch.object(agent, 'download_image', return_value=large_image_data):
                with patch.object(agent, 'generate_images', return_value=[{
                    "url": "https://example.com/large_image.png",
                    "revised_prompt": "Large image",
                    "size": "1024x1024",
                    "quality": "high",
                    "background": "auto",
                    "output_format": "png",
                    "index": 0,
                    "b64_json": None
                }]):
                    results = await agent.generate_and_download_images("test prompt")
                    
                    assert len(results) == 1
                    assert results[0]["data"] == large_image_data
                    assert results[0]["size_bytes"] == len(large_image_data)
    
    @pytest.mark.asyncio
    async def test_unicode_handling_in_responses(self):
        """Test handling of Unicode characters in API responses."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock response with Unicode characters
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/图像.png"
            mock_image_data.revised_prompt = "一只可爱的小狗 🐕"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images("Unicode test 测试")
                
                assert len(results) == 1
                assert "图像.png" in results[0]["url"]
                assert "一只可爱的小狗 🐕" in results[0]["revised_prompt"]