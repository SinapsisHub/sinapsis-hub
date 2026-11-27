from enum import Enum


class Tags(Enum):
    """Enumeration of tags used for categorizing models and algorithms.

    Attributes:
        POLYFUZZ (str): Represents the PolyFuzz string matching framework.
        MATCHING (str): Represents general matching algorithms.
        EMBEDDING (str): Represents embedding-based similarity methods.
        SENTENCE_ENCODER (str): Represents sentence-level encoding models.
        RECONCILIATION (str): Represents reconciliation of two tabular sources.
        TABULAR (str): Represents tabular/DataFrame processing.
    """

    POLYFUZZ = "polyfuzz"
    MATCHING = "matching"
    EMBEDDING = "embedding"
    SENTENCE_ENCODER = "sentence_encoder"
    RECONCILIATION = "reconciliation"
    TABULAR = "tabular"
