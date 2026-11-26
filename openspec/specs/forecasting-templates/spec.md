# Forecasting and Tabular ML Templates

## Purpose
These packages bring time-series forecasting and tabular machine learning into Agents:
- `sinapsis-data-analysis`: scikit-learn and XGBoost training and inference.
- `sinapsis-darts-forecasting`: darts models, preprocessing, metrics and visualization.
- `sinapsis-sktime`: sktime forecasters and classifiers.
- `sinapsis-timesfm`: Google TimesFM 2.5 zero-shot forecasting.

Most models are exposed as dynamically generated wrapper templates.

Citations are relative to `packages/python/forecasting/<package>/src/<module>/templates/`.

## Requirements

### Requirement: Dynamic tabular training templates
`sinapsis-data-analysis` SHALL generate a `<Model>Wrapper` training template for every class in `sklearn.linear_model`, `sklearn.neighbors`, `sklearn.neural_network`, `sklearn.tree`, `sklearn.svm` and `sklearn.cluster`, excluding the names in each module's exclusion list. It SHALL also generate templates for the XGBoost classes XGBClassifier, XGBRegressor, XGBRanker, XGBRFClassifier and XGBRFRegressor. (src: sinapsis-data-analysis training/sklearn_train.py; training/xgboost_train.py)

#### Scenario: Generated names
- **WHEN** the package is imported
- **THEN** templates such as `LinearRegressionWrapper`, `DecisionTreeClassifierWrapper` and `XGBClassifierWrapper` SHALL be resolvable

### Requirement: Tabular training behavior
A training template SHALL read split DataFramePackets, matching `x_train`, `x_test`, `y_train` and `y_test` as substrings of each packet's `source`. It SHALL fit the model, compute metrics and write them to `generic_data`. It SHALL save the model with joblib to `root_dir/model_save_path` only when a test set exists. (src: sinapsis-data-analysis training/ml_base_training.py:31-35)

#### Scenario: Train a classifier
- **GIVEN** the split output of `load_irisWrapper`
- **WHEN** `DecisionTreeClassifierWrapper` executes
- **THEN** accuracy, weighted precision, recall and F1 SHALL be written to generic_data
- **AND** the model SHALL be saved to `model_save_path`

#### Scenario: Regressor metrics
- **WHEN** a regressor wrapper executes
- **THEN** r2, mse and mae SHALL be written to generic_data

### Requirement: Tabular inference
`SKLearnInference` and `XGBoostInference` SHALL load a joblib model from `model_path`, predict on the last DataFrame in `container.data_frames`, and write the predictions to `generic_data`. (src: sinapsis-data-analysis inference/sklearn_inference.py:11; inference/xgboost_inference.py:12)

#### Scenario: Predict with saved model
- **GIVEN** a model saved by a training wrapper
- **WHEN** SKLearnInference executes with `model_path` and `target_key`
- **THEN** predictions SHALL be written to generic_data

### Requirement: darts forecasting models
`TimeSeriesModel` SHALL wrap every `darts.models` model, excluding AutoARIMA, the StatsForecast models, ensembles, conformal models and filters. Each wrapper SHALL re-fit on every execute and write `predictions` for `forecast_horizon` steps. (src: sinapsis_darts_forecasting time_series_model.py:19-38)

#### Scenario: ARIMA forecast
- **GIVEN** a TimeSeriesPacket loaded by `TimeSeriesFromCSVLoader`
- **WHEN** ARIMAWrapper runs with `forecast_horizon: 12`
- **THEN** the packet's `predictions` SHALL contain 12 future steps

#### Scenario: Defaults and unsupported covariates
- **WHEN** `forecast_horizon` is omitted
- **THEN** it SHALL default to 10
- **AND** covariates that the model does not support SHALL be ignored with a warning

### Requirement: darts preprocessing
`TimeSeriesPreprocessor` SHALL wrap `darts.dataprocessing.transformers` with the methods `fit`, `transform`, `fit_transform` and `inverse_transform`. It SHALL store the fitted parameters in the packet's `generic_data`. (src: sinapsis_darts_forecasting time_series_preprocessing.py:32)

#### Scenario: Scale then invert
- **GIVEN** `ScalerWrapper` with `method: fit_transform`
- **WHEN** a later `ScalerWrapper` with `method: inverse_transform` runs
- **THEN** it SHALL reuse the stored fitted parameters

### Requirement: darts metrics
`TimeSeriesMetrics` SHALL wrap `darts.metrics` (for example `maeTimeSeriesWrapper`). It SHALL append a DataFramePacket of overall and per-component metrics. (src: sinapsis_darts_forecasting time_series_metrics.py:23)

#### Scenario: MAE after forecast
- **WHEN** maeTimeSeriesWrapper runs after a validation-mode forecast
- **THEN** a metrics DataFramePacket SHALL be appended to `container.data_frames`

### Requirement: Time-series loading
`TimeSeriesFromCSVLoader`, `TimeSeriesFromDataframeLoader` and `TimeSeriesFromSeriesLoader` SHALL build darts `TimeSeries` objects from a CSV file, a DataFrame or a pandas Series, respectively. (src: sinapsis_darts_forecasting time_series_from_csv_loader.py:35)

#### Scenario: Load CSV
- **WHEN** TimeSeriesFromCSVLoader runs with `loader_params.path_to_csv`
- **THEN** a TimeSeriesPacket with darts content SHALL be produced

### Requirement: Time-series visualization
For each series column, `TimeSeriesVisualization` SHALL append a matplotlib PNG to `container.images` and a Plotly HTML file to `container.files`. Both SHALL include quantile bands. (src: sinapsis_darts_forecasting time_series_visualization.py:53)

#### Scenario: Forecast plot
- **WHEN** visualization runs after a forecast with default `plot_params`
- **THEN** one PNG ImagePacket and one HTML FilePacket SHALL be added per column
- **AND** the quantile bands SHALL span 0.05 to 0.95

### Requirement: sktime model wrappers
`sinapsis-sktime` SHALL generate `<Name>SKTimeWrapper` templates for these sktime modules:
- forecasting: ARIMA, adapters, arch, exponential smoothing, naive, theta and trend
- classification: distance, dictionary, feature, deep-learning, compose and dummy

(src: sinapsis_sktime sktime_forecasters.py; sktime_classifiers.py)

#### Scenario: Generated forecaster
- **WHEN** the package is imported
- **THEN** `ThetaForecasterSKTimeWrapper` SHALL be resolvable

### Requirement: sktime forecasting behavior
A sktime forecaster SHALL fit on `y_train`, predict over the index of `y_test`, write MAPE to `generic_data`, and pickle the model to `model_save_path`. (src: sinapsis_sktime sktime_models_base.py:14)

#### Scenario: Theta forecaster
- **GIVEN** a split of the airline dataset
- **WHEN** ThetaForecasterSKTimeWrapper executes
- **THEN** MAPE SHALL be written to generic_data

### Requirement: TimesFM zero-shot forecasting
`TimesFM` SHALL load its model from Hugging Face at init. It SHALL accept content as a DataFrame or a darts series and write a forecast of `forecast_horizon` steps to `predictions`. (src: sinapsis_timesfm timesfm.py:83-146)

#### Scenario: Defaults
- **WHEN** the attributes are omitted
- **THEN** `model_name` SHALL be `google/timesfm-2.5-200m-pytorch`
- **AND** `device` SHALL be `cpu`
- **AND** `forecast_horizon` SHALL be 12
- **AND** `output_format` SHALL be `darts_time_series`, with `dataframe` as the alternative

#### Scenario: Forecast from DataFrame
- **GIVEN** a CSV loaded as a DataFrame with a `Date` column
- **WHEN** TimesFM executes
- **THEN** 12 forecast steps SHALL be written to `predictions`
