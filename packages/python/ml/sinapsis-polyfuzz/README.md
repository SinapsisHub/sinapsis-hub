<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis PolyFuzz
<br>
</h1>

<h4 align="center">Templates for fuzzy string matching and semantic similarity using PolyFuzz</h4>

<p align="center">
<a href="#installation">🐍  Installation</a> •
<a href="#features"> 🚀 Features</a> •
<a href="#example"> 📚 Usage example</a> •
<a href="#documentation">📙 Documentation</a> •
<a href="#license"> 🔍 License </a>
</p>

**Sinapsis PolyFuzz** provides a powerful and flexible implementation for fuzzy string matching and semantic similarity matching. It integrates [PolyFuzz](https://github.com/MaartenGr/PolyFuzz) models into Sinapsis templates, enabling string matching pipelines with various backends including TF-IDF, Edit Distance, RapidFuzz, Sentence-BERT, Flair (🤗 Transformers, FastText, GloVe), Gensim, spaCy, and Universal Sentence Encoder.

<h2 id="installation"> 🐍  Installation </h2>

Install using your package manager of choice. We encourage the use of `uv`

Example with `uv`:

```bash
  uv pip install sinapsis-polyfuzz  
```

or with raw `pip`:

```bash
  pip install sinapsis-polyfuzz  
```

### Optional Dependencies

PolyFuzz supports multiple embedding backends. Install the extras you need:

```bash
# Sentence-BERT embeddings
uv pip install "sinapsis-polyfuzz[sbert]"  

# Flair embeddings
uv pip install "sinapsis-polyfuzz[flair]"  

# Word2Vec embeddings
uv pip install "sinapsis-polyfuzz[gensim]" 

# Universal Sentence Encoder
uv pip install "sinapsis-polyfuzz[use]"  

# FastText embeddings
uv pip install "sinapsis-polyfuzz[fast]"  

# spaCy for text processing
uv pip install "sinapsis-polyfuzz[spacy]"  

# Install all extras
uv pip install "sinapsis-polyfuzz[all]" 
```

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

This module includes multiple templates tailored for different fuzzy matching approaches:

- **TFIDFWrapper**: Classic TF-IDF based fuzzy string matching using character n-grams and cosine similarity.
- **EditDistanceWrapper**: Edit distance-based matching with customizable distance functions.
- **RapidFuzzWrapper**: Fast implementation of fuzzy string matching (fuzzywuzzy alternative) with MIT license.
- **EmbeddingsWrapper**: Flair-based embeddings matching supporting all 🤗 Transformers models.
- **SentenceTransformersWrapper**: Sentence-BERT embeddings for semantic similarity using sentence-transformers.
- **GensimEmbeddingsWrapper**: Word embeddings matching using Gensim (e.g., Word2Vec, GloVe).
- **SpacyEmbeddingsWrapper**: spaCy embeddings for linguistic similarity matching.
- **USEEmbeddingsWrapper**: Universal Sentence Encoder (USE) for deep semantic similarity using TensorFlow Hub.
- **\*PairWrapper** (e.g. **TFIDFPairWrapper**, **EditDistancePairWrapper**, **RapidFuzzPairWrapper**, ...): Paired-matching variants of every matcher. Instead of a static `to_list`, they match a column of one DataFramePacket against a column of another (selected by `source` or index) and append a `From`/`To`/`Similarity` matches packet. They short-circuit (return the container unchanged) when the reference column is empty, and expose a backend-independent `min_similarity` post-filter that drops weak matches (use this rather than the matcher's own threshold, which only some backends honor). For short alphanumeric codes, **RapidFuzzPairWrapper** is the most reliable — unlike n-gram TF-IDF it does not rank a single-character substitution (e.g. `KML029`→`KML028`) above a formatting variant (`KML029`→`KML29`).
- **ExactMatch**: Splits reference values into exact (normalized) matches against a target column and a non-exact residual. Emits an `exact_matches` packet (`From`/`To`/`Similarity` = 1.0) and a `no_exact_matches` residual packet to feed a downstream fuzzy `*PairWrapper`.

> [!TIP]
> Use CLI command ```sinx-venv templates show-all ``` to show a list with all the available Template names installed with Sinapsis PolyFuzz.

<details>
<summary><strong><span style="font-size: 1.25em;">🌍 General Attributes</span></strong></summary>

All templates share the following attributes defined in `PolyfuzzBaseAttributes`:

- **`target_column` (str, required)**: The name of the column in the DataFrame to be used as the source for matching.
- **`to_list` (list[str], optional)**: A list of strings to match against. If not provided, the model will match within the target column itself.
- **`overwrite` (bool, optional)**: Whether to overwrite the original packet content with results. If False, creates new packets. Defaults to `False`.

</details>

> [!TIP]
> Use CLI command ```sinx-venv templates example-config TEMPLATE_NAME``` to produce an example Agent config for the Template specified in ***TEMPLATE_NAME***.

For example, for ***TFIDFWrapper*** use ```sinx-venv templates example-config TFIDFWrapper``` to produce an example config like:

```yaml
agent:
  name: my_test_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: TFIDFWrapper
  class_name: TFIDFWrapper
  template_input: InputTemplate
  attributes:
    target_column: '`replace_me:<class ''str''>`'
    to_list: null
    overwrite: false
    tfidf_init:
      n_gram_range: !!python/tuple
      - 3
      - 3
      clean_string: true
      min_similarity: 0.75
      top_n: 1
      cosine_method: sparse
      model_id: null
      remove_space_ngrams: true
```

<h2 id='example'>📚 Usage example</h2>

Below is an example YAML configuration for fuzzy string matching using TF-IDF. In this example, we define an agent named `my_test_agent` and configure a matching template to find similar strings between a source column and a target list.

<details>
<summary ><strong><span style="font-size: 1.4em;">Config</span></strong></summary>

```yaml
agent:
  name: my_test_agent
  description: "Agent utilizing TF-IDF for fuzzy string matching."

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: CSVDatasetReader
    class_name: CSVDatasetReader
    template_input: InputTemplate
    attributes:
      root_dir: "artifacts"
      path_to_csv: "example.csv"
      store_as_time_series: false

  - template_name: TFIDFWrapper
    class_name: TFIDFWrapper
    template_input: CSVDatasetReader
    attributes:
      target_column: "from_list"
      to_list:
        - "Apple Inc"
        - "Microsoft Corporation"
        - "Google LLC"
        - "Amazon.com"
        - "Netflix Inc"
        - "Tesla Motors"
        - "Meta Platforms"
        - "NVIDIA Corp"
        - "Intel Corp"
      overwrite: true
      tfidf_init:
        n_gram_range:
          - 3
          - 3
        clean_string: true
        min_similarity: 0.5
        top_n: 1
        cosine_method: sparse
        remove_space_ngrams: true
```
</details>

This configuration defines an **agent** and a sequence of **templates** to perform fuzzy string matching:

1. **InputTemplate**: Entry point for the pipeline.
2. **CSVDatasetReader**: Reads a CSV file containing strings to match (from [sinapsis-data-readers]('../../data/processing/sinapsis_data_readers')).
3. **TFIDFMatcher**: Performs fuzzy matching using TF-IDF with character n-grams, minimum similarity of 0.5, returning top 1 matches.

> [!IMPORTANT]
> The `CSVDatasetReader` template corresponds to [sinapsis-data-readers]('../../data/processing/sinapsis_data_readers'), If you want to use the example, please make sure you install the package.
>
> The `to_list` attribute specifies the reference strings to match against. If omitted, the model will match strings within the target column against themselves.

To run the config, use the CLI:
```bash
sinx-venv jobs run name_of_config.yml
```

<h2 id="documentation">📙 Documentation and resources </h2>
 
- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the  [MIT License](LICENSE-MIT); or the [Apache License 2.0](LICENSE-APACHE) unless otherwise noted.
