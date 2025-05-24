"""Main MCP server implementation for OpenAI image generation using FastMCP."""

import logging
import os
import datetime
import sys


from typing import Optional

from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

from .image_agent import OpenAIImageAgent
from .model_selector import ModelSelector
from .file_organizer import FileOrganizer

# Load environment variables
load_dotenv()

# Configure basic console logging (stderr)
# All detailed logging will be captured by redirecting stderr at the shell level.
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)], # Log to stderr
    force=True
)

logger = logging.getLogger(__name__) # Get logger for the current module

logger.info("MCP Server Script: Initializing...") # Test message

# Create FastMCP server
mcp = FastMCP("openai-image-mcp")

# Global instances - will be initialized on first use
agent: Optional[OpenAIImageAgent] = None
model_selector: Optional[ModelSelector] = None
file_organizer: Optional[FileOrganizer] = None


def get_agent() -> OpenAIImageAgent:
    global agent
    logger.debug("get_agent() called")
    if agent is None:
        logger.info("Initializing OpenAIImageAgent...")
        try:
            agent = OpenAIImageAgent()
            logger.info("OpenAI Image Agent initialized successfully")
        except Exception as e_agent_init:
            logger.error(f"Failed to initialize OpenAIImageAgent: {e_agent_init}", exc_info=True)
            raise 
    return agent

def get_model_selector() -> ModelSelector:
    global model_selector
    if model_selector is None:
        logger.info("Initializing ModelSelector...")
        model_selector = ModelSelector()
    return model_selector

def get_file_organizer() -> FileOrganizer:
    global file_organizer
    if file_organizer is None:
        logger.info("Initializing FileOrganizer...")
        file_organizer = FileOrganizer()
    return file_organizer

@mcp.tool()
def generate_image(
    prompt: str,
    model: str = "auto",
    quality: str = "auto", 
    size: str = "auto",
    style: str = "natural",
    format: str = "png",
    background: str = "auto",
    save_path: Optional[str] = None,
    n: int = 1
) -> str:
    """
    Generate an image using OpenAI's image models with intelligent model selection.
    
    This tool intelligently selects the best model and parameters based on your 
    requirements. Use 'auto' settings to let the tool optimize for your use case.
    
    When to use this tool:
    - Creating new images from text descriptions
    - When you need general-purpose image generation  
    - For single images (use batch_generate for multiple)
    
    Model selection guide:
    - 'auto': Best choice for most cases - tool selects optimal model
    - 'gpt-image-1': When you need text in images or highest quality
    - 'dall-e-3': For artistic images or specific large dimensions
    - 'dall-e-2': For budget-conscious generation or when you need variations
    
    Quality guidelines:
    - 'auto': Recommended - balances quality and cost
    - 'high': Product photos, professional use
    - 'medium': General content, social media
    - 'low': Drafts, iterations, testing
    
    Args:
        prompt: Text description of the desired image
        model: "auto" | "gpt-image-1" | "dall-e-3" | "dall-e-2" (default: "auto")
        quality: "auto" | "low" | "medium" | "high" | "hd" (default: "auto")
        size: "auto" | specific dimensions like "1024x1024" (default: "auto")
        style: "natural" | "vivid" (for DALL-E 3, default: "natural")
        format: "png" | "jpeg" | "webp" (default: "png")
        background: "auto" | "transparent" (default: "auto")
        save_path: Custom save location (default: auto-organized)
        n: Number of images to generate (default: 1)
    
    Examples:
    - Product photo: generate_image("professional photo of wireless headphones", quality="high")
    - Logo design: generate_image("minimal tech startup logo", background="transparent")
    - Illustration: generate_image("children's book illustration of a friendly dragon", model="dall-e-3")
    """
    logger.info(f"MCP TOOL CALLED: generate_image with prompt: '{prompt}'")
    try:
        # Get helper instances
        selector = get_model_selector()
        organizer = get_file_organizer()
        
        # Select optimal parameters using intelligent selection
        config = selector.select_model_and_params(
            use_case="general",
            model=model,
            quality=quality,
            size=size,
            prompt=prompt,
            background=background,
            style=style,
            format=format
        )
        
        logger.debug(f"Selected config: {config}")
        
        # Extract selected parameters
        selected_model = config["model"]
        selected_quality = config["quality"]
        selected_size = config["size"]
        selected_style = config.get("style", style)
        selected_format = config.get("format", format)
        selected_background = config.get("background")

        # Parameter validation
        if selected_model not in ["gpt-image-1", "dall-e-3", "dall-e-2"]:
            return f"Error: Invalid model '{selected_model}'. Must be one of: gpt-image-1, dall-e-3, dall-e-2."
            
        # Model-specific validations
        if selected_model == "dall-e-3":
            if selected_quality not in ["standard", "hd"]:
                return f"Error: Invalid quality '{selected_quality}' for DALL-E 3. Choose 'standard' or 'hd'."
            if selected_style not in ["vivid", "natural"]:
                return f"Error: Invalid style '{selected_style}' for DALL-E 3. Choose 'vivid' or 'natural'."
        elif selected_model == "dall-e-2":
            if selected_quality not in ["standard"]:
                selected_quality = "standard"  # Force standard for DALL-E 2
                
        if selected_format.lower() not in ["png", "jpeg", "jpg", "webp"]:
            return f"Error: Invalid format '{selected_format}'. Choose png, jpeg, or webp."
            
        if n > 1 and selected_model == "dall-e-3":
            logger.warning(f"DALL-E 3 doesn't support n>1, setting n=1")
            n = 1

        # Generate save path
        if save_path is None:
            save_path = organizer.get_save_path(
                use_case="general",
                filename_prefix="generated",
                file_format=selected_format
            )
            
        agent_instance = get_agent()
        
        # Handle different models appropriately
        if selected_model == "gpt-image-1":
            # For GPT-Image-1, we'll need to use the existing generate_and_download_images
            # but adapt it for the new model (this will require agent updates)
            results = agent_instance.generate_and_download_images(
                prompt=prompt,
                model="dall-e-3",  # Temporary fallback until agent supports gpt-image-1
                size=selected_size,
                quality=selected_quality,
                style=selected_style if selected_model == "dall-e-3" else None,
                output_file_format=selected_format.lower(),
                n=n
            )
        else:
            results = agent_instance.generate_and_download_images(
                prompt=prompt, 
                model=selected_model, 
                size=selected_size, 
                quality=selected_quality, 
                style=selected_style if selected_model == "dall-e-3" else None,
                output_file_format=selected_format.lower(),
                n=n
            )
        
        if not results:
            logger.warning("No images generated/downloaded by agent.")
            return "Error: No images were generated or downloaded."
            
        # Process results and save metadata
        response_parts = []
        cost_info = selector.estimate_cost(selected_model, selected_quality, selected_size, n)
        
        for i, result in enumerate(results):
            filepath = result.get("filepath")
            saved_bytes = result.get("saved_image_data_bytes", 0)
            revised_prompt = result.get("revised_prompt", prompt)
            
            # Save metadata
            if filepath:
                metadata = {
                    "original_prompt": prompt,
                    "revised_prompt": revised_prompt,
                    "model": selected_model,
                    "quality": selected_quality,
                    "size": selected_size,
                    "style": selected_style,
                    "format": selected_format,
                    "background": selected_background,
                    "use_case": "general",
                    "cost_estimate": cost_info,
                    "file_size_bytes": saved_bytes
                }
                organizer.save_image_metadata(filepath, metadata)
            
            if i == 0:  # Main response for first image
                response_parts.extend([
                    f"✅ Image generated successfully!",
                    f"📝 Prompt: '{prompt}'",
                    f"🔄 Revised: '{revised_prompt}'" if revised_prompt != prompt else "",
                    f"🤖 Model: {selected_model} (auto-selected)" if model == "auto" else f"🤖 Model: {selected_model}",
                    f"📐 Size: {selected_size}", 
                    f"⚡ Quality: {selected_quality}",
                    f"💾 Format: {selected_format}"
                ])
                
                if selected_model == "dall-e-3":
                    response_parts.append(f"🎨 Style: {selected_style}")
                if selected_background == "transparent":
                    response_parts.append(f"🔍 Background: transparent")
                    
                if filepath and saved_bytes > 0:
                    response_parts.append(f"📁 Saved to: {filepath} ({saved_bytes:,} bytes)")
                    response_parts.append(f"💰 Cost: {cost_info['cost_level']} ({cost_info['cost_type']})")
                else:
                    response_parts.append(f"❌ Failed to save image. Check server logs.")
                    
                # Remove empty strings
                response_parts = [part for part in response_parts if part]
            else:  # Additional images
                if filepath:
                    response_parts.append(f"📁 Image {i+1}: {filepath}")
        
        return "\n".join(response_parts)

    except Exception as e:
        logger.error(f"Error in generate_image tool: {str(e)}", exc_info=True)
        return f"❌ Error generating image: {str(e)}"


@mcp.tool()
def edit_image(
    image_path: str,
    prompt: str,
    mask_path: Optional[str] = None,
    model: str = "dall-e-2",
    size: str = "1024x1024",
    n: int = 1,
    response_format: str = "b64_json"
) -> str:
    """
    Edits an image using a local image file and an optional local mask file.
    Args:
        image_path: Path to the local base image file (e.g., /path/to/image.png).
        prompt: Description of the edits to make.
        mask_path: Optional path to a local mask image file (black and white PNG).
        model: Model to use (typically "dall-e-2" for edits).
        size: Image size (e.g., "1024x1024", "512x512", "256x256" for DALL-E 2).
        n: Number of edited images to generate (1-10, DALL-E 2 supports up to 10).
        response_format: Desired format for OpenAI response ('url' or 'b64_json').
    """
    logger.info(f"MCP TOOL CALLED: edit_image for '{image_path}'")
    try:
        logger.debug(f"Params: image_path='{image_path}', prompt='{prompt}', mask_path='{mask_path}', model='{model}', size='{size}', n={n}, response_format='{response_format}'")
        
        # Basic validation for edit_image
        if model != "dall-e-2": # Currently hardcoded agent support for DALL-E 2 edits
             return f"Error: Invalid model '{model}' for edit_image. Currently only 'dall-e-2' is supported by the agent."
        # DALL-E 2 edit sizes
        valid_edit_sizes = ["1024x1024", "512x512", "256x256"]
        if size not in valid_edit_sizes:
            return f"Error: Invalid size '{size}' for DALL-E 2 edit. Must be one of: {valid_edit_sizes}"
        if not (1 <= n <= 10):
             return f"Error: Number of images 'n' for DALL-E 2 edit must be between 1 and 10."
        if response_format not in ["url", "b64_json"]:
            return f"Error: Invalid response_format '{response_format}'. Choose 'url' or 'b64_json'."


        agent_instance = get_agent()
        results = agent_instance.edit_image(
            image_path=image_path, 
            prompt=prompt, 
            mask_path=mask_path,
            model=model, 
            size=size, 
            n=n,
            response_format=response_format
        )
        
        if not results:
            logger.warning("No images returned from agent edit_image call.")
            return "Error: No images were returned from the edit operation."

        response_lines = [f"Edited {len(results)} image(s) using {model}:"]
        for i, res in enumerate(results, 1):
            response_lines.append(f"  Image {i}:")
            response_lines.append(f"    Original Image Path: {res.get('original_image_path')}")
            if res.get('mask_image_path'):
                 response_lines.append(f"    Mask Image Path: {res.get('mask_image_path')}")
            response_lines.append(f"    Revised Prompt: {res.get('revised_prompt', '(not revised)')}") # Edits may not revise prompt
            if res.get("url"):
                response_lines.append(f"    URL: {res.get('url')}")
            if res.get("b64_json"):
                response_lines.append(f"    b64_json available: True (length approx {len(res['b64_json']) // 4 * 3} bytes)")
            response_lines.append(f"    Determined Format: {res.get('determined_format', 'N/A')}")
            response_lines.append("")
        
        # Note: This tool does not save the edited image to a file yet.
        # It returns URLs or b64_json from OpenAI as per the agent method.
        # User would need to handle saving/displaying from this data.
        return "\n".join(response_lines)

    except FileNotFoundError as e_fnf:
        logger.error(f"File not found error in edit_image tool: {str(e_fnf)}", exc_info=True)
        return f"Error: {str(e_fnf)}"
    except Exception as e:
        logger.error(f"Error in edit_image tool: {str(e)}", exc_info=True)
        return f"Error processing edit_image: {str(e)}"

@mcp.tool()
def edit_image_advanced(
    image_path: str,
    prompt: str,
    mode: str = "inpaint",
    mask_path: Optional[str] = None,
    model: str = "auto",
    strength: float = 0.8,
    save_path: Optional[str] = None
) -> str:
    """
    Advanced image editing with multiple modes and intelligent model selection.
    
    When to use: For modifying existing images with sophisticated control
    
    Modes:
    - "inpaint": Replace specific areas (requires mask)
    - "outpaint": Extend image boundaries  
    - "variation": Create similar versions
    - "style_transfer": Apply artistic styles
    
    Args:
        image_path: Path to source image
        prompt: Edit instructions
        mode: "inpaint" | "outpaint" | "variation" | "style_transfer"
        mask_path: Path to mask image (required for inpaint mode)
        model: "auto" | "gpt-image-1" | "dall-e-2" (default: "auto")
        strength: Edit strength 0.0-1.0 (default: 0.8)
        save_path: Custom save location (default: auto-organized)
    
    Examples:
    - Remove object: edit_image_advanced("photo.jpg", "remove the car", mode="inpaint", mask_path="car_mask.png")
    - Style change: edit_image_advanced("photo.jpg", "make it look like a watercolor painting", mode="style_transfer")
    - Create variation: edit_image_advanced("photo.jpg", "same scene, different lighting", mode="variation")
    """
    logger.info(f"MCP TOOL CALLED: edit_image_advanced with mode '{mode}' for '{image_path}'")
    
    try:
        # Validate input file exists
        if not os.path.exists(image_path):
            return f"❌ Error: Image file not found: {image_path}"
            
        # Validate mode
        valid_modes = ["inpaint", "outpaint", "variation", "style_transfer"]
        if mode not in valid_modes:
            return f"❌ Error: Invalid mode '{mode}'. Choose from: {', '.join(valid_modes)}"
            
        # Validate mask requirements
        if mode == "inpaint" and not mask_path:
            return f"❌ Error: Inpaint mode requires a mask_path"
            
        if mask_path and not os.path.exists(mask_path):
            return f"❌ Error: Mask file not found: {mask_path}"
            
        # Get helper instances
        selector = get_model_selector()
        organizer = get_file_organizer()
        
        # Select model based on mode and requirements
        config = selector.select_model_and_params(
            use_case="edit",
            model=model,
            mode=mode,
            prompt=prompt
        )
        
        selected_model = config["model"]
        logger.info(f"Selected model {selected_model} for {mode} editing")
        
        # Validate model supports the mode
        capabilities = selector.model_capabilities.get(selected_model, {})
        supported_modes = capabilities.get("edit_modes", [])
        
        if mode not in supported_modes:
            return f"❌ Error: Model {selected_model} doesn't support {mode} mode. Supported: {', '.join(supported_modes)}"
            
        # Generate save path
        if save_path is None:
            save_path = organizer.get_save_path(
                use_case="edit",
                filename_prefix=f"edited_{mode}",
                file_format="png"
            )
            
        agent_instance = get_agent()
        
        # Handle different editing modes
        if mode == "variation" and selected_model == "dall-e-2":
            # DALL-E 2 variation endpoint (not implemented yet in agent)
            return f"❌ Error: Variation mode not yet implemented. Use legacy edit_image tool for now."
            
        elif mode in ["inpaint", "style_transfer"]:
            # Use existing edit functionality
            results = agent_instance.edit_image(
                image_path=image_path,
                prompt=prompt,
                mask_path=mask_path,
                model=selected_model if selected_model != "gpt-image-1" else "dall-e-2",  # Fallback until agent supports gpt-image-1
                size="1024x1024",
                n=1,
                response_format="b64_json"
            )
            
            if not results:
                return f"❌ Error: No edited images returned"
                
            result = results[0]
            
            # Get image data and save
            image_data = None
            if result.get("b64_json"):
                import base64
                image_data = base64.b64decode(result["b64_json"])
            elif result.get("url") and result["url"].startswith("http"):
                import requests
                response = requests.get(result["url"], timeout=90)
                response.raise_for_status()
                image_data = response.content
                
            if image_data:
                # Save the edited image
                try:
                    with open(save_path, "wb") as f:
                        f.write(image_data)
                        
                    # Save metadata
                    metadata = {
                        "original_image": image_path,
                        "edit_prompt": prompt,
                        "edit_mode": mode,
                        "model": selected_model,
                        "mask_path": mask_path,
                        "strength": strength,
                        "file_size_bytes": len(image_data)
                    }
                    organizer.save_image_metadata(save_path, metadata)
                    
                    return f"""✅ Image edited successfully!
📝 Mode: {mode}
🖼️ Original: {image_path}
🎭 Edit: {prompt}
🤖 Model: {selected_model}
📁 Saved to: {save_path} ({len(image_data):,} bytes)"""
                    
                except Exception as e:
                    logger.error(f"Failed to save edited image: {e}")
                    return f"❌ Error saving edited image: {str(e)}"
            else:
                return f"❌ Error: No image data received from API"
                
        else:
            return f"❌ Error: Mode '{mode}' not yet implemented"
            
    except Exception as e:
        logger.error(f"Error in edit_image_advanced: {str(e)}", exc_info=True)
        return f"❌ Error in advanced editing: {str(e)}"

@mcp.tool()
def generate_product_image(
    product_description: str,
    background_type: str = "white",
    angle: str = "front",
    lighting: str = "studio",
    props: str = "",
    batch_count: int = 1
) -> str:
    """
    Generate optimized product photography images for e-commerce and catalogs.
    
    When to use: E-commerce, catalogs, product showcases
    Automatically uses GPT-Image-1 with high quality for best realism.
    
    Args:
        product_description: Detailed description of the product
        background_type: "transparent" | "white" | "lifestyle" | "custom" (default: "white")
        angle: "front" | "side" | "top" | "45deg" | "multiple" (default: "front")
        lighting: "studio" | "natural" | "dramatic" (default: "studio")
        props: Additional scene elements or styling notes
        batch_count: Number of variations to generate (1-4, default: 1)
    
    Examples:
    - Simple product: generate_product_image("wireless bluetooth headphones", background_type="transparent")
    - Lifestyle shot: generate_product_image("ceramic coffee mug", background_type="lifestyle", props="coffee beans, wooden table")
    - Multiple angles: generate_product_image("smartphone case", angle="multiple", batch_count=3)
    """
    logger.info(f"MCP TOOL CALLED: generate_product_image for '{product_description}'")
    
    try:
        # Validate parameters
        valid_backgrounds = ["transparent", "white", "lifestyle", "custom"]
        if background_type not in valid_backgrounds:
            return f"❌ Error: Invalid background_type '{background_type}'. Choose from: {', '.join(valid_backgrounds)}"
            
        valid_angles = ["front", "side", "top", "45deg", "multiple"]
        if angle not in valid_angles:
            return f"❌ Error: Invalid angle '{angle}'. Choose from: {', '.join(valid_angles)}"
            
        valid_lighting = ["studio", "natural", "dramatic"]
        if lighting not in valid_lighting:
            return f"❌ Error: Invalid lighting '{lighting}'. Choose from: {', '.join(valid_lighting)}"
            
        if not (1 <= batch_count <= 4):
            return f"❌ Error: batch_count must be between 1 and 4"
        
        # Get helper instances
        organizer = get_file_organizer()
        
        # Build optimized prompt for product photography
        prompt_parts = []
        
        # Base product description
        if background_type == "lifestyle":
            prompt_parts.append(f"Professional lifestyle product photography of {product_description}")
        else:
            prompt_parts.append(f"Professional product photography of {product_description}")
            
        # Angle specification
        angle_descriptions = {
            "front": "front view, centered composition",
            "side": "side profile view, showing depth and form",
            "top": "top-down view, overhead perspective",
            "45deg": "45-degree angle view, three-quarter perspective",
            "multiple": "multiple angles in one frame, product showcase layout"
        }
        prompt_parts.append(angle_descriptions[angle])
        
        # Lighting setup
        lighting_descriptions = {
            "studio": "professional studio lighting, soft shadows, clean highlights",
            "natural": "natural window lighting, soft and even illumination",
            "dramatic": "dramatic lighting with strong contrast and depth"
        }
        prompt_parts.append(lighting_descriptions[lighting])
        
        # Background specification
        if background_type == "transparent":
            prompt_parts.append("isolated on transparent background")
        elif background_type == "white":
            prompt_parts.append("clean white background, seamless backdrop")
        elif background_type == "lifestyle":
            prompt_parts.append("realistic lifestyle setting, contextual environment")
        
        # Additional props
        if props:
            prompt_parts.append(f"with {props}")
            
        # Technical quality specifications
        prompt_parts.extend([
            "sharp focus, high detail, commercial quality",
            "professional photography, high resolution",
            "clean composition, product-focused"
        ])
        
        final_prompt = ", ".join(prompt_parts)
        logger.info(f"Generated product prompt: {final_prompt}")
        
        # Generate images using optimized settings
        results = []
        product_name = product_description.split()[0] if product_description else "product"
        
        for i in range(batch_count):
            # Generate save path for organized storage
            save_path = organizer.get_save_path(
                use_case="product",
                filename_prefix=f"{product_name}_{angle}",
                file_format="png" if background_type == "transparent" else "png",
                product_name=product_name
            )
            
            # Use generate_image with product-optimized settings
            result = generate_image(
                prompt=final_prompt,
                model="gpt-image-1",  # Force GPT-Image-1 for best quality
                quality="high",
                size="1024x1024",  # Standard product photo size
                background="transparent" if background_type == "transparent" else "auto",
                format="png",
                save_path=save_path,
                n=1
            )
            
            results.append(f"Image {i+1}: {result}")
            
        # Create summary response
        response_parts = [
            f"🛍️ Product images generated successfully!",
            f"📦 Product: {product_description}",
            f"🎨 Background: {background_type}",
            f"📐 Angle: {angle}",
            f"💡 Lighting: {lighting}",
            f"🔢 Generated: {batch_count} variation(s)",
            "",
            "📁 Results:"
        ]
        
        response_parts.extend(results)
        
        # Add metadata note
        response_parts.extend([
            "",
            "ℹ️ All images saved with metadata for easy organization.",
            "💡 Tip: Use batch_count > 1 for A/B testing different variations."
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error in generate_product_image: {str(e)}", exc_info=True)
        return f"❌ Error generating product image: {str(e)}"

@mcp.tool()
def generate_ui_asset(
    asset_type: str,
    description: str,
    dimensions: str = "standard",
    theme: str = "auto",
    style_preset: str = "flat",
    export_formats: Optional[str] = "png"
) -> str:
    """
    Create UI/UX design assets optimized for web and app interfaces.
    
    When to use: Web/app design, UI components, interface elements
    Optimizes for web performance with proper naming conventions.
    
    Args:
        asset_type: "icon" | "illustration" | "hero" | "background"
        description: Detailed description of the asset
        dimensions: "standard" | custom like "512x512" (default: "standard")
        theme: "light" | "dark" | "auto" (default: "auto")
        style_preset: "flat" | "gradient" | "3d" | "outline" (default: "flat")
        export_formats: "png" | "svg" | "webp" | "png,webp" (default: "png")
    
    Examples:
    - App icon: generate_ui_asset("icon", "shopping cart with rounded corners", style_preset="flat")
    - Hero image: generate_ui_asset("hero", "modern dashboard interface", dimensions="1200x600", theme="dark")
    - Background: generate_ui_asset("background", "subtle geometric pattern", style_preset="gradient")
    """
    logger.info(f"MCP TOOL CALLED: generate_ui_asset - {asset_type}: '{description}'")
    
    try:
        # Validate parameters
        valid_asset_types = ["icon", "illustration", "hero", "background"]
        if asset_type not in valid_asset_types:
            return f"❌ Error: Invalid asset_type '{asset_type}'. Choose from: {', '.join(valid_asset_types)}"
            
        valid_themes = ["light", "dark", "auto"]
        if theme not in valid_themes:
            return f"❌ Error: Invalid theme '{theme}'. Choose from: {', '.join(valid_themes)}"
            
        valid_styles = ["flat", "gradient", "3d", "outline"]
        if style_preset not in valid_styles:
            return f"❌ Error: Invalid style_preset '{style_preset}'. Choose from: {', '.join(valid_styles)}"
        
        # Get helper instances
        organizer = get_file_organizer()
        
        # Determine optimal dimensions based on asset type
        size_map = {
            "icon": "512x512",
            "illustration": "1024x1024", 
            "hero": "1200x600",
            "background": "1920x1080"
        }
        
        if dimensions == "standard":
            selected_dimensions = size_map[asset_type]
        else:
            selected_dimensions = dimensions
            
        # Build optimized prompt for UI/UX design
        prompt_parts = []
        
        # Asset type specific prompting
        if asset_type == "icon":
            prompt_parts.append(f"Clean, minimalist {asset_type} design of {description}")
            prompt_parts.append("vector-style, simple shapes, clear silhouette")
        elif asset_type == "illustration":
            prompt_parts.append(f"Modern UI illustration of {description}")
            prompt_parts.append("clean lines, digital art style")
        elif asset_type == "hero":
            prompt_parts.append(f"Hero section image showing {description}")
            prompt_parts.append("modern web design, professional layout")
        elif asset_type == "background":
            prompt_parts.append(f"UI background pattern or texture: {description}")
            prompt_parts.append("subtle, non-distracting, tileable")
            
        # Style preset application
        style_descriptions = {
            "flat": "flat design, solid colors, no shadows or depth",
            "gradient": "modern gradients, smooth color transitions",
            "3d": "subtle 3D effects, depth and dimension",
            "outline": "outline style, line art, minimal fills"
        }
        prompt_parts.append(style_descriptions[style_preset])
        
        # Theme application
        if theme == "light":
            prompt_parts.append("light theme, bright colors, white/light backgrounds")
        elif theme == "dark":
            prompt_parts.append("dark theme, dark colors, black/dark backgrounds")
        
        # Technical specifications for UI assets
        prompt_parts.extend([
            "pixel-perfect, crisp edges, web-optimized",
            "professional UI design, modern aesthetic",
            "scalable design, clean composition"
        ])
        
        if asset_type == "icon":
            prompt_parts.append("transparent background, centered, padding around edges")
            
        final_prompt = ", ".join(prompt_parts)
        logger.info(f"Generated UI asset prompt: {final_prompt}")
        
        # Generate save path for organized storage
        save_path = organizer.get_save_path(
            use_case="ui",
            filename_prefix=f"{asset_type}_{style_preset}",
            file_format="png",
            asset_type=asset_type
        )
        
        # Use generate_image with UI-optimized settings
        result = generate_image(
            prompt=final_prompt,
            model="gpt-image-1",  # Best for clean graphics
            quality="medium",     # Balanced for UI assets
            size=selected_dimensions,
            background="transparent" if asset_type == "icon" else "auto",
            format="png",
            save_path=save_path,
            n=1
        )
        
        # Create response with UI-specific information
        response_parts = [
            f"🎨 UI asset generated successfully!",
            f"📱 Type: {asset_type}",
            f"📏 Dimensions: {selected_dimensions}",
            f"🎭 Style: {style_preset}",
            f"🌓 Theme: {theme}",
            "",
            f"📁 Result: {result}",
            "",
            "💡 UI Asset Tips:",
            "• Icons work best with transparent backgrounds",
            "• Heroes should use landscape dimensions (1200x600 or wider)", 
            "• Backgrounds should be subtle to not interfere with content",
            "• Use flat or outline styles for modern web interfaces"
        ]
        
        # Handle multiple export formats if requested
        export_list = [fmt.strip() for fmt in export_formats.split(",")]
        if len(export_list) > 1:
            response_parts.extend([
                "",
                f"🔄 Additional formats requested: {', '.join(export_list[1:])}",
                "💡 Tip: PNG generated. For SVG, consider using design tools for vector conversion."
            ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error in generate_ui_asset: {str(e)}", exc_info=True)
        return f"❌ Error generating UI asset: {str(e)}"

@mcp.tool()
def batch_generate(
    prompts: str,
    variations_per_prompt: int = 1,
    consistent_style: str = "",
    model: str = "auto",
    output_folder: Optional[str] = None
) -> str:
    """
    Efficient bulk image generation with cost optimization and progress tracking.
    
    When to use: Multiple related images, A/B testing, content series
    Cost-optimized batch processing with organized output.
    
    Args:
        prompts: JSON array of prompts or newline-separated prompts
        variations_per_prompt: 1-3 variations per prompt (default: 1)
        consistent_style: Style to maintain across all images
        model: "auto" | "gpt-image-1" | "dall-e-3" | "dall-e-2" (default: "auto")
        output_folder: Custom folder name (default: auto-generated)
    
    Examples:
    - Multiple concepts: batch_generate('["red car", "blue car", "green car"]', variations_per_prompt=2)
    - Style series: batch_generate('["cat", "dog", "bird"]', consistent_style="watercolor painting")
    - A/B testing: batch_generate('["product on white background", "product in lifestyle setting"]', variations_per_prompt=3)
    """
    logger.info(f"MCP TOOL CALLED: batch_generate")
    
    try:
        # Parse prompts input
        import json
        
        if prompts.strip().startswith('['):
            # JSON array format
            try:
                prompt_list = json.loads(prompts)
            except json.JSONDecodeError:
                return f"❌ Error: Invalid JSON format in prompts. Use format: [\"prompt1\", \"prompt2\"]"
        else:
            # Newline-separated format
            prompt_list = [p.strip() for p in prompts.split('\n') if p.strip()]
            
        if not prompt_list:
            return f"❌ Error: No prompts provided"
            
        if len(prompt_list) > 10:
            return f"❌ Error: Maximum 10 prompts allowed per batch. Received {len(prompt_list)}"
            
        if not (1 <= variations_per_prompt <= 3):
            return f"❌ Error: variations_per_prompt must be between 1 and 3"
        
        # Get helper instances
        selector = get_model_selector()
        organizer = get_file_organizer()
        
        # Generate batch ID for organization
        from datetime import datetime
        batch_id = datetime.now().strftime('batch_%Y%m%d_%H%M%S')
        if output_folder:
            batch_id = output_folder
            
        # Select model with batch optimization
        config = selector.select_model_and_params(
            use_case="batch",
            model=model,
            budget_conscious=True  # Optimize for cost in batch operations
        )
        
        selected_model = config["model"]
        selected_quality = config["quality"]
        
        # Calculate total images and cost estimate
        total_images = len(prompt_list) * variations_per_prompt
        cost_info = selector.estimate_cost(selected_model, selected_quality, "1024x1024", total_images)
        
        logger.info(f"Batch generation: {len(prompt_list)} prompts × {variations_per_prompt} variations = {total_images} images")
        logger.info(f"Selected model: {selected_model}, Cost level: {cost_info['cost_level']}")
        
        # Process each prompt
        results = []
        failed_count = 0
        
        for i, base_prompt in enumerate(prompt_list):
            # Apply consistent style if specified
            if consistent_style:
                final_prompt = f"{base_prompt}, {consistent_style}"
            else:
                final_prompt = base_prompt
                
            logger.info(f"Processing prompt {i+1}/{len(prompt_list)}: {final_prompt}")
            
            # Generate variations for this prompt
            for var in range(variations_per_prompt):
                try:
                    # Generate save path
                    save_path = organizer.get_save_path(
                        use_case="batch",
                        filename_prefix=f"prompt{i+1:02d}_var{var+1}",
                        file_format="png",
                        batch_id=batch_id
                    )
                    
                    # Generate image
                    result = generate_image(
                        prompt=final_prompt,
                        model=selected_model,
                        quality=selected_quality,
                        size="1024x1024",
                        save_path=save_path,
                        n=1
                    )
                    
                    results.append({
                        "prompt_index": i + 1,
                        "variation": var + 1,
                        "prompt": base_prompt,
                        "final_prompt": final_prompt,
                        "result": "success",
                        "details": result
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to generate image for prompt {i+1}, variation {var+1}: {e}")
                    failed_count += 1
                    results.append({
                        "prompt_index": i + 1,
                        "variation": var + 1,
                        "prompt": base_prompt,
                        "result": "failed",
                        "error": str(e)
                    })
        
        # Create summary response
        successful_count = total_images - failed_count
        
        response_parts = [
            f"🚀 Batch generation completed!",
            f"📊 Summary: {successful_count}/{total_images} images generated successfully",
            f"📁 Batch ID: {batch_id}",
            f"🤖 Model: {selected_model}",
            f"⚡ Quality: {selected_quality}",
            f"💰 Cost Level: {cost_info['cost_level']} ({cost_info['cost_type']})",
            ""
        ]
        
        if consistent_style:
            response_parts.append(f"🎨 Consistent Style: {consistent_style}")
            response_parts.append("")
        
        # Add detailed results
        response_parts.append("📋 Detailed Results:")
        for result in results:
            if result["result"] == "success":
                response_parts.append(f"✅ Prompt {result['prompt_index']}.{result['variation']}: {result['prompt']}")
            else:
                response_parts.append(f"❌ Prompt {result['prompt_index']}.{result['variation']}: {result['prompt']} - {result['error']}")
        
        if failed_count > 0:
            response_parts.extend([
                "",
                f"⚠️ {failed_count} images failed to generate. Check logs for details.",
                "💡 Tip: Simplify complex prompts or try a different model for better success rates."
            ])
        
        response_parts.extend([
            "",
            f"📂 All images saved to: generated_images/batch_generations/{batch_id}/",
            "💡 Tip: Use consistent_style parameter to maintain visual coherence across the batch."
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error in batch_generate: {str(e)}", exc_info=True)
        return f"❌ Error in batch generation: {str(e)}"

@mcp.tool()
def analyze_and_regenerate(
    image_path: str,
    requirements: str,
    preserve_elements: str = "",
    max_iterations: int = 3
) -> str:
    """
    Iterative image improvement based on requirements with structured feedback loop.
    
    When to use: When initial results need refinement
    Provides cost-aware iteration limiting with analysis feedback.
    
    Args:
        image_path: Path to current image that needs improvement
        requirements: What needs to be improved or changed
        preserve_elements: Elements that should be kept unchanged
        max_iterations: Maximum improvement iterations (1-5, default: 3)
    
    Examples:
    - Improve quality: analyze_and_regenerate("draft.png", "make more professional and polished")
    - Fix issues: analyze_and_regenerate("logo.png", "text needs to be more readable", preserve_elements="colors and overall design")
    - Style adjustment: analyze_and_regenerate("portrait.png", "make it more artistic and painterly")
    """
    logger.info(f"MCP TOOL CALLED: analyze_and_regenerate for '{image_path}'")
    
    try:
        # Validate inputs
        if not os.path.exists(image_path):
            return f"❌ Error: Image file not found: {image_path}"
            
        if not (1 <= max_iterations <= 5):
            return f"❌ Error: max_iterations must be between 1 and 5"
            
        # Get helper instances
        organizer = get_file_organizer()
        
        # Load metadata from original image if available
        metadata_path = f"{os.path.splitext(image_path)[0]}_metadata.json"
        original_metadata = {}
        if os.path.exists(metadata_path):
            try:
                import json
                with open(metadata_path, 'r') as f:
                    original_metadata = json.load(f)
                logger.info(f"Loaded original metadata from {metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
        
        # Extract original prompt if available
        original_prompt = original_metadata.get("original_prompt", "")
        if not original_prompt:
            return f"❌ Error: Cannot find original prompt for iterative improvement. Original image metadata required."
        
        current_image_path = image_path
        iteration_results = []
        
        for iteration in range(max_iterations):
            logger.info(f"Starting iteration {iteration + 1}/{max_iterations}")
            
            # Build improvement prompt
            improvement_parts = []
            
            if iteration == 0:
                improvement_parts.append(f"Improve this image: {original_prompt}")
            else:
                improvement_parts.append(f"Further improve this image based on previous iteration")
                
            improvement_parts.append(f"Requirements: {requirements}")
            
            if preserve_elements:
                improvement_parts.append(f"Preserve these elements: {preserve_elements}")
                
            # Add technical improvement instructions
            improvement_parts.extend([
                "higher quality, more professional",
                "better composition and lighting",
                "enhanced details and clarity"
            ])
            
            improvement_prompt = ", ".join(improvement_parts)
            
            # Generate save path for this iteration
            iteration_save_path = organizer.get_save_path(
                use_case="edit",
                filename_prefix=f"improved_iter{iteration+1}",
                file_format="png"
            )
            
            try:
                # Use edit_image_advanced for iterative improvement
                edit_result = edit_image_advanced(
                    image_path=current_image_path,
                    prompt=improvement_prompt,
                    mode="style_transfer",
                    save_path=iteration_save_path
                )
                
                # Check if edit was successful
                if "✅" in edit_result and os.path.exists(iteration_save_path):
                    iteration_results.append({
                        "iteration": iteration + 1,
                        "status": "success",
                        "image_path": iteration_save_path,
                        "prompt": improvement_prompt,
                        "result": edit_result
                    })
                    
                    # Update current image for next iteration
                    current_image_path = iteration_save_path
                    
                    # Save iteration metadata
                    iteration_metadata = {
                        **original_metadata,
                        "improvement_iteration": iteration + 1,
                        "improvement_requirements": requirements,
                        "preserve_elements": preserve_elements,
                        "improvement_prompt": improvement_prompt,
                        "original_image": image_path,
                        "previous_iteration": current_image_path if iteration > 0 else image_path
                    }
                    organizer.save_image_metadata(iteration_save_path, iteration_metadata)
                    
                else:
                    # Failed iteration
                    iteration_results.append({
                        "iteration": iteration + 1,
                        "status": "failed",
                        "error": edit_result,
                        "prompt": improvement_prompt
                    })
                    logger.error(f"Iteration {iteration + 1} failed: {edit_result}")
                    break
                    
            except Exception as e:
                iteration_results.append({
                    "iteration": iteration + 1,
                    "status": "failed", 
                    "error": str(e),
                    "prompt": improvement_prompt
                })
                logger.error(f"Exception in iteration {iteration + 1}: {e}")
                break
        
        # Create comprehensive response
        successful_iterations = [r for r in iteration_results if r["status"] == "success"]
        failed_iterations = [r for r in iteration_results if r["status"] == "failed"]
        
        response_parts = [
            f"🔄 Iterative improvement completed!",
            f"📈 Successful iterations: {len(successful_iterations)}/{len(iteration_results)}",
            f"🖼️ Original image: {image_path}",
            f"🎯 Requirements: {requirements}",
        ]
        
        if preserve_elements:
            response_parts.append(f"🔒 Preserved: {preserve_elements}")
            
        response_parts.append("")
        
        # Add iteration details
        response_parts.append("📋 Iteration Results:")
        for result in iteration_results:
            if result["status"] == "success":
                response_parts.append(f"✅ Iteration {result['iteration']}: {result['image_path']}")
            else:
                response_parts.append(f"❌ Iteration {result['iteration']}: {result['error']}")
                
        if successful_iterations:
            final_image = successful_iterations[-1]["image_path"]
            response_parts.extend([
                "",
                f"🎉 Final improved image: {final_image}",
                f"📊 Total improvements: {len(successful_iterations)} iterations"
            ])
        else:
            response_parts.extend([
                "",
                "❌ No successful iterations. Try simplifying requirements or using a different approach."
            ])
            
        response_parts.extend([
            "",
            "💡 Tips for better results:",
            "• Be specific about what needs improvement",
            "• Use preserve_elements to maintain good aspects",
            "• Lower max_iterations for cost control"
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error in analyze_and_regenerate: {str(e)}", exc_info=True)
        return f"❌ Error in iterative improvement: {str(e)}"

@mcp.tool()
def get_usage_guide() -> str:
    """
    Retrieve comprehensive LLM usage guidelines and tool selection advice.
    
    When to use: When you need guidance on tool selection, usage patterns, or best practices
    
    This tool returns the complete LLM usage guide including:
    - Quick decision tree for tool selection
    - Parameter recommendations and examples
    - Model selection guidelines
    - Cost optimization tips
    - Common patterns and best practices
    
    Use this tool when:
    - Starting with the image generation tools
    - Unsure which tool to use for a specific task
    - Need parameter recommendations
    - Want to optimize for cost or quality
    - Looking for usage examples
    """
    logger.info("MCP TOOL CALLED: get_usage_guide")
    
    try:
        # Read the LLM.md file directly for single source of truth
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(os.path.dirname(script_dir))
        llm_guide_path = os.path.join(workspace_root, "LLM.md")
        
        with open(llm_guide_path, 'r', encoding='utf-8') as f:
            guide_content = f.read()
            
        logger.info(f"Successfully loaded LLM usage guide from {llm_guide_path}")
        return guide_content
            
    except FileNotFoundError:
        logger.error(f"LLM.md file not found at {llm_guide_path}")
        return f"❌ Error: LLM usage guide file not found. Please ensure LLM.md exists in the project root."
    except Exception as e:
        logger.error(f"Error in get_usage_guide: {str(e)}", exc_info=True)
        return f"❌ Error retrieving usage guide: {str(e)}"

def main():
    logger.info("Main function started. Basic logging to stderr is active.")

    if not os.getenv("OPENAI_API_KEY"):
        logger.error("CRITICAL_MAIN: OPENAI_API_KEY environment variable is required. Server cannot start.")
        return
    
    logger.info("Starting OpenAI Image MCP Server with FastMCP...")
    
    try:
        mcp.run(transport="stdio")
    except Exception as e_mcp_run:
        logger.critical(f"CRITICAL_ERROR_MCP_RUN: mcp.run() failed catastrophically: {e_mcp_run}", exc_info=True)
        # This error will go to stderr, which should be redirected.
        raise 
    finally:
        logger.info("MCP server mcp.run() has exited or an unhandled exception occurred if not caught above.")

if __name__ == "__main__":
    logger.info("Script execution started (__main__).") 
    main()