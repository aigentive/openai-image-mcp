"""Smart model selection logic for optimal image generation."""

import logging
from typing import Dict, Any, Optional, Literal

logger = logging.getLogger(__name__)

ModelType = Literal["auto", "gpt-image-1", "dall-e-3", "dall-e-2"]
QualityType = Literal["auto", "low", "medium", "high", "hd", "standard"]
UseCase = Literal["general", "product", "ui", "batch", "edit", "variation"]

class ModelSelector:
    """Intelligent model and parameter selection based on use case and requirements."""
    
    def __init__(self):
        """Initialize the model selector with decision matrices."""
        self.logger = logger
        
        # Model capabilities matrix
        self.model_capabilities = {
            "gpt-image-1": {
                "text_rendering": "excellent",
                "instruction_following": "excellent", 
                "transparency": True,
                "edit_modes": ["inpaint", "outpaint", "style_transfer"],
                "max_size": "1536x1024",
                "quality_levels": ["low", "medium", "high"],
                "cost_model": "token_based",
                "batch_support": True
            },
            "dall-e-3": {
                "text_rendering": "poor",
                "instruction_following": "good",
                "transparency": False,
                "edit_modes": [],
                "max_size": "1792x1024", 
                "quality_levels": ["standard", "hd"],
                "cost_model": "fixed_per_image",
                "batch_support": False
            },
            "dall-e-2": {
                "text_rendering": "poor",
                "instruction_following": "fair",
                "transparency": False,
                "edit_modes": ["inpaint", "variation"],
                "max_size": "1024x1024",
                "quality_levels": ["standard"],
                "cost_model": "fixed_per_image",
                "batch_support": True
            }
        }
    
    def select_model_and_params(
        self, 
        use_case: UseCase = "general",
        model: ModelType = "auto",
        quality: QualityType = "auto", 
        size: Optional[str] = None,
        prompt: Optional[str] = None,
        background: Optional[str] = None,
        budget_conscious: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Select optimal model and parameters based on requirements.
        
        Args:
            use_case: Primary use case for the image
            model: Requested model or "auto" for intelligent selection
            quality: Requested quality or "auto" for intelligent selection
            size: Requested size or None for auto-selection
            prompt: The generation prompt (analyzed for requirements)
            background: Background preference
            budget_conscious: Whether to optimize for cost
            **kwargs: Additional context parameters
            
        Returns:
            Dict with optimal model, quality, size, and other parameters
        """
        
        # If model is explicitly specified, validate and use it
        if model != "auto":
            selected_model = model
            self.logger.info(f"Using explicitly requested model: {selected_model}")
        else:
            selected_model = self._select_optimal_model(
                use_case, prompt, background, budget_conscious, **kwargs
            )
            
        # Select quality based on use case and model
        selected_quality = self._select_quality(
            quality, selected_model, use_case, budget_conscious
        )
        
        # Select size based on use case and model capabilities
        selected_size = self._select_size(
            size, selected_model, use_case
        )
        
        # Select additional parameters
        additional_params = self._select_additional_params(
            selected_model, use_case, background, **kwargs
        )
        
        result = {
            "model": selected_model,
            "quality": selected_quality,
            "size": selected_size,
            **additional_params
        }
        
        self.logger.info(f"Selected configuration: {result}")
        return result
    
    def _select_optimal_model(
        self, 
        use_case: UseCase, 
        prompt: Optional[str], 
        background: Optional[str],
        budget_conscious: bool,
        **kwargs
    ) -> str:
        """Select the best model based on requirements analysis."""
        
        # Analyze prompt for requirements
        needs_text = self._prompt_needs_text(prompt) if prompt else False
        needs_transparency = background == "transparent"
        
        # Use case specific logic
        if use_case == "edit":
            # Check if editing is requested
            edit_mode = kwargs.get("mode", "inpaint")
            if edit_mode in ["variation"]:
                return "dall-e-2"  # Only DALL-E 2 supports variations
            elif edit_mode in ["inpaint", "outpaint", "style_transfer"]:
                return "gpt-image-1"  # Best editing capabilities
                
        elif use_case == "ui":
            return "gpt-image-1"  # Best for clean graphics and transparency
            
        elif use_case == "product":
            return "gpt-image-1"  # Best realism and detail for products
            
        elif use_case == "batch":
            if budget_conscious:
                return "dall-e-2"  # Most cost-effective for batches
            else:
                return "gpt-image-1"  # Best quality
                
        # General case decision tree
        if budget_conscious and not (needs_text or needs_transparency):
            return "dall-e-2"
            
        if needs_text or needs_transparency:
            return "gpt-image-1"
            
        # For artistic/creative content without special requirements
        if prompt and any(term in prompt.lower() for term in 
                         ["artistic", "painting", "abstract", "creative", "style"]):
            return "dall-e-3"
            
        # Default to GPT-Image-1 for best overall experience
        return "gpt-image-1"
    
    def _select_quality(
        self, 
        quality: QualityType, 
        model: str, 
        use_case: UseCase,
        budget_conscious: bool
    ) -> str:
        """Select optimal quality setting."""
        
        if quality != "auto":
            # Map quality to model-specific values
            if model == "dall-e-3":
                return "hd" if quality in ["high", "hd"] else "standard"
            elif model == "dall-e-2":
                return "standard"  # Only option
            else:  # gpt-image-1
                if quality == "hd":
                    return "high"  # Map hd to high for consistency
                return quality
        
        # Auto quality selection
        if budget_conscious:
            if model == "gpt-image-1":
                return "low"
            return "standard"
            
        # Use case based quality
        quality_map = {
            "product": "high",
            "ui": "medium", 
            "batch": "medium" if not budget_conscious else "low",
            "edit": "high",
            "general": "medium"
        }
        
        selected = quality_map.get(use_case, "medium")
        
        # Adjust for model capabilities
        if model == "dall-e-3":
            return "hd" if selected == "high" else "standard"
        elif model == "dall-e-2":
            return "standard"
            
        return selected
    
    def _select_size(self, size: Optional[str], model: str, use_case: UseCase) -> str:
        """Select optimal image size."""
        
        if size and size != "auto":
            # Validate requested size against model capabilities
            if model == "dall-e-2":
                # Only square formats supported
                valid_sizes = ["256x256", "512x512", "1024x1024"]
                if size not in valid_sizes:
                    return "1024x1024"  # Fallback to largest supported
            return size
            
        # Use case based size preferences
        size_preferences = {
            "product": "1024x1024",  # Square for product shots
            "ui": "1024x1024",       # Square for most UI elements
            "batch": "1024x1024",    # Standard size for efficiency
            "edit": "1024x1024",     # Standard for editing
            "general": "1024x1024"   # Safe default
        }
        
        preferred = size_preferences.get(use_case, "1024x1024")
        
        # Validate size is supported by model
        if model == "dall-e-2":
            # Only square formats
            if preferred not in ["256x256", "512x512", "1024x1024"]:
                return "1024x1024"
                
        return preferred
    
    def _select_additional_params(
        self, 
        model: str, 
        use_case: UseCase, 
        background: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Select additional parameters like style, format, etc."""
        
        params = {}
        
        # Background handling
        if background == "transparent" and model == "gpt-image-1":
            params["background"] = "transparent"
            params["format"] = "png"  # Required for transparency
        elif background:
            params["background"] = background
            
        # Style parameter for DALL-E 3
        if model == "dall-e-3":
            style = kwargs.get("style", "natural")
            if use_case in ["product", "ui"]:
                params["style"] = "natural"  # More realistic for these uses
            else:
                params["style"] = style
                
        # Format selection
        if "format" not in params:
            format_map = {
                "product": "png",    # High quality
                "ui": "png",         # Clean graphics
                "batch": "jpeg",     # Smaller files
                "general": "png"     # Safe default
            }
            params["format"] = format_map.get(use_case, "png")
            
        return params
    
    def _prompt_needs_text(self, prompt: str) -> bool:
        """Analyze if prompt requires text rendering."""
        text_indicators = [
            "text", "writing", "words", "letters", "sign", "label", 
            "logo", "typography", "font", "readable", "inscription"
        ]
        return any(indicator in prompt.lower() for indicator in text_indicators)
    
    def estimate_cost(
        self, 
        model: str, 
        quality: str, 
        size: str, 
        n: int = 1
    ) -> Dict[str, Any]:
        """Estimate generation cost for the given parameters."""
        
        if model == "gpt-image-1":
            # Token-based pricing (approximate)
            quality_tokens = {
                "low": 272,
                "medium": 1056, 
                "high": 4160
            }
            
            # Size multipliers for non-square formats
            size_multiplier = 1.0
            if "1536" in size:
                size_multiplier = 1.5
            elif "1792" in size:
                size_multiplier = 1.75
                
            base_tokens = quality_tokens.get(quality, 1056)
            total_tokens = int(base_tokens * size_multiplier * n)
            
            return {
                "model": model,
                "cost_type": "token_based",
                "estimated_tokens": total_tokens,
                "cost_level": "variable"
            }
            
        else:  # DALL-E 3 or DALL-E 2
            cost_levels = {
                ("dall-e-2", "256x256"): "low",
                ("dall-e-2", "512x512"): "medium", 
                ("dall-e-2", "1024x1024"): "medium-high",
                ("dall-e-3", "1024x1024", "standard"): "high",
                ("dall-e-3", "1024x1024", "hd"): "very-high",
                ("dall-e-3", "1792x1024", "standard"): "very-high",
                ("dall-e-3", "1792x1024", "hd"): "extremely-high"
            }
            
            key = (model, size, quality) if model == "dall-e-3" else (model, size)
            cost_level = cost_levels.get(key, "medium")
            
            return {
                "model": model,
                "cost_type": "fixed_per_image", 
                "images": n,
                "cost_level": cost_level
            }