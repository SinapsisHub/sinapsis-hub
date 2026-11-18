<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Darts-Forecasting
<br>
</h1>

<h3 align="center">Train, evaluate and visualise time-series forecasts using Darts.</h3>

## Overview

**`sinapsis-darts-forecasting`** — Module for handling time series data and forecasting using Darts.

Forecasting depends on carefully aligning time indexes, covariates, horizons and metrics. Darts Templates make those stages explicit rather than hiding them inside a single prediction call.

### Where it fits

Use Darts when you need its forecasting model families and time-series abstractions. Optional Pandas and visualization integrations support tabular ingestion and plotting but are not always required.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-darts-forecasting
# or
pip install sinapsis-darts-forecasting
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `pandas` | Pandas support. **Dependencies:** `pandas` |
| `all` | Bundle declared by this package; its manifest includes `pandas`, `time-series-visualization`. |
| `time-series-visualization` | Time series visualization support. **Dependencies:** `matplotlib`, `numpy`, `pandas`, `pillow`, `plotly` |

For example:

```bash
uv pip install "sinapsis-darts-forecasting[pandas]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

The **Sinapsis Darts Forecasting** provides a powerful and flexible implementation for time series forecasting using the [Darts library](https://unit8co.github.io/darts/README.html).
<details>
<summary><strong><span style="font-size: 1.25em;">TimeSeriesFromCSVLoader</span></strong></summary>

Loads one or more columns from a CSV file directly into a `TimeSeriesPacket` using `TimeSeries.from_csv()`. Supports assigning the result to any packet attribute (`content`, `past_covariates`, `future_covariates`, `predictions`) and can either create a new packet or update an existing one in the container.

The following attributes apply to `TimeSeriesFromCSVLoader`:
- **`root_dir` (str | None, optional)**: Base directory prepended to `path_to_csv`. If omitted, `path_to_csv` is used as-is.
- **`assign_to` (Literal, required)**: The `TimeSeriesPacket` attribute where the loaded series is stored. One of `"content"`, `"past_covariates"`, `"future_covariates"`, `"predictions"`.
- **`reuse_packet` (bool, optional)**: If `True`, assigns the loaded series to the first existing `TimeSeriesPacket` in the container instead of creating a new one. Useful when loading multiple columns (e.g., target + covariates) into the same packet. Defaults to `False`.
- **`loader_params` (FromCSVKwargs, required)**: CSV-specific loading parameters:
  - `path_to_csv` (str): Filename or relative path to the CSV file.
  - `time_col` (str | None): Column name to use as the time index.
  - `value_cols` (str | list[str] | None): Column(s) to use as series values.
  - `freq` (str | None): Time series frequency (e.g., `"D"` for daily, `"H"` for hourly).
  - `fill_missing_dates` (bool): If `True`, inserts rows for missing timestamps. Defaults to `False`.
  - `fillna_value` (float | None): Fill value for any resulting NaNs after date insertion.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">TimeSeriesFromDataframeLoader</span></strong></summary>

Converts Pandas `DataFrame` objects already present in a `TimeSeriesPacket` into Darts `TimeSeries` instances using `TimeSeries.from_dataframe()`. Useful when upstream templates deliver DataFrames that need to be converted before forecasting.

The following attributes apply to `TimeSeriesFromDataframeLoader`:
- **`apply_to` (list[Literal], required)**: List of `TimeSeriesPacket` attributes to convert. Valid values: `"content"`, `"past_covariates"`, `"future_covariates"`, `"predictions"`.
- **`from_pandas_kwargs` (FromDataFrameKwargs, optional)**: Keyword arguments forwarded to `TimeSeries.from_dataframe()`:
  - `time_col` (str | None): Column to use as the time index.
  - `value_cols` (str | list[str] | None): Column(s) to use as the series values.
  - `freq` (str | None): Time series frequency (e.g., `"D"`, `"H"`).
  - `fill_missing_dates` (bool): Insert rows for missing timestamps. Defaults to `False`.
  - `fillna_value` (float | None): Value used to fill NaNs introduced by date filling.
  - `make_copy` (bool): Whether to copy the underlying NumPy array. Defaults to `True`.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">TimeSeriesFromSeriesLoader</span></strong></summary>

Converts Pandas `Series` objects already present in a `TimeSeriesPacket` into Darts `TimeSeries` instances using `TimeSeries.from_series()`. The series index is automatically converted to timestamps via `to_timestamp()` before conversion.

The following attributes apply to `TimeSeriesFromSeriesLoader`:
- **`apply_to` (list[Literal], required)**: List of `TimeSeriesPacket` attributes to convert. Valid values: `"content"`, `"past_covariates"`, `"future_covariates"`, `"predictions"`.
- **`from_pandas_kwargs` (FromPandasBaseKwargs, optional)**: Keyword arguments forwarded to `TimeSeries.from_series()`:
  - `freq` (str | None): Time series frequency (e.g., `"D"`, `"H"`).
  - `fill_missing_dates` (bool): Insert rows for missing timestamps. Defaults to `False`.
  - `fillna_value` (float | None): Value used to fill NaNs introduced by date filling.
  - `make_copy` (bool): Whether to copy the underlying NumPy array. Defaults to `True`.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">Darts Transformers</span></strong></summary>

Dynamic wrapper that exposes every transformer from `darts.dataprocessing.transformers` as an individual Sinapsis template (e.g., `ScalerWrapper`, `MissingValuesFillerWrapper`, `BoxCoxWrapper`). Transformations are applied to the selected `TimeSeriesPacket` attributes in-place.

For stateful transformers (e.g., `Scaler`), fitted parameters can be persisted in `TimeSeriesPacket.generic_data` and recovered automatically for inverse transforms — enabling clean scaler/unscaler pairs in a pipeline without manual state management.

The following attributes apply to all Darts Transformer templates:
- **`apply_to` (list[Literal], required)**: `TimeSeriesPacket` attributes to transform. Valid values: `"content"`, `"past_covariates"`, `"future_covariates"`, `"predictions"`.
- **`method` (Literal, required)**: Transformation method to call. One of `"fit"`, `"transform"`, `"fit_transform"`, `"inverse_transform"`.
- **`transform_kwargs` (dict[str, Any], optional)**: Extra keyword arguments forwarded to the chosen method (e.g., `{"method": "linear"}` for `MissingValuesFiller`). Defaults to `{}`.
- **`params_key` (str | None, optional)**: Key under which fitted parameters are stored in `TimeSeriesPacket.generic_data`. Required when pairing a `fit_transform` step with a later `inverse_transform`. Defaults to `None` (no storage).

Additional transformer-specific init arguments can be set via the `*_init` key (e.g., `missingvaluesfiller_init`, `scaler_init`). These are forwarded directly to the transformer constructor.

> [!NOTE]
> For a full list of available transformers, see the [Darts transformers documentation](https://unit8co.github.io/darts/generated_api/darts.dataprocessing.transformers.html).
</details>
<details>
<summary><strong><span style="font-size: 1.25em;">Darts Models</span></strong></summary>

The following attribute apply only to templates from Darts Models:
- **`forecast_horizon` (int, optional)**: Number of future time steps the model should predict. Defaults to `10`.
- **`validation_mode` (bool, optional)**: If `True`, the model is trained on all but the last `forecast_horizon` steps of the target series and predictions are generated for that held-out window, enabling metric evaluation. Defaults to `False`.

Additional model-specific attributes can be dynamically assigned through the class initialization dictionary (`*_init` attributes). These correspond directly to the constructor arguments of the chosen Darts model and are typically used for hyperparameter configuration.

> [!NOTE]
> Not all Darts models support both `past_covariates` and `future_covariates`. Unsupported covariates are automatically ignored at runtime based on each model's `supports_past_covariates` / `supports_future_covariates` properties.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">TimeSeriesVisualization</span></strong></summary>

Generates per-packet visualizations of the historical target series alongside the model's predictions. For each `TimeSeriesPacket` that contains predictions, the template produces:

- One **Matplotlib PNG image** per time series column, stored as `ImagePacket` objects in `container.images`.
- One **interactive Plotly HTML file** per time series column, stored as `FilePacket` objects in `container.files`.

HTML files are named `<html_figure_save_path>_<packet_id>_<column>.html` so that multiple packets and multivariate series never overwrite each other.

The following attributes apply to `TimeSeriesVisualization`:
- **`html_figure_save_path` (str, optional)**: Base filename for the output HTML files. Defaults to `"forecast_plot.html"`.
- **`root_dir` (str, optional)**: Root directory where HTML files are saved. Defaults to `SINAPSIS_CACHE_DIR`. Parent directories are created automatically if they do not exist.
- **`plot_params` (TimeSeriesPlotParams, optional)**: Nested model to customise the appearance of both Matplotlib and Plotly figures. Available sub-fields:
  - `target_series_label` (str): Legend label for the historical series. Defaults to `"Historical"`.
  - `predictions_label` (str): Legend label for the predicted series. Defaults to `"Predictions"`.
  - `title` (str): Figure title. Defaults to `"Time Series Forecast Results"`.
  - `x_axis_title` (str): X-axis label. Defaults to `"Time"`.
  - `low_quantile` (float): Lower quantile bound for probabilistic prediction intervals (Matplotlib only). Defaults to `0.05`.
  - `high_quantile` (float): Upper quantile bound for probabilistic prediction intervals (Matplotlib only). Defaults to `0.95`.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">TimeSeriesMetrics</span></strong></summary>

Dynamic wrapper that exposes every metric from `darts.metrics` as an individual Sinapsis template (e.g., `maeTimeSeriesWrapper`, `mseTimeSeriesWrapper`, `rmseTimeSeriesWrapper`). The selected metric is applied to the predictions and ground truth of each `TimeSeriesPacket`, and the result is stored in `TimeSeriesPacket.generic_data` keyed by the metric function name.


The following attributes apply to all metric templates. They are specified as a nested dictionary under the metric function name (e.g., `mae: {}`):
- **`intersect` (bool, optional)**: When `True`, only the overlapping time interval between ground truth and predictions is used. Defaults to `True`.
- **`q` (float | list[float] | None, optional)**: Quantile(s) to evaluate for probabilistic or quantile predictions. Defaults to `None` (median for stochastic predictions).
- **`n_jobs` (int, optional)**: Number of parallel jobs when evaluating over a sequence of series. Defaults to `1`.
- **`verbose` (bool, optional)**: Whether to print progress. Defaults to `False`.

The following parameters are intentionally excluded and cannot be overridden via the template config (they are managed internally):
`actual_series`, `pred_series`, `component_reduction`, `series_reduction`, `time_reduction`.
</details>


For example, for ***TimeSeriesFromDataframeLoader*** use ```sinx templates example-config TimeSeriesFromDataframeLoader``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_darts_forecasting_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: TimeSeriesFromDataframeLoader
  class_name: TimeSeriesFromDataframeLoader
  template_input: InputTemplate
  attributes:
    apply_to: 'content'
    from_pandas_kwargs: {}
```

## Example Agent

The following is adapted directly from the package’s shipped [`time_series_arima.yml`](src/sinapsis_darts_forecasting/configs/time_series_arima.yml) configuration. Save it as `my_darts_forecasting_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_darts_forecasting_agent
  description: 'agent to perform time series forecasting using the Prophet model from darts'


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

- template_name: TimeSeriesFromDataframeLoader-1
  class_name: TimeSeriesFromDataframeLoader
  template_input: CSVReader
  attributes:
    apply_to: ["content"]
    from_pandas_kwargs:
      value_cols: "Volume BTC"
      time_col: "Date"
      fill_missing_dates: True
      freq: "D"


- template_name: TimeSeries
  class_name: ARIMAWrapper
  template_input: TimeSeriesFromDataframeLoader-1
  attributes:
    forecast_horizon: 30
    arima_init: {}
```

```bash
sinx jobs run my_darts_forecasting_agent.yaml
```

More configurations: [`time_series_arima.yml`](src/sinapsis_darts_forecasting/configs/time_series_arima.yml), [`time_series_xgb.yml`](src/sinapsis_darts_forecasting/configs/time_series_xgb.yml), [`time_series_arima_metrics.yml`](src/sinapsis_darts_forecasting/configs/time_series_arima_metrics.yml), [`time_series_prophet.yml`](src/sinapsis_darts_forecasting/configs/time_series_prophet.yml), [`time_series_arima_visualization.yml`](src/sinapsis_darts_forecasting/configs/time_series_arima_visualization.yml), [`time_series_lstm.yml`](src/sinapsis_darts_forecasting/configs/time_series_lstm.yml), [`time_series_nbeats_visualization.yml`](src/sinapsis_darts_forecasting/configs/time_series_nbeats_visualization.yml), [`time_series_lstm_visualization.yml`](src/sinapsis_darts_forecasting/configs/time_series_lstm_visualization.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
