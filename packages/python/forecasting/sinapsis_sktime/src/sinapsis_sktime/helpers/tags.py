from enum import Enum


class Tags(str, Enum):
    """Tags for sinapsis-sktime templates."""

    CLASSIFICATION = "classification"
    DYNAMIC = "dynamic"
    INFERENCE = "inference"
    FORECASTING = "forecasting"
    MODELS = "models"
    PREDICTION = "prediction"
    SKTIME = "sktime"
