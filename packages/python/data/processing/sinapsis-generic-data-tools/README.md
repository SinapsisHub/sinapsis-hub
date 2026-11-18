<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Generic-Data-Tools
<br>
</h1>

<h3 align="center">Lightweight transformations and routing utilities for DataContainers.</h3>

## Overview

**`sinapsis-generic-data-tools`** — Collection of generic data tools.

The small operations between model calls—chunking text, filtering packets, changing image colours, buffering, or aggregating provenance—often determine whether a workflow is usable. Generic data tools make these steps reusable without bundling a full model.

### Where it fits

Install optional media libraries only for the data types you process (`cv2`, `pillow`, `pydub`, `torch`, `numpy`). Avoid unnecessary conversions when packets already contain a suitable native representation.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-generic-data-tools
# or
pip install sinapsis-generic-data-tools
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `pillow` | Pillow support. **Dependencies:** `pillow` |
| `pydub` | Pydub support. **Dependencies:** `pydub`, `audioop-lts` |
| `all` | Bundle declared by this package; its manifest includes `cv2`, `numpy`, `pillow`, `pydub`, `torch`. |
| `cv2` | Cv2 support. **Dependencies:** `opencv-python-headless` |
| `torch` | PyTorch-backed operations. **Dependencies:** `torch` |
| `numpy` | Numpy support. **Dependencies:** `numpy` |

For example:

```bash
uv pip install "sinapsis-generic-data-tools[pillow]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

## Template discovery and examples

The package exposes Template implementations including `ContextChunker`, `PacketBufferQueue`, `TextContentFilter`, `MaskNonROIs`, `SourceHistoryAggregator`, `ImageColorConversionNumpy`.

Inspect the installed environment for the exact classes and validated attributes, then generate a starter configuration:

```bash
sinx templates show-all
sinx templates example-config ContextChunker
```

These commands inspect the installed Template set; some base classes are internal and cannot be instantiated as an Agent node.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
