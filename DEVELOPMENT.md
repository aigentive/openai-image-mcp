# Development Guide

This document covers the technical implementation, architecture, testing, and contribution guidelines for the OpenAI Image MCP Server.

## 🏗️ Architecture

### Core Components

```
src/openai_image_mcp/
├── server.py              # FastMCP server with 13 MCP tools
├── session_manager.py     # Session lifecycle management
├── responses_client.py    # OpenAI Responses API client
├── conversation_builder.py # Context and conversation management
├── image_processor.py     # Image I/O and processing
└── file_organizer.py      # Structured file management
```

### Key Design Patterns

**Session Management**: Thread-safe session lifecycle with UUID tracking
- **O(1) session lookup** using dictionary-based storage
- **Automatic cleanup** with configurable timeouts
- **Thread-safe operations** using RLock for concurrent access

**Conversation Context**: Automatic history building and context trimming
- **Multi-turn conversations** with persistent memory
- **Context trimming** at 50 turns to manage token limits
- **Reference preservation** for image continuity

**Advanced API Integration**: OpenAI Responses API with retry logic
- **Structured tool calls** for image generation
- **Automatic retry** with exponential backoff
- **Error categorization** for appropriate handling

**Comprehensive Error Handling**: Structured error responses with recovery suggestions
- **Error types** for programmatic handling
- **Recovery guidance** for common issues
- **Logging integration** for debugging

**Metadata-Rich Storage**: Full conversation and generation context preservation
- **Complete audit trail** of all generations
- **Parameter preservation** for reproducibility
- **Session continuity** through promote functionality

## 🛠️ MCP Tools

### Session Management
- `create_image_session` - Start new conversational session
- `generate_image_in_session` - Generate with session context
- `get_session_status` - Session information and history
- `list_active_sessions` - All active sessions overview
- `close_session` - End session and cleanup resources

### Image Generation
- `generate_image` - General purpose with optional session integration
- `edit_image` - Image editing with session support
- `generate_product_image` - E-commerce optimized generation
- `generate_ui_asset` - UI/UX design asset creation
- `analyze_and_improve_image` - Analysis and improvement workflows

### Utility Tools
- `promote_image_to_session` - Bridge one-shot to conversational workflows
- `get_usage_guide` - Comprehensive usage documentation
- `get_server_stats` - Server health and statistics

## 🧪 Testing

Run the full test suite to ensure everything works:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/openai_image_mcp

# Verbose output
poetry run pytest -v
```


## 📁 File Organization

### Generated Content Structure

```
workspace/
├── generated_images/
│   ├── sessions/
│   │   └── [session_id]/         # Session-based generations
│   │       ├── conversation_log.json
│   │       └── images/
│   │           ├── image_001.png
│   │           ├── image_001_metadata.json
│   │           └── ...
│   ├── single_shot/              # Non-session generations  
│   ├── products/                 # Product showcases
│   ├── ui_assets/               # UI/design assets
│   └── style_series/            # Style-consistent series
```

### Metadata Format

Each generated image includes comprehensive metadata:

```json
{
  "original_prompt": "User's original request",
  "revised_prompt": "AI-refined prompt",
  "model": "gpt-4o",
  "generation_params": {
    "quality": "high",
    "size": "1024x1024",
    "style": "natural"
  },
  "session_id": "uuid-if-applicable",
  "created_at": "2025-05-25T10:00:00Z",
  "generation_id": "unique-generation-uuid",
  "file_size_bytes": 150000,
  "use_case": "general"
}
```

## 🛠️ Development Installation

### Install from Source

```bash
git clone https://github.com/aigentive/openai-image-mcp.git
cd openai-image-mcp

# Set up Python environment with Poetry (recommended)
# Optional: Use pyenv for Python version management
pyenv install 3.11.0  # or latest 3.10+
pyenv local 3.11.0

# Install dependencies with Poetry
poetry install

# Run tests to verify installation
poetry run pytest
```

### Claude Desktop Development Configuration

Copy configuration from `mcp-config.poetry.json`:

```json
{
  "mcpServers": {
    "openai-image-mcp-dev": {
      "command": "sh",
      "args": [
        "-c",
        "poetry run python -m openai_image_mcp.server 2> mcp_server_stderr.log"
      ],
      "cwd": "/path/to/openai-image-mcp",
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Testing Development Setup

```bash
# Run all tests
poetry run pytest

# Test the server starts without errors  
poetry run python -m openai_image_mcp.server

# Check logs for any startup issues
tail -f mcp_server_stderr.log
```

### Use in Another Project

```bash
# In your project directory
poetry add --editable /path/to/openai-image-mcp

# Or from git directly
poetry add git+https://github.com/aigentive/openai-image-mcp.git
```

## 🤝 Contributing

For detailed contribution guidelines, code style, and development workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).

This development guide provides technical information for developers working with the codebase. For usage instructions, see README.md. For LLM-specific guidance, see LLM.md.
