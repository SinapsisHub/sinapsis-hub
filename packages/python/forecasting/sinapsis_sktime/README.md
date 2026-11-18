<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Sktime
<br>
</h1>

<h3 align="center">Apply sktime estimators and forecasting models to time-series data.</h3>

## Overview

**`sinapsis-sktime`** — Module for handling time series data and forecasting using sktime.

sktime offers a scikit-learn-style ecosystem for classical and modern time-series modelling. Sinapsis wraps its fitting/prediction workflows so they can share ingestion and result handling with other components.

### Where it fits

Choose compatible estimator extras (`estimators`, `torch`, `tensorflow`) and preserve the time index and forecasting horizon. Not every model requires a deep-learning backend.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-sktime
# or
pip install sinapsis-sktime
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `pandas` | Pandas support. **Dependencies:** `pandas` |
| `estimators` | Estimators support. **Dependencies:** `arch`, `joblib`, `numba`, `pmdarima`, `prophet` and 5 more |
| `torch` | PyTorch-backed operations. **Dependencies:** `torch` |
| `tensorflow` | Tensorflow support. **Dependencies:** `tensorflow` |
| `all` | Bundle declared by this package; its manifest includes `pandas`, `estimators`, `torch`, `tensorflow`. It does not include `data-tools`. |
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers[sklearn-datasets,sktime-datareaders]`, `sinapsis-data-writers` |

For example:

```bash
uv pip install "sinapsis-sktime[pandas]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis SKTime** provides a powerful and flexible implementation for time series forecasting using the [sktime library](https://www.sktime.org/en/stable/).

<details>
<summary><strong><span style="font-size: 1.25em;">ThetaForecaster</span></strong></summary>

The following attributes apply to ThetaForecaster template:
- **`generic_field_key_data` (str, required)**: The key of the generic field containing the time series data.

This template loads time series data from the specified generic field key and creates a TimeSeriesPacket which is then added to the DataContainer.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">SKTime Forecasters</span></strong></summary>

The following attributes apply to all SKTime forecasting templates:
- **`generic_field_for_data` (str, optional)**: The key of the generic field where datasets are stored. Defaults to "SKTimeDatasets".
- **`model_save_path` (str, required)**: Path where the trained model will be saved.
- **`n_steps_ahead` (int, optional)**: Number of steps ahead to forecast. Defaults to 37.

The package provides access to a wide range of forecasting models from sktime, including:
- ARCH
- StatsForecastARCH
- StatsForecastGARCH
- ARIMA
- AutoARIMA
- ExponentialSmoothing
- StatsModelsARIMA
- NaiveForecaster
- NaiveVariance
- ThetaForecaster
- ThetaModularForecaster
- TrendForecaster
- PolynomialTrendForecaster
</details>


For example, for ***ThetaForecaster*** use ```sinx templates example-config ThetaForecasterSKTimeWrapper``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_sktime_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: ThetaForecasterSKTimeWrapper
  class_name: ThetaForecasterSKTimeWrapper
  template_input: InputTemplate
  attributes:
    root_dir: '`replace_me:<class ''str''>`'
    model_save_path: '`replace_me:<class ''str''>`'
    n_steps_ahead: 37
    thetaforecaster_init:
      initial_level: null
      deseasonalize: true
      sp: 1
      deseasonalize_model: multiplicative
```

## Example Agent

The following is adapted directly from the package’s shipped [`sktime_arima_forecaster.yml`](src/sinapsis_sktime/configs/sktime_arima_forecaster.yml) configuration. Save it as `my_sktime_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_sktime_agent

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: load_airlineWrapper
    class_name: load_airlineWrapper
    template_input: InputTemplate
    attributes:
      split_dataset: true
      train_size: 0.8
      store_as_time_series: True
      load_airline:
        {}

  - template_name: ARIMASKTimeWrapper
    class_name: ARIMASKTimeWrapper
    template_input: load_airlineWrapper
    attributes:
      generic_field_key: load_airlineWrapper
      n_steps_ahead: 12
      forecast_horizon_in_fit: true
      model_save_path: "artifacts/arima.pkl"
      task_type: "forecasting"
      arima_init: {}
```

```bash
sinx jobs run my_sktime_agent.yaml
```

More configurations: [`sktime_arima_forecaster.yml`](src/sinapsis_sktime/configs/sktime_arima_forecaster.yml), [`sktime_bossensemble_classifier.yml`](src/sinapsis_sktime/configs/sktime_bossensemble_classifier.yml), [`sktime_trend_forecaster.yml`](src/sinapsis_sktime/configs/sktime_trend_forecaster.yml), [`airline_sktime_forecaster.yml`](src/sinapsis_sktime/configs/airline_sktime_forecaster.yml), [`sktime_kneighbors_classifier.yml`](src/sinapsis_sktime/configs/sktime_kneighbors_classifier.yml), [`longley_sktime_classifier.yaml`](src/sinapsis_sktime/configs/longley_sktime_classifier.yaml), [`airline_sktime_forecaster_worker.yml`](src/sinapsis_sktime/configs/airline_sktime_forecaster_worker.yml), [`longley_sktime_classifier_worker.yaml`](src/sinapsis_sktime/configs/longley_sktime_classifier_worker.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
