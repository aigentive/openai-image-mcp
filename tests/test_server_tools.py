"""Tests for MCP server tools."""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai_image_mcp.server import generate_and_download_image, edit_image
from openai_image_mcp.image_agent import OpenAIImageAgent


class TestMCPServerTools:
    """Test cases for MCP server tools."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock OpenAI Image Agent."""
        agent = MagicMock(spec=OpenAIImageAgent)
        return agent
    
    def test_generate_and_download_image_basic_success(self, mock_agent):
        """Test successful image generation and download via MCP tool."""
        # Mock agent response
        mock_results = [{
            "filepath": "/path/to/image.png",
            "saved_image_data_bytes": 12345,
            "revised_prompt": "A cute puppy in a park",
            "requested_size": "1024x1024",
            "requested_quality": "standard"
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        # Patch the global agent
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("a cute puppy")
            
            assert "Image generation request processed" in result
            assert "Prompt: 'a cute puppy'" in result
            assert "Revised Prompt: 'A cute puppy in a park'" in result
            assert "Image saved to: /path/to/image.png (12345 bytes)" in result
            
            # Verify agent was called correctly
            mock_agent.generate_and_download_images.assert_called_once_with(
                prompt="a cute puppy",
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                style="vivid",
                output_file_format="png",
                n=1
            )
    
    def test_generate_and_download_image_custom_params(self, mock_agent):
        """Test image generation with custom parameters."""
        mock_results = [{
            "filepath": "/path/to/image.jpeg",
            "saved_image_data_bytes": 54321,
            "revised_prompt": "A test image",
            "requested_size": "1792x1024",
            "requested_quality": "hd"
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image(
                prompt="test image",
                size="1792x1024",
                quality="hd",
                output_file_format="jpeg"
            )
            
            assert "Image generation request processed" in result
            assert "Size: 1792x1024" in result
            assert "Quality: hd" in result
    
    def test_generate_and_download_image_n_parameter(self, mock_agent):
        """Test that n parameter is handled (currently forced to 1)."""
        mock_results = [{
            "filepath": "/path/to/image.png",
            "saved_image_data_bytes": 12345,
            "revised_prompt": "A test image",
            "requested_size": "1024x1024",
            "requested_quality": "standard"
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test images", n=5)
            
            assert "Image generation request processed" in result
            # Verify n was forced to 1
            mock_agent.generate_and_download_images.assert_called_once()
            call_args = mock_agent.generate_and_download_images.call_args[1]
            assert call_args["n"] == 1
    
    def test_generate_and_download_image_invalid_model(self, mock_agent):
        """Test validation of invalid model parameter."""
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test prompt", model="invalid-model")
            
            assert "Error: Invalid model 'invalid-model'" in result
    
    def test_generate_and_download_image_invalid_quality(self, mock_agent):
        """Test validation of invalid quality parameter for DALL-E 3."""
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test prompt", quality="invalid")
            
            assert "Error: Invalid quality 'invalid'" in result
    
    def test_generate_and_download_image_invalid_style(self, mock_agent):
        """Test validation of invalid style parameter for DALL-E 3."""
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test prompt", style="invalid")
            
            assert "Error: Invalid style 'invalid'" in result
    
    
    
    def test_generate_and_download_image_invalid_format(self, mock_agent):
        """Test validation of invalid output_file_format parameter."""
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test prompt", output_file_format="invalid")
            
            assert "Error: Invalid output_file_format 'invalid'" in result
    
    def test_generate_and_download_image_agent_exception(self, mock_agent):
        """Test handling of agent exceptions."""
        mock_agent.generate_and_download_images.side_effect = Exception("API Error")
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test prompt")
            
            assert "Error processing generate_and_download_image: API Error" in result
    
    def test_generate_and_download_image_success(self, mock_agent):
        """Test successful image generation and download."""
        mock_results = [{
            "filepath": "/path/to/image.png",
            "saved_image_data_bytes": 12345,
            "revised_prompt": "A cute puppy in a park",
            "requested_size": "1024x1024",
            "requested_quality": "standard"
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("a cute puppy")
            
            assert "Image generation request processed" in result
            assert "Prompt: 'a cute puppy'" in result
            assert "Revised Prompt: 'A cute puppy in a park'" in result
            assert "Image saved to: /path/to/image.png (12345 bytes)" in result
            
            # Verify agent was called correctly
            mock_agent.generate_and_download_images.assert_called_once_with(
                prompt="a cute puppy",
                model="dall-e-3",
                size="1024x1024",
                quality="standard",
                style="vivid",
                output_file_format="png",
                n=1
            )
    
    def test_generate_and_download_image_download_failed(self, mock_agent):
        """Test when download fails."""
        mock_results = [{
            "filepath": None,
            "saved_image_data_bytes": 0,
            "revised_prompt": "A cute puppy in a park",
            "requested_size": "1024x1024",
            "requested_quality": "standard"
        }]
        mock_agent.generate_and_download_images.return_value = mock_results
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("a cute puppy")
            
            assert "Download or file processing failed" in result
    
    def test_generate_and_download_image_no_results(self, mock_agent):
        """Test when no images are generated."""
        mock_agent.generate_and_download_images.return_value = []
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = generate_and_download_image("test prompt")
            
            assert "Error: No images were generated or downloaded" in result
    
    def test_edit_image_success(self, mock_agent):
        """Test successful image editing."""
        mock_results = [{
            "url": "https://example.com/edited_image.png",
            "revised_prompt": "A blue puppy in a park",
            "original_image_path": "/path/to/original.png",
            "mask_image_path": None,
            "determined_format": "png"
        }]
        mock_agent.edit_image.return_value = mock_results
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = edit_image(
                image_path="/path/to/original.png",
                prompt="make it blue"
            )
            
            assert "Edited 1 image(s) using dall-e-2" in result
            assert "Original Image Path: /path/to/original.png" in result
            assert "URL: https://example.com/edited_image.png" in result
            assert "Revised Prompt: A blue puppy in a park" in result
            
            # Verify agent was called correctly
            mock_agent.edit_image.assert_called_once_with(
                image_path="/path/to/original.png",
                prompt="make it blue",
                mask_path=None,
                model="dall-e-2",
                size="1024x1024",
                n=1,
                response_format="b64_json"
            )
    
    def test_edit_image_with_mask(self, mock_agent):
        """Test image editing with mask."""
        mock_results = [{
            "url": "https://example.com/edited_image.png",
            "revised_prompt": "A blue puppy in a park",
            "original_image_path": "/path/to/original.png",
            "mask_image_path": "/path/to/mask.png",
            "determined_format": "png"
        }]
        mock_agent.edit_image.return_value = mock_results
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = edit_image(
                image_path="/path/to/original.png",
                prompt="make it blue",
                mask_path="/path/to/mask.png"
            )
            
            assert "Mask Image Path: /path/to/mask.png" in result
            
            # Verify mask was passed correctly
            call_args = mock_agent.edit_image.call_args[1]
            assert call_args["mask_path"] == "/path/to/mask.png"
    
    def test_edit_image_validation_errors(self, mock_agent):
        """Test validation errors in edit_image."""
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            # Test invalid model
            result = edit_image("/path/to/image.png", "prompt", model="dall-e-3")
            assert "Error: Invalid model 'dall-e-3'" in result
            
            # Test invalid size
            result = edit_image("/path/to/image.png", "prompt", size="invalid")
            assert "Error: Invalid size 'invalid'" in result
            
            # Test invalid n
            result = edit_image("/path/to/image.png", "prompt", n=0)
            assert "Error: Number of images 'n' for DALL-E 2 edit must be between 1 and 10" in result
    
    def test_edit_image_agent_exception(self, mock_agent):
        """Test handling of agent exceptions in edit_image."""
        mock_agent.edit_image.side_effect = Exception("Edit failed")
        
        with patch('openai_image_mcp.server.get_agent', return_value=mock_agent):
            result = edit_image("/path/to/image.png", "prompt")
            
            assert "Error processing edit_image: Edit failed" in result