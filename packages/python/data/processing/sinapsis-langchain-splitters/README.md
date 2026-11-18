<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Langchain Splitters
<br>
</h1>

<h3 align="center">Split and aggregate document text using LangChain strategies.</h3>

## Overview

**`sinapsis_langchain_splitters`** — Package that provides support for Langchain splitters module.

Chunk boundaries affect retrieval quality, search cost and model context usage. Exposing splitters as Templates makes chunking configurable and testable separately from the vector store or language model.

> [!NOTE]
> **LangChain Dependency Status**
>
> LangChain sunset its `langchain-community` package in May 2026.
>
> `sinapsis-langchain-splitters` primarily builds upon the separately maintained
> `langchain-text-splitters` package, which provides the underlying text-splitting
> implementations.
>
> Although `langchain-community` remains listed as a dependency in the current
> package release, its deprecation does not extend to `langchain-text-splitters`.
>
> Supported splitting strategies and configuration options depend on the
> installed version of `langchain-text-splitters`.
### Where it fits

Select regex or language-aware splitting to match the content. Optional `spacy` or `konlpy` packages are not needed for every text-splitting strategy.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis_langchain_splitters
# or
pip install sinapsis_langchain_splitters
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `spacy` | Spacy support. **Dependencies:** `spacy` |
| `konlpy` | Konlpy support. **Dependencies:** `konlpy` |
| `all` | Bundle declared by this package; its manifest includes `konlpy`, `spacy`. |

For example:

```bash
uv pip install "sinapsis_langchain_splitters[spacy]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

## Text splitting and dynamic wrappers

This package wraps splitters from `langchain-text-splitters` as **dynamic Sinapsis Templates**. Instead of maintaining a fixed implementation of each splitter, `LangChainTextSplitterBase` creates Template classes from the splitter constructors exposed by the installed library. This allows supported options to follow compatible upstream releases without duplicating every constructor signature in Sinapsis. New splitters still depend on the installed `langchain-text-splitters` version and the package's discovery filters.

The wrapper accepts text from a `TextPacket` or LangChain `Document` data carried under a configured `generic_key`. It outputs smaller chunks with source/context metadata for downstream embedding, search, classification and retrieval. Chunk boundaries affect retrieval quality: smaller chunks improve localisation but may lose context; larger chunks retain context at the cost of more input tokens and less precise matches.

### Available approaches

- `RecursiveCharacterTextSplitterWrapper` — recursive splitting over configurable separators. Appropriate for paragraphs and prose where maintaining natural boundaries matters.
- `RegexTurnSplitter` — split a conversation or transcript on a regular expression matching turn boundaries.
- `PatternAggregatorSplitter` — collect and aggregate matching text patterns for workflows that need grouped segments.
- Other compatible dynamic splitter wrappers — generated from the installed LangChain splitter constructors.

### Example: split long text into contextual chunks

Create `my_text_splitter_agent.yaml`:

```yaml
agent:
  name: my_text_splitter_agent

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Text
    class_name: TextInput
    template_input: Input
    attributes:
      text: "A long document can contain multiple sections. Splitters keep retrieval chunks manageable."

  - template_name: Split
    class_name: RecursiveCharacterTextSplitterWrapper
    template_input: Text
    attributes:
      add_document_as_text_packet: true
      generic_key: null
      recursivecharactertextsplitter_init:
        chunk_size: 500
        chunk_overlap: 50
        separators: ["\n\n", "\n", " ", ""]
```

```bash
uv pip install sinapsis-data-readers
sinx jobs run my_text_splitter_agent.yaml
```

The `TextInput` Template comes from `sinapsis-data-readers`; install that package alongside this one for the example. For real documents, replace the text input with a document reader. Inspect `sinx templates example-config RecursiveCharacterTextSplitterWrapper` for the exact dynamically generated fields in your installed environment.

## Template discovery and examples

The package exposes Template implementations including `RegexTurnSplitter`, `PatternAggregatorSplitter`.

Inspect the installed environment for the exact classes and validated attributes, then generate a starter configuration:

```bash
sinx templates show-all
sinx templates example-config RegexTurnSplitter
```

These commands inspect the installed Template set; some base classes are internal and cannot be instantiated as an Agent node.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
