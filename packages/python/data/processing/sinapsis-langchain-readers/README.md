<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Langchain Readers
<br>
</h1>

<h3 align="center">Load documents and external content through LangChain connectors.</h3>

## Overview

**`sinapsis_langchain_readers`** — Package that provides support for Langchain community data loaders.

A retrieval pipeline must first convert many kinds of sources into documents. This integration isolates source-specific loading from downstream chunking, indexing and embedding.

> [!WARNING]
> **Upstream Deprecation — LangChain Community**
>
> LangChain officially sunset the `langchain-community` package in May 2026,
> moving toward independently maintained, provider-specific integration packages.
>
> `sinapsis-langchain-readers` currently relies on `langchain-community`
> for its document loader implementations.
>
> Existing Templates may continue to work with compatible dependency versions.
> However, because the upstream package is no longer maintained, these
> integrations may not receive new features, compatibility updates, or bug fixes.
>
> Future versions of this Sinapsis integration may transition to dedicated
> LangChain provider packages where suitable alternatives are available.
>
> **This notice concerns the upstream dependency, not a deprecation of
> `sinapsis-langchain-readers` itself.**

### Where it fits

Choose the extra matching the source you intend to read—web, Wikipedia, PDFs, databases, cloud storage or productivity systems. Provider authentication and parser limitations remain source-specific.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis_langchain_readers
# or
pip install sinapsis_langchain_readers
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `langchain-webpages-readers` | LangChain connectors for webpages readers. **Dependencies:** `apify-client`, `arxiv`, `beautifulsoup4`, `browserbase`, `dgml-utils` and 9 more |
| `langchain-wikipedia-readers` | LangChain connectors for wikipedia readers. **Dependencies:** `wikipedia` |
| `langchain-pdfs-readers` | LangChain connectors for pdfs readers. **Dependencies:** `bibtexparser`, `pdfplumber`, `pymupdf`, `pypdf` |
| `langchain-unstructured-readers` | LangChain connectors for unstructured readers. **Dependencies:** `langchain-unstructured`, `unstructured[pdf]`, `unstructured-client`, `python-magic`, `msoffcrypto-tool` |
| `langchain-cloud-readers` | LangChain connectors for cloud readers. **Dependencies:** `amazon-textract-caller`, `assemblyai`, `atlassian-python-api`, `azure-ai-generative`, `azure-storage-blob` and 16 more |
| `langchain-social-readers` | LangChain connectors for social readers. **Dependencies:** `langchain-yt-dlp`, `mastodon-py`, `nest-asyncio`, `pandas`, `telethon` and 2 more |
| `langchain-productivity-tools-readers` | LangChain connectors for productivity tools readers. **Dependencies:** `lxml` |
| `langchain-common-readers` | LangChain connectors for common readers. **Dependencies:** `bs4`, `jq` |
| `langchain-database-readers` | LangChain connectors for database readers. **Dependencies:** `fauna`, `langchain`, `langchain-google-alloydb-pg`, `motor`, `pyowm` |
| `langchain-productivity-tools` | LangChain connectors for productivity tools. **Dependencies:** `gitpython` |
| `all` | Bundle declared by this package; its manifest includes `langchain-productivity-tools`, `langchain-database-readers`, `langchain-common-readers`, `langchain-productivity-tools-readers`, `langchain-social-readers`, `langchain-cloud-readers`, `langchain-unstructured-readers`, `langchain-pdfs-readers`, `langchain-wikipedia-readers`, `langchain-webpages-readers`. It does not include `langchain-wepages-readers`. |
| `langchain-wepages-readers` | LangChain connectors for wepages readers. **Dependencies:** `youtube-transcript-api` |

For example:

```bash
uv pip install "sinapsis_langchain_readers[langchain-webpages-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis Langchain** module provides wrapper templates for **LangChain's community data loaders**, making them seamlessly usable within Sinapsis.
> [!NOTE]
> Each loader template supports one attribute:
> - **`add_document_as_text_packet`** (`bool`, default: `False`): Whether to add the loaded document as a text packet.
> Other attributes can be dynamically assigned through the class initialization dictionary (`class init attributes`).


For example, for ***WikipediaLoaderWrapper*** use ```sinx templates example-config WikipediaLoaderWrapper``` to produce the following example config:

```yaml
agent:
  name: agent to load Wikipedia documents using WikipediaLoaderWrapper template
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: WikipediaLoaderWrapper
  class_name: WikipediaLoaderWrapper
  template_input: InputTemplate
  attributes:
    add_document_as_text_packet: false
    wikipedialoader_init:
        query: the query for wikipedia
        lang: en
        load_max_docs: 5000
        load_all_available_meta: False
        doc_content_chars_max: 4000,
```

A complete list of available document loader classes in LangChain can be found at:
[LangChain Community Document Loaders](https://python.langchain.com/api_reference/community/document_loaders.html#langchain-community-document-loaders)

<details>
<summary><strong><span style="font-size: 1.25em;">🚫 Excluded Loaders</span></strong></summary>

Some base classes or loaders that required additional configuration have been excluded and support for this will be included in future releases.

- **Blob**
- **BlobLoader**
- **OracleTextSplitter**
- **OracleDocLoader**
- **TrelloLoaderExecute**
- **TwitterTweetLoader**
- **TrelloLoader**
- **GoogleApiYoutubeLoader**
- **GoogleApiClient**
- **DiscordChatLoader**
- **AssemblyAIAudioTranscriptLoader**
- **ArcGISLoader**

For all other supported loaders, refer to the LangChain API reference linked above.
</details>

## Example Agent

The following is adapted directly from the package’s shipped [`one_drive_loader.yml`](src/sinapsis_langchain_readers/configs/one_drive_loader.yml) configuration. Save it as `my_sinapsis_langchain_readers_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_sinapsis_langchain_readers_agent
  description: "One Drive Loader example"

templates:

- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: LangChainOneDriveLoader
  class_name: LangChainOneDriveLoader
  template_input: InputTemplate
  attributes:
    add_document_as_text_packet: false
    folder_id: folder_id
    drive_id: drive_id
    auth_with_token: false
    token_path: /path/to/token.txt
```

```bash
sinx jobs run my_sinapsis_langchain_readers_agent.yaml
```

More configurations: [`one_drive_loader.yml`](src/sinapsis_langchain_readers/configs/one_drive_loader.yml), [`wikipedia_loader.yml`](src/sinapsis_langchain_readers/configs/wikipedia_loader.yml), [`google_drive_loader.yml`](src/sinapsis_langchain_readers/configs/google_drive_loader.yml), [`test_config.yaml`](src/sinapsis_langchain_readers/configs/test_config.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
