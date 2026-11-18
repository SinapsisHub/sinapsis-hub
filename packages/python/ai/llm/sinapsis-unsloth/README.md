<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Unsloth
<br>
</h1>

<h3 align="center">Fine-tune, run, merge and export language models with Unsloth.</h3>

## Overview

**`sinapsis-unsloth`** — Package for fine-tuning, running and exporting Large Language Models with Unsloth.

Training and deployment require different steps: dataset preparation, adapter fine-tuning, inference and model export. Keeping them as Templates helps build repeatable training workflows where checkpoints and export outputs can be used by later stages.

### Where it fits

This package is primarily for GPU-equipped model development. Review model-specific requirements and choose the Hugging Face or FlashAttention extras only when those paths are needed.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-unsloth
# or
pip install sinapsis-unsloth
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `huggingface` | Huggingface support. **Dependencies:** `unsloth[huggingface]` |
| `flashattention` | Flashattention support. **Dependencies:** `ninja`, `packaging`, `flash-attn`, `torch` |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers` |
| `all` | Bundle declared by this package; its manifest includes `huggingface`, `flashattention`, `sinapsis-data-readers`. |

For example:

```bash
uv pip install "sinapsis-unsloth[huggingface]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

The templates support all capabilities from Unsloth for efficient LLM fine-tuning, inference, and model export, including:

- **Optimized Training**: 4-bit (QLoRA), 8-bit, 16-bit, and full precision fine-tuning
- **Hardware Efficiency**: Reduced GPU memory usage with Unsloth's optimized kernels
- **Flexible Export**: GGUF quantization and Merged model export options for deployment
- **High-Performance Inference**: Native 4-bit inference with dynamic chat templating and streaming

<h3> Templates Supported</h3>

<h4>Training</h4>

* **UnslothPretrainer**: Designed for continued pretraining (domain adaptation) on raw text. Features efficient sequence packing and specific learning rate controls for embeddings.

* **UnslothInstructTrainer**: Optimized for instruction fine-tuning. Processes standard instruction-input-response triplets with configurable preambles and dynamic formatting (handling optional inputs gracefully).

* **UnslothConversationTrainer**: Specialized for conversational AI fine-tuning with chat datasets. Supports both **ShareGPT** and **Alpaca** formats (with auto-conversion), handles dynamic chat templating, and supports response-only loss masking.

<h4>Inference</h4>

* **UnslothInferenceCompletion**: Raw text completion template for base models or custom formatting needs.

* **UnslothInferenceInstruct**: Streamlined inference for instruction-tuned models using standard task preambles.

* **UnslothInferenceConversational**: Manages multi-turn chat history, system prompts, and dynamic chat template application for conversational models.

* **UnslothInferenceReasoning**: Extends conversational inference to support Chain-of-Thought (CoT) models (e.g., DeepSeek-R1), handling the extraction of internal reasoning traces.

<h4>Export</h4>

* **UnslothExportGGUF**: Exports models to GGUF format for efficient CPU/Edge inference (e.g., Llama.cpp). Supports configurable quantization methods (q4_k_m, q8_0, etc.).

* **UnslothExportMerged**: Merges LoRA adapters back into the base model (16-bit or 4-bit) for deployment on vLLM, or pushes directly to the Hugging Face Hub.

<details>
<summary id="configuration"><strong><span style="font-size: 1.25em;">🌍 General Attributes</span></strong></summary>

The `model_args` attribute controls how Unsloth loads and configures the model.

- **`model_name`** (`str`, required): Model ID or local path.
- **`cache_dir`** (`str`): Cache directory. Default: `SINAPSIS_CACHE_DIR`.
- **`max_seq_length`** (`int`): Maximum sequence length. Default: `2048`.
- **`dtype`** (`"auto" | "bfloat16" | "float16"`): Weight precision. Default: `"auto"`.
- **`load_in_4bit`** (`bool`): Enable 4-bit quantization. Default: `True`.
- **`load_in_8bit`** (`bool`): Enable 8-bit quantization. Default: `False`.
- **`load_in_16bit`** (`bool`): Load weights in FP16. Default: `False`.
- **`full_finetuning`** (`bool`): Enable full fine-tuning. Default: `False`.
- **`device_map`** (`str`): Device placement strategy. Default: `"sequential"`.
- **`use_gradient_checkpointing`** (`str`): Checkpointing mode. Default: `"unsloth"`.
- **`fast_inference`** (`bool`): Enable optimized inference. Default: `False`.
- **`gpu_memory_utilization`** (`float`): Max GPU memory fraction. Default: `0.5`.
- **`random_state`** (`int`): Random seed. Default: `3407`.
- **`max_lora_rank`** (`int`): Maximum LoRA rank. Default: `64`.

</details>

<details>
<summary id="configuration"><strong><span style="font-size: 1.25em;">⚙️ Fine-tuning Attributes</span></strong></summary>

These attributes apply to all fine-tuning templates:

- **`lora_args`** (`UnslothLoraArgs`)
  - LoRA configuration (rank, alpha, dropout, target modules, gradient checkpointing).

- **`trainer_args`** (`UnslothTrainerArgs`)
  - Trainer options (text field, packing, sequence length, loss type).

- **`training_args`** (`UnslothTrainingArgs`)
  - Hugging Face training parameters (batch size, learning rate, logging, saving).

- **`train_dataset`** (`DatasetConfig`)
  - Dataset configuration, including:
    - `loader_args` (source and loading parameters)
    - `map_args` (preprocessing)
    - `shuffle` (shuffling behavior)
    - `pre_tokenize` (tokenization options)

- **`resume_from_checkpoint`** (`bool`)
  - Resume training from the last checkpoint.

- **`save_path`** (`str`)
  - Directory where fine-tuned adapters or weights will be saved.

</details>

<details>
<summary id="inference"><strong><span style="font-size: 1.25em;">🧠 Inference Attributes</span></strong></summary>

These attributes configure Unsloth-based inference templates.

- **`rag_context_key`** (`str | None`)
  - Metadata key used to retrieve optional RAG context.

- **`generate_args`** (`UnslothGenerateArgs`)
  - Token generation settings (sampling, length, stopping, temperature, penalties).

- **`stream`** (`bool`)
  - Enables token-by-token console streaming during generation.

</details>


<details>
<summary id="export"><strong><span style="font-size: 1.25em;">📦 Export Attributes</span></strong></summary>

These attributes configure Unsloth-based model export templates.

- **`export_args`** (`UnslothExportBaseArgs`)
  - Export parameters such as save path, shard size, and memory limits.

- **`push_to_hub`** (`bool`)
  - Enables pushing the exported model to the Hugging Face Hub.

</details>


For example, for ***UnslothPretrainer*** use ```sinx templates example-config UnslothPretrainer``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_unsloth_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: UnslothPretrainer
  class_name: UnslothPretrainer
  template_input: InputTemplate
  attributes:
    model_args:
      model_name: '`replace_me:<class ''str''>`'
      cache_dir: /path/to/sinapsis/.cache
      max_seq_length: 2048
      dtype: auto
      load_in_4bit: true
      load_in_8bit: false
      load_in_16bit: false
      full_finetuning: false
      device_map: sequential
      use_gradient_checkpointing: unsloth
      fast_inference: false
      gpu_memory_utilization: 0.5
      random_state: 3407
      max_lora_rank: 64
    lora_args:
      r: 16
      target_modules:
      - q_proj
      - k_proj
      - v_proj
      - o_proj
      - gate_proj
      - up_proj
      - down_proj
      lora_alpha: 16
      lora_dropout: 0.0
      bias: none
      use_gradient_checkpointing: unsloth
      random_state: 3407
      use_rslora: false
      modules_to_save: null
      loftq_config: '`replace_me:<class ''dict''>`'
    trainer_args:
      dataset_text_field: text
      dataset_num_proc: null
      max_length: 1024
      packing: false
      packing_strategy: bfd
      eval_packing: false
      completion_only_loss: null
      assistant_only_loss: false
      loss_type: nll
      activation_offloading: false
    training_args:
      output_dir: trainer_output
      overwrite_output_dir: false
      eval_strategy: 'no'
      eval_steps: null
      per_device_train_batch_size: 8
      per_device_eval_batch_size: 8
      gradient_accumulation_steps: 1
      eval_accumulation_steps: null
      torch_empty_cache_steps: null
      learning_rate: 5.0e-05
      weight_decay: 0.0
      max_grad_norm: 1.0
      num_train_epochs: 3.0
      max_steps: null
      lr_scheduler_type: linear
      warmup_ratio: 0.0
      warmup_steps: null
      logging_strategy: steps
      logging_first_step: false
      logging_steps: 500
      save_strategy: steps
      save_steps: 500
      save_only_model: false
      use_cpu: false
      seed: 3407
      data_seed: null
      bf16: false
      fp16: false
      dataloader_drop_last: false
      dataloader_num_workers: 0
      remove_unused_columns: true
      load_best_model_at_end: false
      metric_for_best_model: loss
      optim: adamw_torch
      report_to: none
      push_to_hub: false
      hub_model_id: null
      embedding_learning_rate: 5.0e-05
    train_dataset:
      loader_args:
        path: '`replace_me:<class ''str''>`'
        name: null
        data_dir: null
        data_files: null
        split: null
        cache_dir: /path/to/sinapsis/.cache
        features: null
        num_proc: null
      map_args:
        desc: null
        batched: false
        batch_size: 1000
        num_proc: 0
        keep_in_memory: false
        load_from_cache_file: true
      shuffle:
        enabled: false
        args:
          seed: null
          keep_in_memory: false
          load_from_cache_file: true
      pre_tokenize:
        enabled: false
        args:
          add_special_tokens: true
          padding: do_not_pad
          truncation: do_not_truncate
          max_length: null
          stride: 0
          is_split_into_words: false
          padding_side: null
          verbose: true
        map_args:
          desc: null
          batched: false
          batch_size: 1000
          num_proc: 0
          keep_in_memory: false
          load_from_cache_file: true
    resume_from_checkpoint: false
    save_path: '`replace_me:<class ''str''>`'
```

## Example Agent

The following is adapted directly from the package’s shipped [`inference_completion.yaml`](src/sinapsis_unsloth/configs/inference_completion.yaml) configuration. Save it as `my_unsloth_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_unsloth_agent

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: TextInput
  class_name: TextInput
  template_input: InputTemplate
  attributes:
    text: "Tomorrow I'm going to"

- template_name: UnslothInferenceCompletion
  class_name: UnslothInferenceCompletion
  template_input: TextInput
  attributes:
    model_args:
      model_name: unsloth/Meta-Llama-3.1-8B
      dtype: "bfloat16"
      max_seq_length: 2056
      load_in_4bit: true
      device_map: "auto"
      gpu_memory_utilization: 1
    generate_args:
      max_new_tokens: 32
      temperature: 0.7
      do_sample: false
    streaming: true
```

```bash
sinx jobs run my_unsloth_agent.yaml
```

More configurations: [`model_export_gguf.yaml`](src/sinapsis_unsloth/configs/model_export_gguf.yaml), [`model_export_merged.yaml`](src/sinapsis_unsloth/configs/model_export_merged.yaml), [`inference_completion.yaml`](src/sinapsis_unsloth/configs/inference_completion.yaml), [`inference_instruct.yaml`](src/sinapsis_unsloth/configs/inference_instruct.yaml), [`inference_conversational.yaml`](src/sinapsis_unsloth/configs/inference_conversational.yaml), [`inference_reasoning.yaml`](src/sinapsis_unsloth/configs/inference_reasoning.yaml), [`instruct_fine_tuning.yaml`](src/sinapsis_unsloth/configs/instruct_fine_tuning.yaml), [`continued_pretraining.yaml`](src/sinapsis_unsloth/configs/continued_pretraining.yaml), [`conversational_fine_tuning.yaml`](src/sinapsis_unsloth/configs/conversational_fine_tuning.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
