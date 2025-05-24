# OpenAI Image MCP Server

A Model Context Protocol (MCP) server that provides comprehensive OpenAI image generation capabilities to LLM applications like Claude Desktop. Generate, edit, and create images using OpenAI's powerful image models with intelligent model selection and organized file management.

## 🌟 Features

- **🤖 Smart Model Selection**: Automatic selection of optimal models (GPT-Image-1, DALL-E 3, DALL-E 2) based on use case
- **📁 Organized File Management**: Automatic categorization and metadata tracking for all generated images  
- **🎯 Specialized Tools**: Purpose-built tools for products, UI assets, batch processing, and iterative improvement
- **💰 Cost Optimization**: Budget-aware defaults and transparent cost estimation
- **🔧 MCP-Compliant**: Built with the official Python MCP SDK using FastMCP
- **📊 Progress Tracking**: Real-time feedback and structured responses
- **🛡️ Robust Error Handling**: Comprehensive validation and informative error messages
- **🎨 Multiple Edit Modes**: Inpainting, outpainting, variations, and style transfer

## 🛠️ Available Tools

### Core Tools

#### `generate_image`
General-purpose image generation with intelligent model selection.

**When to use:** Default choice for most image generation needs

**Parameters:**
- `prompt` (required): Text description of desired image
- `model`: "auto" | "gpt-image-1" | "dall-e-3" | "dall-e-2" (default: "auto")
- `quality`: "auto" | "low" | "medium" | "high" | "hd" (default: "auto")
- `size`: "auto" | specific dimensions (default: "auto")
- `background`: "auto" | "transparent" (default: "auto")
- `format`: "png" | "jpeg" | "webp" (default: "png")

**Examples:**
```python
# Professional product photo
generate_image("professional photo of wireless headphones", quality="high")

# Logo with transparent background  
generate_image("minimal tech startup logo", background="transparent")

# Artistic illustration
generate_image("children's book illustration of a friendly dragon", model="dall-e-3")
```

#### `edit_image_advanced`
Sophisticated image editing with multiple modes.

**When to use:** For modifying existing images with advanced control

**Parameters:**
- `image_path` (required): Path to source image
- `prompt` (required): Edit instructions
- `mode`: "inpaint" | "outpaint" | "variation" | "style_transfer" (default: "inpaint")
- `mask_path`: Path to mask image (required for inpaint mode)
- `model`: "auto" | "gpt-image-1" | "dall-e-2" (default: "auto")

**Examples:**
```python
# Remove object with mask
edit_image_advanced("photo.jpg", "remove the car", mode="inpaint", mask_path="car_mask.png")

# Style transformation
edit_image_advanced("photo.jpg", "make it look like a watercolor painting", mode="style_transfer")

# Create variation
edit_image_advanced("photo.jpg", "same scene, different lighting", mode="variation")
```

### Specialized Tools

#### `generate_product_image`
Optimized for e-commerce and product photography.

**When to use:** E-commerce, catalogs, product showcases

**Parameters:**
- `product_description` (required): Detailed product description
- `background_type`: "transparent" | "white" | "lifestyle" | "custom" (default: "white")
- `angle`: "front" | "side" | "top" | "45deg" | "multiple" (default: "front")
- `lighting`: "studio" | "natural" | "dramatic" (default: "studio")
- `batch_count`: Number of variations 1-4 (default: 1)

#### `generate_ui_asset`
Create UI/UX design assets optimized for web and apps.

**When to use:** Web/app design, UI components, interface elements

**Parameters:**
- `asset_type` (required): "icon" | "illustration" | "hero" | "background"
- `description` (required): Asset details
- `theme`: "light" | "dark" | "auto" (default: "auto")
- `style_preset`: "flat" | "gradient" | "3d" | "outline" (default: "flat")

#### `batch_generate`
Efficient bulk image generation with cost optimization.

**When to use:** Multiple related images, A/B testing, content series

**Parameters:**
- `prompts` (required): JSON array of prompts or newline-separated
- `variations_per_prompt`: 1-3 variations each (default: 1)
- `consistent_style`: Style to maintain across batch
- `model`: "auto" | specific model (default: "auto")

#### `analyze_and_regenerate`
Iterative image improvement with structured feedback.

**When to use:** When initial results need refinement

**Parameters:**
- `image_path` (required): Current image to improve
- `requirements` (required): What needs improvement
- `preserve_elements`: Elements to keep unchanged
- `max_iterations`: Iteration limit 1-5 (default: 3)

### Utility Tools

#### `get_usage_guide`
Retrieve comprehensive LLM usage guidelines and tool selection advice.

**When to use:** When you need guidance on tool selection or usage patterns

## 🧠 Smart Model Selection

The server automatically selects the optimal model based on your requirements:

| Use Case | Auto-Selected Model | Quality | Rationale |
|----------|-------------------|---------|-----------|
| Text in images | GPT-Image-1 | High | Superior text rendering |
| Product photos | GPT-Image-1 | High | Best realism and detail |
| UI assets | GPT-Image-1 | Medium | Clean graphics, transparency |
| Artistic content | DALL-E 3 | HD | Larger sizes, artistic styles |
| Budget/batch | DALL-E 2 | Standard | Cost optimization |

## 📁 File Organization

Generated images are automatically organized:

```
workspace/
├── generated_images/
│   ├── general/              # General purpose images
│   ├── products/             # Product photography
│   │   └── [product_name]/   # Organized by product
│   ├── ui_assets/            # UI/UX design assets
│   │   ├── icons/
│   │   ├── illustrations/
│   │   ├── heroes/
│   │   └── backgrounds/
│   ├── batch_generations/    # Batch processing results
│   │   └── [batch_id]/
│   ├── edited_images/        # Edited/modified images
│   └── variations/           # Image variations
```

Each image includes metadata with generation parameters, costs, and timestamps.

> **Note:** The `generated_images/` directory is automatically created and excluded from version control (.gitignore).

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/openai-image-mcp.git
cd openai-image-mcp

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 2. Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 3. Test the Server

```bash
# Test locally
poetry run python examples/test_client.py

# Or run the server directly
poetry run python -m openai_image_mcp.server
```

### 4. Integration with Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "openai-image-mcp": {
      "command": "poetry",
      "args": ["run", "python", "-m", "openai_image_mcp.server"],
      "cwd": "/path/to/openai-image-mcp",
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

## 📖 Usage Examples

### Smart Auto Mode (Recommended)

```python
# The server automatically selects the best model and parameters
generate_image("professional headshot of a business executive")
# → Uses GPT-Image-1, high quality, optimized settings

generate_image("abstract artistic painting with vibrant colors")  
# → Uses DALL-E 3, HD quality, artistic optimization

generate_image("simple app icon with rounded corners", background="transparent")
# → Uses GPT-Image-1, medium quality, PNG with transparency
```

### Product Photography Workflow

```python
# Generate multiple product shots
generate_product_image(
    product_description="wireless bluetooth headphones",
    background_type="transparent", 
    angle="multiple",
    batch_count=3
)
# → Creates organized product folder with multiple angles
```

### UI Design Workflow

```python
# Create app icons
generate_ui_asset(
    asset_type="icon",
    description="shopping cart with rounded modern design",
    style_preset="flat",
    theme="light"
)

# Generate hero images
generate_ui_asset(
    asset_type="hero", 
    description="modern dashboard interface mockup",
    dimensions="1200x600",
    theme="dark"
)
```

### Batch Content Creation

```python
# Generate series with consistent style
batch_generate(
    prompts='["red sports car", "blue mountain bike", "green sailboat"]',
    consistent_style="minimalist vector illustration",
    variations_per_prompt=2
)
```

### Iterative Improvement

```python
# Improve image quality iteratively
analyze_and_regenerate(
    image_path="draft_logo.png",
    requirements="make more professional and add subtle drop shadow",
    preserve_elements="colors and overall shape",
    max_iterations=3
)
```

## 🏗️ Architecture

```
openai-image-mcp/
├── src/
│   └── openai_image_mcp/
│       ├── server.py           # Enhanced MCP server with 6 tools
│       ├── image_agent.py      # OpenAI API integration
│       ├── model_selector.py   # Intelligent model selection
│       └── file_organizer.py   # Structured file management
├── tests/                      # Comprehensive test suite
│   ├── test_model_selector.py  # Model selection tests
│   ├── test_file_organizer.py  # File organization tests
│   └── test_enhanced_server_tools.py  # Enhanced tool tests
├── LLM.md                      # LLM usage guidelines
└── examples/
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
poetry run pytest

# Test specific components
poetry run pytest tests/test_model_selector.py
poetry run pytest tests/test_file_organizer.py
poetry run pytest tests/test_enhanced_server_tools.py

# Run with coverage
poetry run pytest --cov=src/openai_image_mcp
```

## 💡 Best Practices

### For LLMs

1. **Use "auto" mode** - Let the server select optimal settings
2. **Be specific in prompts** - Detailed descriptions yield better results
3. **Choose specialized tools** - Use purpose-built tools for better results
4. **Consider cost** - Use batch processing for multiple related images

### For Developers

1. **Check metadata** - All images include generation metadata
2. **Handle errors gracefully** - The server provides detailed error information
3. **Monitor costs** - Use the cost estimation features
4. **Organize files** - Leverage the automatic categorization system

## 📋 Requirements

- Python 3.10+
- OpenAI API key with image generation access
- Poetry for dependency management

## 🔐 Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `LOG_LEVEL` (optional): Logging level (default: INFO)

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid model" errors**
   - The server auto-selects models; use "auto" for model parameter

2. **"Quality not supported" errors**  
   - Different models support different quality levels; use "auto" for quality

3. **File organization issues**
   - The server creates directories automatically; ensure write permissions

4. **Cost concerns**
   - Use "auto" quality and batch processing for cost optimization
   - Check cost estimates in responses

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please submit a Pull Request.

## 🔗 Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Claude Desktop](https://claude.ai/desktop)