# OpenAI GPT-Image-1 MCP Server

A Model Context Protocol (MCP) server that exposes OpenAI GPT-Image-1 image generation capabilities to LLM applications like Claude Desktop.

## 🌟 Features

- **OpenAI GPT-Image-1 Integration**: Generate high-quality images using the latest GPT-Image-1 model
- **MCP-Compliant Server**: Built with the official Python MCP SDK using FastMCP
- **Flexible Image Parameters**: Configure size, quality, background, format, and number of images
- **Progress Tracking**: Real-time progress updates during image generation
- **Error Handling**: Robust error handling with informative messages
- **Image Download**: Optional image data download for further processing

## 🛠️ Available Tools

### `generate_image`
Generate images using OpenAI GPT-Image-1 with comprehensive options.

**Parameters:**
- `prompt` (required): Description of the image to generate
- `size`: Image dimensions - options: `1024x1024`, `1536x1024`, `1024x1536` (default: `1024x1024`)
- `quality`: Image quality - options: `high`, `medium`, `low` (default: `high`)
- `background`: Background type - options: `auto`, `transparent` (default: `auto`)
- `output_format`: Output format - options: `png`, `jpeg`, `webp` (default: `png`)
- `n`: Number of images to generate, 1-10 (default: `1`)

### `generate_and_download_image`
Generate a single image and download the image data for processing.

**Parameters:**
- `prompt` (required): Description of the image to generate
- `size`: Image dimensions (same options as above)
- `quality`: Image quality (same options as above)
- `background`: Background type (same options as above)
- `output_format`: Output format (same options as above)

### `edit_image`
Edit an existing image using OpenAI GPT-Image-1 editing capabilities.

**Parameters:**
- `image_url` (required): URL of the base image to edit
- `prompt` (required): Description of the edits to make
- `mask_url`: Optional URL of mask image for targeted editing (default: "")
- `size`: Image dimensions - options: `1024x1024`, `1536x1024`, `1024x1536` (default: `1024x1024`)
- `quality`: Image quality - options: `high`, `medium`, `low` (default: `high`)
- `output_format`: Output format - options: `png`, `jpeg`, `webp` (default: `png`)
- `n`: Number of edited images to generate, 1-10 (default: `1`)

## 🚀 Quick Start

### 1. Installation

Run the setup script to install dependencies and configure the environment:

```bash
./setup.sh
```

Or manually:

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Copy environment template
cp .env.example .env
```

### 2. Configuration

Edit the `.env` file and add your OpenAI API key:

```bash
nano .env
```

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Test the Server

Test the server locally:

```bash
poetry run python examples/test_client.py
```

Or run the server directly:

```bash
poetry run python -m src.openai_image_mcp.server
```

### 4. Integration with Claude Desktop

Add the server to your Claude Desktop MCP configuration:

1. Open Claude Desktop settings
2. Navigate to the MCP configuration section
3. Add the following configuration (update the path to match your installation):

```json
{
  "mcpServers": {
    "openai-image-mcp": {
      "command": "python",
      "args": ["-m", "src.openai_image_mcp.server"],
      "cwd": "/Users/lazabogdan/Code/openai-image-mcp",
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

## 📖 Usage Examples

### Basic Image Generation

```python
# In Claude Desktop or through MCP client
generate_image(
    prompt="A futuristic cityscape at sunset with flying cars",
    size="1024x1024",
    quality="high",
    background="auto",
    output_format="png"
)
```

### High-Quality Portrait with Transparent Background

```python
generate_image(
    prompt="Professional portrait of a software engineer working on AI",
    size="1024x1536",
    quality="high",
    background="transparent",
    output_format="png"
)
```

### Multiple Variations

```python
generate_image(
    prompt="Abstract art representing the concept of artificial intelligence",
    size="1024x1024",
    quality="high",
    background="auto",
    output_format="webp",
    n=3
)
```

### Image Editing

```python
edit_image(
    image_url="https://example.com/my-image.png",
    prompt="Add a sunset in the background and change the colors to warmer tones",
    size="1024x1024",
    quality="high",
    output_format="png"
)
```

## 🏗️ Architecture

The project is structured as follows:

```
openai-image-mcp/
├── src/
│   └── openai_image_mcp/
│       ├── __init__.py
│       ├── server.py          # FastMCP server implementation
│       └── image_agent.py     # OpenAI DALL-E integration
├── examples/
│   └── test_client.py         # Test client for development
├── .env.example               # Environment variables template
├── mcp-config.json           # Claude Desktop configuration
├── setup.sh                  # Installation script
└── pyproject.toml           # Poetry configuration
```

### Key Components

- **FastMCP Server**: Modern MCP server implementation with lifespan management
- **OpenAI Image Agent**: Handles GPT-Image-1 API interactions with async support
- **Progress Tracking**: Real-time feedback during image generation
- **Error Handling**: Comprehensive error handling and validation

## 🔧 Development

### Setting up Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd openai-image-mcp
./setup.sh

# Run tests
poetry run python examples/test_client.py

# Run with development logging
LOG_LEVEL=DEBUG poetry run python -m src.openai_image_mcp.server
```

### Code Quality

The project uses:
- **Black**: Code formatting
- **isort**: Import sorting  
- **mypy**: Type checking
- **pytest**: Testing

```bash
# Format code
poetry run black src/ examples/

# Sort imports
poetry run isort src/ examples/

# Type checking
poetry run mypy src/

# Run tests
poetry run pytest
```

## 📋 Requirements

- Python 3.9+
- OpenAI API key
- Poetry (for dependency management)

## 🔐 Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `OPENAI_ORG_ID` (optional): Your OpenAI organization ID
- `LOG_LEVEL` (optional): Logging level (default: INFO)

## 🐛 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**
   - Ensure your `.env` file contains a valid OpenAI API key
   - Check that the `.env` file is in the project root directory

2. **"Module not found" errors**
   - Run `poetry install` to install dependencies
   - Ensure you're using the correct Python path in MCP configuration

3. **"Permission denied" on setup.sh**
   - Run `chmod +x setup.sh` to make the script executable

4. **Server not responding in Claude Desktop**
   - Check the MCP configuration path is correct
   - Verify the server starts successfully when run directly
   - Check Claude Desktop logs for error messages

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Claude Desktop](https://claude.ai/desktop)