# -*- coding: utf-8 -*-
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_diarization.base_models.supported_models import DEFAULT_CANARY_MODEL, SUPPORTED_CANARY_MODELS
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.canary_asr import CanaryTranscriber
from sinapsis_diarization.templates.base_asr_template import BaseASRAttributes, SinapsisBaseASR


class SinapsisCanaryASR(SinapsisBaseASR):
    """Canary ASR template. Transcribes an audio using the Canary model:
    NVIDIA NeMo Canary-Qwen-2.5B is an English speech recognition model
    that achieves state-of-the art performance on multiple English speech
    benchmarks. With 2.5 billion parameters and running at 418 RTFx,
    Canary-Qwen-2.5B supports automatic speech-to-text recognition (ASR)
    in English with punctuation and capitalization (PnC)

    Supported models:
    'nvidia/canary-qwen-2.5b'

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
    - template_name: SinapsisCanaryASR
    class_name: SinapsisCanaryASR
    template_input: InputTemplate
    attributes:
        model_name: nvidia/canary-qwen-2.5b
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0
        root_dir: null
        audio_file_path: null


    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[Tags.ASR, Tags.AUDIO, Tags.CANARY, Tags.TRANSCRIPTION],
    )

    class AttributesBaseModel(BaseASRAttributes):
        model_name: SUPPORTED_CANARY_MODELS = DEFAULT_CANARY_MODEL

    attributes: AttributesBaseModel

    def make_inference_engine(self):
        return CanaryTranscriber(
            model_name=self.attributes.model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
        )
