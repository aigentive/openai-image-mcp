"""Main MCP server implementation for OpenAI conversational image generation using Responses API."""

import logging
import os
import sys
import json
from typing import Optional, Dict, Any

from mcp.server import FastMCP
from dotenv import load_dotenv

from .session_manager import SessionManager, ImageSession
from .responses_client import ResponsesAPIClient
from .conversation_builder import ConversationBuilder
from .image_processor import ImageProcessor
from .file_organizer import FileOrganizer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)],
    force=True
)

logger = logging.getLogger(__name__)
logger.info("Conversational Image MCP Server initializing...")

# Create FastMCP server
mcp = FastMCP("openai-image-mcp")

# Global instances
session_manager: Optional[SessionManager] = None
responses_client: Optional[ResponsesAPIClient] = None
conversation_builder: Optional[ConversationBuilder] = None
image_processor: Optional[ImageProcessor] = None
file_organizer: Optional[FileOrganizer] = None


def get_session_manager() -> SessionManager:
    """Get or create session manager instance."""
    global session_manager
    if session_manager is None:
        max_sessions = int(os.getenv("MCP_MAX_SESSIONS", "100"))
        session_timeout = int(os.getenv("MCP_SESSION_TIMEOUT", "3600")) // 3600  # Convert to hours
        session_manager = SessionManager(max_sessions=max_sessions, session_timeout_hours=session_timeout)
        logger.info("SessionManager initialized")
    return session_manager


def get_responses_client() -> ResponsesAPIClient:
    """Get or create responses client instance."""
    global responses_client
    if responses_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("CRITICAL: OPENAI_API_KEY environment variable is required")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        responses_client = ResponsesAPIClient(api_key=api_key)
        logger.info("ResponsesAPIClient initialized")
    return responses_client


def get_conversation_builder() -> ConversationBuilder:
    """Get or create conversation builder instance."""
    global conversation_builder
    if conversation_builder is None:
        conversation_builder = ConversationBuilder()
        logger.info("ConversationBuilder initialized")
    return conversation_builder


def get_file_organizer() -> FileOrganizer:
    """Get or create file organizer instance."""
    global file_organizer
    if file_organizer is None:
        # Auto-detect workspace root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(os.path.dirname(script_dir))
        file_organizer = FileOrganizer(workspace_root=workspace_root)
        logger.info("FileOrganizer initialized")
    return file_organizer


def get_image_processor() -> ImageProcessor:
    """Get or create image processor instance."""
    global image_processor
    if image_processor is None:
        image_processor = ImageProcessor(
            file_organizer=get_file_organizer(),
            responses_client=get_responses_client()
        )
        logger.info("ImageProcessor initialized")
    return image_processor


# Session Management MCP Tools

@mcp.tool()
def create_image_session(
    description: str,
    model: str = "gpt-4o",
    session_name: Optional[str] = None
) -> Dict[str, Any]:
    """Create new conversational image generation session.
    
    Args:
        description: Initial description/context for the session
        model: OpenAI model to use (gpt-4o, gpt-4.1, gpt-4o-mini)
        session_name: Optional human-readable name
        
    Returns:
        {
            "session_id": "uuid-string",
            "model": "gpt-4o", 
            "created_at": "2025-05-25T10:00:00Z",
            "status": "active"
        }
    """
    try:
        logger.info(f"Creating image session with model {model}")
        
        manager = get_session_manager()
        session = manager.create_session(
            description=description,
            model=model,
            session_name=session_name
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "model": session.model,
            "created_at": session.created_at.isoformat(),
            "status": "active",
            "session_name": session.session_name,
            "description": description
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "session_creation_error"
        }


@mcp.tool()
def generate_image_in_session(
    session_id: str,
    prompt: str,
    reference_image_path: Optional[str] = None,
    mask_image_path: Optional[str] = None,
    quality: str = "auto",
    size: str = "auto",
    background: str = "auto"
) -> Dict[str, Any]:
    """Generate image within existing session context.
    
    Args:
        session_id: UUID of existing session
        prompt: Generation/editing instruction
        reference_image_path: Path to reference image for editing
        mask_image_path: Path to mask for inpainting (requires reference_image_path)
        quality: Image quality (low, medium, high, auto)
        size: Image size (1024x1024, 1536x1024, 1024x1536, auto)
        background: Background type (transparent, auto)
        
    Returns:
        {
            "success": true,
            "image_path": "/organized/path/to/image.png",
            "image_generation_id": "ig_123",
            "revised_prompt": "Enhanced prompt used",
            "metadata": {...},
            "session_context": "Brief summary of what happened"
        }
    """
    try:
        logger.info(f"Generating image in session {session_id}")
        
        # Get session
        manager = get_session_manager()
        session = manager.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "error_type": "session_not_found",
                "available_sessions": [s.session_id for s in manager.list_active_sessions()]
            }
        
        # Update session activity
        manager.update_activity(session_id)
        
        # Build user input
        builder = get_conversation_builder()
        user_input = builder.build_user_input_from_params(
            prompt=prompt,
            reference_image_path=reference_image_path,
            mask_image_path=mask_image_path
        )
        
        # Prepare tools configuration
        tools_config = {
            "quality": quality,
            "size": size,
            "background": background
        }
        
        # Handle mask image if provided
        if mask_image_path:
            if not reference_image_path:
                return {
                    "success": False,
                    "error": "mask_image_path requires reference_image_path",
                    "error_type": "invalid_parameters"
                }
            
            try:
                processor = get_image_processor()
                mask_validation = processor.validate_image_file(mask_image_path)
                if not mask_validation["valid"]:
                    return {
                        "success": False,
                        "error": f"Invalid mask image: {mask_validation['errors']}",
                        "error_type": "invalid_mask_image"
                    }
                
                # Upload mask to OpenAI Files API
                client = get_responses_client()
                mask_file_id = client.create_file_from_path(mask_image_path)
                tools_config["mask_file_id"] = mask_file_id
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to process mask image: {str(e)}",
                    "error_type": "mask_processing_error"
                }
        
        # Add conversation turn
        manager.add_conversation_turn(session_id, "user", user_input)
        
        # Make API call
        client = get_responses_client()
        api_result = client.generate_with_conversation(session, user_input, tools_config)
        
        if not api_result["success"]:
            return {
                "success": False,
                "error": api_result["error"],
                "error_type": api_result["error_type"],
                "retryable": api_result.get("retryable", False)
            }
        
        # Process generation results
        generation_calls = api_result["generation_calls"]
        if not generation_calls:
            return {
                "success": False,
                "error": "No images generated",
                "error_type": "no_generation_result"
            }
        
        # Process the first generation call
        processor = get_image_processor()
        generation_call = processor.process_generation_result(
            generation_calls[0], 
            session,
            use_case="general"
        )
        
        # Add to session
        manager.add_generated_image(session_id, generation_call)
        
        # Add assistant response to conversation
        assistant_content = builder.format_assistant_response([generation_call])
        manager.add_conversation_turn(session_id, "assistant", assistant_content)
        
        # Build response
        session_context = f"Generated image {len(session.generated_images)} in conversation with {len(session.conversation_history)} turns"
        
        return {
            "success": True,
            "image_path": generation_call.image_path,
            "image_generation_id": generation_call.id,
            "revised_prompt": generation_call.revised_prompt,
            "original_prompt": generation_call.prompt,
            "metadata": {
                "session_id": session_id,
                "model": session.model,
                "generation_params": generation_call.generation_params,
                "created_at": generation_call.created_at.isoformat()
            },
            "session_context": session_context
        }
        
    except Exception as e:
        logger.error(f"Failed to generate image in session {session_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "generation_error"
        }


@mcp.tool()
def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get current session status and recent activity.
    
    Returns:
        {
            "session_id": "uuid",
            "active": true,
            "created_at": "timestamp",
            "last_activity": "timestamp", 
            "model": "gpt-4o",
            "total_generations": 5,
            "recent_images": ["path1", "path2"],
            "conversation_summary": "Brief context summary"
        }
    """
    try:
        manager = get_session_manager()
        summary = manager.get_session_summary(session_id)
        
        if not summary:
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "error_type": "session_not_found",
                "available_sessions": [s.session_id for s in manager.list_active_sessions()]
            }
        
        return {
            "success": True,
            **summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get session status for {session_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "status_error"
        }


@mcp.tool()
def list_active_sessions() -> Dict[str, Any]:
    """List all active sessions.
    
    Returns:
        {
            "sessions": [
                {
                    "session_id": "uuid",
                    "session_name": "Logo Design Session",
                    "created_at": "timestamp",
                    "last_activity": "timestamp",
                    "total_generations": 3
                }
            ],
            "total_active": 5
        }
    """
    try:
        manager = get_session_manager()
        sessions = manager.list_active_sessions()
        
        session_summaries = []
        for session in sessions:
            session_summaries.append({
                "session_id": session.session_id,
                "session_name": session.session_name,
                "description": session.description,
                "model": session.model,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "total_generations": len(session.generated_images)
            })
        
        return {
            "success": True,
            "sessions": session_summaries,
            "total_active": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list active sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "list_error"
        }


@mcp.tool()
def close_session(session_id: str) -> Dict[str, Any]:
    """Close session and clean up resources.
    
    Returns:
        {
            "status": "closed",
            "session_id": "uuid",
            "final_image_count": "5"
        }
    """
    try:
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "error_type": "session_not_found"
            }
        
        final_image_count = len(session.generated_images)
        
        # Clean up session resources
        processor = get_image_processor()
        processor.cleanup_temp_files(session)
        
        # Close session
        success = manager.close_session(session_id)
        
        if success:
            return {
                "success": True,
                "status": "closed",
                "session_id": session_id,
                "final_image_count": str(final_image_count)
            }
        else:
            return {
                "success": False,
                "error": "Failed to close session",
                "error_type": "close_error"
            }
        
    except Exception as e:
        logger.error(f"Failed to close session {session_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "close_error"
        }


# Simplified Generation Tools (Session-Optional)

@mcp.tool()
def generate_image(
    prompt: str,
    session_id: Optional[str] = None,
    model: str = "gpt-4o",
    quality: str = "auto",
    size: str = "auto",
    background: str = "auto",
    use_case: str = "general"
) -> Dict[str, Any]:
    """Generate image with optional session context.
    
    If session_id provided, uses session context. Otherwise creates single-shot generation.
    
    Args:
        prompt: Text prompt for image generation
        session_id: Optional UUID of existing session for context
        model: OpenAI model to use (gpt-4o, gpt-4.1, gpt-4o-mini)
        quality: Image quality (low, medium, high, auto)
        size: Image size (1024x1024, 1536x1024, 1024x1536, auto)
        background: Background type (transparent, auto)
        use_case: Use case for file organization (general, product, ui, etc.)
        
    Returns:
        Generation result with image path and metadata
    """
    try:
        if session_id:
            # Use existing session
            return generate_image_in_session(
                session_id=session_id,
                prompt=prompt,
                quality=quality,
                size=size,
                background=background
            )
        else:
            # Create temporary session for single-shot generation
            logger.info(f"Creating single-shot generation with model {model}")
            
            manager = get_session_manager()
            temp_session = manager.create_session(
                description=f"Single-shot generation: {prompt[:100]}...",
                model=model,
                session_name="Temporary Generation"
            )
            
            try:
                # Generate image in temporary session
                result = generate_image_in_session(
                    session_id=temp_session.session_id,
                    prompt=prompt,
                    quality=quality,
                    size=size,
                    background=background
                )
                
                # Add single-shot indicator to result
                if result.get("success"):
                    result["single_shot"] = True
                    result["temporary_session_id"] = temp_session.session_id
                
                return result
                
            finally:
                # Clean up temporary session
                manager.close_session(temp_session.session_id)
        
    except Exception as e:
        logger.error(f"Failed to generate image: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "generation_error"
        }


@mcp.tool()
def edit_image(
    image_path: str,
    prompt: str,
    session_id: Optional[str] = None,
    mask_path: Optional[str] = None,
    quality: str = "auto"
) -> Dict[str, Any]:
    """Edit existing image with optional session context.
    
    Args:
        image_path: Path to image file to edit
        prompt: Editing instruction
        session_id: Optional UUID of existing session for context
        mask_path: Optional path to mask for inpainting
        quality: Image quality (low, medium, high, auto)
        
    Returns:
        Edit result with new image path and metadata
    """
    try:
        # Validate input image
        processor = get_image_processor()
        validation = processor.validate_image_file(image_path)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Invalid input image: {validation['errors']}",
                "error_type": "invalid_input_image"
            }
        
        if session_id:
            # Use existing session
            return generate_image_in_session(
                session_id=session_id,
                prompt=prompt,
                reference_image_path=image_path,
                mask_image_path=mask_path,
                quality=quality
            )
        else:
            # Create temporary session for single-shot editing
            logger.info(f"Creating single-shot edit for {image_path}")
            
            manager = get_session_manager()
            temp_session = manager.create_session(
                description=f"Single-shot edit: {prompt[:100]}...",
                model="gpt-4o",
                session_name="Temporary Edit"
            )
            
            try:
                # Edit image in temporary session
                result = generate_image_in_session(
                    session_id=temp_session.session_id,
                    prompt=prompt,
                    reference_image_path=image_path,
                    mask_image_path=mask_path,
                    quality=quality
                )
                
                # Add single-shot indicator to result
                if result.get("success"):
                    result["single_shot"] = True
                    result["temporary_session_id"] = temp_session.session_id
                    result["original_image_path"] = image_path
                
                return result
                
            finally:
                # Clean up temporary session
                manager.close_session(temp_session.session_id)
        
    except Exception as e:
        logger.error(f"Failed to edit image: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "edit_error"
        }


# Specialized Image Generation Tools

@mcp.tool()
def generate_product_image(
    product_description: str,
    session_id: Optional[str] = None,
    background_type: str = "white",
    angle: str = "front",
    lighting: str = "studio",
    batch_count: int = 1
) -> Dict[str, Any]:
    """Generate product images with specialized parameters.
    
    Args:
        product_description: Description of the product
        session_id: Optional session for context
        background_type: Background type (white, transparent, lifestyle)
        angle: Product angle (front, side, three-quarter, top)
        lighting: Lighting setup (studio, natural, dramatic, soft)
        batch_count: Number of variations to generate (1-3)
        
    Returns:
        Product image generation results
    """
    try:
        # Validate parameters
        valid_backgrounds = ["white", "transparent", "lifestyle"]
        valid_angles = ["front", "side", "three-quarter", "top"]
        valid_lighting = ["studio", "natural", "dramatic", "soft"]
        
        if background_type not in valid_backgrounds:
            return {
                "success": False,
                "error": f"Invalid background_type '{background_type}'. Valid: {valid_backgrounds}",
                "error_type": "invalid_parameters"
            }
        
        if angle not in valid_angles:
            return {
                "success": False,
                "error": f"Invalid angle '{angle}'. Valid: {valid_angles}",
                "error_type": "invalid_parameters"
            }
        
        if lighting not in valid_lighting:
            return {
                "success": False,
                "error": f"Invalid lighting '{lighting}'. Valid: {valid_lighting}",
                "error_type": "invalid_parameters"
            }
        
        if not 1 <= batch_count <= 3:
            return {
                "success": False,
                "error": "batch_count must be between 1 and 3",
                "error_type": "invalid_parameters"
            }
        
        # Build specialized product prompt
        prompt_parts = [
            f"Professional product photography of {product_description}",
            f"{angle} view",
            f"{lighting} lighting"
        ]
        
        if background_type == "white":
            prompt_parts.append("clean white background")
        elif background_type == "transparent":
            prompt_parts.append("transparent background, isolated product")
        elif background_type == "lifestyle":
            prompt_parts.append("lifestyle setting, contextual background")
        
        prompt_parts.append("high quality, commercial photography style")
        
        final_prompt = ", ".join(prompt_parts)
        
        # Generate with appropriate settings
        background_setting = "transparent" if background_type == "transparent" else "auto"
        
        results = []
        for i in range(batch_count):
            result = generate_image(
                prompt=final_prompt,
                session_id=session_id,
                quality="high",
                size="1024x1024",
                background=background_setting,
                use_case="product"
            )
            results.append(result)
        
        return {
            "success": True,
            "product_description": product_description,
            "background_type": background_type,
            "angle": angle,
            "lighting": lighting,
            "batch_count": batch_count,
            "results": results,
            "summary": f"Generated {batch_count} product images with {background_type} background"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate product image: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "product_generation_error"
        }


@mcp.tool()
def generate_ui_asset(
    asset_type: str,
    description: str,
    session_id: Optional[str] = None,
    theme: str = "modern",
    style_preset: str = "flat",
    size_preset: str = "standard"
) -> Dict[str, Any]:
    """Generate UI assets like icons, illustrations, backgrounds.
    
    Args:
        asset_type: Type of asset (icon, illustration, background, hero)
        description: Description of the asset
        session_id: Optional session for context
        theme: Visual theme (modern, classic, minimal, playful)
        style_preset: Style preset (flat, 3d, outline, filled)
        size_preset: Size preset (small, standard, large)
        
    Returns:
        UI asset generation results
    """
    try:
        # Validate parameters
        valid_asset_types = ["icon", "illustration", "background", "hero"]
        valid_themes = ["modern", "classic", "minimal", "playful"]
        valid_styles = ["flat", "3d", "outline", "filled"]
        valid_sizes = ["small", "standard", "large"]
        
        if asset_type not in valid_asset_types:
            return {
                "success": False,
                "error": f"Invalid asset_type '{asset_type}'. Valid: {valid_asset_types}",
                "error_type": "invalid_parameters"
            }
        
        if theme not in valid_themes:
            return {
                "success": False,
                "error": f"Invalid theme '{theme}'. Valid: {valid_themes}",
                "error_type": "invalid_parameters"
            }
        
        if style_preset not in valid_styles:
            return {
                "success": False,
                "error": f"Invalid style_preset '{style_preset}'. Valid: {valid_styles}",
                "error_type": "invalid_parameters"
            }
        
        # Build specialized UI asset prompt
        prompt_parts = []
        
        if asset_type == "icon":
            prompt_parts.extend([
                f"{style_preset} style icon",
                f"{description}",
                f"{theme} design",
                "clean, professional, suitable for UI"
            ])
        elif asset_type == "illustration":
            prompt_parts.extend([
                f"{style_preset} illustration",
                f"{description}",
                f"{theme} style",
                "vector-style, clean lines"
            ])
        elif asset_type == "background":
            prompt_parts.extend([
                f"{theme} background pattern",
                f"{description}",
                f"{style_preset} design",
                "seamless, subtle, non-distracting"
            ])
        elif asset_type == "hero":
            prompt_parts.extend([
                f"hero image for {description}",
                f"{theme} style",
                f"{style_preset} design",
                "engaging, professional, web-ready"
            ])
        
        final_prompt = ", ".join(prompt_parts)
        
        # Set size based on preset and asset type
        size_map = {
            ("icon", "small"): "512x512",
            ("icon", "standard"): "1024x1024", 
            ("icon", "large"): "1024x1024",
            ("illustration", "small"): "1024x1024",
            ("illustration", "standard"): "1024x1024",
            ("illustration", "large"): "1536x1024",
            ("background", "small"): "1024x1024",
            ("background", "standard"): "1024x1024",
            ("background", "large"): "1536x1024",
            ("hero", "small"): "1536x1024",
            ("hero", "standard"): "1536x1024",
            ("hero", "large"): "1536x1024"
        }
        
        size = size_map.get((asset_type, size_preset), "1024x1024")
        
        # Generate with appropriate settings
        result = generate_image(
            prompt=final_prompt,
            session_id=session_id,
            quality="high",
            size=size,
            background="transparent" if asset_type in ["icon", "illustration"] else "auto",
            use_case="ui"
        )
        
        if result.get("success"):
            result.update({
                "asset_type": asset_type,
                "theme": theme,
                "style_preset": style_preset,
                "size_preset": size_preset,
                "ui_asset_summary": f"{style_preset} {asset_type} in {theme} theme"
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate UI asset: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "ui_asset_error"
        }


@mcp.tool()
def analyze_and_improve_image(
    image_path: str,
    improvement_goals: str,
    session_id: Optional[str] = None,
    preserve_elements: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze existing image and generate improved version.
    
    Args:
        image_path: Path to image to analyze and improve
        improvement_goals: What aspects to improve (quality, composition, style, etc.)
        session_id: Optional session for context
        preserve_elements: Elements to preserve during improvement
        
    Returns:
        Analysis and improvement results
    """
    try:
        # Validate input image
        processor = get_image_processor()
        validation = processor.validate_image_file(image_path)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Invalid input image: {validation['errors']}",
                "error_type": "invalid_input_image"
            }
        
        # Build improvement prompt
        prompt_parts = [
            f"Improve this image by {improvement_goals}",
            "maintain the core subject and composition"
        ]
        
        if preserve_elements:
            prompt_parts.append(f"preserve the {preserve_elements}")
        
        prompt_parts.extend([
            "enhance quality and visual appeal",
            "professional result"
        ])
        
        final_prompt = ", ".join(prompt_parts)
        
        # Use edit_image function
        result = edit_image(
            image_path=image_path,
            prompt=final_prompt,
            session_id=session_id,
            quality="high"
        )
        
        if result.get("success"):
            result.update({
                "improvement_goals": improvement_goals,
                "preserved_elements": preserve_elements,
                "analysis_summary": f"Improved {improvement_goals} while preserving {preserve_elements or 'original composition'}"
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze and improve image: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "improvement_error"
        }


# Server statistics and management

@mcp.tool()
def get_usage_guide() -> Dict[str, Any]:
    """Get comprehensive usage guide for the image generation tools.
    
    Returns:
        Complete usage guide with examples and best practices
    """
    try:
        # Read the LLM.md file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(os.path.dirname(script_dir))
        guide_path = os.path.join(workspace_root, "LLM.md")
        
        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_content = f.read()
            
            return {
                "success": True,
                "version": "latest",
                "architecture": "Session-based Conversational Image Generation",
                "guide_content": guide_content,
                "last_updated": "May 25, 2025",
                "total_tools": 11,
                "key_features": [
                    "Multi-turn conversational sessions",
                    "Advanced model access (GPT-4o, GPT-4.1)",
                    "Context-aware image refinement", 
                    "Organized file storage",
                    "Reference image editing",
                    "Specialized tools for products and UI"
                ],
                "quick_start": {
                    "session_workflow": [
                        "create_image_session('Project description')",
                        "generate_image_in_session(session_id, 'initial prompt')",
                        "generate_image_in_session(session_id, 'refinement')",
                        "close_session(session_id)"
                    ],
                    "single_shot": [
                        "generate_image('description')",
                        "edit_image('/path/to/image.png', 'changes')",
                        "generate_product_image('product description')"
                    ]
                }
            }
        else:
            return {
                "success": False,
                "error": "Usage guide file not found",
                "error_type": "file_not_found"
            }
            
    except Exception as e:
        logger.error(f"Failed to get usage guide: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "guide_error"
        }


@mcp.tool()
def promote_image_to_session(image_path: str, session_description: str, session_name: Optional[str] = None) -> Dict[str, Any]:
    """Promote a one-shot generated image to a new conversational session.
    
    This creates a new session and reconstructs the conversation context from the image's
    metadata, allowing you to continue refining the image with full conversational context.
    
    Args:
        image_path: Path to the image to promote (must have metadata)
        session_description: Description for the new session
        session_name: Optional friendly name for the session
        
    Returns:
        {
            "success": true,
            "session_id": "new-session-uuid",
            "session_name": "Logo Design Session",
            "original_context": {
                "prompt": "original prompt",
                "model": "gpt-4o",
                "generation_params": {...}
            },
            "ready_for_refinement": true
        }
    """
    try:
        # Validate image exists
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"Image not found: {image_path}",
                "error_type": "image_not_found"
            }
        
        # Load image metadata
        organizer = get_file_organizer()
        metadata_path = image_path.replace('.png', '_metadata.json').replace('.jpg', '_metadata.json').replace('.jpeg', '_metadata.json')
        
        if not os.path.exists(metadata_path):
            return {
                "success": False,
                "error": f"Image metadata not found. Cannot promote images without generation context.",
                "error_type": "metadata_not_found",
                "help": "Only images generated by this server can be promoted to sessions"
            }
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read metadata: {str(e)}",
                "error_type": "metadata_read_error"
            }
        
        # Extract original context
        original_prompt = metadata.get('original_prompt') or metadata.get('prompt')
        if not original_prompt:
            return {
                "success": False,
                "error": "No original prompt found in metadata",
                "error_type": "incomplete_metadata"
            }
        
        # Create new session
        manager = get_session_manager()
        session = manager.create_session(
            description=session_description,
            model=metadata.get('model', 'gpt-4o'),
            session_name=session_name
        )
        
        # Reconstruct conversation context
        builder = get_conversation_builder()
        
        # Add the original generation as conversation history
        original_user_input = builder.build_user_input_from_params(prompt=original_prompt)
        manager.add_conversation_turn(session.session_id, "user", original_user_input)
        
        # Create ImageGenerationCall from metadata
        from .session_manager import ImageGenerationCall
        import uuid
        from datetime import datetime
        
        generation_call = ImageGenerationCall(
            id=str(uuid.uuid4()),
            prompt=original_prompt,
            revised_prompt=metadata.get('revised_prompt', original_prompt),
            image_path=image_path,
            generation_params=metadata.get('generation_params', {}),
            created_at=datetime.fromisoformat(metadata.get('created_at', datetime.now().isoformat()))
        )
        
        # Add to session
        manager.add_generated_image(session.session_id, generation_call)
        
        # Add assistant response to conversation
        assistant_content = builder.format_assistant_response([generation_call])
        manager.add_conversation_turn(session.session_id, "assistant", assistant_content)
        
        logger.info(f"Promoted image {image_path} to session {session.session_id}")
        
        return {
            "success": True,
            "session_id": session.session_id,
            "session_name": session.session_name or session_description,
            "session_description": session.description,
            "original_context": {
                "prompt": original_prompt,
                "revised_prompt": metadata.get('revised_prompt'),
                "model": metadata.get('model'),
                "generation_params": metadata.get('generation_params', {}),
                "created_at": metadata.get('created_at')
            },
            "promoted_image": {
                "path": image_path,
                "generation_id": generation_call.id
            },
            "ready_for_refinement": True,
            "next_steps": [
                f"Use generate_image_in_session('{session.session_id}', 'make it more...') to refine",
                f"Use get_session_status('{session.session_id}') to check progress",
                f"Use close_session('{session.session_id}') when done"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to promote image to session: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "promotion_error"
        }


@mcp.tool()
def get_server_stats() -> Dict[str, Any]:
    """Get server statistics and status.
    
    Returns:
        Server statistics including active sessions, memory usage, etc.
    """
    try:
        manager = get_session_manager()
        stats = manager.get_stats()
        
        return {
            "success": True,
            "server_version": "latest-responses-api",
            "api_type": "OpenAI Responses API",
            **stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get server stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "stats_error"
        }


def main():
    """Main entry point for the MCP server."""
    try:
        # Validate environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("CRITICAL_MAIN: OPENAI_API_KEY environment variable is required. Server cannot start.")
            return
        
        logger.info("Starting OpenAI Image MCP Server with Responses API")
        
        # Initialize global instances
        get_session_manager()
        get_responses_client()
        get_conversation_builder()
        get_file_organizer()
        get_image_processor()
        
        logger.info("All components initialized successfully")
        
        # Run the MCP server
        mcp.run()
        
    except Exception as e:
        logger.error(f"CRITICAL_MAIN: Server startup failed: {e}")


if __name__ == "__main__":
    main()