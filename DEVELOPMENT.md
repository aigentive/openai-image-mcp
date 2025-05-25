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

### Test Structure

```
tests/
├── test_file_organizer.py        # File management (16 tests)
├── test_responses_integration.py # Session architecture (20 tests)
├── test_server.py                # MCP integration (6 tests)  
└── test_usage_guide.py          # Documentation tools (4 tests)
```

### Running Tests

```bash
# Full test suite (40 tests)
poetry run pytest

# Specific components
poetry run pytest tests/test_responses_integration.py  # Session architecture
poetry run pytest tests/test_file_organizer.py        # File management
poetry run pytest tests/test_server.py                # MCP integration

# With coverage
poetry run pytest --cov=src/openai_image_mcp

# Verbose output
poetry run pytest -v
```

### Test Categories

**Unit Tests**: Individual component functionality
- Session management operations
- File organization logic
- Error handling scenarios

**Integration Tests**: Component interaction validation
- Complete generation workflows
- Session promotion functionality  
- MCP tool integration

**Error Handling Tests**: Failure mode validation
- Invalid parameters
- Missing files
- Network failures
- Malformed data

## 🚀 Installation & Setup

### Prerequisites

- Python 3.11+
- Poetry for dependency management
- OpenAI API key with GPT-4o/GPT-4.1 access

### Development Installation

```bash
# Clone repository
git clone https://github.com/your-username/openai-image-mcp.git
cd openai-image-mcp

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install pre-commit hooks (optional)
poetry run pre-commit install
```

### Environment Configuration

```bash
# Required
export OPENAI_API_KEY="your_openai_api_key_here"

# Optional configuration
export MCP_MAX_SESSIONS="100"          # Maximum concurrent sessions
export MCP_SESSION_TIMEOUT="3600"      # Session timeout in seconds
export LOG_LEVEL="INFO"                # Logging level
```

### Local Testing

```bash
# Run server locally
poetry run python -m openai_image_mcp.server

# Test with example client
poetry run python examples/test_client.py

# Run integration tests
poetry run pytest tests/test_responses_integration.py -v
```

## 🔧 Configuration

### MCP Client Integration

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

#### Other MCP Clients

The server follows standard MCP protocol and works with any compatible client:

```bash
# Direct execution
poetry run python -m openai_image_mcp.server

# With custom configuration
MCP_MAX_SESSIONS=50 poetry run python -m openai_image_mcp.server
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

## 🐛 Debugging & Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure proper Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use Poetry
poetry run python -m openai_image_mcp.server
```

**Session Timeout Issues**
```bash
# Increase timeout
export MCP_SESSION_TIMEOUT="7200"  # 2 hours
```

**Memory Issues with Large Sessions**
```bash
# Reduce max sessions
export MCP_MAX_SESSIONS="25"
```

### Logging Configuration

```python
# Enable debug logging
export LOG_LEVEL="DEBUG"

# Custom logging in code
import logging
logging.getLogger("openai_image_mcp").setLevel(logging.DEBUG)
```

### Performance Monitoring

```python
# Get server statistics
result = get_server_stats()
print(f"Active sessions: {result['active_sessions']}")
print(f"Memory usage: {result['memory_usage']}")
```

## 🤝 Contributing

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/your-username/openai-image-mcp.git
   cd openai-image-mcp
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-functionality
   ```

3. **Development**
   ```bash
   poetry install
   # Make changes
   poetry run pytest  # Ensure tests pass
   ```

4. **Submit PR**
   - Ensure all tests pass
   - Add tests for new functionality
   - Update documentation
   - Follow code style guidelines

### Code Style

- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all modules/classes/functions
- **Error Handling**: Structured error responses with appropriate types
- **Logging**: Use structured logging with appropriate levels

### Adding New Tools

1. **Define Tool Function**
   ```python
   @mcp.tool()
   def new_tool(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
       """Tool description."""
       try:
           # Implementation
           return {"success": True, "result": "..."}
       except Exception as e:
           logger.error(f"New tool failed: {e}")
           return {
               "success": False,
               "error": str(e),
               "error_type": "tool_error"
           }
   ```

2. **Add Tests**
   ```python
   def test_new_tool():
       """Test new tool functionality."""
       result = new_tool("test_param")
       assert result["success"] is True
   ```

3. **Update Documentation**
   - Add to LLM.md usage guide
   - Update README.md tool list
   - Add examples and use cases

### Testing Guidelines

- **Coverage**: Aim for >90% test coverage
- **Error Cases**: Test all error conditions
- **Integration**: Test tool interactions
- **Documentation**: Test examples in documentation

### Release Process

1. **Version Bump**: Update version in pyproject.toml
2. **Testing**: Full test suite must pass
3. **Documentation**: Update README.md and LLM.md
4. **Tag Release**: Create git tag for version
5. **Deploy**: Update production configurations

## 📚 API Reference

### Session Manager

```python
class SessionManager:
    def create_session(description: str, model: str, session_name: Optional[str]) -> ImageSession
    def get_session(session_id: str) -> Optional[ImageSession]
    def add_conversation_turn(session_id: str, role: str, content: Any) -> None
    def add_generated_image(session_id: str, generation_call: ImageGenerationCall) -> None
    def close_session(session_id: str) -> bool
```

### Responses Client

```python
class ResponsesAPIClient:
    def generate_with_conversation(session: ImageSession, user_input: List[Dict], tools_config: Dict) -> Dict
    def create_file_from_path(file_path: str) -> str
    def create_file_from_bytes(file_bytes: bytes, filename: str) -> str
```

### File Organizer

```python
class FileOrganizer:
    def get_save_path(use_case: str, prompt: str, subdir: Optional[str]) -> str
    def save_image_metadata(image_path: str, metadata: Dict) -> str
    def get_recent_images(use_case: Optional[str], limit: int) -> List[Dict]
```

## 🔐 Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables for sensitive configuration
- Consider using secret management services in production

### File System Access
- Images are stored in organized directories
- Metadata files contain generation parameters only
- No execution of user-provided code

### Input Validation
- All user inputs are validated before processing
- File paths are sanitized to prevent directory traversal
- Image uploads are validated for format and size

### Network Security
- All API calls use HTTPS
- Retry logic includes circuit breaker patterns
- Rate limiting considerations for production use

## 📊 Performance Optimization

### Session Management
- Use dictionary-based O(1) lookups
- Implement automatic cleanup for expired sessions
- Consider Redis for distributed deployments

### Memory Management
- Conversation history trimming at 50 turns
- Lazy loading of image data
- Garbage collection of unused sessions

### API Efficiency
- Batch operations where possible
- Connection pooling for HTTP requests
- Caching of frequently accessed data

## 📈 Monitoring & Observability

### Metrics to Track
- Session creation/closure rates
- Generation success/failure rates
- API response times
- Memory usage patterns
- Error frequency by type

### Logging Strategy
- Structured logging with JSON format
- Correlation IDs for request tracing
- Different log levels for different environments
- Integration with log aggregation systems

### Health Checks
```python
# Built-in health check
result = get_server_stats()
# Monitor: active_sessions, memory_usage, api_health
```

This development guide provides comprehensive technical information for contributors and maintainers. For usage instructions, see README.md. For LLM-specific guidance, see LLM.md.