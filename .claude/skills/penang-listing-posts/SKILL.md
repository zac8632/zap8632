---
name: json-prompt-generator
description: Analyze reference images and generate ready-to-use structured JSON prompts for AI image generators like ChatGPT Image 2, Nano Banana, Midjourney, and Higgsfield. Use whenever the user uploads a reference image and asks for a prompt, JSON prompt, image-to-prompt conversion, image recreation, reverse-engineering, or asks to describe an image in structured prompt format. Also use when the user mentions "prompt from reference", "recreate this image", or asks for help generating images in a specific style. Do NOT use for general image questions like "what is in this image", image editing, or asking Claude to describe an image conversationally.
---

# JSON Prompt Generator

Analyze reference images and produce ready-to-use structured JSON prompts that capture every visual quality needed to reproduce the image in an AI image generator.

## Workflow

1. **Analyze the reference image** — Identify every visual element: subject, style, lighting, materials, textures, environment, composition, camera angle, color palette, mood, atmosphere, and any visible typography or UI elements.
2. **Categorize observations** into the JSON schema sections (see Schema below).
3. **Output a single valid JSON prompt** — ready to paste with zero edits.
4. **Provide a brief plain-English breakdown** (3-5 sentences) explaining key creative decisions so the user can tweak if needed.
5. **Suggest 1-3 tweaks** — concrete variations the user might want to try.

## Response Format

Structure every response with these three sections in this exact order:

### Analysis
3-5 sentence breakdown of what you observe in the reference and the key creative decisions you're encoding.

### JSON Prompt
The full JSON block following the schema below.

### Tweaks
1-3 optional suggestions for variations (e.g., "swap to dramatic side-lighting", "try 35mm focal length for a wider environmental feel", "darken the background to charcoal for a moody version").

## JSON Schema

Every prompt must follow this structure. Populate each section based on what you observe in the reference image. Omit sections that aren't relevant — don't pad with generic filler.

```json
{
  "prompt": {
    "scene": {
      "description": "One dense, detailed paragraph covering subject, action, setting, mood, dominant colour palette, and ALL typography/UI elements with exact text. This is the most important single field — write it as if it could stand alone as a complete image prompt.",
      "subject": "Primary subject with specific physical details (pose, clothing, expression, object specifics)",
      "setting": "Location, environment, context, period/era if relevant",
      "action": "What is happening — or 'static' with description if nothing is moving"
    },
    "style": {
      "primary": "photorealistic | cinematic | documentary | editorial | fine art | commercial | illustrated | painted | [describe specific style]",
      "rendering_quality": "hyperrealistic | detailed | high-resolution | stylized",
      "surface_textures": "Describe the dominant texture treatment across the scene",
      "lighting": "Specific description — direction, quality, colour temperature, number of sources, how light interacts with the scene"
    },
    "technical": {
      "camera": {
        "focal_length": "exact mm — e.g., 24mm, 35mm, 50mm, 85mm, 100mm macro, 200mm",
        "aperture": "exact f-stop — e.g., f/1.4, f/1.8, f/2.8, f/4, f/5.6, f/8, f/11",
        "depth_of_field": "very shallow | shallow | moderate | moderate-shallow | deep — plus description of what's sharp vs soft",
        "angle": "eye level | low angle | high angle | overhead | dutch angle | first-person POV | three-quarter overhead | [specific degrees]"
      },
      "resolution": "high definition | ultra high definition | 2K | cinema-grade | editorial print quality",
      "rendering": "Shutter speed effects, noise/grain character, colour depth, bokeh quality, any post-processing look",
      "physics_accuracy": "Light behaviour specifics — refraction, caustics, reflection accuracy, shadow directionality, material interactions (only include if relevant)"
    },
    "materials": {
      "skin": "Pore detail, natural imperfections, ethnic diversity details, jewellery, tattoos (only if people present)",
      "fabric": "Thread patterns, realistic drape, wear indicators, specific fabric types and weights (only if fabric present)",
      "surfaces": "Scratches, patina, oxidation, natural irregularities — describe each distinct surface material",
      "transparency": "Refraction accuracy, surface interactions, liquid behaviour, glass properties (only if transparent elements present)"
    },
    "environment": {
      "atmosphere": "Distance haze, fog, weather effects, humidity, volumetric light, air quality",
      "time": "Time of day, season, temperature cues, natural vs artificial light mix",
      "particles": "Dust, moisture, smoke, steam, pollen, rain — anything suspended in the air"
    },
    "composition": {
      "perspective": "Perspective type, vanishing points, depth layering, leading lines",
      "framing": "rule of thirds | golden ratio | centered | symmetrical | natural frame-within-frame | split layout | [describe]",
      "subject_placement": "Precise positioning within the frame, visual weight distribution, eye path",
      "ui_elements": "EXACT text for every visible text element — headers, taglines, body copy, labels, slide counters, brand handles. Specify font style, weight, colour, alignment, and position for each. Only include if the reference contains visible text/typography."
    },
    "quality": {
      "include": ["8-12 positive quality keywords specific to THIS image"],
      "avoid": ["6-10 failure modes specific to THIS image"],
      "reference_standard": "Real-world photography/cinematography reference — specific photographers, publications, films, or design systems whose visual language matches"
    }
  }
}
```

## Core Rules

These rules determine quality. Follow them closely.

1. **Be specific, not generic.** "Warm golden-hour sunlight raking across the subject at 15 degrees from camera-left" beats "natural lighting." Precision is what makes the output useful.

2. **Match the reference image's actual qualities.** Don't default to "photorealistic" if the image is illustrated. Don't add cinematic grain if the reference is clean commercial photography. Describe what you see, not what sounds impressive.

3. **Separate visual elements into distinct objects.** If the scene has a person, a table, and a window — describe each element's materials, lighting interaction, and spatial relationship independently.

4. **Omit irrelevant sections.** A landscape with no people doesn't need `skin` textures. A product shot on white doesn't need atmospheric particles. A studio shot doesn't need the `environment` section. Keep the JSON clean — no filler.

5. **Validate JSON before outputting.** Correct brackets, commas, quotation marks. No trailing commas. The user must be able to paste this directly with zero edits.

6. **Quality keywords are non-negotiable.** Every prompt must include the `quality` object with `include` and `avoid` arrays tailored to the specific reference image — not generic.

7. **Camera settings must be realistic and match the look.**
   - Very blurry background → f/1.4–f/2.0
   - Moderately soft background → f/2.8–f/4
   - Most things sharp → f/5.6–f/8
   - Everything sharp → f/11–f/16
   - Compressed perspective / telephoto feel → 85mm–200mm
   - Normal perspective → 50mm
   - Wide/environmental → 24mm–35mm
   - Exaggerated foreground → 16mm–24mm

8. **Describe the dominant colour palette in the scene description.** This helps nail the tone. Include hex codes where relevant, especially for branded content.

9. **Every visible text element must be spelled out exactly in ui_elements.** Don't paraphrase headlines or captions — reproduce them character-for-character with font style, weight, and colour notes.

## Section-Specific Guidance

### scene
The `description` field is the most important single field. Write it as one dense, detailed paragraph that could stand alone as a complete image prompt. Include the colour palette here. The other fields (`subject`, `setting`, `action`) break out specifics for structured parsing.

### style
Match the actual image. Common pairings:
- Street/documentary → "documentary", "detailed", natural textures, available light
- Studio product → "commercial", "hyperrealistic", controlled textures, studio lighting
- Film still → "cinematic", "hyperrealistic", graded textures, dramatic lighting
- Magazine editorial → "editorial lifestyle", "hyperrealistic", natural textures, mixed lighting
- Fine art → "fine art", "detailed" or "stylized", expressive textures, artistic lighting
- Illustrated → "illustrated digital painting" or "vector flat", "stylized", painterly textures

### technical
Camera settings should be inferrable from the image. See the rules above for aperture/focal length matching.

### materials
Only include subsections that are visible in the image. Describe each material independently with enough detail that a renderer could recreate the surface. Focus on imperfections and wear — these are what make materials look real.

### environment
Skip this section entirely for studio shots on seamless backgrounds. For outdoor or environmental shots, be specific about atmospheric conditions — they dramatically affect the final render.

### composition
The `ui_elements` field is critical for any image with visible text (carousels, posters, infographics, magazine covers). Specify exact text content, font style/weight, colour, alignment, position. Treat every text element as its own object.

### quality
The `include` array should contain 8-12 keywords specific to this image's strengths. The `avoid` array should contain 6-10 potential failure modes specific to this image. The `reference_standard` should cite real photographers, publications, films, or design systems whose visual language matches.

## Multiple Images

If the user shares multiple reference images in one message, generate a separate JSON prompt for each, labelled (Image 1, Image 2, etc.), and note any shared visual language at the end.

## Modifications

If the user asks to adjust a previously generated prompt, output the full updated JSON (not a diff) and note what changed and why.

## Carousel / Multi-Slide Sets

If the user requests a multi-slide carousel, generate one full JSON prompt per slide, numbered (1/N, 2/N, etc.), keeping the brand language, layout system, and typography consistent across all slides. The hero subject changes per slide; everything else stays locked.

## Video Prompts

If the user specifies the output is for video, add a `motion` object to the JSON:

```json
"motion": {
  "camera_movement": "static | slow pan | tracking | dolly | handheld | crane | orbit",
  "subject_movement": "Describe any movement of subjects or elements",
  "duration_feel": "brief moment | sustained | continuous | looping",
  "speed": "real-time | slow motion | time-lapse | hyperlapse"
}
```

## Examples

See the `references/` folder for a worked example showing a reference image analysis, the full JSON output, and the resulting tweaks suggestions.
