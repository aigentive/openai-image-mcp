"""Tests for ModelSelector functionality."""

import pytest
from src.openai_image_mcp.model_selector import ModelSelector

class TestModelSelector:
    """Test cases for the ModelSelector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.selector = ModelSelector()
    
    def test_init(self):
        """Test ModelSelector initialization."""
        assert self.selector is not None
        assert hasattr(self.selector, 'model_capabilities')
        assert 'gpt-image-1' in self.selector.model_capabilities
        assert 'dall-e-3' in self.selector.model_capabilities
        assert 'dall-e-2' in self.selector.model_capabilities
    
    def test_auto_model_selection_general(self):
        """Test automatic model selection for general use case."""
        config = self.selector.select_model_and_params(
            use_case="general",
            model="auto",
            prompt="a beautiful landscape"
        )
        
        assert config["model"] in ["gpt-image-1", "dall-e-3", "dall-e-2"]
        assert config["quality"] in ["low", "medium", "high", "standard", "hd"]
        assert config["size"] in ["1024x1024", "1536x1024", "1024x1536"]
    
    def test_text_detection_in_prompt(self):
        """Test detection of text requirements in prompts."""
        # Should detect text requirement
        assert self.selector._prompt_needs_text("logo with text") == True
        assert self.selector._prompt_needs_text("create a sign") == True
        assert self.selector._prompt_needs_text("readable inscription") == True
        
        # Should not detect text requirement
        assert self.selector._prompt_needs_text("a cat sitting") == False
        assert self.selector._prompt_needs_text("landscape photo") == False
    
    def test_model_selection_for_text(self):
        """Test model selection when text is required."""
        config = self.selector.select_model_and_params(
            use_case="general",
            model="auto",
            prompt="logo with readable text"
        )
        
        # Should prefer GPT-Image-1 for text
        assert config["model"] == "gpt-image-1"
    
    def test_model_selection_for_product(self):
        """Test model selection for product photography."""
        config = self.selector.select_model_and_params(
            use_case="product",
            model="auto"
        )
        
        # Should prefer GPT-Image-1 for products
        assert config["model"] == "gpt-image-1"
        assert config["quality"] == "high"
    
    def test_model_selection_for_ui(self):
        """Test model selection for UI assets."""
        config = self.selector.select_model_and_params(
            use_case="ui",
            model="auto"
        )
        
        # Should prefer GPT-Image-1 for UI
        assert config["model"] == "gpt-image-1"
    
    def test_budget_conscious_selection(self):
        """Test budget-conscious model selection."""
        config = self.selector.select_model_and_params(
            use_case="batch",
            model="auto",
            budget_conscious=True
        )
        
        # Should prefer cheaper options
        assert config["model"] == "dall-e-2"
        assert config["quality"] in ["standard", "low"]
    
    def test_explicit_model_selection(self):
        """Test explicit model selection overrides auto."""
        config = self.selector.select_model_and_params(
            use_case="general",
            model="dall-e-3",
            quality="hd"
        )
        
        assert config["model"] == "dall-e-3"
        assert config["quality"] == "hd"
    
    def test_transparency_background(self):
        """Test transparent background handling."""
        config = self.selector.select_model_and_params(
            use_case="general",
            model="auto",
            background="transparent"
        )
        
        # Should prefer GPT-Image-1 for transparency
        assert config["model"] == "gpt-image-1"
        assert config.get("background") == "transparent"
        assert config.get("format") == "png"
    
    def test_edit_mode_selection(self):
        """Test model selection for different edit modes."""
        # Variation mode should prefer DALL-E 2
        config = self.selector.select_model_and_params(
            use_case="edit",
            model="auto",
            mode="variation"
        )
        assert config["model"] == "dall-e-2"
        
        # Inpaint should prefer GPT-Image-1
        config = self.selector.select_model_and_params(
            use_case="edit",
            model="auto",
            mode="inpaint"
        )
        assert config["model"] == "gpt-image-1"
    
    def test_cost_estimation_gpt_image_1(self):
        """Test cost estimation for GPT-Image-1."""
        cost = self.selector.estimate_cost("gpt-image-1", "medium", "1024x1024", 1)
        
        assert cost["cost_type"] == "token_based"
        assert "estimated_tokens" in cost
        assert cost["estimated_tokens"] > 0
    
    def test_cost_estimation_dall_e_3(self):
        """Test cost estimation for DALL-E 3."""
        cost = self.selector.estimate_cost("dall-e-3", "hd", "1792x1024", 2)
        
        assert cost["cost_type"] == "fixed_per_image"
        assert cost["images"] == 2
        assert cost["cost_level"] in ["high", "very-high", "extremely-high"]
    
    def test_cost_estimation_dall_e_2(self):
        """Test cost estimation for DALL-E 2."""
        cost = self.selector.estimate_cost("dall-e-2", "standard", "512x512", 3)
        
        assert cost["cost_type"] == "fixed_per_image"
        assert cost["images"] == 3
        assert cost["cost_level"] in ["low", "medium", "medium-high"]
    
    def test_quality_mapping_dall_e_3(self):
        """Test quality parameter mapping for DALL-E 3."""
        # High should map to hd
        config = self.selector.select_model_and_params(
            model="dall-e-3",
            quality="high"
        )
        assert config["quality"] == "hd"
        
        # Medium should map to standard
        config = self.selector.select_model_and_params(
            model="dall-e-3", 
            quality="medium"
        )
        assert config["quality"] == "standard"
    
    def test_quality_mapping_dall_e_2(self):
        """Test quality parameter mapping for DALL-E 2."""
        config = self.selector.select_model_and_params(
            model="dall-e-2",
            quality="high"  # Should be forced to standard
        )
        assert config["quality"] == "standard"
    
    def test_size_validation_dall_e_2(self):
        """Test size validation for DALL-E 2."""
        config = self.selector.select_model_and_params(
            model="dall-e-2",
            size="1792x1024"  # Should fallback to 1024x1024
        )
        assert config["size"] == "1024x1024"
    
    def test_artistic_prompt_detection(self):
        """Test detection of artistic prompts for DALL-E 3."""
        config = self.selector.select_model_and_params(
            use_case="general",
            model="auto",
            prompt="watercolor painting of mountains"
        )
        # Should prefer DALL-E 3 for artistic content
        assert config["model"] == "dall-e-3"