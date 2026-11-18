<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Timesfm
<br>
</h1>

<h3 align="center">Forecast with the TimesFM foundation model.</h3>

## Overview

**`sinapsis-timesfm`** — Module for time series forecasting using Google's TimesFM foundation model.

Foundation forecasting models can provide predictions without training a new model for each series. The TimesFM Template can be combined with Darts or data-reader stages to create repeatable forecasting evaluations.

### Where it fits

Select the `torch`, `flax` or `xreg` extra according to the implementation path. Model weights, forecast horizon and covariate support determine the valid workflow.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-timesfm
# or
pip install sinapsis-timesfm
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `torch` | PyTorch-backed operations. **Dependencies:** `timesfm[torch]` |
| `flax` | Flax support. **Dependencies:** `timesfm[flax]` |
| `xreg` | Xreg support. **Dependencies:** `timesfm[xreg]` |
| `all` | Bundle declared by this package; its manifest includes `flax`, `torch`, `xreg`, `sinapsis-darts-forecasting`, `sinapsis-data-readers`. |
| `sinapsis-darts-forecasting` | Sinapsis darts forecasting support. **Dependencies:** `sinapsis-darts-forecasting` |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers` |

For example:

```bash
uv pip install "sinapsis-timesfm[torch]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

<details>
<summary><strong><span style="font-size: 1.25em;">TimesFM</span></strong></summary>

Zero-shot time series forecasting template powered by Google's TimesFM 2.5 foundation model. Accepts pandas DataFrames or Darts TimeSeries as input, automatically sorts by time, and produces point forecasts with optional quantile predictions.

The following attributes apply to the `TimesFM` template:
- **`model_name` (str, optional)**: Hugging Face model identifier for TimesFM. Defaults to `"google/timesfm-2.5-200m-pytorch"`.
- **`forecasting_config` (ForecastConfigBM, optional)**: Forecasting behavior configuration passed to `TimesFM.compile()`. Defaults to `ForecastConfigBM()`.
- **`forecast_horizon` (int, optional)**: Number of future steps to predict for each input series. Defaults to `12`.
- **`validation_mode` (bool, optional)**: If `True`, reserves the last `forecast_horizon` points for validation. Defaults to `False`.
- **`time_series_output_format` (Literal, optional)**: Output format for predictions. One of `"pandas_dataframe"` or `"darts_series"`. Defaults to `"pandas_dataframe"`.
- **`device` (str, optional)**: Torch device used for inference, for example `"cpu"` or `"cuda:0"`. Defaults to `"cpu"`.
- **`time_format` (str | None, optional)**: Explicit datetime format for parsing and formatting. Defaults to `None` (auto-inferred).
- **`time_column_name` (str, optional)**: Name of the time column in the input dataframe. Defaults to `"Date"`.
</details>


For example, for ***TimesFM*** use ```sinx templates example-config TimesFM``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_timesfm_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: TimesFM
  class_name: TimesFM
  template_input: InputTemplate
  attributes:
    model_name: google/timesfm-2.5-200m-pytorch
    forecasting_config:
      max_context: 0
      max_horizon: 0
      normalize_inputs: false
      window_size: 0
      per_core_batch_size: 1
      use_continuous_quantile_head: false
      force_flip_invariance: true
      infer_is_positive: true
      fix_quantile_crossing: false
      return_backcast: false
    forecast_horizon: 12
    validation_mode: false
    time_series_output_format: pandas_dataframe
    device: cpu
    time_format: null
    time_column_name: Date
```

## Example Agent

The following is adapted directly from the package’s shipped [`timesfm_from_df.yml`](src/sinapsis_timesfm/configs/timesfm_from_df.yml) configuration. Save it as `my_timesfm_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_timesfm_agent
  description: "agent to perform time series forecasting using the TimesFM model from google"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: CSVReader
    class_name: CSVDatasetReader
    template_input: InputTemplate
    attributes:
      root_dir: ./artifacts
      path_to_csv: bitcoin.csv
      store_as_time_series: true

  - template_name: TimesFM
    class_name: TimesFM
    template_input: CSVReader
    attributes:
      validation_mode: True
      model_name: "google/timesfm-2.5-200m-pytorch"
      device: "cpu"
      time_series_output_format: "darts_series" # options: "pandas_dataframe", "darts_series"
      forecasting_config:
        max_context: 1024
        max_horizon: 256
        normalize_inputs: true
        use_continuous_quantile_head: true
        force_flip_invariance: true
        infer_is_positive: true
        fix_quantile_crossing: true

      forecast_horizon: 30

  - template_name: MAETimeSeriesMetrics
    class_name: maeTimeSeriesWrapper
    template_input: TimesFM
    attributes:
      mae: {}

  - template_name: TimeSeriesVisualization
    class_name: TimeSeriesVisualization
    template_input: MAETimeSeriesMetrics
    attributes:
      root_dir: artifacts/html_viz
      html_figure_save_path: "forecast_plot.html"

  - template_name: ImageSaver
    class_name: ImageSaver
    template_input: TimeSeriesVisualization
    attributes:
      save_dir: image_viz
      root_dir: artifacts/image_viz
```

```bash
sinx jobs run my_timesfm_agent.yaml
```

More configurations: [`timesfm_from_df.yml`](src/sinapsis_timesfm/configs/timesfm_from_df.yml), [`timesfm_from_darts_ts.yml`](src/sinapsis_timesfm/configs/timesfm_from_darts_ts.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
