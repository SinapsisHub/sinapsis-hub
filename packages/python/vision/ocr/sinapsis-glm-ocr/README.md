<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis GLM-OCR
<br>
</h1>

<h3 align="center">Vision-language document parsing with text, formula, table and batch modes.</h3>

## Overview

`sinapsis-glm-ocr` exposes **GLM-OCR** as `GLMOCRInference` and `GLMOCRBatchInference`. These Templates process image packets with a multimodal model and return generated text. Rather than hard-coding one recognition task, the request is controlled through the Template's `prompt`.

### When transcription alone is not enough

The GLM-OCR model supports prompts for **text recognition, table recognition, formula recognition, and structured information extraction**. That is useful for invoice fields, forms and scientific pages where the required output may be a schema or a representation of document structure instead of raw word boxes. The batch Template can process multiple images together when the model and device have sufficient memory.

This is a **vision-language generation workflow**, not a small, word-by-word OCR recogniser. Inference costs more compute than basic text spotting, and generated structured output still needs validation. The code uses a GPU-oriented Transformers stack and configured attention kernels; size your environment for the selected model.

## Installation

Requires **Python 3.13+**, compatible PyTorch/Transformers dependencies and a supported acceleration environment:

```bash
uv pip install sinapsis-glm-ocr
```

To read image files using the example below:

```bash
uv pip install "sinapsis-glm-ocr[sinapsis-data-readers]"
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
uv pip install "sinapsis-glm-ocr[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

## Templates and key attributes

`GLMOCRInference` processes images individually; `GLMOCRBatchInference` supports batch generation over multiple images.

| Attribute | Meaning |
|---|---|
| `prompt` | Instruction such as `Text Recognition:`, `Formula Recognition:` or `Table Recognition:`. |
| `init_args.pretrained_model_name_or_path` | Model source (default `zai-org/GLM-OCR`). |
| `init_args.torch_dtype` | Model precision configuration. |
| `init_args.attn_implementation` | Attention implementation compatible with your installation. |
| `init_args.device_map` | Device placement configuration. |
| `generation_config.max_new_tokens` | Maximum text-generation length. |
| `generation_config.do_sample` | Sampling mode; deterministic settings may suit extraction. |

### Example: extract a table

Save as `my_glm_ocr_agent.yaml`:

```yaml
agent:
  name: my_glm_ocr_agent

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Scans
    class_name: FolderImageDatasetCV2
    template_input: Input
    attributes:
      data_dir: dataset/input

  - template_name: ExtractTable
    class_name: GLMOCRInference
    template_input: Scans
    attributes:
      prompt: "Table Recognition:"
      generation_config:
        max_new_tokens: 2048
        do_sample: false
```

```bash
sinx jobs run my_glm_ocr_agent.yaml
```

The returned text can be parsed into rows or passed into a validation Template. For schema-driven extraction, supply a prompt that clearly specifies the required JSON structure and validate the result before writing it to a database.

Shipped examples: [text](src/sinapsis_glm_ocr/configs/inference_text.yaml), [table](src/sinapsis_glm_ocr/configs/inference_table.yaml), [JSON extraction](src/sinapsis_glm_ocr/configs/inference_json.yaml), and [batch](src/sinapsis_glm_ocr/configs/inference_batch.yaml).

### Practical constraints

- Batch inference can increase throughput but also raises peak device-memory usage.
- Prompts specify the desired representation; they do not guarantee that every output conforms to a schema.
- For simple CPU-friendly multilingual text recognition, a conventional OCR package may be more economical.

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
