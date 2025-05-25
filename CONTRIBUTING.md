# Contributing to OpenAI Image MCP

We welcome contributions! This guide will help you get started with contributing to the OpenAI Image MCP server.

## 🛠️ Development Setup

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed installation and setup instructions.

## 🤝 Development Workflow

### 1. Fork & Clone
```bash
git clone https://github.com/aigentive/openai-image-mcp.git
cd openai-image-mcp
```

### 2. Create Feature Branch
```bash
git checkout -b feature/new-functionality
```

### 3. Development
```bash
poetry install
# Make changes
poetry run pytest  # Ensure tests pass
```

### 4. Submit PR
- Ensure all tests pass
- Add tests for new functionality
- Update documentation
- Follow code style guidelines

## 📝 Code Style

- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all modules/classes/functions
- **Error Handling**: Structured error responses with appropriate types
- **Logging**: Use structured logging with appropriate levels

## 🔧 Adding New Tools

### 1. Define Tool Function
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

### 2. Add Tests
Add appropriate tests for new functionality - see existing tests for patterns.

### 3. Update Documentation
- Add to LLM.md usage guide
- Update README.md tool list
- Add examples and use cases

## 🧪 Testing

Run the full test suite to ensure everything works:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_server.py
```

## 📋 Pull Request Checklist

- [ ] Tests pass locally (`poetry run pytest`)
- [ ] New functionality includes tests
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] Type hints added for new functions
- [ ] Error handling follows project patterns

## 🐛 Reporting Issues

When reporting issues, please include:
- Python version
- Poetry version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

## 💡 Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Describe the use case
- Explain why it would be valuable
- Consider if it fits the project scope

Thank you for contributing to OpenAI Image MCP!