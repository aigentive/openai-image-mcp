"""Integration tests for the OpenAI Image MCP Server."""

import pytest
import os
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai_image_mcp.server import mcp, main
from openai_image_mcp.image_agent import OpenAIImageAgent


class TestIntegration:
    """Integration tests for the complete MCP server workflow."""
    
    @pytest.mark.asyncio
    async def test_server_lifecycle(self):
        """Test server initialization and shutdown lifecycle."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Test that server can be created
            assert mcp is not None
            assert hasattr(mcp, 'tool')
            assert hasattr(mcp, 'run')
    
    @pytest.mark.asyncio
    async def test_end_to_end_image_generation_mock(self):
        """Test complete end-to-end image generation workflow with mocks."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Create a real agent instance but mock the OpenAI API
            agent = OpenAIImageAgent()
            
            # Mock the OpenAI client response
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/generated_image.png"
            mock_image_data.revised_prompt = "A detailed cute puppy sitting in a sunny park"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                # Test the complete workflow
                results = await agent.generate_images(
                    prompt="a cute puppy",
                    size="1024x1024",
                    quality="high",
                    n=1
                )
                
                # Verify results
                assert len(results) == 1
                assert results[0]["url"] == "https://example.com/generated_image.png"
                assert results[0]["revised_prompt"] == "A detailed cute puppy sitting in a sunny park"
                assert results[0]["size"] == "1024x1024"
                assert results[0]["quality"] == "high"
                assert results[0]["format"] == "png"
    
    @pytest.mark.asyncio
    async def test_end_to_end_download_workflow(self):
        """Test complete download workflow."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock generate_images
            mock_generate_results = [{
                "url": "https://example.com/generated_image.png",
                "revised_prompt": "A detailed cute puppy",
                "size": "1024x1024",
                "quality": "high",
                "background": "auto",
                "output_format": "png",
                "index": 0,
                "b64_json": None
            }]
            
            # Mock image download
            mock_image_data = b"fake image data content"
            
            with patch.object(agent, 'generate_images', return_value=mock_generate_results):
                with patch.object(agent, 'download_image', return_value=mock_image_data):
                    results = await agent.generate_and_download_images("a cute puppy")
                    
                    assert len(results) == 1
                    assert results[0]["data"] == mock_image_data
                    assert results[0]["size_bytes"] == len(mock_image_data)
                    assert results[0]["url"] == "https://example.com/generated_image.png"
    
    @pytest.mark.asyncio 
    async def test_end_to_end_edit_workflow(self):
        """Test complete image editing workflow."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock image downloads
            mock_original_data = b"original image data"
            mock_mask_data = b"mask image data"
            
            # Mock OpenAI edit response
            mock_edited_data = MagicMock()
            mock_edited_data.url = "https://example.com/edited_image.png"
            mock_edited_data.revised_prompt = "A blue cute puppy sitting in a sunny park"
            mock_edited_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_edited_data]
            
            def mock_download(url):
                if "mask" in url:
                    return mock_mask_data
                return mock_original_data
            
            with patch.object(agent, 'download_image', side_effect=mock_download):
                with patch.object(agent.client.images, 'edit', return_value=mock_response) as mock_edit:
                    results = await agent.edit_image(
                        image_url="https://example.com/original.png",
                        prompt="make it blue",
                        mask_url="https://example.com/mask.png"
                    )
                    
                    # Verify the edit API was called correctly
                    mock_edit.assert_called_once()
                    call_args = mock_edit.call_args[1]
                    assert call_args["model"] == "gpt-image-1"
                    assert call_args["image"] == mock_original_data
                    assert call_args["mask"] == mock_mask_data
                    assert call_args["prompt"] == "make it blue"
                    
                    # Verify results
                    assert len(results) == 1
                    assert results[0]["url"] == "https://example.com/edited_image.png"
                    assert results[0]["original_image"] == "https://example.com/original.png"
                    assert results[0]["mask_image"] == "https://example.com/mask.png"
    
    @pytest.mark.asyncio
    async def test_multiple_operations_workflow(self):
        """Test performing multiple operations in sequence."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock responses for multiple operations
            mock_image_data_1 = MagicMock()
            mock_image_data_1.url = "https://example.com/image1.png"
            mock_image_data_1.revised_prompt = "First image"
            mock_image_data_1.b64_json = None
            
            mock_image_data_2 = MagicMock()
            mock_image_data_2.url = "https://example.com/image2.png"
            mock_image_data_2.revised_prompt = "Second image"
            mock_image_data_2.b64_json = None
            
            mock_response_1 = MagicMock()
            mock_response_1.data = [mock_image_data_1]
            
            mock_response_2 = MagicMock()
            mock_response_2.data = [mock_image_data_2]
            
            with patch.object(agent.client.images, 'generate', side_effect=[mock_response_1, mock_response_2]):
                # Generate first image
                results_1 = await agent.generate_images("first prompt")
                assert len(results_1) == 1
                assert results_1[0]["url"] == "https://example.com/image1.png"
                
                # Generate second image
                results_2 = await agent.generate_images("second prompt")
                assert len(results_2) == 1
                assert results_2[0]["url"] == "https://example.com/image2.png"
                
                # Verify both calls were made
                assert agent.client.images.generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error handling and recovery in workflows."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # First call fails, second succeeds
            mock_image_data = MagicMock()
            mock_image_data.url = "https://example.com/recovery_image.png"
            mock_image_data.revised_prompt = "Recovery image"
            mock_image_data.b64_json = None
            
            mock_response = MagicMock()
            mock_response.data = [mock_image_data]
            
            with patch.object(agent.client.images, 'generate', side_effect=[Exception("API Error"), mock_response]):
                # First call should fail
                with pytest.raises(Exception, match="API Error"):
                    await agent.generate_images("failing prompt")
                
                # Second call should succeed
                results = await agent.generate_images("successful prompt")
                assert len(results) == 1
                assert results[0]["url"] == "https://example.com/recovery_image.png"
    
    @pytest.mark.asyncio
    async def test_parameter_combinations(self):
        """Test various parameter combinations work correctly."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Test different parameter combinations
            test_cases = [
                {
                    "params": {"size": "1024x1024", "quality": "high"},
                    "expected_api_params": {"size": "1024x1024", "quality": "high"}
                },
                {
                    "params": {"size": "1536x1024", "quality": "low"},
                    "expected_api_params": {"size": "1536x1024", "quality": "low"}
                },
                {
                    "params": {"size": "1024x1536", "quality": "high"},
                    "expected_api_params": {"size": "1024x1536", "quality": "high"}
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                mock_image_data = MagicMock()
                mock_image_data.url = f"https://example.com/test_image_{i}.png"
                mock_image_data.revised_prompt = f"Test image {i}"
                mock_image_data.b64_json = None
                
                mock_response = MagicMock()
                mock_response.data = [mock_image_data]
                
                with patch.object(agent.client.images, 'generate', return_value=mock_response) as mock_generate:
                    results = await agent.generate_images("test prompt", **test_case["params"])
                    
                    # Verify correct parameters were passed to API
                    call_args = mock_generate.call_args[1]
                    assert call_args["model"] == "gpt-image-1"
                    assert call_args["prompt"] == "test prompt"
                    
                    for key, value in test_case["expected_api_params"].items():
                        assert call_args[key] == value
                    
                    # Verify results match parameters
                    assert len(results) == 1
                    assert results[0]["size"] == test_case["params"]["size"]
                    assert results[0]["quality"] == test_case["params"]["quality"]
                    assert results[0]["format"] == "png"
    
    def test_main_function_missing_api_key(self):
        """Test main function behavior when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('openai_image_mcp.server.logger') as mock_logger:
                with patch.object(mcp, 'run') as mock_run:
                    # Import and call main
                    main()
                    
                    # Verify error was logged and server didn't run
                    mock_logger.error.assert_called_with("OPENAI_API_KEY environment variable is required")
                    mock_run.assert_not_called()
    
    def test_main_function_with_api_key(self):
        """Test main function behavior with valid API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch.object(mcp, 'run') as mock_run:
                main()
                
                # Verify server.run() was called
                mock_run.assert_called_once()