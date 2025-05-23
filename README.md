# OpenAI Image MCP Server

A Model Context Protocol (MCP) server that provides OpenAI image generation capabilities to LLM applications like Claude Desktop. Generate, edit, and download high-quality images using OpenAI's powerful image models.

## 🌟 Features

- **OpenAI Image Integration**: Generate high-quality images using OpenAI's image models
- **MCP-Compliant Server**: Built with the official Python MCP SDK using FastMCP
- **Comprehensive Testing**: 61 tests covering all functionality with 100% pass rate
- **Flexible Image Parameters**: Configure size, quality, background, format, and number of images
- **Image Editing**: Edit existing images with prompts and optional masks
- **Progress Tracking**: Real-time progress updates during image generation
- **Robust Error Handling**: Comprehensive error handling with informative messages
- **Image Download**: Optional image data download for further processing
- **Async Support**: Full async/await support for optimal performance

## 🛠️ Available Tools

### `generate_image`
Generate images using OpenAI's image models with comprehensive options.

**Parameters:**
- `prompt` (required): Description of the image to generate
- `size`: Image dimensions - `1024x1024`, `1536x1024`, `1024x1536`, `auto` (default: `1024x1024`)
- `quality`: Image quality - `high`, `medium`, `low`, `auto` (default: `high`)
- `background`: Background type - `auto`, `transparent` (default: `auto`) [Note: Parameter accepted but ignored by GPT-Image-1]
- `output_format`: Output format - `png`, `jpeg`, `webp` (default: `png`) [Note: Parameter accepted but ignored by GPT-Image-1]
- `n`: Number of images to generate, 1-10 (default: `1`)

**Returns:** Detailed information about generated images including URLs and metadata.

### `generate_and_download_image`
Generate a single image and download the image data for processing.

**Parameters:**
- `prompt` (required): Description of the image to generate
- `size`: Image dimensions (same options as above)
- `quality`: Image quality (same options as above)
- `background`: Background type (same options as above)
- `output_format`: Output format (same options as above)

**Returns:** Image information with download status and size details.

### `edit_image`
Edit an existing image using OpenAI's image editing capabilities.

**Parameters:**
- `image_url` (required): URL of the base image to edit
- `prompt` (required): Description of the edits to make
- `mask_url`: Optional URL of mask image for targeted editing (default: "")
- `size`: Image dimensions - `1024x1024`, `1536x1024`, `1024x1536`, `auto` (default: `1024x1024`)
- `quality`: Image quality - `high`, `medium`, `low`, `auto` (default: `high`)
- `output_format`: Output format - `png`, `jpeg`, `webp` (default: `png`)
- `n`: Number of edited images to generate, 1-10 (default: `1`)

**Returns:** Information about edited images including URLs and metadata.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/aigentive/openai-image-mcp.git
cd openai-image-mcp

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
poetry run python -m openai_image_mcp.server
```

### 4. Integration with Claude Desktop

Add the server to your Claude Desktop MCP configuration:

1. Open Claude Desktop settings
2. Navigate to the MCP configuration section  
3. Copy the example configuration file and customize it:

```bash
cp mcp-config.json.example mcp-config.json
```

4. Edit the configuration file with your specific paths and API key:

```json
{
  "mcpServers": {
    "openai-image-mcp": {
      "command": "poetry",
      "args": ["run", "python", "-m", "openai_image_mcp.server"],
      "cwd": "/path/to/your/openai-image-mcp",
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

5. Import this configuration into Claude Desktop

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
│       └── image_agent.py     # OpenAI image integration
├── tests/                     # Comprehensive test suite (61 tests)
│   ├── test_image_agent.py    # Agent unit tests
│   ├── test_server_tools.py   # Server tool tests
│   ├── test_integration.py    # Integration tests
│   ├── test_error_handling.py # Error handling tests
│   └── test_server.py         # Basic server tests
├── examples/
│   └── test_client.py         # Test client for development
├── .env.example               # Environment variables template
├── mcp-config.json.example    # Claude Desktop configuration template
└── pyproject.toml            # Poetry configuration
```

### Key Components

- **FastMCP Server**: Modern MCP server implementation with lifespan management
- **OpenAI Image Agent**: Handles OpenAI API interactions with async support
- **Progress Tracking**: Real-time feedback during image generation
- **Comprehensive Testing**: 61 tests covering all functionality and edge cases
- **Error Handling**: Robust error handling and validation

## 🔧 Development

### Setting up Development Environment

```bash
# Clone and setup
git clone https://github.com/aigentive/openai-image-mcp.git
cd openai-image-mcp

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env to add your OpenAI API key

# Run tests to verify installation
poetry run pytest

# Run test client
poetry run python examples/test_client.py

# Run with development logging
LOG_LEVEL=DEBUG poetry run python -m openai_image_mcp.server
```

### Testing

The project includes a comprehensive test suite with 61 tests:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src/openai_image_mcp

# Run specific test category
poetry run pytest tests/test_image_agent.py      # Unit tests
poetry run pytest tests/test_server_tools.py    # Server tool tests
poetry run pytest tests/test_integration.py     # Integration tests
poetry run pytest tests/test_error_handling.py  # Error handling tests
```

### Code Quality

The project uses:
- **Black**: Code formatting
- **isort**: Import sorting  
- **mypy**: Type checking
- **pytest**: Testing with asyncio support

```bash
# Format code
poetry run black src/ tests/ examples/

# Sort imports
poetry run isort src/ tests/ examples/

# Type checking
poetry run mypy src/

# Run full quality check
poetry run pytest && poetry run mypy src/ && poetry run black --check src/
```

## 📋 Requirements

- Python 3.10+
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