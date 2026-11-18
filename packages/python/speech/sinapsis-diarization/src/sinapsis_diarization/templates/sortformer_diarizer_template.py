# -*- coding: utf-8 -*-
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_diarization.base_models.supported_models import DEFAULT_SORTFORMER_MODEL, SUPPORTED_SORTFORMER_MODELS
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.sortformer_diarizer import SortformerEngine
from sinapsis_diarization.templates.base_diarizer_template import BaseDiarizerAttributes, SinapsisBaseDiarizer


class SortformerDiarizerAttributes(BaseDiarizerAttributes):
    model_name: SUPPORTED_SORTFORMER_MODELS = DEFAULT_SORTFORMER_MODEL


class SinapsisSortformerDiarizer(SinapsisBaseDiarizer):
    """Sortformer Diarizer Template. Runs a diarization pipeline with sortformer models.
    Sortformer[1] is a novel end-to-end neural model for speaker diarization,
    trained with unconventional objectives compared to existing end-to-end diarization models.
    Streaming Sortformer[2] employs an Arrival-Order Speaker Cache (AOSC) to store frame-level
    acoustic embeddings of previously observed speakers.
    Sortformer resolves permutation problem in diarization following
    the arrival-time order of the speech segments from each speaker.

    Supported models:
    'nvidia/diar_streaming_sortformer_4spk-v2.1'

    Attributes:
    model_name (str): name of model to run
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    root_dir(str): Path to root directory. Optional
    audio_file_path (str): Path to audio file. Optional

    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: SinapsisSortformerDiarizer
    class_name: SinapsisSortformerDiarizer
    template_input: InputTemplate
    attributes:
        model_name: nvidia/diar_streaming_sortformer_4spk-v2.1
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0
        root_dir: /root/.cache/sinapsis
        audio_file_path: null


    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[Tags.AUDIO, Tags.DIARIZATION, Tags.SORTFORMER, Tags.SPEAKER_DIARIZATION],
    )
    AttributesBaseModel = SortformerDiarizerAttributes
    attributes: AttributesBaseModel

    def make_inference_engine(self):
        return SortformerEngine(
            model_name=self.attributes.model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
        )
