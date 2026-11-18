<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Dfine
<br>
</h1>

<h3 align="center">Train and deploy D-FINE object detectors.</h3>

## Overview

**`sinapsis-dfine`** — Training and inference templates based on the D-FINE architecture.

D-FINE provides a detector family for localisation tasks. Separate training, fine-tuning and inference Templates make experiments repeatable while keeping downstream annotation and tracking components unchanged.

### Where it fits

Different checkpoints and export targets have different accuracy and latency trade-offs. Use the optional data-reader, writer and visualisation extras for complete evaluation workflows.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-dfine
# or
pip install sinapsis-dfine
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers` |
| `sinapsis-data-visualization` | Render plots or annotate results for inspection. **Dependencies:** `sinapsis-data-visualization[all]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-visualization`, `sinapsis-data-writers`. |

For example:

```bash
uv pip install "sinapsis-dfine[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

The **Sinapsis D-FINE** module provides two main templates for **inference** and **training**:

- **`DFINETraining`**: A highly flexible template for fine-tuning D-FINE models on custom data. It is designed for rapid setup while still offering deep control.
  - **Effortless Setup**: Automatically infers class labels directly from the dataset, eliminating the need to manually create id2label maps.
  - **Flexible Data Sources**: Seamlessly loads datasets from both local directories and the Hugging Face Hub.
  - **Adaptable to Your Data**: Easily adapts to different dataset schemas by allowing users to specify custom keys for annotations (bbox, category, etc.) via the annotation_keys attribute.
  - **Powerful Customization**: Provides granular control over every aspect of training through structured Pydantic models for hyperparameters, data mapping, and more.
- **`DFINEInference`**: A streamlined and efficient template for running trained D-FINE models.
  - **High-Performance**: Processes images in batches for maximum throughput on the target hardware.
  - **Structured Output**: Generates clear, structured annotations for each image, including bounding boxes, confidence scores, and class labels, ready for downstream tasks.

<details>
<summary><strong><span style="font-size: 1.25em;">🌍 General Attributes</span></strong></summary>

Both templates share the following attributes:
- **`model_path` (str, optional)**: The model identifier from the Hugging Face Hub or a local path to the model and processor files. Defaults to `"ustc-community/dfine-nano-coco"`.
- **`model_cache_dir` (str, optional)**: Directory to cache downloaded model files. Defaults to the path specified by the `SINAPSIS_CACHE_DIR` environment variable.
- **`threshold` (float, required)**: The confidence score threshold (from 0.0 to 1.0) for filtering detections. For inference, it discards all detections below this value from the final output. For training, it is used on the validation dataset to filter predictions before calculating evaluation metrics.
- **`device` (Literal["auto", "cuda", "cpu"], optional)**: The hardware device to run the model on. Defaults to `"auto"`, which automatically selects `"cuda"` if a compatible GPU is available, otherwise falls back to `"cpu"`.

</details>
<details>
<summary><strong><span style="font-size: 1.25em;">Specific Attributes</span></strong></summary>

There are some attributes specific to the templates used:
- `DFINEInference` has one additional attribute:
    - **`batch_size` (int, optional)**: The number of images to process in a single batch. Defaults to `8`.
- `DFINETraining` has nine additional attributes:
    - **`training_mode` (Literal["fine-tune", "from-scratch"], optional)**: Specifies the training strategy.
    - **`dataset_path` (str, required)**: Path to the dataset to be loaded.
    - **`id2label` (dict[int, str] | None, optional)**: An optional mapping from class ID to label name. It's recommended to let the template infer this from the dataset. This attribute should only be used as a fallback if the dataset features are non-standard.
    - **`annotation_keys` (AnnotationKeys, optional)**: A configuration object that specifies the dictionary keys for accessing annotation data within the dataset.
      - **`bbox` (str, optional)**: The dictionary key for the bounding box annotations. Defaults to `"bbox"`.
      - **`category` (str, optional)**: The dictionary key for the category/class label annotations. Defaults to `"category"`.
      - **`area` (str, optional)**: The dictionary key for the bounding box area. If not provided, area will be calculated from the bbox. Defaults to `"area"`.
    - **`validation_split_size` (float, optional)**: The proportion of the dataset to reserve for validation. Defaults to `0.15`
    - **`mapping_args` (DatasetMappingArgs, optional)**: Parameters for the dataset preprocessing step.
      - **`batch_size` (int, optional)**: The batch size for applying transformations. A larger size can speed up preprocessing but requires more RAM. Defaults to `16`.
      - **`num_proc` (int, optional)**: The number of CPU processes to use for mapping. Defaults to `0` (no multiprocessing).
    - **`image_size` (TrainingImageSize, optional)**: The target image size for image resizing.
      - **`width` (int, optional)**: The target width for image resizing. Defaults to `640`.
      - **`height` (int, optional)**: The target height for image resizing. Defaults to `640`.
    - **`training_args` (TrainingArgs, optional)**: A nested configuration object for all Hugging Face `Trainer` hyperparameters. Refer to the [official documentation](https://huggingface.co/docs/transformers/main_classes/trainer#transformers.TrainingArguments) for the full list of possible arguments.
    - **`save_dir` (str, required)**: Path to the directory where the fine-tuned model will be saved.

</details>

<details>
<summary><strong><span style="font-size: 1.25em;">📁 Supported Dataset Structure</span></strong></summary>

To ensure compatibility and smooth training, the `DFINETraining` template relies on a specific dataset structure. This format is inspired by the widely used COCO dataset, making it easy to adapt many existing object detection datasets.

**IMPORTANT**: The `DFINETraining` template expects datasets to follow a specific **nested (COCO-style) format**. This ensures consistency and reliability during the data transformation process.

Each example in your dataset must contain at least two features:
1.  **`image`**: A PIL Image object.
2.  **`objects`**: A dictionary that acts as a container for all annotations related to the image.

The `objects` dictionary must contain parallel lists for the annotations. The keys for these lists are configurable via the `annotation_keys` attribute.

**Example of a single dataset entry:**
```python
{
  'image': <PIL.Image object>,
  'objects': {
    'bbox': [[x, y, width, height], [x, y, width, height], ...],
    'category': [label_id_1, label_id_2, ...],
    'area': [area_1, area_2, ...]  # This is optional and will be calculated if not present
  }
}
```
<details>
<summary><strong><span style="font-size: 1.1em;">Preparing a Local Dataset</span></strong></summary>

To load a local dataset of images, the files must be structured with a `metadata.jsonl` file, which is the standard method for the Hugging Face `datasets` library.

1. The folder structure should be organized as follows:

```bash
my_dataset/
|--- train/
|   |--- image1.jpg
|   |--- image2.png
|   |--- metadata.jsonl
|--- validation/
    |--- image3.jpg
    |--- metadata.jsonl
```

2. A `metadata.jsonl` file must be created. Each line in this file is a JSON object describing one image and its annotations.

Example line in `train/metadata.jsonl`:

```json
{"file_name": "image1.jpg", "objects": {"bbox": [[22, 34, 100, 150]], "category": [3]}}
```

3. The dataset can be loaded by providing the path to the root folder (`my_dataset/`). The template will automatically find and parse the `metadata.jsonl` files.

For more detailed information on creating image datasets for object detection, refer to the official [Hugging Face documentation](https://huggingface.co/docs/datasets/image_dataset#object-detection).

</details>

</details>

<details>
<summary><strong><span style="font-size: 1.25em;">Advanced Configuration</span></strong></summary>

<h4>License Validation for Hub Datasets</h4>

For commercial safety, the `DFINETraining` template automatically validates that datasets from the Hugging Face Hub have a permissive license. This check can be managed using an environment variable.

- **`ALLOW_UNVETTED_DATASETS`**:
  - **Default Behavior (`True`):** By default, the license check is **skipped**. This is to provide a smooth experience for local development and testing.
  - **Production Behavior (`False`):** For production environments, this variable **must** be explicitly set to `False` to enforce the license validation and ensure only commercially safe datasets are used.

**Example (for production):**
```bash
export ALLOW_UNVETTED_DATASETS=False
```

</details>


For example, for ***DFINEInference*** use ```sinx templates example-config DFINEInference``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_dfine_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: DFINEInference
  class_name: DFINEInference
  template_input: InputTemplate
  attributes:
    model_path: ustc-community/dfine-nano-coco
    model_cache_dir: '/path/to/sinapsis/cache'
    threshold: '`replace_me:<class ''float''>`'
    device: auto
    batch_size: 8
```

## Example Agent

The following is adapted directly from the package’s shipped [`demo.yml`](src/sinapsis_dfine/configs/demo.yml) configuration. Save it as `my_dfine_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_dfine_agent
  description: "Agent that runs inferences on images using the gradio interface"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: DFINEInference
    class_name: DFINEInference
    template_input: InputTemplate
    attributes:
      model_path: ustc-community/dfine-nano-coco
      batch_size: 16
      threshold: 0.5
      device: cuda

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: DFINEInference
    attributes:
      overwrite: true
      randomized_color: false
```

```bash
sinx jobs run my_dfine_agent.yaml
```

More configurations: [`fine_tuning.yml`](src/sinapsis_dfine/configs/fine_tuning.yml), [`demo.yml`](src/sinapsis_dfine/configs/demo.yml), [`inference.yml`](src/sinapsis_dfine/configs/inference.yml), [`fine-tuning.yml`](src/sinapsis_dfine/configs/fine-tuning.yml), [`training.yml`](src/sinapsis_dfine/configs/training.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
