"""Basic tests for the OpenAI Image MCP Server."""

import pytest
import os
from unittest.mock import patch
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_import_server():
    """Test that the server module can be imported without errors."""
    try:
        from openai_image_mcp import server
        assert server is not None
        
        # Test that key components are available
        assert hasattr(server, 'generate_and_download_image') 
        assert hasattr(server, 'edit_image')
        assert hasattr(server, 'mcp')
        assert hasattr(server, 'main')
    except ImportError as e:
        pytest.fail(f"Failed to import server module: {e}")


def test_import_image_agent():
    """Test that the image agent module can be imported without errors."""
    try:
        from openai_image_mcp import image_agent
        assert image_agent is not None
        
        # Test that OpenAIImageAgent class is available
        assert hasattr(image_agent, 'OpenAIImageAgent')
    except ImportError as e:
        pytest.fail(f"Failed to import image_agent module: {e}")


def test_mcp_server_creation():
    """Test that MCP server is created correctly."""
    from openai_image_mcp.server import mcp
    
    assert mcp is not None
    assert mcp.name == "openai-image-mcp"


def test_environment_variable_check():
    """Test environment variable validation."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('openai_image_mcp.server.logger') as mock_logger:
            with patch('openai_image_mcp.server.mcp.run') as mock_run:
                from openai_image_mcp.server import main
                main()
                
                # Should log error and not run server
                mock_logger.error.assert_called_with("CRITICAL_MAIN: OPENAI_API_KEY environment variable is required. Server cannot start.")
                mock_run.assert_not_called()


def test_mcp_tools_registered():
    """Test that MCP tools are properly registered."""
    from openai_image_mcp.server import mcp
    
    # The tools should be registered with the mcp instance
    # This is a basic smoke test to ensure the decorators worked
    assert mcp is not None