<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Huggingface-Transformers
<br>
</h1>

<h3 align="center">Use Transformers pipelines and model-specific vision or language operations as Templates.</h3>

## Overview

**`sinapsis-huggingface-transformers`** — Templates for HuggingFace Transformers, supporting automatic-speech-recognition, text-to-speech, translation and summarization templates.

Transformers spans speech recognition, translation, summarisation and vision-language tasks. A common wrapper lets these models integrate with Sinapsis packets and declarative Agent configurations instead of requiring separate application orchestration for each task.

### Where it fits

Model compatibility and processor requirements vary considerably. Choose a task and checkpoint that match the Template and your device; generic pipeline support does not imply every model supports every modality.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-huggingface-transformers
# or
pip install sinapsis-huggingface-transformers
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">📦 Features</h2>

Sinapsis Hugging Face Transformers provides customizable inference templates for a variety of tasks, including **image captioning**, **object detection**, **instance segmentation**, **speech-to-text**, and **text-to-speech**.

**Templates:**


- **ImageToTextTransformers**: Generates textual descriptions from input images using Hugging Face image-to-text models.
- **PaliGemmaInference**: Generate captions for images.
- **PaliGemmaDetection**: Detect specific objects in images.
- **SpeechToTextTransformers**: Converts spoken audio into text using automatic speech recognition (ASR) models.
- **SummarizationTransformers**: Summarizes long text into concise summaries using Hugging Face summarization models.
- **TextToSpeechTransformers**: Converts text into lifelike audio using text-to-speech (TTS) models.
- **TranslationTransformers**: Translates text from a source language to a target language using Hugging Face translation models.

## Example Agent

The following is adapted directly from the package’s shipped [`pali_gemma_inference.yml`](src/sinapsis_huggingface_transformers/configs/pali_gemma_inference.yml) configuration. Save it as `my_huggingface_transformers_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_huggingface_transformers_agent
  description: Agent to perform visual question answering using paligemma model.

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: PaliGemmaInference
  class_name: PaliGemmaInference
  template_input: InputTemplate
  attributes:
    model_path: google/paligemma2-3b-pt-224
    processor_path: google/paligemma2-3b-pt-224
    prompt: "How many plants are there in the image?"
    torch_dtype: "float16"
    device: "cuda"
```

```bash
sinx jobs run my_huggingface_transformers_agent.yaml
```

More configurations: [`pali_gemma_inference.yml`](src/sinapsis_huggingface_transformers/configs/pali_gemma_inference.yml), [`speech_to_text.yml`](src/sinapsis_huggingface_transformers/configs/speech_to_text.yml), [`pali_gemma_detection.yml`](src/sinapsis_huggingface_transformers/configs/pali_gemma_detection.yml), [`text_to_speech.yml`](src/sinapsis_huggingface_transformers/configs/text_to_speech.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
