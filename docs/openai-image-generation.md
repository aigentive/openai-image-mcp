# OpenAI Image Generation API Reference

**Document Date:** May 24, 2025  
**Source:** OpenAI Platform Documentation  
**Models Covered:** GPT-Image-1, DALL-E 3, DALL-E 2

## Overview

The OpenAI API provides powerful image generation and editing capabilities through multiple models and APIs. This document covers all available options, parameters, use cases, and implementation details for working with images as both input and output.

## API Types

### 1. Image API
Traditional endpoint-based API with three main capabilities:
- **Generations**: Generate images from text prompts
- **Edits**: Modify existing images using prompts
- **Variations**: Generate variations of existing images (DALL-E 2 only)

**Supported Models:** `gpt-image-1`, `dall-e-3`, `dall-e-2`

### 2. Responses API
Conversational API supporting multi-turn interactions:
- **Multi-turn editing**: Iterative high-fidelity edits
- **Streaming**: Partial image display during generation
- **Flexible inputs**: File IDs and base64 images
- **Context awareness**: Images within conversation flow

**Supported Models:** `gpt-image-1` only (for image generation tool)

## Model Comparison

| Model | API Support | Capabilities | Use Case |
|-------|-------------|--------------|----------|
| **GPT-Image-1** | Image API: Generations, Edits<br>Responses API: Full support | • Superior instruction following<br>• Text rendering<br>• Detailed editing<br>• Real-world knowledge<br>• Transparent backgrounds | **Recommended**: Best overall choice for high-quality, contextual image generation |
| **DALL-E 3** | Image API: Generations only | • Higher image quality than DALL-E 2<br>• Larger resolutions (1792x1024, 1024x1792)<br>• Automatic prompt enhancement<br>• HD quality option | **Previous generation**: Good quality but limited compared to GPT-Image-1 |
| **DALL-E 2** | Image API: Generations, Edits, Variations | • Lower cost<br>• Concurrent requests<br>• Inpainting with masks<br>• Image variations | **Legacy**: Cost-effective option, advanced editing features |

> **Note**: OpenAI recommends using GPT-Image-1 over DALL-E 3 for better experience and capabilities.

## Image Generation

### Basic Generation (Image API)

```python
from openai import OpenAI
import base64

client = OpenAI()

result = client.images.generate(
    model="gpt-image-1",
    prompt="A children's book drawing of a veterinarian using a stethoscope to listen to the heartbeat of a baby otter.",
    size="1024x1024",
    quality="high",
    background="transparent"
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

with open("otter.png", "wb") as f:
    f.write(image_bytes)
```

### Multi-turn Generation (Responses API)

```python
import openai
import base64

# Initial generation
response = openai.responses.create(
    model="gpt-4.1-mini",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

# Extract image
image_generation_calls = [
    output for output in response.output 
    if output.type == "image_generation_call"
]

# Follow-up edit
response_followup = openai.responses.create(
    model="gpt-4.1-mini",
    input=[
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "Now make it look realistic"}],
        },
        {
            "type": "image_generation_call",
            "id": image_generation_calls[0].id,
        },
    ],
    tools=[{"type": "image_generation"}],
)
```

### Streaming Generation

```python
from openai import OpenAI
import base64

client = OpenAI()

stream = client.responses.create(
    model="gpt-4.1",
    input="Draw a gorgeous image of a river made of white owl feathers",
    stream=True,
    tools=[{"type": "image_generation", "partial_images": 2}],
)

for event in stream:
    if event.type == "response.image_generation_call.partial_image":
        idx = event.partial_image_index
        image_base64 = event.partial_image_b64
        image_bytes = base64.b64decode(image_base64)
        with open(f"river_{idx}.png", "wb") as f:
            f.write(image_bytes)
```

### DALL-E 3 Generation (Image API)

```python
from openai import OpenAI

client = OpenAI()

# Basic DALL-E 3 generation
result = client.images.generate(
    model="dall-e-3",
    prompt="a white siamese cat",
    size="1024x1024",
    quality="standard",
    response_format="url"  # or "b64_json"
)

print(result.data[0].url)

# High-quality generation with larger size
result = client.images.generate(
    model="dall-e-3",
    prompt="a futuristic cityscape at sunset",
    size="1792x1024",  # Landscape format
    quality="hd",
    response_format="b64_json"
)

# Access the revised prompt
print("Original prompt:", "a futuristic cityscape at sunset")
print("Revised prompt:", result.data[0].revised_prompt)
```

#### DALL-E 3 Prompting Tips

DALL-E 3 automatically rewrites prompts for safety and detail enhancement. To get outputs closer to your original request:

```python
# Add this instruction to minimize prompt modifications
prompt = """I NEED to test how the tool works with extremely simple prompts. 
DO NOT add any detail, just use it AS-IS: a red apple on a white table"""

result = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024"
)
```

#### DALL-E 3 Specific Parameters

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `size` | `1024x1024`, `1024x1792`, `1792x1024`, `auto` | `1024x1024` | Supports portrait and landscape |
| `quality` | `standard`, `hd` | `standard` | HD costs more but higher quality |
| `response_format` | `url`, `b64_json` | `url` | URL for hosted images, b64 for direct data |
| `style` | Not supported | N/A | Unlike GPT-Image-1, no style parameter |

#### DALL-E 3 Limitations

- **No Image Editing**: Edit endpoint not available
- **No Variations**: Cannot generate variations of existing images
- **Text Rendering**: Struggles with legible text
- **Instruction Following**: Has trouble with precise instructions
- **Photorealism**: Cannot generate highly photorealistic images
- **Prompt Modification**: Always modifies prompts, cannot be disabled

### DALL-E 2 Generation (Image API)

```python
from openai import OpenAI

client = OpenAI()

# Basic DALL-E 2 generation
result = client.images.generate(
    model="dall-e-2",
    prompt="a white siamese cat",
    size="1024x1024",
    quality="standard",
    n=1,
)

print(result.data[0].url)

# Generate multiple images at once
result = client.images.generate(
    model="dall-e-2",
    prompt="a futuristic robot in a garden",
    size="512x512",
    n=4,  # Generate 4 variations
    response_format="url"
)

for i, image in enumerate(result.data):
    print(f"Image {i+1}: {image.url}")
```

#### DALL-E 2 Image Editing (Inpainting)

```python
from openai import OpenAI

client = OpenAI()

# Edit an image using a mask
result = client.images.edit(
    model="dall-e-2",
    image=open("sunlit_lounge.png", "rb"),
    mask=open("mask.png", "rb"),
    prompt="A sunlit indoor lounge area with a pool containing a flamingo",
    n=1,
    size="1024x1024",
)

print(result.data[0].url)
```

#### DALL-E 2 Image Variations

```python
from openai import OpenAI

client = OpenAI()

# Generate variations of an existing image
result = client.images.create_variation(
    model="dall-e-2",
    image=open("corgi_and_cat_paw.png", "rb"),
    n=3,  # Generate 3 variations
    size="1024x1024"
)

for i, image in enumerate(result.data):
    print(f"Variation {i+1}: {image.url}")
```

#### DALL-E 2 Specific Parameters

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `size` | `256x256`, `512x512`, `1024x1024` | `1024x1024` | Square formats only |
| `quality` | `standard` | `standard` | Fixed quality level |
| `n` | `1-10` | `1` | Can generate multiple images per request |
| `response_format` | `url`, `b64_json` | `url` | URL for hosted images, b64 for direct data |

#### DALL-E 2 File Requirements

**For Image Editing and Variations:**
- Must be square PNG images
- Maximum size: 4MB
- For masks: Must contain alpha channel
- Transparent areas in mask will be replaced
- Filled areas in mask remain unchanged

#### DALL-E 2 Limitations

- **Text Rendering**: Struggles with legible text
- **Instruction Following**: Has trouble following instructions
- **Realism**: Cannot generate realistic images
- **Size Limitations**: Only square formats (256x256, 512x512, 1024x1024)
- **Quality**: Fixed standard quality only
- **Older Model**: Significant limitations compared to newer models

> **Note**: OpenAI recommends using GPT-Image-1 over DALL-E 2 for better experience.

## Image Editing

### Using Reference Images

```python
from openai import OpenAI
import base64

client = OpenAI()

prompt = """Generate a photorealistic image of a gift basket on a white background 
labeled 'Relax & Unwind' with a ribbon and handwriting-like font, 
containing all the items in the reference pictures."""

# Multiple input methods
base64_image1 = encode_image("body-lotion.png")
file_id1 = create_file("incense-kit.png")

response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image1}",
                },
                {
                    "type": "input_image",
                    "file_id": file_id1,
                }
            ],
        }
    ],
    tools=[{"type": "image_generation"}],
)
```

### Inpainting with Masks

```python
from openai import OpenAI

client = OpenAI()

fileId = create_file("sunlit_lounge.png")
maskId = create_file("mask.png")

response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "generate an image of the same sunlit indoor lounge area with a pool but the pool should contain a flamingo",
                },
                {
                    "type": "input_image",
                    "file_id": fileId,
                }
            ],
        },
    ],
    tools=[
        {
            "type": "image_generation",
            "quality": "high",
            "input_image_mask": {
                "file_id": maskId,
            },
        },
    ],
)
```

**Mask Requirements:**
- Same format and size as base image
- Must contain alpha channel
- Transparent areas will be replaced
- Filled areas remain unchanged
- Maximum size: 25MB

## Parameters Reference

### Size Options

**GPT-Image-1:**
- `1024x1024` (square) - Default, fastest generation
- `1536x1024` (landscape)
- `1024x1536` (portrait)
- `auto` - Model selects optimal size

**DALL-E 3:**
- `1024x1024` (square) - Default
- `1792x1024` (landscape) - Wider format
- `1024x1792` (portrait) - Taller format
- `auto` - Model selects optimal size

**DALL-E 2:**
- `1024x1024`, `512x512`, `256x256` (square only)

### Quality Options

**GPT-Image-1:**
- `low` - Fastest, lowest token cost
- `medium` - Balanced quality/speed
- `high` - Best quality, highest token cost
- `auto` - Model selects optimal quality (default)

**DALL-E 3:**
- `standard` - Default quality
- `hd` - Higher quality, increased cost

**DALL-E 2:**
- Quality is fixed (no quality parameter)

### Format Options
- `png` - Default, supports transparency
- `jpeg` - Smaller file size, supports compression
- `webp` - Modern format, supports transparency and compression

### Compression (JPEG/WebP only)
- Range: `0-100%`
- Example: `output_compression=50` for 50% compression

### Background Options
- `transparent` - Only with PNG/WebP, works best with medium/high quality
- `auto` - Default, model decides

### Moderation Levels (GPT-Image-1 only)
- `auto` - Standard filtering (default)
- `low` - Less restrictive filtering

## Token Usage and Costs

### GPT-Image-1 Token Costs

| Quality | Square (1024×1024) | Portrait (1024×1536) | Landscape (1536×1024) |
|---------|-------------------|---------------------|---------------------|
| Low     | 272 tokens        | 408 tokens          | 400 tokens          |
| Medium  | 1,056 tokens      | 1,584 tokens        | 1,568 tokens        |
| High    | 4,160 tokens      | 6,240 tokens        | 6,208 tokens        |

### DALL-E 3 Fixed Costs

DALL-E 3 uses fixed pricing per image (not token-based):

| Size | Quality | Cost per Image |
|------|---------|----------------|
| 1024×1024 | Standard | Fixed rate |
| 1024×1024 | HD | Higher fixed rate |
| 1024×1792 | Standard | Higher fixed rate |
| 1024×1792 | HD | Highest fixed rate |
| 1792×1024 | Standard | Higher fixed rate |
| 1792×1024 | HD | Highest fixed rate |

> **Note**: See [OpenAI Pricing Page](https://openai.com/pricing) for current DALL-E 3 rates.

### DALL-E 2 Fixed Costs

DALL-E 2 uses fixed pricing per image based on size:

| Size | Cost per Image | Use Case |
|------|----------------|----------|
| 256×256 | Lowest fixed rate | Thumbnails, previews |
| 512×512 | Medium fixed rate | Social media, web graphics |
| 1024×1024 | Higher fixed rate | High-quality images |

**Additional Operations:**
- **Image Edits**: Same pricing as generations
- **Image Variations**: Same pricing as generations
- **Multiple Images**: Cost scales linearly with `n` parameter

### Cost Calculation by Model

**GPT-Image-1:**
```
Total Cost = Input Text Tokens + Input Image Tokens (if editing) + Output Image Tokens
```

**DALL-E 3 & DALL-E 2:**
```
Total Cost = Fixed Cost per Image × Number of Images
```

### Streaming Costs (GPT-Image-1 only)
- Each partial image adds **100 additional tokens**
- Can request 1-3 partial images via `partial_images` parameter

## Use Cases and Examples

### 1. Simple Image Generation
```python
# Basic generation for logos, illustrations, concept art
client.images.generate(
    model="gpt-image-1",
    prompt="Modern minimalist logo for a tech startup",
    size="1024x1024",
    background="transparent"
)
```

### 2. Product Photography
```python
# Product images with specific styling
client.images.generate(
    model="gpt-image-1",
    prompt="Professional product photo of wireless headphones on marble surface with soft lighting",
    size="1536x1024",
    quality="high"
)
```

### 3. Character Consistency
```python
# Multi-turn for consistent character development
# First: Generate base character
# Follow-up: "Same character but in different pose/setting"
```

### 4. Image-to-Image Transformation
```python
# Transform style while keeping content
response = client.responses.create(
    model="gpt-4.1",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Transform this photo into a watercolor painting style"},
                {"type": "input_image", "file_id": original_image_id}
            ]
        }
    ],
    tools=[{"type": "image_generation"}]
)
```

### 5. Batch Processing
```python
# Generate multiple variations
for prompt_variation in prompt_list:
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt_variation,
        n=1  # Note: GPT-Image-1 supports n parameter
    )
```

### 6. DALL-E 3 Specific Use Cases

```python
# High-resolution artwork
result = client.images.generate(
    model="dall-e-3",
    prompt="An oil painting of a medieval castle on a hilltop at golden hour",
    size="1792x1024",  # Landscape format
    quality="hd"
)

# Poster design with simple prompts
prompt = """I NEED to test how the tool works with extremely simple prompts. 
DO NOT add any detail, just use it AS-IS: minimalist poster design with blue circle"""

result = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1792",  # Portrait format for poster
    quality="hd"
)

# Artistic style generation (DALL-E 3 excels at artistic styles)
result = client.images.generate(
    model="dall-e-3",
    prompt="A watercolor painting of cherry blossoms in springtime",
    size="1024x1024",
    quality="standard"
)
```

### 7. DALL-E 2 Specific Use Cases

```python
# Cost-effective batch generation
prompts = [
    "a red sports car",
    "a blue mountain landscape", 
    "a green forest scene"
]

for prompt in prompts:
    result = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="512x512",  # Lower cost option
        n=3  # Generate multiple variations
    )
    
    for i, image in enumerate(result.data):
        # Save each variation
        download_image(image.url, f"{prompt}_{i}.png")

# Image editing workflow
original_image = "room.png"
mask_image = "room_mask.png"

# Edit specific parts of an image
result = client.images.edit(
    model="dall-e-2",
    image=open(original_image, "rb"),
    mask=open(mask_image, "rb"),
    prompt="A cozy living room with a fireplace and warm lighting",
    size="1024x1024",
    n=2  # Generate 2 edit variations
)

# Generate variations of successful images
best_image = "best_result.png"

variations = client.images.create_variation(
    model="dall-e-2",
    image=open(best_image, "rb"),
    n=4,  # Create 4 variations
    size="1024x1024"
)

# Thumbnail generation for previews
result = client.images.generate(
    model="dall-e-2",
    prompt="product icon for mobile app",
    size="256x256",  # Small size for thumbnails
    n=5  # Multiple options to choose from
)
```

### 8. Model Selection Guidelines

```python
# Choose model based on requirements

def select_model_for_task(task_type, quality_needed, budget_conscious):
    if task_type == "conversational" or quality_needed == "highest":
        return "gpt-image-1"
    elif task_type == "single_generation" and quality_needed == "high":
        return "dall-e-3"
    elif task_type in ["editing", "variations"] or budget_conscious:
        return "dall-e-2"
    else:
        return "gpt-image-1"  # Default recommendation

# Usage examples
model = select_model_for_task("editing", "medium", True)  # Returns "dall-e-2"
model = select_model_for_task("single_generation", "highest", False)  # Returns "gpt-image-1"
```

## Input Image Handling

### Supported Input Methods

1. **Base64 Data URLs**
   ```python
   "image_url": f"data:image/jpeg;base64,{base64_string}"
   ```

2. **File IDs** (via Files API)
   ```python
   file_id = client.files.create(
       file=open("image.png", "rb"),
       purpose="vision"
   ).id
   ```

3. **Direct URLs** (coming soon to Responses API)

### File Requirements
- **Maximum size**: 25MB
- **Supported formats**: PNG, JPEG, WebP, GIF
- **For masks**: Must include alpha channel

## Limitations and Considerations

### Model-Specific Limitations

#### GPT-Image-1
- **Latency**: Complex prompts may take up to 2 minutes
- **Text Rendering**: Improved but still challenging for precise text placement
- **Consistency**: May struggle with recurring characters across generations
- **Composition Control**: Difficulty with precise element placement in complex layouts

#### DALL-E 3
- **No Image Editing**: Edit endpoint not available
- **No Variations**: Cannot generate variations of existing images
- **Text Rendering**: Struggles with legible text
- **Instruction Following**: Has trouble with precise instructions
- **Photorealism**: Cannot generate highly photorealistic images
- **Prompt Modification**: Always modifies prompts, cannot be disabled

#### DALL-E 2
- **Text Rendering**: Struggles with legible text (most limited)
- **Instruction Following**: Has trouble following instructions
- **Realism**: Cannot generate realistic images
- **Size Limitations**: Only square formats (256x256, 512x512, 1024x1024)
- **Quality**: Fixed standard quality only
- **Older Architecture**: Significant limitations compared to newer models

### File Size and Format Limitations

| Model | Input Image Size | Supported Formats | Mask Requirements |
|-------|-----------------|-------------------|-------------------|
| **GPT-Image-1** | 25MB max | PNG, JPEG, WebP, GIF | Must match base image size, alpha channel required |
| **DALL-E 3** | Not applicable | Not applicable | No editing support |
| **DALL-E 2** | 4MB max | PNG only | Square PNG with alpha channel, same size as base |

### Content Moderation
- All prompts and images filtered per OpenAI content policy
- Configurable moderation strictness with GPT-Image-1 only
- Some content categories may be restricted across all models

### Technical Limitations by Model

**Token-based models (GPT-Image-1):**
- Token limits apply to both input and output
- Cost varies with complexity and size

**Fixed-cost models (DALL-E 2, DALL-E 3):**
- Fixed pricing per image regardless of complexity
- File size restrictions more stringent

## Best Practices

### 1. Prompt Engineering
```python
# Good: Specific, descriptive prompts
"Professional headshot of a confident business woman in navy blue suit, 
soft natural lighting, corporate office background, shot with 85mm lens"

# Avoid: Vague prompts
"Picture of a person"
```

### 2. Quality vs. Cost Optimization
```python
# For previews/thumbnails: use low quality
# For final output: use high quality
# For social media: medium quality often sufficient
```

### 3. Format Selection
```python
# PNG: When transparency needed
# JPEG: For photographs, when file size matters
# WebP: Best of both worlds, modern browsers
```

### 4. Multi-turn Workflows
```python
# 1. Generate base image
# 2. Review and provide feedback
# 3. Refine with specific edits
# 4. Final touches and style adjustments
```

### 5. Error Handling
```python
try:
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )
except Exception as e:
    # Handle rate limits, content policy violations, etc.
    print(f"Generation failed: {e}")
```

## Supported Models for Responses API

The following models support image generation tools in the Responses API:
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4.1`
- `gpt-4.1-mini`
- `gpt-4.1-nano`
- `o3`

## Advanced Features

### Revised Prompts
GPT-Image-1 automatically revises prompts for better results:

```python
# Access revised prompt from response
{
    "id": "ig_123",
    "type": "image_generation_call",
    "status": "completed",
    "revised_prompt": "A gray tabby cat hugging an otter. The otter is wearing an orange scarf...",
    "result": "..."
}
```

### Transparent Backgrounds
```python
# Enable transparency for sprites, logos, cutouts
client.images.generate(
    model="gpt-image-1",
    prompt="2D pixel art sprite of a tabby cat",
    background="transparent",
    quality="high",
    format="png"  # Required for transparency
)
```

### Streaming for Better UX
```python
# Show progressive results to users
stream = client.responses.create(
    model="gpt-4.1",
    input=prompt,
    stream=True,
    tools=[{"type": "image_generation", "partial_images": 3}]
)
```

---

**Note**: This documentation is based on OpenAI's official platform documentation as of May 24, 2025. Features and parameters may evolve. Always refer to the latest OpenAI API documentation for the most current information.