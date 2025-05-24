"""Tests for enhanced server tools functionality."""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from src.openai_image_mcp.server import (
    generate_image, 
    edit_image_advanced,
    generate_product_image,
    generate_ui_asset,
    batch_generate,
    analyze_and_regenerate,
    get_model_selector,
    get_file_organizer
)

class TestEnhancedServerTools:
    """Test cases for enhanced server tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the global instances to avoid initialization issues
        self.mock_selector = Mock()
        self.mock_organizer = Mock()
        self.mock_agent = Mock()
        
        # Set up default mock responses
        self.mock_selector.select_model_and_params.return_value = {
            "model": "gpt-image-1",
            "quality": "medium",
            "size": "1024x1024",
            "format": "png"
        }
        
        self.mock_selector.estimate_cost.return_value = {
            "cost_type": "token_based",
            "estimated_tokens": 1000,
            "cost_level": "medium"
        }
        
        self.mock_organizer.get_save_path.return_value = "/tmp/test_image.png"
        self.mock_organizer.save_image_metadata.return_value = "/tmp/test_image_metadata.json"
        
        # Mock successful image generation
        self.mock_agent.generate_and_download_images.return_value = [{
            "filepath": "/tmp/test_image.png",
            "saved_image_data_bytes": 50000,
            "revised_prompt": "test revised prompt",
            "requested_quality": "medium",
            "requested_size": "1024x1024"
        }]
    
    @patch('src.openai_image_mcp.server.get_model_selector')
    @patch('src.openai_image_mcp.server.get_file_organizer') 
    @patch('src.openai_image_mcp.server.get_agent')
    def test_generate_image_basic(self, mock_get_agent, mock_get_organizer, mock_get_selector):
        """Test basic image generation with auto parameters."""
        mock_get_selector.return_value = self.mock_selector
        mock_get_organizer.return_value = self.mock_organizer
        mock_get_agent.return_value = self.mock_agent
        
        result = generate_image("a beautiful landscape")
        
        assert "✅ Image generated successfully!" in result
        assert "Model: gpt-image-1 (auto-selected)" in result
        assert "test_image.png" in result
        
        # Verify method calls
        self.mock_selector.select_model_and_params.assert_called_once()
        self.mock_organizer.get_save_path.assert_called()  # Called multiple times for save_paths
        call_args = self.mock_agent.generate_and_download_images.call_args
        assert "save_paths" in call_args[1]  # Verify save_paths parameter is passed
        assert "file_organizer" in call_args[1]  # Verify file_organizer parameter is passed
    
    @patch('src.openai_image_mcp.server.get_model_selector')
    @patch('src.openai_image_mcp.server.get_file_organizer')
    @patch('src.openai_image_mcp.server.get_agent')
    def test_generate_image_explicit_model(self, mock_get_agent, mock_get_organizer, mock_get_selector):
        """Test image generation with explicit model selection."""
        mock_get_selector.return_value = self.mock_selector
        mock_get_organizer.return_value = self.mock_organizer
        mock_get_agent.return_value = self.mock_agent
        
        self.mock_selector.select_model_and_params.return_value = {
            "model": "dall-e-3",
            "quality": "hd",
            "size": "1024x1024",
            "style": "vivid"
        }
        
        result = generate_image(
            prompt="artistic landscape",
            model="dall-e-3",
            quality="hd",
            style="vivid"
        )
        
        assert "✅ Image generated successfully!" in result
        assert "Model: dall-e-3" in result
        
        # Verify explicit parameters were passed
        call_args = self.mock_selector.select_model_and_params.call_args
        assert call_args[1]["model"] == "dall-e-3"
        assert call_args[1]["quality"] == "hd"
    
    @patch('src.openai_image_mcp.server.get_model_selector')
    @patch('src.openai_image_mcp.server.get_file_organizer')
    @patch('src.openai_image_mcp.server.get_agent')
    def test_generate_image_transparent_background(self, mock_get_agent, mock_get_organizer, mock_get_selector):
        """Test image generation with transparent background."""
        mock_get_selector.return_value = self.mock_selector
        mock_get_organizer.return_value = self.mock_organizer
        mock_get_agent.return_value = self.mock_agent
        
        self.mock_selector.select_model_and_params.return_value = {
            "model": "gpt-image-1",
            "quality": "medium",
            "size": "1024x1024",
            "background": "transparent",
            "format": "png"
        }
        
        result = generate_image(
            prompt="logo design",
            background="transparent"
        )
        
        assert "✅ Image generated successfully!" in result
        assert "Background: transparent" in result
        
        # Verify background parameter was passed
        call_args = self.mock_selector.select_model_and_params.call_args
        assert call_args[1]["background"] == "transparent"
    
    def test_generate_image_invalid_model(self):
        """Test image generation with invalid model."""
        result = generate_image("test prompt", model="invalid-model")
        
        assert "Error: Invalid model 'invalid-model'" in result
    
    def test_generate_image_invalid_format(self):
        """Test image generation with invalid format."""
        with patch('src.openai_image_mcp.server.get_model_selector') as mock_get_selector:
            mock_get_selector.return_value = self.mock_selector
            self.mock_selector.select_model_and_params.return_value = {
                "model": "gpt-image-1",
                "quality": "medium", 
                "size": "1024x1024",
                "format": "invalid"
            }
            
            result = generate_image("test prompt", format="invalid")
            
            assert "Error: Invalid format 'invalid'" in result
    
    @patch('os.path.exists')
    @patch('src.openai_image_mcp.server.get_model_selector')
    @patch('src.openai_image_mcp.server.get_file_organizer')
    def test_edit_image_advanced_file_not_found(self, mock_get_organizer, mock_get_selector, mock_exists):
        """Test edit_image_advanced with non-existent file."""
        mock_exists.return_value = False
        
        result = edit_image_advanced(
            image_path="/nonexistent/image.png",
            prompt="improve this image"
        )
        
        assert "❌ Error: Image file not found" in result
    
    @patch('os.path.exists')
    def test_edit_image_advanced_invalid_mode(self, mock_exists):
        """Test edit_image_advanced with invalid mode."""
        mock_exists.return_value = True
        
        result = edit_image_advanced(
            image_path="/test/image.png",
            prompt="improve this image",
            mode="invalid_mode"
        )
        
        assert "❌ Error: Invalid mode 'invalid_mode'" in result
    
    @patch('os.path.exists')
    def test_edit_image_advanced_inpaint_no_mask(self, mock_exists):
        """Test edit_image_advanced inpaint mode without mask."""
        mock_exists.return_value = True
        
        result = edit_image_advanced(
            image_path="/test/image.png",
            prompt="remove object",
            mode="inpaint"
        )
        
        assert "❌ Error: Inpaint mode requires a mask_path" in result
    
    def test_generate_product_image_invalid_background(self):
        """Test generate_product_image with invalid background type."""
        result = generate_product_image(
            product_description="test product",
            background_type="invalid"
        )
        
        assert "❌ Error: Invalid background_type 'invalid'" in result
    
    def test_generate_product_image_invalid_angle(self):
        """Test generate_product_image with invalid angle."""
        result = generate_product_image(
            product_description="test product",
            angle="invalid"
        )
        
        assert "❌ Error: Invalid angle 'invalid'" in result
    
    def test_generate_product_image_invalid_lighting(self):
        """Test generate_product_image with invalid lighting."""
        result = generate_product_image(
            product_description="test product",
            lighting="invalid"
        )
        
        assert "❌ Error: Invalid lighting 'invalid'" in result
    
    def test_generate_product_image_invalid_batch_count(self):
        """Test generate_product_image with invalid batch count."""
        result = generate_product_image(
            product_description="test product",
            batch_count=10  # Too high
        )
        
        assert "❌ Error: batch_count must be between 1 and 4" in result
    
    @patch('src.openai_image_mcp.server.get_file_organizer')
    @patch('src.openai_image_mcp.server.generate_image')
    def test_generate_product_image_success(self, mock_generate_image, mock_get_organizer):
        """Test successful product image generation."""
        mock_get_organizer.return_value = self.mock_organizer
        mock_generate_image.return_value = "✅ Image generated successfully!"
        
        result = generate_product_image(
            product_description="wireless headphones",
            background_type="transparent",
            angle="front",
            lighting="studio"
        )
        
        assert "🛍️ Product images generated successfully!" in result
        assert "Product: wireless headphones" in result
        assert "Background: transparent" in result
        assert "Angle: front" in result
        assert "Lighting: studio" in result
    
    def test_generate_ui_asset_invalid_type(self):
        """Test generate_ui_asset with invalid asset type."""
        result = generate_ui_asset(
            asset_type="invalid",
            description="test asset"
        )
        
        assert "❌ Error: Invalid asset_type 'invalid'" in result
    
    def test_generate_ui_asset_invalid_theme(self):
        """Test generate_ui_asset with invalid theme."""
        result = generate_ui_asset(
            asset_type="icon",
            description="test icon",
            theme="invalid"
        )
        
        assert "❌ Error: Invalid theme 'invalid'" in result
    
    def test_generate_ui_asset_invalid_style(self):
        """Test generate_ui_asset with invalid style preset."""
        result = generate_ui_asset(
            asset_type="icon",
            description="test icon",
            style_preset="invalid"
        )
        
        assert "❌ Error: Invalid style_preset 'invalid'" in result
    
    @patch('src.openai_image_mcp.server.get_file_organizer')
    @patch('src.openai_image_mcp.server.generate_image')
    def test_generate_ui_asset_success(self, mock_generate_image, mock_get_organizer):
        """Test successful UI asset generation."""
        mock_get_organizer.return_value = self.mock_organizer
        mock_generate_image.return_value = "✅ Image generated successfully!"
        
        result = generate_ui_asset(
            asset_type="icon",
            description="shopping cart icon",
            theme="light",
            style_preset="flat"
        )
        
        assert "🎨 UI asset generated successfully!" in result
        assert "Type: icon" in result
        assert "Style: flat" in result
        assert "Theme: light" in result
    
    @patch('src.openai_image_mcp.server.get_model_selector')
    @patch('src.openai_image_mcp.server.get_file_organizer') 
    def test_batch_generate_invalid_json(self, mock_get_organizer, mock_get_selector):
        """Test batch_generate with invalid JSON format."""
        mock_get_selector.return_value = self.mock_selector
        mock_get_organizer.return_value = self.mock_organizer
        
        result = batch_generate(
            prompts='["invalid json'  # Malformed JSON
        )
        
        assert "Error: Invalid JSON format" in result
    
    def test_batch_generate_no_prompts(self):
        """Test batch_generate with empty prompts."""
        result = batch_generate(prompts="")
        
        assert "❌ Error: No prompts provided" in result
    
    def test_batch_generate_too_many_prompts(self):
        """Test batch_generate with too many prompts."""
        prompts = ['"prompt' + str(i) + '"' for i in range(15)]
        prompts_json = '[' + ','.join(prompts) + ']'
        
        result = batch_generate(prompts=prompts_json)
        
        assert "❌ Error: Maximum 10 prompts allowed" in result
    
    def test_batch_generate_invalid_variations(self):
        """Test batch_generate with invalid variations count."""
        result = batch_generate(
            prompts='["test prompt"]',
            variations_per_prompt=5  # Too high
        )
        
        assert "❌ Error: variations_per_prompt must be between 1 and 3" in result
    
    @patch('src.openai_image_mcp.server.get_model_selector')
    @patch('src.openai_image_mcp.server.get_file_organizer') 
    @patch('src.openai_image_mcp.server.generate_image')
    def test_batch_generate_success(self, mock_generate_image, mock_get_organizer, mock_get_selector):
        """Test successful batch generation."""
        mock_get_selector.return_value = self.mock_selector
        mock_get_organizer.return_value = self.mock_organizer
        mock_generate_image.return_value = "✅ Image generated successfully!"
        
        result = batch_generate(
            prompts='["red car", "blue car"]',
            variations_per_prompt=2,
            consistent_style="watercolor"
        )
        
        assert "🚀 Batch generation completed!" in result
        assert "4/4 images generated successfully" in result
        assert "Consistent Style: watercolor" in result
    
    @patch('os.path.exists')
    def test_analyze_and_regenerate_file_not_found(self, mock_exists):
        """Test analyze_and_regenerate with non-existent file."""
        mock_exists.return_value = False
        
        result = analyze_and_regenerate(
            image_path="/nonexistent/image.png",
            requirements="improve quality"
        )
        
        assert "❌ Error: Image file not found" in result
    
    def test_analyze_and_regenerate_invalid_iterations(self):
        """Test analyze_and_regenerate with invalid max_iterations."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = analyze_and_regenerate(
                image_path="/test/image.png",
                requirements="improve quality",
                max_iterations=10  # Too high
            )
            
            assert "❌ Error: max_iterations must be between 1 and 5" in result
    
    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('json.load')
    def test_analyze_and_regenerate_no_metadata(self, mock_json_load, mock_open, mock_exists):
        """Test analyze_and_regenerate with missing metadata."""
        mock_exists.side_effect = lambda path: "/test/image.png" in path  # Image exists, metadata doesn't
        mock_json_load.return_value = {}  # Empty metadata
        
        result = analyze_and_regenerate(
            image_path="/test/image.png",
            requirements="improve quality"
        )
        
        assert "❌ Error: Cannot find original prompt" in result
    
    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('json.load')
    @patch('src.openai_image_mcp.server.get_file_organizer')
    @patch('src.openai_image_mcp.server.edit_image_advanced')
    def test_analyze_and_regenerate_success(self, mock_edit, mock_get_organizer, mock_json_load, mock_open, mock_exists):
        """Test successful analyze_and_regenerate."""
        # Mock file existence and metadata
        mock_exists.return_value = True
        mock_json_load.return_value = {"original_prompt": "original test prompt"}
        mock_get_organizer.return_value = self.mock_organizer
        mock_edit.return_value = "✅ Image edited successfully!"
        
        self.mock_organizer.get_save_path.return_value = "/tmp/improved_iter1.png"
        
        result = analyze_and_regenerate(
            image_path="/test/image.png",
            requirements="make it more professional",
            preserve_elements="colors",
            max_iterations=2
        )
        
        assert "🔄 Iterative improvement completed!" in result
        assert "Requirements: make it more professional" in result
        assert "Preserved: colors" in result
        
        # Verify edit_image_advanced was called
        mock_edit.assert_called()