# LLM Usage Guide: OpenAI Image Generation MCP Tools

**Version:** 1.0  
**Updated:** January 24, 2025  
**For:** Large Language Models using the OpenAI Image MCP Server

## Quick Decision Tree

**Start here for tool selection:**

1. 🆕 **Need to create a new image?** → `generate_image`
2. ✏️ **Need to modify existing image?** → `edit_image_advanced`  
3. 🛍️ **Creating product photos?** → `generate_product_image`
4. 🎨 **Making UI/web assets?** → `generate_ui_asset`
5. 📚 **Need multiple images?** → `batch_generate`
6. 🔄 **Image needs improvement?** → `analyze_and_regenerate`
7. ❓ **Need usage guidance?** → `get_usage_guide`

## Core Principles

### 1. Embrace "Auto" Mode
- **Default to "auto"** for model, quality, and size parameters
- The server intelligently selects optimal settings based on your requirements
- Only specify explicit values when you have specific needs

### 2. Be Specific in Prompts
- **Good:** "Professional product photo of wireless noise-canceling headphones on white background with soft studio lighting"
- **Poor:** "Picture of headphones"

### 3. Use Specialized Tools
- Don't use `generate_image` for everything
- Specialized tools provide better results for their use cases

### 4. Consider Cost
- Batch operations are more cost-effective
- "auto" quality balances cost and quality
- GPT-Image-1 uses token-based pricing, DALL-E uses fixed pricing

## Tool Reference Guide

### `generate_image` - Your Primary Tool

**When to use:**
- General image generation
- Single images
- When unsure which specialized tool to use

**Key Parameters:**
```
prompt (required): Be detailed and specific
model: "auto" (recommended) | "gpt-image-1" | "dall-e-3" | "dall-e-2"
quality: "auto" (recommended) | "low" | "medium" | "high" | "hd"
background: "auto" | "transparent" (for logos/icons)
format: "png" (default) | "jpeg" | "webp"
```

**Smart Defaults:**
- Model selection based on prompt analysis
- Quality optimization for use case
- Cost-aware parameter selection

**Examples:**
```python
# Let the server optimize everything
generate_image("sunset landscape with mountains")

# Specify requirements
generate_image("company logo with transparent background", 
               background="transparent", quality="high")

# Force specific model for artistic work
generate_image("abstract watercolor painting", model="dall-e-3")
```

### `edit_image_advanced` - For Image Modifications

**When to use:**
- Modifying existing images
- Removing/adding objects
- Style transformations
- Creating variations

**Modes:**
- **"inpaint"**: Replace specific areas (requires mask)
- **"outpaint"**: Extend image boundaries  
- **"variation"**: Create similar versions
- **"style_transfer"**: Apply artistic styles

**Examples:**
```python
# Remove object (requires mask)
edit_image_advanced("photo.jpg", "remove the car", 
                   mode="inpaint", mask_path="car_mask.png")

# Style transformation
edit_image_advanced("portrait.jpg", "make it look like a Renaissance painting", 
                   mode="style_transfer")

# Create variation
edit_image_advanced("logo.png", "same design but with blue color scheme", 
                   mode="variation")
```

### `generate_product_image` - For E-commerce

**When to use:**
- Product photography
- E-commerce listings
- Catalog images
- Marketing materials

**Key Features:**
- Automatically uses GPT-Image-1 for best realism
- Organized file storage by product
- Professional photography optimization

**Background Types:**
- **"transparent"**: For product cutouts, overlays
- **"white"**: Clean, professional backgrounds
- **"lifestyle"**: Products in real-world settings
- **"custom"**: Specify in prompt

**Examples:**
```python
# Clean product shot
generate_product_image("wireless mouse", background_type="white", 
                      angle="45deg", lighting="studio")

# Lifestyle scene
generate_product_image("coffee mug", background_type="lifestyle", 
                      props="coffee beans, wooden table, morning light")

# Multiple angles for catalog
generate_product_image("smartphone", angle="multiple", batch_count=3)
```

### `generate_ui_asset` - For Design Assets

**When to use:**
- App/web design
- Icons and illustrations
- Hero images
- UI components

**Asset Types:**
- **"icon"**: App icons, interface icons (auto-sized to 512x512)
- **"illustration"**: Detailed graphics (1024x1024)
- **"hero"**: Banner/header images (1200x600)
- **"background"**: UI backgrounds (1920x1080)

**Style Presets:**
- **"flat"**: Modern flat design
- **"gradient"**: Gradient effects
- **"3d"**: Subtle depth and shadows
- **"outline"**: Line art style

**Examples:**
```python
# App icon
generate_ui_asset("icon", "shopping cart with rounded modern design", 
                 style_preset="flat", theme="light")

# Hero image
generate_ui_asset("hero", "team collaboration in modern office", 
                 dimensions="1200x600", theme="light")

# Background pattern
generate_ui_asset("background", "subtle geometric pattern", 
                 style_preset="gradient", theme="dark")
```

### `batch_generate` - For Multiple Images

**When to use:**
- Content series
- A/B testing variations
- Multiple related images
- Social media content

**Input Formats:**
- JSON array: `'["prompt1", "prompt2", "prompt3"]'`
- Newline-separated: `"prompt1\nprompt2\nprompt3"`

**Key Features:**
- Cost optimization for bulk generation
- Consistent styling across batch
- Organized output folders
- Progress tracking

**Examples:**
```python
# Social media series
batch_generate('["Monday motivation quote", "Tuesday tip", "Wednesday wisdom"]',
               consistent_style="minimalist typography on pastel background")

# Product variations
batch_generate('["red sports car", "blue sports car", "green sports car"]',
               variations_per_prompt=2, model="dall-e-3")

# A/B testing
batch_generate('["CTA button - primary blue", "CTA button - success green"]',
               variations_per_prompt=3)
```

### `analyze_and_regenerate` - For Iterative Improvement

**When to use:**
- Initial results need refinement
- Quality improvement
- Fixing specific issues
- Iterative design process

**Best Practices:**
- Be specific about what needs improvement
- Use `preserve_elements` to maintain good aspects
- Set appropriate `max_iterations` for cost control

**Examples:**
```python
# Improve quality
analyze_and_regenerate("draft_logo.png", 
                      "make more professional and polished",
                      preserve_elements="colors and overall layout")

# Fix specific issues
analyze_and_regenerate("portrait.jpg",
                      "improve lighting and make eyes more prominent",
                      max_iterations=2)
```

## Model Selection Cheat Sheet

| **Need** | **Use Model** | **Why** |
|----------|---------------|---------|
| Text in images | GPT-Image-1 | Superior text rendering |
| Product photos | GPT-Image-1 | Best realism and detail |
| UI/icons | GPT-Image-1 | Clean graphics, transparency |
| Artistic images | DALL-E 3 | Artistic styles, larger sizes |
| Budget option | DALL-E 2 | Most cost-effective |
| Batch generation | DALL-E 2 | Cost optimization |
| **Default choice** | **"auto"** | **Smart selection** |

## Quality Guidelines

| **Quality** | **Use For** | **Cost** |
|-------------|-------------|----------|
| "auto" | Most cases | Optimized |
| "low" | Drafts, testing | Lowest |
| "medium" | Social media, web | Balanced |
| "high" | Professional, print | Higher |
| "hd" | Premium output | Highest |

## Cost Optimization Tips

### 1. Smart Defaults
- Use "auto" for model and quality
- Let the server optimize parameters

### 2. Batch Processing
- Use `batch_generate` for multiple related images
- More cost-effective than individual calls

### 3. Quality Selection
- "auto" quality balances cost and output
- Only use "high"/"hd" when necessary

### 4. Model Awareness
- **GPT-Image-1**: Token-based (varies with complexity)
- **DALL-E 3**: Fixed per image (higher cost)
- **DALL-E 2**: Fixed per image (lower cost)

## Common Patterns

### Logo Design
```python
generate_image("minimalist logo for tech startup", 
               background="transparent", quality="high", format="png")
```

### Social Media Content
```python
batch_generate('["Monday motivation", "Tuesday tip", "Wednesday wisdom"]',
               consistent_style="Instagram post, colorful gradient background")
```

### Product Catalog
```python
generate_product_image("product name", background_type="white", 
                      angle="multiple", batch_count=4)
```

### Website Assets
```python
# Hero image
generate_ui_asset("hero", "modern team working together", 
                 dimensions="1200x600")

# Icons
generate_ui_asset("icon", "download symbol", style_preset="outline")
```

### Image Improvement
```python
analyze_and_regenerate("draft.png", "make more professional",
                      preserve_elements="composition and colors")
```

## Error Handling

### Common Issues & Solutions

1. **"Invalid model" errors**
   - Use "auto" instead of specific model names
   - Let the server choose optimal models

2. **"Quality not supported" errors**
   - Use "auto" for quality parameter
   - Different models support different quality levels

3. **File not found errors**
   - Ensure image paths are correct
   - Check file permissions

4. **Content policy violations**
   - Revise prompts to avoid restricted content
   - Be more specific and professional in descriptions

## File Organization

Generated images are automatically organized:

```
workspace/generated_images/
├── general/           # generate_image outputs
├── products/          # generate_product_image outputs
│   └── [product]/     # Organized by product name
├── ui_assets/         # generate_ui_asset outputs
│   ├── icons/
│   ├── illustrations/
│   └── heroes/
├── batch_generations/ # batch_generate outputs
│   └── [batch_id]/
├── edited_images/     # edit_image_advanced outputs
└── variations/        # Image variations
```

## Best Practices Summary

### ✅ Do This
- Use "auto" mode as default
- Be specific and detailed in prompts
- Choose specialized tools for specific use cases
- Use batch processing for multiple images
- Check generated metadata for insights
- Leverage automatic file organization

### ❌ Avoid This
- Generic, vague prompts
- Forcing specific models without reason
- Using `generate_image` for everything
- Ignoring cost implications
- Requesting unsupported parameter combinations

## Quick Reference

```markdown
# Most Common Patterns

# General image
generate_image("detailed prompt here")

# Logo/icon
generate_image("logo description", background="transparent")

# Product photo
generate_product_image("product description", background_type="white")

# UI asset
generate_ui_asset("icon", "icon description", style_preset="flat")

# Multiple images
batch_generate('["prompt1", "prompt2"]', consistent_style="style description")

# Improve image
analyze_and_regenerate("image.png", "improvement description")
```

---

**Remember:** When in doubt, use "auto" mode and let the server optimize for you. The intelligent selection system is designed to provide the best results with minimal configuration.