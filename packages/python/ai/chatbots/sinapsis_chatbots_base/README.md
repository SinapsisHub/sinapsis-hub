<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Chatbots-Base
<br>
</h1>

<h3 align="center">Shared building blocks for LLM conversations, message construction and streaming.</h3>

## Overview

**`sinapsis-chatbots-base`** — Sinapsis templates for shared chatbot foundations.

The chatbots foundation separates the mechanics of conversation formatting, contextualisation, and stream handling from a particular model provider. This makes it easier to switch between endpoint-hosted and locally running models without rewriting surrounding Templates.

### Where it fits

The package includes endpoint-oriented and multi-modal paths; install the optional `endpoint` or `torch` dependencies only when your chatbot stack uses them. A base Template is not a complete hosted model service.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-chatbots-base
# or
pip install sinapsis-chatbots-base
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `torch` | PyTorch-backed operations. **Dependencies:** `torch` |
| `endpoint` | Endpoint-hosted model integration. **Dependencies:** `openai` |
| `all` | Bundle declared by this package; its manifest includes `torch`, `endpoint`. |

For example:

```bash
uv pip install "sinapsis-chatbots-base[torch]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

- **LLMConversationInput**: Creates an `LLMConversationPacket` from a prompt, system prompt, and packet metadata.
- **QueryContextualizeFromFile**: Builds packet contexts from files or documents already loaded into the container.
- **EndpointLLMCompletion**: Sends chat requests to OpenAI-compatible endpoints such as OpenAI, Ollama, llama.cpp server, vLLM server, or compatible hosted APIs.
- **EndpointLLMCompletionWithMCP**: Adds MCP tool support on top of `EndpointLLMCompletion` for OpenAI-compatible endpoints.
- **EndpointLLMStreamingCompletion**: Streams chat-completion chunks from OpenAI-compatible endpoints and emits partial packet updates.
- **EndpointLLMMultiModal**: Sends text + image user turns to OpenAI-compatible multimodal endpoints.

> [!NOTE]
> `EndpointLLMCompletionWithMCP` is currently validated for llama.cpp served Qwen 3.5 models and other OpenAI-compatible endpoints may also work depending on tool-calling behavior.

## Example Agent

The following is adapted directly from the package’s shipped [`streaming.yaml`](src/sinapsis_chatbots_base/configs/streaming.yaml) configuration. Save it as `my_chatbots_base_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_chatbots_base_agent
  description: Demonstrates streaming text generation with a vLLM OpenAI-compatible endpoint.

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: LLMConversationInput
    class_name: LLMConversationInput
    template_input: InputTemplate
    attributes:
      prompt: "Give three short tips for staying organized during a busy week."
      system_prompt: "You are a helpful assistant."

  - template_name: EndpointLLMStreamingCompletion
    class_name: EndpointLLMStreamingCompletion
    template_input: LLMConversationInput
    attributes:
      init_args:
        base_url: "http://127.0.0.1:8000/v1"
        llm_model_name: "Qwen/Qwen3-4B-Thinking-2507"
      completion_args:
        max_tokens: 1024
        temperature: 0.7
        top_p: 0.8
```

```bash
sinx jobs run my_chatbots_base_agent.yaml
```

More configurations: [`llamacpp_server.yaml`](src/sinapsis_chatbots_base/configs/llamacpp_server.yaml), [`gemini_api.yaml`](src/sinapsis_chatbots_base/configs/gemini_api.yaml), [`openai_api.yaml`](src/sinapsis_chatbots_base/configs/openai_api.yaml), [`ollama_chat.yaml`](src/sinapsis_chatbots_base/configs/ollama_chat.yaml), [`vllm_server.yaml`](src/sinapsis_chatbots_base/configs/vllm_server.yaml), [`streaming.yaml`](src/sinapsis_chatbots_base/configs/streaming.yaml), [`multimodal.yaml`](src/sinapsis_chatbots_base/configs/multimodal.yaml), [`bedrock_mantle_openai.yaml`](src/sinapsis_chatbots_base/configs/bedrock_mantle_openai.yaml), [`ollama_with_mcp.yaml`](src/sinapsis_chatbots_base/configs/ollama_with_mcp.yaml), [`structured_outputs.yaml`](src/sinapsis_chatbots_base/configs/structured_outputs.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
