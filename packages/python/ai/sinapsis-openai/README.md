<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis OpenAI
<br>
</h1>

<h3 align="center">OpenAI APIs as dynamic, type-checked Sinapsis Templates.</h3>

## Overview

`sinapsis-openai` integrates OpenAI's **chat completions, speech transcription and translation, speech synthesis, image creation, image-to-image generation, and image inpainting** into Sinapsis Agents. Input and output are handled through the framework's `DataContainer` and typed packets, so an OpenAI request can sit between readers, retrieval steps, local models, postprocessors and writers.

### Dynamic Templates, not a hard-coded model catalogue

The integration is built on Sinapsis's `BaseDynamicWrapperTemplate`. Rather than manually maintaining a new Pydantic schema for every parameter introduced by the OpenAI Python SDK, each wrapper introspects SDK client and endpoint signatures and generates its Template class and configuration fields **on demand**.

This matters in a fast-moving API: when a compatible newer `openai` SDK exposes additional parameters or model identifiers, the dynamic wrappers can pick them up without a corresponding hand-written Sinapsis wrapper for every variant. **The source of truth is the installed SDK and the provider's API**, not an out-of-date, fixed list in this README. Installing this package does not automatically upgrade the OpenAI SDK or guarantee that every new endpoint is already wrapped.

The wrapper also keeps the boundary between the two kinds of configuration clear:

- `openai_init`: parameters passed to the `OpenAI(...)` client, such as connection options, retries, or an API key.
- `model`: model identifier selected for the Template's endpoint.
- `create` / `generate` / `edit`: request-specific parameters reflected from the corresponding SDK method (depending on the Template).

The generated attributes are Pydantic-backed, so invalid or incompatible configurations can be surfaced during validation rather than scattered through custom integration code.

### Bring your own OpenAI account and API key

Calls are made with **your OpenAI API credentials and provider entitlements**. The usual setup is an environment variable:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

The implementation also accepts a key through `openai_init.api_key` when using per-Template client configuration. In the current implementation a non-empty `OPENAI_API_KEY` environment variable takes precedence over `openai_init.api_key`. For multiple accounts or projects, configure the environment and client values deliberately. Do not commit credentials in Agent YAML files.

Requests use the account's model access, quotas, and billing; the package does not provide or proxy shared OpenAI credentials.

## Installation

Python **3.13+** is required. Install the package from PyPI:

```bash
uv pip install sinapsis-openai
# or
pip install sinapsis-openai
```

For the runnable text-input example below, the `data-readers` extra installs the `TextInput` Template:

```bash
uv pip install "sinapsis-openai[data-readers]"
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `webapp-gradio` | Interactive Gradio demonstration. **Dependencies:** `sinapsis[webapp]` |
| `data-readers` | Input adapters for example workflows. **Dependencies:** `sinapsis-data-readers` |
| `all` | Bundle declared by this package; its manifest includes `webapp-gradio`, `data-readers`, `audio-generation`, `image-generation`, `encode-results`. It does not include `data-writers`. |
| `audio-generation` | Audio generation and related audio-output dependencies. **Dependencies:** `pydub`, `sinapsis-openai[encode-results]` |
| `image-generation` | Image generation and related image-output dependencies. **Dependencies:** `numpy`, `pillow`, `sinapsis-openai[encode-results]` |
| `encode-results` | Encode generated results into useful Sinapsis data representations. **Dependencies:** `sinapsis-generic-data-tools` |
| `data-writers` | Output adapters for example workflows. **Dependencies:** `sinapsis-data-writers` |

For example:

```bash
uv pip install "sinapsis-openai[webapp-gradio]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`, `ty`). These support source development and testing and are **not** runtime extras.

## Template families

| Template | What enters the Agent | What it provides |
|---|---|---|
| `OpenAIChatWrapper` | Text packets | Chat completions returned as new `TextPacket` items. |
| `OpenAIAudioTranscriptionWrapper` | Audio content / files | Speech-to-text output for downstream text processing. |
| `OpenAIAudioTranslationWrapper` | Audio content / files | Audio translation to text using the supported translation endpoint. |
| `OpenAIAudioCreationWrapper` | Text packets | Generated audio for playback, storage or further processing. |
| `OpenAIImageCreationWrapper` | Text prompt | Generated images returned through the configured result representation. |
| `OpenAIImageToImageGenerationWrapper` | Image and prompt | Image generation conditioned on an existing image. |
| `OpenAIImageInpaintingWrapper` | Image, optional mask, and prompt | Editing of selected image regions. |

The wrappers are defined in [`openai_chat.py`](src/sinapsis_openai/templates/openai_chat.py), [`openai_audio.py`](src/sinapsis_openai/templates/openai_audio.py), and [`openai_images.py`](src/sinapsis_openai/templates/openai_images.py). Actual generated class names and valid attribute fields depend on the installed SDK; inspect them with:

```bash
sinx templates show-all
sinx templates docstring OpenAIChatWrapper
sinx templates example-config OpenAIChatWrapper
```

### Practical example: text input → OpenAI chat → result packet

Create `my_openai_agent.yaml`:

```yaml
agent:
  name: my_openai_agent
  description: "Answer an incoming question through OpenAI"

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Question
    class_name: TextInput
    template_input: Input
    attributes:
      text: "Explain why native binary payloads matter in an AI pipeline."

  - template_name: Answer
    class_name: OpenAIChatWrapper
    template_input: Question
    attributes:
      model: gpt-4o-mini  # Replace with any supported model accessible to your account
      openai_init: {}
      create: {}
```

```bash
export OPENAI_API_KEY="your-openai-api-key"
sinx jobs run my_openai_agent.yaml
```

`TextInput` is provided by `sinapsis-data-readers` and installed through the `data-readers` extra shown above. The graph feeds a `TextPacket` to the chat wrapper and appends the generated response as another text packet. You can then chain validation, persistence, a search index or another model without adopting an OpenAI-specific data contract.

This example uses a commonly supported model identifier for illustration, **not a permanent recommendation or list of currently available models**. Models must be supported by the installed SDK and your OpenAI account.

### Additional workflows

The package includes reference configurations for [chat](src/sinapsis_openai/configs/config_file_chat.yaml), [audio generation](src/sinapsis_openai/configs/config_audio_generation.yaml), [audio translation](src/sinapsis_openai/configs/config_file_audio_translation.yaml), [image creation](src/sinapsis_openai/configs/config_image_creation.yaml), [image-to-image generation](src/sinapsis_openai/configs/config_image_to_image_generation.yaml), and [inpainting](src/sinapsis_openai/configs/config_image_inpainting.yaml).

For example, a content workflow might generate a concise explanation with chat, turn the text into speech, and save both packets. An image workflow may start with a reference image and use inpainting only on designated regions. These examples share the same Agent graph model, but the required input packet type and endpoint parameters differ.

### Runtime considerations

- **Network and cost:** calls are remote API operations; latency, quotas, rate limits and billing come from OpenAI.
- **Credentials:** pass your own key securely. `OPENAI_API_KEY` takes precedence over a key in `openai_init` when set.
- **API evolution:** dynamic signatures reduce wrapper maintenance, but new SDK functionality still requires installing an SDK version that exposes it. Test model and endpoint compatibility when upgrading.
- **Packet output:** generation and decoding are still governed by the chosen Template and its output mode; downstream steps should expect the appropriate text, image or audio packets.

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
