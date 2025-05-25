# LLM Usage Guide: OpenAI Image Generation MCP Tools

**Updated:** May 25, 2025  
**Architecture:** Session-based Conversational Image Generation using OpenAI Responses API  
**For:** Large Language Models using the OpenAI Image MCP Server

## 🚀 Key Features

### Session-Based Conversations
- **Multi-turn image generation** with persistent context
- **Iterative refinement** through conversation
- **Context awareness** - images improve based on previous generations
- **Advanced models** - GPT-4o, GPT-4.1 with image generation tools

### Powerful New Capabilities
- **Conversational workflows** - "Make it more blue" references previous image
- **Session memory** - Context preserved across multiple tool calls
- **Advanced editing** - Reference previous images for consistency
- **Better quality** - GPT-4o provides superior results

## 🎯 Quick Decision Tree

**Choose your approach:**

### 🔄 Multi-turn Projects (Recommended)
1. **Start session** → `create_image_session`
2. **Generate in session** → `generate_image_in_session`
3. **Refine iteratively** → `generate_image_in_session` (with feedback)
4. **Manage sessions** → `get_session_status`, `list_active_sessions`, `close_session`

### ⚡ Single-shot Generation (Quick Tasks)
1. **General images** → `generate_image`
2. **Edit existing** → `edit_image`
3. **Product photos** → `generate_product_image`
4. **UI assets** → `generate_ui_asset`
5. **Improve images** → `analyze_and_improve_image`

### 🔄 Hybrid Workflow: Promote One-Shot to Session
**Best of both worlds** - Start quick, expand when needed:
6. **Promote to session** → `promote_image_to_session` (bridges one-shot and conversational workflows)

### 📊 Server Management
- **Server stats** → `get_server_stats`
- **Usage guidance** → `get_usage_guide`

## 💡 Core Principles

### 1. Sessions Enable Context
- **Best Practice:** Use sessions for any project requiring multiple images or refinements
- **Benefit:** Each generation builds on previous context
- **Example:** "Make it more minimalist" - system knows what "it" refers to

### 2. Advanced Models by Default
- **Default Model:** GPT-4o (best quality and capabilities)
- **Alternative:** GPT-4.1 (advanced features), GPT-4o-mini (cost-effective)
- **Auto-selection:** System chooses optimal model for your task

### 3. Conversation-Driven Refinement
- **Iterative:** Start rough, refine through conversation
- **Natural Language:** "Make it bluer", "Add more contrast", "Try a different angle"
- **Context Aware:** System remembers what you're working on

### 4. Organized Output
- **Automatic:** All images saved to organized folders
- **Metadata:** Rich metadata saved with each generation
- **Tracking:** Session history and generation lineage preserved

## 🛠️ Session-Based Workflow (Recommended)

### Starting a New Project

```python
# Create a session for your project
create_image_session(
    description="Logo design for tech startup",
    model="gpt-4o",  # or "auto"
    session_name="TechCorp Logo Project"
)
# Returns: {"session_id": "uuid-123", "status": "active", ...}
```

### Generating and Refining Images

```python
# Generate initial image with context
generate_image_in_session(
    session_id="uuid-123",
    prompt="Modern minimalist logo for AI company"
)

# Refine based on result (system knows context)
generate_image_in_session(
    session_id="uuid-123", 
    prompt="Make it more geometric and add blue accent colors"
)

# Further refinement (builds on previous context)
generate_image_in_session(
    session_id="uuid-123",
    prompt="Perfect! Now create a horizontal version for headers"
)
```

### Advanced Session Features

```python
# Reference previous images for editing
generate_image_in_session(
    session_id="uuid-123",
    prompt="Remove the background to make it transparent",
    reference_image_path="/path/to/previous/image.png"
)

# Inpainting with mask
generate_image_in_session(
    session_id="uuid-123", 
    prompt="Replace the text with 'TechCorp'",
    reference_image_path="/path/to/logo.png",
    mask_image_path="/path/to/text_mask.png"
)
```

### Hybrid Workflow: Start Simple, Expand Later

```python
# 1. Quick one-shot for immediate need
result = generate_image("modern office workspace") 
# Returns: {"image_path": "/path/to/office.png", "single_shot": true}

# 2. Later, decide you want to refine it
session = promote_image_to_session(
    image_path=result["image_path"],
    session_description="Office workspace refinement project",
    session_name="Office Design Session"
)
# Returns: {"session_id": "uuid-456", "ready_for_refinement": true}

# 3. Now refine with full conversational context  
result2 = generate_image_in_session(
    session["session_id"],
    "make it more colorful and add some plants"
)

# 4. Continue iterating with natural language
result3 = generate_image_in_session(
    session["session_id"],
    "add a coffee machine in the corner and warmer lighting"
)
```

**Perfect for:**
- Testing concepts before committing to full sessions
- Quick deliverables that might need refinement later  
- Uncertain scope projects
- Bridging ad-hoc requests with structured workflows

### Session Management

```python
# Check session status
get_session_status("uuid-123")
# Returns: conversation summary, recent images, activity

# List all active sessions
list_active_sessions()
# Returns: all your active sessions

# Close when done
close_session("uuid-123")
# Returns: final image count and cleanup confirmation
```

## ⚡ Single-Shot Tools (Quick Tasks)

### `generate_image` - General Purpose

**Best for:** Quick single images, testing ideas

```python
# Auto-optimized generation
generate_image("sunset over mountain lake")

# With specific requirements  
generate_image(
    prompt="company logo with transparent background",
    quality="high",
    background="transparent",
    size="1024x1024"
)

# With session context (optional)
generate_image(
    prompt="landscape painting", 
    session_id="uuid-123"  # Adds to existing session
)
```

### `edit_image` - Image Modifications

**Best for:** Quick edits, one-off modifications

```python
# Basic editing
edit_image(
    image_path="/path/to/image.png",
    prompt="make the sky more dramatic"
)

# With session context
edit_image(
    image_path="/path/to/image.png", 
    prompt="apply the same style as our previous images",
    session_id="uuid-123"
)

# Inpainting with mask
edit_image(
    image_path="/path/to/image.png",
    prompt="remove the person",
    mask_path="/path/to/person_mask.png"
)
```

## 🎨 Specialized Tools

### `generate_product_image` - E-commerce Focused

**Optimized for:** Product photography, commercial use

```python
# Clean product shot
generate_product_image(
    product_description="wireless noise-canceling headphones",
    background_type="white",      # "white", "transparent", "lifestyle"
    angle="three-quarter",        # "front", "side", "three-quarter", "top"
    lighting="studio",            # "studio", "natural", "dramatic", "soft"
    batch_count=3                 # Generate variations
)

# Lifestyle scene
generate_product_image(
    product_description="ceramic coffee mug",
    background_type="lifestyle", 
    session_id="uuid-123"        # Add to existing session
)
```

### `generate_ui_asset` - Design Assets

**Optimized for:** UI/UX design, web assets

```python
# App icon
generate_ui_asset(
    asset_type="icon",            # "icon", "illustration", "background", "hero"
    description="shopping cart with modern design",
    theme="modern",               # "modern", "classic", "minimal", "playful"
    style_preset="flat",          # "flat", "3d", "outline", "filled"
    size_preset="standard"        # "small", "standard", "large"
)

# Hero image
generate_ui_asset(
    asset_type="hero",
    description="team collaboration in modern office",
    theme="minimal",
    session_id="uuid-123"         # Part of design system session
)
```

### `analyze_and_improve_image` - AI-Powered Enhancement

**Best for:** Quality improvement, fixing issues

```python
# General improvement
analyze_and_improve_image(
    image_path="/path/to/image.png",
    improvement_goals="enhance quality and make more professional",
    preserve_elements="composition and color scheme"
)

# Specific fixes with session context
analyze_and_improve_image(
    image_path="/path/to/draft.png",
    improvement_goals="improve lighting and add more contrast", 
    session_id="uuid-123"        # Maintains design consistency
)
```

## 🎯 Model Selection Guide

### Automatic Selection (Recommended)
```python
# Let the system choose optimal model
create_image_session(description="Logo design")  # Uses GPT-4o by default

# Explicit auto-selection
create_image_session(description="Product photos", model="auto")
```

### Manual Selection
| **Model** | **Best For** | **Capabilities** |
|-----------|--------------|------------------|
| **GPT-4o** | General use, highest quality | Superior instruction following, text rendering, detail |
| **GPT-4.1** | Advanced features | Latest capabilities, experimental features |
| **GPT-4o-mini** | Cost-effective | Good quality at lower cost |
| **o3** | Future use | Next-generation capabilities (when available) |

## 🔄 Conversation Patterns

### Progressive Refinement
```python
# Session 1: Initial concept
create_image_session("Logo design exploration")
generate_image_in_session(session_id, "modern tech logo")

# Session 2: Style direction  
generate_image_in_session(session_id, "make it more minimalist")

# Session 3: Color refinement
generate_image_in_session(session_id, "try it in blue and white")

# Session 4: Final adjustments
generate_image_in_session(session_id, "perfect! now make a horizontal version")
```

### Design System Development
```python
# Create session for design system
create_image_session("Mobile app UI design system", session_name="AppUI v2")

# Generate primary components
generate_image_in_session(session_id, "primary button with rounded corners")
generate_image_in_session(session_id, "secondary button in same style")
generate_image_in_session(session_id, "icon set matching this aesthetic")
```

### Product Catalog Creation
```python
# Session for product line
create_image_session("Wireless audio product catalog")

# Generate different products with consistent style
generate_product_image("wireless earbuds", session_id=session_id)
generate_product_image("over-ear headphones", session_id=session_id) 
generate_product_image("bluetooth speaker", session_id=session_id)
```

## 📁 File Organization

The system automatically organizes generated images:

```
workspace/generated_images/
├── general/                    # generate_image outputs
│   └── session_abc123_*.png   # Organized by session
├── products/                   # generate_product_image outputs  
│   └── [product_name]/        # Grouped by product
├── ui_assets/                  # generate_ui_asset outputs
│   ├── icons/
│   ├── illustrations/
│   ├── backgrounds/
│   └── heroes/
├── edited_images/              # edit_image outputs
├── batch_generations/          # Batch operations
└── variations/                 # Image variations
```

### Metadata Files
Each image includes rich metadata:
```json
{
  "session_id": "uuid-123",
  "generation_call_id": "ig_456", 
  "original_prompt": "modern logo",
  "revised_prompt": "A modern, minimalist logo design...",
  "model": "gpt-4o",
  "conversation_length": 5,
  "created_at": "2025-05-25T10:30:00Z"
}
```

## 💰 Cost Optimization

### Session-Based Efficiency
- **Context Reuse:** Build on previous generations instead of starting fresh
- **Targeted Refinements:** "Make it bluer" vs regenerating completely
- **Batch Context:** Multiple related images in same session share context

### Smart Quality Settings
```python
# Auto-optimized (recommended)
generate_image_in_session(session_id, prompt, quality="auto")

# Explicit quality for specific needs
generate_image_in_session(session_id, prompt, quality="high")  # Premium output
generate_image_in_session(session_id, prompt, quality="medium") # Balanced
```

## 🛠️ Advanced Features

### Reference Images
```python
# Use previous generation as reference
generate_image_in_session(
    session_id="uuid-123",
    prompt="same style but different color",
    reference_image_path="/path/to/previous.png"
)
```

### Inpainting and Masking
```python
# Selective editing with masks
generate_image_in_session(
    session_id="uuid-123", 
    prompt="change the background to a sunset",
    reference_image_path="/path/to/image.png",
    mask_image_path="/path/to/background_mask.png"
)
```

### Session Continuation
```python
# Resume work on existing session
sessions = list_active_sessions()
session_id = sessions["sessions"][0]["session_id"]

# Continue where you left off
generate_image_in_session(session_id, "let's try a different approach")
```

## 🔧 Best Practices

### ✅ Recommended Workflow

1. **Start with Sessions** for any multi-image project
2. **Use Natural Language** for refinements ("make it more X")
3. **Build Iteratively** - start rough, refine through conversation
4. **Leverage Context** - reference "the previous image" naturally
5. **Use Specialized Tools** for specific domains (product, UI)
6. **Monitor Sessions** - check status and manage active sessions

### 📋 Common Patterns

#### Logo Design Session
```python
session = create_image_session("Logo design for TechCorp")
generate_image_in_session(session_id, "modern tech company logo")
generate_image_in_session(session_id, "make it more geometric")
generate_image_in_session(session_id, "add blue gradient") 
generate_image_in_session(session_id, "create transparent background version")
```

#### Product Photography Session
```python
session = create_image_session("Product catalog for wireless headphones")
generate_product_image("wireless headphones", session_id=session_id, angle="front")
generate_product_image("same headphones", session_id=session_id, angle="side")
generate_image_in_session(session_id, "lifestyle shot with person wearing them")
```

#### UI Design System Session
```python
session = create_image_session("Mobile app UI components")
generate_ui_asset("icon", "home icon", session_id=session_id)
generate_ui_asset("icon", "profile icon in same style", session_id=session_id)
generate_ui_asset("button", "primary button matching icons", session_id=session_id)
```

### ❌ Common Mistakes

- **Not using sessions** for related images (misses context benefits)
- **Too vague prompts** - "make it better" vs "increase contrast and saturation"
- **Forgetting session_id** when you want context
- **Creating too many sessions** - group related work together
- **Not closing sessions** when done (resource waste)

## 📊 Session Management

### Monitoring Active Sessions
```python
# See all your sessions
sessions = list_active_sessions()
print(f"You have {sessions['total_active']} active sessions")

# Check specific session details
status = get_session_status("uuid-123")
print(f"Session has {status['total_generations']} images")
```

### Resource Management
```python
# Close completed sessions
close_session("uuid-123")

# Check server resource usage
stats = get_server_stats()
print(f"Server has {stats['active_sessions']} sessions active")
```

## 🆘 Troubleshooting

### Session Issues
- **"Session not found"** - Check session_id, session may have expired
- **"Max sessions reached"** - Close unused sessions with `close_session`
- **"Session timeout"** - Sessions expire after 1 hour of inactivity

### Generation Issues  
- **"Invalid parameters"** - Use "auto" for model/quality when unsure
- **"Content policy violation"** - Refine prompt to be more specific/professional
- **"No context available"** - Ensure you're using correct session_id

### File Issues
- **"Image not found"** - Check file paths, ensure images exist
- **"Invalid mask"** - Mask must be same size as reference image
- **"Upload failed"** - Check file size (25MB limit) and format

## 🎯 Quick Reference

### Essential Session Workflow
```python
# 1. Start session
session = create_image_session("Project description")

# 2. Generate and refine
generate_image_in_session(session["session_id"], "initial prompt")
generate_image_in_session(session["session_id"], "refinement instruction")

# 3. Clean up
close_session(session["session_id"])
```

### Single-Shot Quick Tasks
```python
# Quick image
generate_image("description")

# Quick edit  
edit_image("/path/to/image.png", "change description")

# Specialized generation
generate_product_image("product description")
generate_ui_asset("icon", "icon description")
```

### Server Management
```python
# Check resources
get_server_stats()

# Get help
get_usage_guide()
```

---

## 🚀 Getting Started

**New to v2.0?** Start with a simple session:

```python
# Create your first session
session = create_image_session("Testing the new system")

# Generate an image
result = generate_image_in_session(
    session["session_id"], 
    "a beautiful sunset over mountains"
)

# Refine it naturally
result2 = generate_image_in_session(
    session["session_id"],
    "make the colors more vibrant"
)

# Check your session
status = get_session_status(session["session_id"])

# Close when done
close_session(session["session_id"])
```

The session-based approach enables natural, conversational image generation that builds on context for superior results. Start with sessions for any project involving multiple images or refinements!

---

**Remember:** Sessions are your superpower. Use them for any project requiring multiple images, refinements, or consistency across generations. The conversation-driven approach produces dramatically better results than isolated single-shot generations.