<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Vowpal-Wabbit
<br>
</h1>

<h3 align="center">Contextual bandit learning and prediction with Vowpal Wabbit.</h3>

## Overview

**`sinapsis-vowpal-wabbit`** — Package for Vowpal Wabbit algorithms, featuring high-performance implementations of Contextual Bandits (ADF) and reinforcement learning patterns.

Contextual bandits model decisions where feedback arrives after selecting an action. Wrapping exploration, learning and scoring in Templates helps connect data preparation, action selection and updates in one observable flow.

### Where it fits

Use this for online decision policies with explicit action/reward semantics, not as a drop-in replacement for standard classification. Explore/exploit settings and logging policy affect learning quality.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-vowpal-wabbit
# or
pip install sinapsis-vowpal-wabbit
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers` |
| `all` | Bundle declared by this package; its manifest includes `scikit-learn`, `sentence-transformers`, `sinapsis-data-readers`. |
| `sentence-transformers` | Sentence transformers support. **Dependencies:** `sentence-transformers` |
| `scikit-learn` | Scikit learn support. **Dependencies:** `scikit-learn` |

For example:

```bash
uv pip install "sinapsis-vowpal-wabbit[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

This repository implements specific templates for Vowpal Wabbit's most powerful reductions:

- **CBExploreADFPredict**: Handles real-time inference for Contextual Bandits using Action-Dependent Features (ADF).

- **CBExploreADFLearn**: Template to perform offline learning. It iterates through historical datasets (context, action, reward) for a defined number of epochs to optimize the model weights before deployment.

- **CBExploreADFPredictEmbeddings**: Handles real-time inference for Contextual Bandits using Action-Dependent Features (ADF) enhanced with text embeddings. This template processes incoming context and actions by combining traditional raw text features with vector-based embeddings to provide more nuanced, semantically aware predictions in production environments.

- **CBExploreADFLearnEmbeddings**: Template for offline learning that incorporates text embeddings into the optimization process. It iterates through historical datasets (context, actions, and rewards) over a defined number of epochs. By training on a combination of raw text and sentence based embeddings, it captures deeper semantic relationships to more effectively optimize model weights prior to deployment.

## Example Agent

The following is adapted directly from the package’s shipped [`cb_explore_adf_predict_from_pdf_loader.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_predict_from_pdf_loader.yaml) configuration. Save it as `my_vowpal_wabbit_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_vowpal_wabbit_agent

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: PyPDFLoaderWrapper_70780
    class_name: PyPDFLoaderWrapper
    template_input: InputTemplate
    attributes:
      pypdfloader_init:
        mode: single
        file_path: "path"
        extract_images: false
        extraction_mode: plain
        pages_delimiter: "\n\f"
        extraction_kwargs: { }
        images_inner_format: text
      #add_document_as_text_packet: True

  - template_name: Splitter
    class_name: RegexTurnSplitter
    template_input: InputTemplate
    attributes:
      generic_key: PyPDFLoaderWrapper_70780
      pattern_1: ['User 1', 'User 2']
      pattern_2: "\\d{2}:\\d{2}"

      return_as_text_packets: true

  - template_name: CBExploreADFPredict
    class_name: CBExploreADFPredictEmbeddings
    template_input: Splitter
    attributes:
      random_seed: 42
      actions:
        [
          "contact_customer_service",
          "schedule_follow_up_meeting",
          "send_email_with_product_information",
          "register_new_client",
          "provide_financing_options",
        ]
      model_path: artifacts/cb_model-embeddings-quadratic.vw
      threshold: 0
      remove_special_characters: True
      vw_workspace_params:
        exploration_method: epsilon
        exploration_value: 0.3
        adaptive: True
        normalized: True
        quiet: True
        quadratic_interactions: [":A"]
```

```bash
sinx jobs run my_vowpal_wabbit_agent.yaml
```

More configurations: [`cb_explore_adf_learn_embeddings.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_learn_embeddings.yaml), [`cb_explore_adf_predict_from_pdf_loader.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_predict_from_pdf_loader.yaml), [`cb_explore_adf_predict_embeddings.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_predict_embeddings.yaml), [`cb_explore_adf_learn.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_learn.yaml), [`cb_explore_adf_predict.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_predict.yaml), [`cb_explore_adf_predict_from_pdf_loader_summary.yaml`](src/sinapsis_vowpal_wabbit/configs/cb_explore_adf_predict_from_pdf_loader_summary.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
