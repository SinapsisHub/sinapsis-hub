from enum import Enum


class Tags(str, Enum):
    """Enum of tag strings used to label BERTopic-related templates."""

    BERTOPIC = "BERTopic"
    TOPIC_MODELING = "Topic_Modeling"
    VISUALIZATION = "Visualization"
    NLP = "NLP"
    EMBEDDINGS = "Embeddings"
    CLUSTERING = "Clustering"
