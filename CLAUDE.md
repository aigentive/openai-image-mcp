# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_server.py

# Run with coverage
poetry run pytest --cov=src/openai_image_mcp

# Code formatting
poetry run black .
poetry run isort .
```

### Package Operations
```bash
# Build package
poetry build

# Publish to PyPI
poetry publish

# Version bump
poetry version patch  # or minor/major
```

### MCP Server Testing
```bash
# Run server locally
poetry run python -m openai_image_mcp.server

# Test with Claude Code
claude --mcp-config mcp-config.private.json --mcp-debug
```

## Core Architecture

### Session-Based Conversational Design

The system is built around **multi-turn conversations** with persistent memory, not traditional stateless API calls. Key architectural patterns:

- **Session Manager**: Thread-safe session lifecycle with O(1) UUID lookup
- **Conversation Builder**: Automatic context trimming at 50 turns, preserves image references
- **Responses API Client**: Uses OpenAI Responses API (requires `openai>=1.82.0`) with exponential backoff retry logic
- **File Organizer**: Structured storage with comprehensive metadata preservation

### Component Interaction Flow

1. **MCP Tool Call** → `server.py` (13 available tools)
2. **Session Creation** → `session_manager.py` (UUID-based, thread-safe)
3. **Context Building** → `conversation_builder.py` (multi-turn history)
4. **API Call** → `responses_client.py` (OpenAI Responses API with tools)
5. **Image Processing** → `image_processor.py` (download, save, metadata)
6. **File Organization** → `file_organizer.py` (structured directories, metadata JSON)

### MCP Tools Organization

**Session Management** (5 tools): `create_image_session`, `generate_image_in_session`, `get_session_status`, `list_active_sessions`, `close_session`

**Image Generation** (5 tools): `generate_image`, `edit_image`, `generate_product_image`, `generate_ui_asset`, `analyze_and_improve_image`

**Utility Tools** (3 tools): `promote_image_to_session`, `get_usage_guide`, `get_server_stats`

### Key Technical Details

- **OpenAI Dependency**: Requires `openai>=1.82.0` for Responses API support
- **Session Limits**: Max 100 concurrent sessions, 1-hour timeout
- **Error Handling**: Structured responses with error types and recovery guidance
- **Metadata**: Complete generation lineage with conversation context
- **File Structure**: Organized by use case (general/, products/, ui_assets/, etc.)

### Configuration Files

- **`mcp-config.pypi.json`**: Production PyPI installation config
- **`mcp-config.poetry.json`**: Development Poetry-based config
- **`mcp-config.private.json`**: Local testing with API key (gitignored)

All MCP configs use `sh -c` wrapper with stderr redirect to prevent server hangs.

### Environment Variables

- `OPENAI_API_KEY` (required): API authentication
- `MCP_MAX_SESSIONS` (optional, default: 100): Concurrent session limit
- `MCP_SESSION_TIMEOUT` (optional, default: 3600): Session timeout in seconds
- `LOG_LEVEL` (optional, default: INFO): Logging verbosity

### Testing Patterns

- **Import Tests**: Validate core module loading and dependency resolution
- **Integration Tests**: Mock OpenAI API responses for session workflows
- **File Organization Tests**: Workspace directory creation and metadata handling
- **Documentation Tests**: Verify usage guide content and structure

When working with this codebase, remember that the primary value proposition is **conversational image generation** - users can say "make it more blue" and the system understands context from previous generations in the same session.