"""Main MCP server implementation for OpenAI image generation using FastMCP."""

import logging
import os
import datetime
import sys

# --- Simple file write test (keeping this for sanity check) ---
try:
    script_dir_for_debug = os.path.dirname(os.path.abspath(__file__))
    workspace_root_for_debug = os.path.dirname(os.path.dirname(script_dir_for_debug))
    debug_file_path = os.path.join(workspace_root_for_debug, "debug_write_test.txt")
    with open(debug_file_path, "w") as f_debug:
        f_debug.write(f"DEBUG_WRITE_TEST: File write test successful at: {datetime.datetime.now()}\n")
except Exception as e_debug:
    print(f"CRITICAL_ERROR_DEBUG_WRITE: Failed to write debug_write_test.txt to {debug_file_path}: {e_debug}", file=sys.stderr)
    pass
# --- End simple file write test ---

from typing import Optional

from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

from .image_agent import OpenAIImageAgent

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

# Global agent instance - will be initialized on first use
agent: Optional[OpenAIImageAgent] = None


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

@mcp.tool()
def generate_and_download_image(
    prompt: str,
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    output_file_format: str = "png",
    n: int = 1
) -> str:
    """
    Generates and downloads an image, saving it to a local file.
    Returns information including the local filepath.
    Args:
        prompt: The image generation prompt.
        model: Model to use (e.g., "dall-e-3", "dall-e-2").
        size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792" for DALL-E 3).
        quality: Image quality ("standard", "hd" for DALL-E 3).
        style: Style for DALL-E 3 ("vivid", "natural").
        output_file_format: Format to save the image as (e.g., "png", "jpeg").
        n: Number of images to generate (currently fixed to 1 by agent method).
    """
    logger.info(f"MCP TOOL CALLED: generate_and_download_image with prompt: '{prompt}'")
    try:
        logger.debug(f"Params: prompt='{prompt}', model='{model}', size='{size}', quality='{quality}', style='{style}', output_file_format='{output_file_format}', n={n}")

        # Basic Parameter Validation (can be expanded)
        if model not in ["dall-e-3", "dall-e-2"]:
            return f"Error: Invalid model '{model}'. Choose 'dall-e-3' or 'dall-e-2'."
        if quality not in ["standard", "hd"] and model == "dall-e-3":
             return f"Error: Invalid quality '{quality}' for DALL-E 3. Choose 'standard' or 'hd'."
        if style not in ["vivid", "natural"] and model == "dall-e-3":
            return f"Error: Invalid style '{style}' for DALL-E 3. Choose 'vivid' or 'natural'."
        if output_file_format.lower() not in ["png", "jpeg", "jpg"]:
            return f"Error: Invalid output_file_format '{output_file_format}'. Choose png or jpeg."
        if n != 1:
            # Agent method generate_and_download_images currently implies n=1 for simplicity of file handling
            logger.warning(f"Number of images 'n' is currently fixed to 1 for generate_and_download_image by the agent, requested n={n} ignored.")
            n = 1 # Force n=1 for now based on current agent impl.

        agent_instance = get_agent()
        results = agent_instance.generate_and_download_images(
            prompt=prompt, 
            model=model, 
            size=size, 
            quality=quality, 
            style=style if model == "dall-e-3" else None, # Pass style only if DALL-E 3
            output_file_format=output_file_format.lower(),
            n=n # Agent will process this n (currently implies 1 result in list for this func)
        )
        
        if not results:
            logger.warning("No images generated/downloaded by agent.")
            return "Error: No images were generated or downloaded."
        
        result = results[0] # Expecting one result from generate_and_download_images
        
        filepath = result.get("filepath")
        saved_bytes = result.get("saved_image_data_bytes", 0)
        revised_prompt = result.get("revised_prompt", prompt)
        actual_quality = result.get("requested_quality", quality) # from agent metadata
        actual_size = result.get("requested_size", size) # from agent metadata

        if filepath and saved_bytes > 0:
            status_message = f"Image saved to: {filepath} ({saved_bytes} bytes)"
        elif saved_bytes > 0 and not filepath:
            status_message = f"Image data processed ({saved_bytes} bytes), but file save failed. Check server logs."
        else:
            status_message = "Download or file processing failed. Check server logs."

        response_parts = [
            f"Image generation request processed.",
            f"Prompt: '{prompt}'",
            f"Revised Prompt: '{revised_prompt}'" if revised_prompt and revised_prompt != prompt else "Revised Prompt: (same as original)",
            f"Model: {model}",
            f"Size: {actual_size}",
            f"Quality: {actual_quality}",
        ]
        if model == "dall-e-3":
            response_parts.append(f"Style: {style}")
        response_parts.append(f"File Output Format: {output_file_format.lower()}")
        response_parts.append(status_message)
        
        return "\n".join(response_parts)

    except Exception as e:
        logger.error(f"Error in generate_and_download_image tool: {str(e)}", exc_info=True)
        return f"Error processing generate_and_download_image: {str(e)}"

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