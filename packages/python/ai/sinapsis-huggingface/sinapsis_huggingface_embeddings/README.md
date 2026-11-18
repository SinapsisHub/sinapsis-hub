<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Huggingface-Embeddings
<br>
</h1>

<h3 align="center">Extract embeddings from text, images and speech inputs.</h3>

## Overview

`sinapsis-huggingface-embeddings` provides two complementary ways to create embeddings within Sinapsis: **text embeddings** with `HuggingFaceEmbeddingExtractor`, and **speaker embeddings** with `SpeakerEmbeddingFromAudio`. They address different tasks and produce vectors that are not interchangeable.

Text embeddings are useful for semantic search, deduplication and retrieval-augmented generation. The extractor uses a configured Hugging Face embedding model through LlamaIndex, reads `TextPacket` content, and attaches the resulting vector to `packet.embedding`. A downstream indexer or nearest-neighbour search Template can consume that representation without knowing which embedding framework produced it.

Speaker embeddings describe acoustic speaker characteristics. The audio Template loads a SpeechBrain encoder, resamples incoming audio to 16 kHz when needed, and can attach the speaker vector to audio packets or corresponding text packets. This helps associate a transcript with a voice, compare segments for speaker similarity, or group audio by a consistent speaker identity.

### Scope and model choice

These Templates **do not** implement a general image-embedding model or document chunker in the supplied source. For text retrieval, use the same embedding model and preprocessing for indexed documents and queries. For speaker comparison, use compatible encoder weights and normalization settings across the data being compared.

## Installation

Python **3.13+**:

```bash
uv pip install sinapsis-huggingface-embeddings
```

The package includes its text embedding and SpeechBrain/audio dependencies in the base distribution; no runtime optional extras are declared. Its `dev` dependency group contains development tools, not an additional inference feature.

## Template reference

| Template | Input | Output and configuration |
|---|---|---|
| `HuggingFaceEmbeddingExtractor` | `DataContainer.texts` | Writes query embeddings into each `TextPacket.embedding`; requires `model_name`. |
| `SpeakerEmbeddingFromAudio` | `DataContainer.audios` | Attaches vectors to the packets selected by `target_packet` (`texts` or `audios`); supports `model_path`, `normalize`, `data_cache_dir`. |

`SpeakerEmbeddingFromAudio` accepts a single audio packet for multiple target packets, or one audio packet per target packet. Other cardinalities raise a `ValueError`; this matters when you align diarized speech segments with their transcript packets.

### Example: semantic embeddings for text packets

Save as `my_text_embeddings_agent.yaml`:

```yaml
agent:
  name: my_text_embeddings_agent

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Question
    class_name: TextInput
    template_input: Input
    attributes:
      text: "How does a universal data contract help AI pipelines?"

  - template_name: TextEmbeddings
    class_name: HuggingFaceEmbeddingExtractor
    template_input: Question
    attributes:
      model_name: sentence-transformers/all-MiniLM-L6-v2
```

The `TextInput` step comes from the separate `sinapsis-data-readers` package:

```bash
uv pip install sinapsis-data-readers
sinx jobs run my_text_embeddings_agent.yaml
```

The result is a `TextPacket` with a vector attached to its embedding field, ready for a compatible vector-store or similarity-search Template. Inference may download model weights on first use.

### Example: speaker embeddings on audio packets

For an Agent that has already produced audio packets, include the following downstream Template:

```yaml
- template_name: SpeakerFeatures
  class_name: SpeakerEmbeddingFromAudio
  template_input: YourAudioReader
  attributes:
    model_path: speechbrain/spkrec-xvect-voxceleb
    target_packet: audios
    normalize: true
```

The embedding is a speaker representation, not a transcript or a content embedding. It can be useful for speaker grouping, but any identity decisions require appropriate thresholds, enrolment data and privacy considerations.

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
