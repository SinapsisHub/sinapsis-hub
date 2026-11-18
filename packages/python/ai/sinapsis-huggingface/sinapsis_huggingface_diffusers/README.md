<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Huggingface-Diffusers
<br>
</h1>

<h3 align="center">Compose image and video generation with Hugging Face Diffusers.</h3>

## Overview

**`sinapsis-huggingface-diffusers`** — Templates for HuggingFace Diffusers, supporting text-to-image, image-to-image, video generation, and inpainting workflows.

Image generation is often one stage in a wider pipeline: prompt preparation, generation, mask processing, upscaling and saving. Diffusers Templates let each stage exchange Sinapsis image packets while allowing the underlying pipeline to change.

### Where it fits

Text-to-image, image-to-image and inpainting have different input requirements. High-resolution and video generation can consume substantial VRAM; pick the model pipeline and optional transforms appropriate to the task.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-huggingface-diffusers
# or
pip install sinapsis-huggingface-diffusers
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-image-transforms` | Sinapsis image transforms support. **Dependencies:** `sinapsis-albumentations` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-image-transforms`. |

For example:

```bash
uv pip install "sinapsis-huggingface-diffusers[sinapsis-image-transforms]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">📦 Features</h2>

The templates in this package include functionality to:

- **TextToImageDiffusers**: Generates images from text prompts.
- **ImageToImageDiffusers**: Modifies images using text-guided transformations.
- **InpaintingDiffusers**: Supports selective image editing using masks or bounding boxes.
- **ImageToVideoGenXLDiffusers**: Converts images into videos using the **I2VGen-XL** model.

## Example Agent

The following is adapted directly from the package’s shipped [`text_to_image.yml`](src/sinapsis_huggingface_diffusers/configs/text_to_image.yml) configuration. Save it as `my_huggingface_diffusers_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_huggingface_diffusers_agent
  description: "Diffusers text to image generation"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: TextToImageDiffusers
    class_name: TextToImageDiffusers
    template_input: InputTemplate
    attributes:
      model_path: stable-diffusion-v1-5/stable-diffusion-v1-5
      device: cuda
      torch_dtype: "float16"
      enable_model_cpu_offload: false
      overwrite_images: true
      generation_params:
        prompt: "A majestic castle on top of a mountain, surrounded by clouds during sunset"
        height: 1024
        width: 1024
        num_inference_steps: 50
        guidance_scale: 7.5
        negative_prompt: "low quality, blurry, distorted"
        num_images_per_prompt: 1
```

```bash
sinx jobs run my_huggingface_diffusers_agent.yaml
```

More configurations: [`text_to_image.yml`](src/sinapsis_huggingface_diffusers/configs/text_to_image.yml), [`image_to_image.yml`](src/sinapsis_huggingface_diffusers/configs/image_to_image.yml), [`inpainting.yml`](src/sinapsis_huggingface_diffusers/configs/inpainting.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
