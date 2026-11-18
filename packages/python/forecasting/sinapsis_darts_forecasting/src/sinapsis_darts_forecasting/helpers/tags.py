from enum import Enum


class Tags(str, Enum):
    """Tags for sinapsis-darts-forecasting templates."""

    DARTS = "darts"
    DATA = "data"
    DATAFRAMES = "dataframes"
    DYNAMIC = "dynamic"
    FORECASTING = "forecasting"
    METRICS = "metrics"
    MODELS = "models"
    PANDAS = "pandas"
    PREPROCESSING = "preprocessing"
    TIME_SERIES = "time_series"
    TRANSFORMS = "transforms"
    VISUALIZATION = "visualization"
    PLOTLY = "plotly"
    MATPLOTLIB = "matplotlib"
