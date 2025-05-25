"""Test for the get_usage_guide tool."""

import pytest
import os
from unittest.mock import patch, mock_open, MagicMock
from src.openai_image_mcp.server import get_usage_guide

class TestUsageGuide:
    """Test cases for the get_usage_guide tool."""
    
    def test_get_usage_guide_success(self):
        """Test successful loading of LLM.md file."""
        mock_content = """# LLM Usage Guide
        
## Quick Decision Tree
1. Need to create a new image? → `generate_image`
2. Need to modify existing image? → `edit_image_advanced`

## Key Principles
- Use "auto" for model selection
"""
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('os.path.exists', return_value=True):
                result = get_usage_guide()
                
        assert "LLM Usage Guide" in result["guide_content"]
        assert "Quick Decision Tree" in result["guide_content"]
        assert "generate_image" in result["guide_content"]
        assert result["success"] is True
        assert len(result["guide_content"]) > 100  # Should be substantial content
    
    def test_get_usage_guide_file_not_found(self):
        """Test handling when LLM.md file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = get_usage_guide()
            
        assert result["success"] is False
        assert result["error_type"] == "guide_error"
        assert "File not found" in result["error"]
    
    def test_get_usage_guide_permission_error(self):
        """Test handling of file permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = get_usage_guide()
            
        assert result["success"] is False
        assert result["error_type"] == "guide_error"
        assert "Permission denied" in result["error"]
    
    def test_get_usage_guide_reads_actual_file(self):
        """Test that the tool reads the actual LLM.md file when it exists."""
        # This test will use the real file system
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(script_dir)
        llm_guide_path = os.path.join(workspace_root, "LLM.md")
        
        if os.path.exists(llm_guide_path):
            result = get_usage_guide()
            
            # Check that it contains expected content from our LLM.md
            assert result["success"] is True
            assert "Quick Decision Tree" in result["guide_content"]
            assert "session" in result["guide_content"].lower()  # Should mention sessions
            assert result["architecture"] == "Session-based Conversational Image Generation"
            assert "Multi-turn conversational sessions" in result["key_features"]
            assert len(result["guide_content"]) > 1000  # Should be comprehensive
        else:
            pytest.skip("LLM.md file not found in workspace root")