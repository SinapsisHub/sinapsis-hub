<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Bertopic
<br>
</h1>

<h3 align="center">Train and apply BERTopic topic models within Agent graphs.</h3>

## Overview

**`sinapsis-bertopic`** — Package for topic modeling using BERTopic, including templates for fitting models and making predictions.

Topic modelling helps explore large collections of messages or documents without a predefined taxonomy. The package separates fitting, inference and downstream result handling for repeatable topic analysis.

### Where it fits

Quality depends on embedding models, preprocessing and clustering choices. A trained topic model should be applied to data prepared consistently with the training corpus.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-bertopic
# or
pip install sinapsis-bertopic
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `wikipedia-reader` | Wikipedia reader support. **Dependencies:** `sinapsis-langchain-readers[langchain-wikipedia-readers]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers[opencv]` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-writers`, `wikipedia-reader`. |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers` |

For example:

```bash
uv pip install "sinapsis-bertopic[wikipedia-reader]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

This package includes a publisher Template and a Worker agent

- **BERTopicFitModel**: A template class for fitting BERTopic models and saving them to disk.
- **BERTopicFitModelFromDataFrame**: A template class for fitting BERTopic models using data from a DataFrame and saving the model to disk.
- **BERTopicPredict**: Template for topic prediction using BERTopic models.


For example, for ***BERTopicPredict*** use ```sinx templates example-config BERTopicPredict``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_bertopic_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: BERTopicPredict
  class_name: BERTopicPredict
  template_input: InputTemplate
  attributes:
    root_dir: /root/.cache/sinapsis
    export_visualization_to_image: true
    image_export_params:
      format: png
      width: null
      height: null
      scale: null
      validate_figure: true
    sentence_model_name: sentence-transformers/all-MiniLM-L6-v2
    model_path: '`replace_me:<class ''str''>`'
    visualize_predictions: true
    visualize_topics: true
    historical_data_path: null
    prediction_viz_path: prediction_viz.html
    visualize_topics_params:
      topics: null
      top_n_topics: null
      use_ctfidf: false
      custom_labels: false
      title: <b>Intertopic Distance Map</b>
      figure_width: 650
      figure_height: 650
    save_topic_visualization_path: topics_visualization.html
```

## Example Agent

The following is adapted directly from the package’s shipped [`bertopic_predict.yml`](src/sinapsis_bertopic/configs/bertopic_predict.yml) configuration. Save it as `my_bertopic_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_bertopic_agent
  description: Topic inference agent for mapping text to pretrained BERTopic models.
  long_description: >
    This agent performs semantic inference by mapping new text data onto a pretrained BERTopic model.
    It leverages high-dimensional embeddings to categorize unstructured content—such as data on
    Autonomous Vehicles—into established thematic clusters, ensuring consistent classification without
    the need for additional training.

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: PyPDFLoaderWrapper_70780
    class_name: WikipediaLoaderWrapper
    template_input: InputTemplate
    attributes:
      add_document_as_text_packet: true
      wikipedialoader_init:
        query: foreign exchange mechanics and currency markets
        lang: en
        load_max_docs: 1
        load_all_available_meta: false
        doc_content_chars_max: 4000

  - template_name: PyPDFLoaderWrapper_70781
    class_name: WikipediaLoaderWrapper
    template_input: PyPDFLoaderWrapper_70780
    attributes:
      add_document_as_text_packet: true
      wikipedialoader_init:
        query: trading strategies & market dynamics
        lang: en
        load_max_docs: 1
        load_all_available_meta: false
        doc_content_chars_max: 4000

  - template_name: PyPDFLoaderWrapper_70782
    class_name: WikipediaLoaderWrapper
    template_input: PyPDFLoaderWrapper_70781
    attributes:
      add_document_as_text_packet: true
      wikipedialoader_init:
        query: fintech trends and innovations
        lang: en
        load_max_docs: 1
        load_all_available_meta: false
        doc_content_chars_max: 4000


  - template_name: BERTopic
    template_input: PyPDFLoaderWrapper_70782
    class_name: BERTopicPredict
    attributes:
      root_dir: "artifacts"
      prediction_viz_path: "bertopic_prediction_visualization.html"
      bertopic_model_params:
        calculates_probabilities: true
      visualize_predictions: true
      historical_data_path: "artifacts/training_data.pkl" # Path to historical data used for visualization
      #model_path: "MaartenGr/BERTopic_Wikipedia" # Points to model stored in HF Hub
      model_path: "artifacts/bert_model_finance-5" # Points to local saved model
```

```bash
sinx jobs run my_bertopic_agent.yaml
```

More configurations: [`bertopic_fit_model_worker.yml`](src/sinapsis_bertopic/configs/bertopic_fit_model_worker.yml), [`bertopic_fit_model_from_dataframe.yml`](src/sinapsis_bertopic/configs/bertopic_fit_model_from_dataframe.yml), [`bertopic_predict.yml`](src/sinapsis_bertopic/configs/bertopic_predict.yml), [`bertopic_fit_model.yml`](src/sinapsis_bertopic/configs/bertopic_fit_model.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
