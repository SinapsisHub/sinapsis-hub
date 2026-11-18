from enum import Enum


class Tags(str, Enum):
    """Tags."""

    ANOMALIB = "anomalib"
    ANOMALY_DETECTION = "anomaly_detection"
    DYNAMIC = "dynamic"
    EXPORT = "export"
    INFERENCE = "inference"
    MODELS = "models"
    OPENVINO = "openvino"
    PYTORCH = "pytorch"
    TRAINING = "training"
