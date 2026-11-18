<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis DeepSeek OCR
<br>
</h1>

<h3 align="center">Prompt-driven, GPU-backed document OCR with optional spatial grounding.</h3>

## Overview

`sinapsis-deepseek-ocr` integrates **DeepSeek-OCR and DeepSeek-OCR-2** through a `DeepSeekOCRInference` Template. Instead of a traditional word recogniser, the implementation loads a vision-language model through Transformers and applies a configurable instruction to each input image.

### Document understanding instead of just text spotting

Prompt-driven OCR is valuable when the objective is not merely “find the words” but “extract the information that matters from this page.” The Template accepts a `prompt` such as `"OCR the image."` and can return model-generated text as a `TextPacket`. That makes it suitable for document transcription, complex page content and postprocessing into Markdown or another structured representation.

With `enable_grounding: true`, the Template adds a grounding marker to the prompt, parses regions returned by the model, and appends bounding boxes as image annotations. This enables a spatial output path for highlighting or retrieving text regions.

**Trade-off:** the implementation explicitly loads the model on **CUDA**, uses FlashAttention by default, and needs more compute and memory than a conventional OCR detector. It is not the first choice for low-power or CPU-only text spotting. Model output is generated text and can require validation; grounding works when the selected model produces output in the expected format.

## Installation

Requires **Python 3.13+** and a compatible CUDA/PyTorch environment. The base package already depends on Transformers, PyTorch and FlashAttention:

```bash
uv pip install sinapsis-deepseek-ocr
```

For the example with a folder reader:

```bash
uv pip install "sinapsis-deepseek-ocr[sinapsis-data-readers]"
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers[opencv]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |
| `sinapsis-data-visualization` | Render plots or annotate results for inspection. **Dependencies:** `sinapsis-data-visualization[visualization-matplotlib]` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-writers`, `sinapsis-data-visualization`. |

For example:

```bash
uv pip install "sinapsis-deepseek-ocr[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

## `DeepSeekOCRInference` Template

| Attribute | Meaning |
|---|---|
| `prompt` | Natural-language instruction used to guide OCR output (default: `"OCR the image."`). |
| `enable_grounding` | When `true`, parse region coordinates and append image annotations; otherwise add a text packet. |
| `mode` | Resolution/cropping preset: `tiny`, `small`, `gundam`, `base`, `large`. |
| `init_args.pretrained_model_name_or_path` | `deepseek-ai/DeepSeek-OCR` or `deepseek-ai/DeepSeek-OCR-2` in the current schema. |
| `init_args.torch_dtype` | `auto`, `float16`, or `bfloat16`. |
| `init_args.attn_implementation` | `flash_attention_2` or `eager`. |

The resolution presets are defined in [`mode_registry.py`](src/sinapsis_deepseek_ocr/helpers/mode_registry.py). `tiny` and `small` reduce resolution; `gundam` uses a cropping path; `base` and `large` use larger target sizes. Higher resolutions can help small text but increase processing cost.

### Example: extract text from scanned pages

Save this as `my_deepseek_ocr_agent.yaml`:

```yaml
agent:
  name: my_deepseek_ocr_agent

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Pages
    class_name: FolderImageDatasetCV2
    template_input: Input
    attributes:
      data_dir: dataset/input

  - template_name: ReadPage
    class_name: DeepSeekOCRInference
    template_input: Pages
    attributes:
      prompt: "OCR the image."
      enable_grounding: false
      mode: base
```

```bash
sinx jobs run my_deepseek_ocr_agent.yaml
```

The Template appends model-generated text to the `DataContainer`. To retain located text regions instead, set `enable_grounding: true` and use a compatible grounding prompt/model; then consume the resulting `ImageAnnotations` with drawing or extraction Templates.

Shipped examples: [plain text](src/sinapsis_deepseek_ocr/configs/inference_plain_text.yaml), [grounding](src/sinapsis_deepseek_ocr/configs/inference_grounding.yaml), and [visual demo](src/sinapsis_deepseek_ocr/configs/inference_demo.yaml).

### Model and deployment considerations

- Local inference uses **your own model weights and GPU**, not a hosted API call.
- The initialization schema enables `trust_remote_code` for supported checkpoints; review the model repository and its code before deploying.
- The model may output Markdown-like text or grounded regions based on the prompt, but downstream consumers should validate unstructured/generated content before relying on it as canonical structured data.
- For fast, multilingual recognition and simple labels, a smaller conventional OCR stack such as EasyOCR may offer lower operational complexity.

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
