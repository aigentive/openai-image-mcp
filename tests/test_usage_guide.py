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
                
        assert "LLM Usage Guide" in result
        assert "Quick Decision Tree" in result
        assert "generate_image" in result
        assert len(result) > 100  # Should be substantial content
    
    def test_get_usage_guide_file_not_found(self):
        """Test handling when LLM.md file is not found."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = get_usage_guide()
            
        assert "Error: LLM usage guide file not found" in result
        assert "LLM.md exists in the project root" in result
    
    def test_get_usage_guide_permission_error(self):
        """Test handling of file permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = get_usage_guide()
            
        assert "Error retrieving usage guide" in result
    
    def test_get_usage_guide_reads_actual_file(self):
        """Test that the tool reads the actual LLM.md file when it exists."""
        # This test will use the real file system
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(script_dir)
        llm_guide_path = os.path.join(workspace_root, "LLM.md")
        
        if os.path.exists(llm_guide_path):
            result = get_usage_guide()
            
            # Check that it contains expected content from our LLM.md
            assert "Quick Decision Tree" in result
            assert "generate_image" in result
            assert "Model Selection Cheat Sheet" in result or "Model Cheat Sheet" in result
            assert "Cost Optimization" in result
            assert len(result) > 1000  # Should be comprehensive
        else:
            pytest.skip("LLM.md file not found in workspace root")