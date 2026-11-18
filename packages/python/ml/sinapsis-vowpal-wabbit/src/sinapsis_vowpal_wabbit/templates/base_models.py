from typing import Literal

from pydantic import BaseModel

DEFAULT_STOP_WORDS = [
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "you're",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
]


class TrainTestSplitParams(BaseModel):
    """Parameters for train-test split configuration."""

    train_size: float | None = None
    test_size: float | None = None
    shuffle: bool = True


class VWWorkspaceParams(BaseModel):
    """Workspace parameters for Vowpal Wabbit configuration."""

    bit_precision: int = 24

    quadratic_interactions: list[str] = []
    cubic_interactions: list[str] = []
    ngram_namespaces: list[str] = []
    ngram_size: int = 2

    learning_rate: float | None = None
    l1: float = 0.0
    l2: float = 0.0


class SentenceTransformerParams(BaseModel):
    """Configuration parameters for the SentenceTransformer model."""

    model_name: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    precision: Literal["float32", "int8", "uint8", "binary", "ubinary"] = "float32"
    normalize_embeddings: bool = True
    device: str = "cuda:0"
