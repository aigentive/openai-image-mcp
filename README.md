![OpenAI Image MCP Hero](assets/hero-image.png)

# OpenAI Image MCP Server

A Model Context Protocol (MCP) server that provides conversational OpenAI image generation capabilities. Generate, edit, and refine images through multi-turn conversations with advanced models like GPT-4o and GPT-4.1.

## 🎯 What Problems Does This Solve?

### Traditional Image Generation Pain Points

❌ **Single-shot limitations** - "Make it more blue" requires re-describing everything  
❌ **No conversation memory** - Each request starts from scratch  
❌ **Context loss** - Can't reference previous images naturally  
❌ **Manual workflows** - Complex multi-step processes require multiple tools

### Our Solution

✅ **Conversational refinement** - "Make it more blue" works naturally  
✅ **Session memory** - Builds on previous context automatically  
✅ **Reference awareness** - "Use the same style as the previous image"  
✅ **Integrated workflows** - Single interface for complex creative projects

## 🚀 Key Capabilities

### 🔄 Session-Based Conversations

```python
# Start a focused session
session = create_image_session("Logo design for tech startup")

# Initial generation
result1 = generate_image_in_session(session_id, "modern tech logo")

# Natural refinement - no need to repeat everything
result2 = generate_image_in_session(session_id, "make it more minimalist")

# Build on context
result3 = generate_image_in_session(session_id, "try it in dark blue")
```

### 🔄 Hybrid Workflows

Start simple, expand when needed:

```python
# Quick one-shot for immediate need
result = generate_image("modern office workspace")

# Later, promote to session for refinement
session = promote_image_to_session(
    result["image_path"],
    "Office workspace refinement project"
)

# Continue with conversational context
generate_image_in_session(session_id, "add more plants and warmer lighting")
```

### 🎨 Specialized Tools

- **Product photography** - E-commerce optimized with multiple angles
- **UI/UX assets** - Design elements with consistent styling
- **Reference-based editing** - Use existing images as style guides
- **Batch processing** - Multiple variations with consistent themes

## 🎯 Perfect For

### LLM Applications

- **Claude Desktop integration** - Conversational image workflows
- **AI assistants** - Contextual image generation capabilities
- **Chatbots** - Visual content creation with memory

### Creative Workflows

- **Iterative design** - Refine concepts through conversation
- **Brand development** - Consistent visual identity across assets
- **Product visualization** - Multiple angles and contexts
- **Content creation** - Blog headers, social media, presentations

### Development Teams

- **Rapid prototyping** - Quick UI mockups and concepts
- **Documentation** - Visual aids and diagrams
- **Marketing assets** - Consistent brand imagery
- **User testing** - Visual variations for A/B testing

## 🚀 Quick Start

### 1. Installation

**Requirements:** Python 3.10 or higher

```bash
# Install the package
pip install openai-image-mcp
```

**If you need to upgrade Python:**

```bash
# Using pyenv (recommended)
pyenv install 3.11.8
pyenv global 3.11.8
pip install openai-image-mcp

# Or using Homebrew (macOS)
brew install python@3.11
python3.11 -m pip install openai-image-mcp
```

For development installation from source, see [DEVELOPMENT.md](DEVELOPMENT.md)

### 2. Claude Desktop Integration

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "openai-image-mcp": {
      "command": "sh",
      "args": [
        "-c",
        "openai-image-mcp 2> mcp_server_stderr.log"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here"
      }
    }
  }
}
```

For development setup and alternative configurations, see [DEVELOPMENT.md](DEVELOPMENT.md)

### 3. Start Creating

```python
# Create a session for your project
session = create_image_session("Website hero images")

# Generate with natural language
generate_image_in_session(session_id, "modern tech office with diverse team")

# Refine naturally
generate_image_in_session(session_id, "make the lighting warmer")

# Add context
generate_image_in_session(session_id, "create a mobile version of this scene")
```

## 🛠️ Available Tools

### Core Session Management

- `create_image_session` - Start conversational session
- `generate_image_in_session` - Generate with context awareness
- `get_session_status` - View conversation history and progress
- `close_session` - End session and cleanup

### Image Generation & Editing

- `generate_image` - General purpose (session optional)
- `edit_image` - Modify existing images
- `generate_product_image` - E-commerce optimized
- `generate_ui_asset` - UI/UX design elements
- `analyze_and_improve_image` - AI-powered image enhancement

### Workflow Tools

- `promote_image_to_session` - Upgrade one-shot to conversational
- `list_active_sessions` - Manage multiple projects
- `get_usage_guide` - Comprehensive tool documentation

## 🎯 Usage Patterns

### 📱 **Conversational Design Sessions** (Recommended)

Best for: Multi-image projects, iterative refinement, brand consistency

```python
session = create_image_session("App icon design")
generate_image_in_session(session_id, "colorful chat app icon")
generate_image_in_session(session_id, "make it more professional")
generate_image_in_session(session_id, "try different color schemes")
```

### ⚡ **Quick One-Shot Generation**

Best for: Immediate needs, single images, uncertain scope

```python
generate_image("professional headshot for LinkedIn")
generate_product_image("wireless headphones", background_type="white")
```

### 🔄 **Hybrid Start-Simple-Expand-Later**

Best for: Testing concepts, uncertain requirements, flexible workflows

```python
# Start quick
result = generate_image("logo concept for bakery")

# Expand when needed
session = promote_image_to_session(result["image_path"], "Bakery brand development")
generate_image_in_session(session_id, "create business card version")
```

## 🎨 Example Workflows

### Brand Identity Development

```python
session = create_image_session("TechCorp brand identity")

# Logo concepts
generate_image_in_session(session_id, "modern tech company logo")
generate_image_in_session(session_id, "make it more geometric and minimal")

# Expand to brand elements
generate_image_in_session(session_id, "business card design using this logo")
generate_image_in_session(session_id, "website header with the logo")
```

### Product Marketing Suite

```python
session = create_image_session("Wireless headphones marketing")

# Product shots
generate_product_image("premium wireless headphones", angle="45deg")
result = promote_image_to_session(previous_result["image_path"], "headphones campaign")

# Marketing variations
generate_image_in_session(session_id, "lifestyle shot with person using them")
generate_image_in_session(session_id, "create packaging design mockup")
```

## 📚 Documentation

- **[LLM.md](LLM.md)** - Comprehensive guide for LLMs using this server
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Technical implementation, testing, and contribution guide

## 📋 Requirements

- **Python 3.10+** (3.11+ recommended)
- **OpenAI API key** with GPT-4o/GPT-4.1 access
- Poetry for dependency management (development only)

## 🔐 Environment Variables

- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `MCP_MAX_SESSIONS` (optional) - Maximum concurrent sessions (default: 100)
- `MCP_SESSION_TIMEOUT` (optional) - Session timeout in seconds (default: 3600)

## 🤝 Contributing

We welcome contributions! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for:

- Technical architecture details
- Development setup instructions
- Testing guidelines
- Code style requirements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Resources

- [Model Context Protocol](https://modelcontextprotocol.io/) - Protocol specification
- [OpenAI Responses API](https://platform.openai.com/docs/guides/responses) - Underlying API
- [Claude Desktop](https://claude.ai/desktop) - Primary integration target
