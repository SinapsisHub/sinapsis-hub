<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis
<br>
</h1>

<h3 align="center">
A single contract for the AI ecosystem.
</h3>

<p align="center">
  <strong>Python-native. Type-safe. Composable.</strong>
</p>

<p align="center">
  Build AI systems from reusable Python components. Combine models, libraries, APIs, and custom code through a shared computational contract, without coupling your application to one framework or execution environment.
</p>

<p align="center">
  <a href="https://docs.sinapsis.tech/">📚 Documentation</a> ·
  <a href="https://docs.sinapsis.tech/docs/latest/tutorials">🚀 Tutorials</a> ·
  <a href="https://sinapsis.tech/">🌐 Website</a>
</p>

---

## Overview

**Sinapsis** is a Python framework for building computational systems from reusable **Templates** and composing them into **Agents**. A Template encapsulates a capability—a model, an API call, data processing, or any other Python computation. An Agent connects Templates into a declarative workflow through consistent interfaces and a shared data model.

The **`sinapsis` package is the stable, public Python API** for this framework. It exposes the interfaces used by applications, integrations, and Template developers while relying on **`sinapsis-core`** for the underlying implementation.

```text
Applications · Templates · Integrations · Platform tooling
                         │
                         ▼
                    sinapsis
               Stable public Python API
                         │
                         ▼
                  sinapsis-core
             Framework implementation
```

This separation allows `sinapsis-core` to evolve without requiring downstream projects to follow internal refactors. Code integrating with the framework should use supported **`sinapsis.*` imports**, rather than importing directly from `sinapsis_core` internals.

`sinapsis` is a public interface to the core—not a separate runtime or an alternative validation layer.

## Why Sinapsis?

### Python-first by design

Python is the common language across much of AI and machine learning. Sinapsis builds on that ecosystem instead of replacing it: implement capabilities with ordinary Python code, use familiar libraries and package tooling, and compose those capabilities without repeatedly writing bespoke integration layers.

**Use the Python tools you already know.** Sinapsis provides the common structure that lets them work together.

### Type safety with Pydantic

Sinapsis uses **Pydantic** to define and validate Agent schemas, Template configuration, and structured framework models. Validation happens at the framework's schema boundaries, so invalid definitions and incompatible configuration values can be caught early rather than surfacing as obscure runtime errors.

This gives Python developers typed models, explicit contracts, and predictable serialization—while retaining the flexibility of Python and declarative YAML configuration.

### A single computational and data contract

Templates communicate through a common data model built around **`DataContainer`** and typed packets for content such as text, images, audio, time series, and binary data. Components can focus on their own computation rather than inventing new data conventions for every integration.

### Compose and reuse

Build a capability once as a Template, use it across Agents, or compose Agents into larger systems. Sinapsis supports declarative dependencies, orchestration, and reusable configurations across different AI/ML domains—not just LLM applications.

### Separate what runs from where it runs

The Agent and Template contract describes the computation independently of its execution environment. The wider Sinapsis ecosystem can build on that contract for local, remote, and distributed execution without requiring a new application model.

## Installation

**Python 3.13** is required. We recommend [`uv`](https://docs.astral.sh/uv/), although `pip` is also supported.

With `uv`:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install sinapsis
```

Or with `pip`:

```bash
python3.13 -m pip install sinapsis
```

No `--extra-index-url` is needed. Install additional Template packages only for the capabilities your application uses; these may bring their own optional dependencies.

## Quick start

### 1. Define an Agent

Create `agent.yml`:

```yaml
agent:
  name: hello_world

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: HelloWorld
    class_name: HelloWorld
    template_input: Input
    attributes:
      display_text: "Hello from Sinapsis!"
```

An Agent defines **what** runs and how Templates connect. The Template classes referenced in a configuration must be available in the environment when the Agent is executed.

### 2. Validate the definition through Python

The `sinapsis.agent` module exposes the canonical Agent schema builder:

```python
from pathlib import Path

import yaml
from sinapsis.agent import AgentSchema, generic_agent_schema_builder

configuration = yaml.safe_load(Path("agent.yml").read_text(encoding="utf-8"))

agent_schema: AgentSchema = generic_agent_schema_builder(configuration)

# Export a JSON-compatible definition for APIs, storage, or other integrations.
validated_definition = agent_schema.model_dump(mode="json")
```

`generic_agent_schema_builder()` validates the definition using the canonical core schema and returns an `AgentSchema` Pydantic model. Consumers should reuse this validation path, not create a second Agent-graph validator or alter core-generated schema fields.

### 3. Use the common data model

The public interface also exposes the framework's shared transport types:

```python
from sinapsis.data_transport import DataContainer
```

Templates exchange data through the same container contract instead of requiring a different transport model for every library or modality.

### 4. Execute your Agent

To run the YAML workflow, use the **separately distributed Sinapsis CLI** (`sinx`) or the Sinapsis APIs and platform tooling. For example, in an environment where the CLI and required Templates are installed:

```bash
sinx-venv jobs run agent.yml
```

The CLI is a separate package; installing `sinapsis` alone does not imply that `sinx` is installed. See the [tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials) for end-to-end workflows.

## Public API and compatibility

`sinapsis` exists to give downstream code a clear, durable integration boundary. Core runtime and implementation modules can be reorganized while the supported public imports remain consistent.

For example:

```python
from sinapsis.agent import AgentSchema, generic_agent_schema_builder
from sinapsis.data_transport import DataContainer
```

When building against Sinapsis:

- **Import from `sinapsis.*`.** Avoid relying on internal `sinapsis_core.*` module locations.
- **Validate through the canonical schema builder.** Keep one authoritative definition of an Agent and its structure.
- **Preserve typed contracts.** Use the framework's Pydantic schemas and common data containers rather than custom parallel representations.
- **Rely on package boundaries.** Use public API contracts for integrations; treat undocumented core internals as implementation details.

The public API is intentionally smaller than the full set of internal symbols in `sinapsis-core`. Stability applies to supported interfaces, not every implementation detail.

## Repository

Sinapsis is developed in the **[Sinapsis Hub monorepo](https://github.com/SinapsisHub/sinapsis-hub)** alongside `sinapsis-core`, Template packages, applications, and platform services. Each package has its own responsibilities and release lifecycle.

This README documents the **`sinapsis` Python distribution**. For the broader ecosystem, architecture, and deployment options, see the monorepo README and official documentation.

## Documentation and resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Unless otherwise noted, `sinapsis` is dual-licensed under your choice of the **MIT License** or the **Apache License, Version 2.0** (`MIT OR Apache-2.0`). See `LICENSE-MIT` and `LICENSE-APACHE` in the monorepo for the full terms.

---

<p align="center">
  <strong>Build faster. Integrate less. Get to production sooner.</strong>
</p>

<p align="center">
  <a href="https://sinapsis.tech/">🌐 Website</a> ·
  <a href="https://docs.sinapsis.tech/">📚 Documentation</a> ·
  <a href="https://github.com/SinapsisHub">📁 GitHub</a>
</p>
