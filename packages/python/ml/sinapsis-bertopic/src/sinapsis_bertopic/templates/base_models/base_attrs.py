from typing import Any, Literal

from pydantic import BaseModel, Field

supported_metrics = Literal[
    "euclidean",
    "manhattan",
    "chebyshev",
    "minkowski",
    "canberra",
    "braycurtis",
    "mahalanobis",
    "wminkowski",
    "seuclidean",
    "cosine",
    "correlation",
    "haversine",
    "hamming",
    "jaccard",
    "dice",
    "russelrao",
    "kulsinski",
    "ll_dirichlet",
    "hellinger",
    "rogerstanimoto",
    "sokalmichener",
    "sokalsneath",
    "yule]",
]

supported_init_embbedings = Literal["spectral", "random", "pca", "tswspectral"]


class UMAPModelParams(BaseModel):
    """Configuration parameters for the UMAP dimensionality reduction model."""

    n_neighbors: int = 15
    n_components: int = 2
    metric: supported_metrics = "euclidean"
    metric_kwds: dict | None = None
    output_metric: str = "euclidean"
    output_metric_kwds: dict | None = None
    n_epochs: int | None = None
    learning_rate: float = 1.0
    init: supported_init_embbedings = "spectral"
    min_dist: float = 0.1
    spread: float = 1.0
    low_memory: bool = True
    n_jobs: int = -1
    set_op_mix_ratio: float = 1.0
    local_connectivity: float = 1.0
    repulsion_strength: float = 1.0
    negative_sample_rate: int = 5
    transform_queue_size: float = 4.0
    a: float | None = None
    b: float | None = None
    random_state: int | None = None
    angular_rp_forest: bool = False
    target_n_neighbors: int = -1
    target_metric: str = "categorical"
    target_metric_kwds: dict | None = None
    target_weight: float = 0.5
    transform_seed: int = 42
    transform_mode: Literal["embedding", "graph"] = "embedding"
    force_approximation_algorithm: bool = False
    verbose: bool = False
    tqdm_kwds: dict | None = None
    unique: bool = False
    densmap: bool = False
    dens_lambda: float = 2.0
    dens_frac: float = 0.3
    dens_var_shift: float = 0.1
    output_dens: bool = False
    disconnection_distance: float | None = None
    precomputed_knn: tuple = (None, None, None)


supported_algorithms = Literal["best", "prims_kdtree", "prims_balltree", "boruvka_kdtree", "boruvka_balltree"]


class HDBSCANModelParams(BaseModel):
    """Configuration parameters for the HDBSCAN clustering model."""

    min_cluster_size: int = 5
    min_samples: int | None = None
    cluster_selection_epsilon: float = 0.0
    cluster_selection_persistence: float = 0.0
    max_cluster_size: int = 0
    metric: Literal["euclidean", "manhattan"] = "euclidean"
    alpha: float = 1.0
    p: int | None = None
    algorithm: supported_algorithms = "best"
    leaf_size: int = 40
    approx_min_span_tree: bool = True
    gen_min_span_tree: bool = False
    core_dist_n_jobs: int = 4
    cluster_selection_method: Literal["eom", "leaf"] = "eom"
    allow_single_cluster: bool = False
    prediction_data: bool = True
    branch_detection_data: bool = False
    match_reference_implementation: bool = False
    cluster_selection_epsilon_max: float = Field(default_factory=lambda: float("inf"))
    kwargs: dict[str, Any] = Field(default_factory=dict)


class BERTopicModelParams(BaseModel):
    """Configuration parameters for the BERTopic model."""

    language: str = "english"
    top_n_words: int = 10
    n_gram_range: tuple[int, int] = (1, 1)
    min_topic_size: int = 5
    nr_topics: int | str | None = None
    low_memory: bool = False
    calculate_probabilities: bool = False
    seed_topic_list: list[list[str]] | None = None
    zeroshot_topic_list: list[str] | None = None
    zeroshot_min_similarity: float = 0.7


class ToImageParams(BaseModel):
    """Parameters for exporting a Plotly figure to an image file."""

    format: Literal["png", "jpg", "jpeg", "webp", "svg", "pdf"] = "png"
    width: int | None = None
    height: int | None = None
    scale: int | float | None = None
    validate_figure: bool = Field(alias="validate", default=True)


class VisualizeTopicsParams(BaseModel):
    """Parameters for BERTopic topic visualization."""

    topics: list[int] | None = None
    top_n_topics: int | None = None
    use_ctfidf: bool = False
    custom_labels: bool = False
    title: str = "<b>Intertopic Distance Map</b>"
    figure_width: int = Field(alias="width", default=650)
    figure_height: int = Field(alias="height", default=650)


class VisualizeDocumentsParams(BaseModel):
    """Parameters for BERTopic document visualization."""

    topics: list[int] | None = None
    sample: float | None = None
    hide_annotations: bool = False
    hide_document_hover: bool = False
    custom_labels: bool = False
    title: str = "<b>Documents and Topics</b>"
    width: int = 1200
    height: int = 750


class BERTopicSaveModelParams(BaseModel):
    """Parameters for serializing and saving a fitted BERTopic model."""

    serialization: Literal["safetensors", "pytorch", "pickle"] = "safetensors"
    save_ctfidf: bool = True


class CTFIDFModelParams(BaseModel):
    """Configuration parameters for the c-TF-IDF model."""

    bm25_weighting: bool = True
    reduce_frequent_words: bool = True
    seed_multiplier: int = 2
    seed_words: list[str] | None = None
