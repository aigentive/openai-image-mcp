"""Basic tests for the OpenAI Image MCP Server."""

import pytest
import os
from unittest.mock import patch, AsyncMock
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
    async def test_generate_images_mock(self):
        """Test image generation with mocked OpenAI client."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = OpenAIImageAgent()
            
            # Mock the OpenAI client response
            mock_response = AsyncMock()
            mock_response.data = [
                AsyncMock(
                    url="https://example.com/image1.png",
                    revised_prompt="A test image prompt"
                )
            ]
            
            with patch.object(agent.client.images, 'generate', return_value=mock_response):
                results = await agent.generate_images("test prompt")
                
                assert len(results) == 1
                assert results[0]["url"] == "https://example.com/image1.png"
                assert results[0]["revised_prompt"] == "A test image prompt"
                assert results[0]["size"] == "1024x1024"
                assert results[0]["quality"] == "standard"
                assert results[0]["style"] == "vivid"


def test_import_server():
    """Test that the server module can be imported without errors."""
    try:
        from openai_image_mcp import server
        assert server is not None
    except ImportError as e:
        pytest.fail(f"Failed to import server module: {e}")


def test_import_image_agent():
    """Test that the image agent module can be imported without errors."""
    try:
        from openai_image_mcp import image_agent
        assert image_agent is not None
    except ImportError as e:
        pytest.fail(f"Failed to import image_agent module: {e}")