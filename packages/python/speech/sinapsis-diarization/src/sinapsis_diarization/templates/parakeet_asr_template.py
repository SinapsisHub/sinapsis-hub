# -*- coding: utf-8 -*-
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_diarization.base_models.supported_models import DEFAULT_PARAKEET_MODEL, SUPPORTED_PARAKEET_MODELS
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.parakeet_asr import ParakeetASR
from sinapsis_diarization.templates.base_asr_template import BaseASRAttributes, SinapsisBaseASR


class SinapsisParakeetASR(SinapsisBaseASR):
    """Parakeet ASR template. Transcribes an audio using the Parakeet models.
    Parakeet  is a 600-million-parameter automatic speech recognition (ASR) model designed
    for high-quality English transcription, featuring support for punctuation,
    capitalization, and accurate timestamp prediction.

    Supported models:
    'parakeet-tdt-0.6b-v2'
    'parakeet-tdt-0.6b-v3'

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
    - template_name: SinapsisParakeetASR
    class_name: SinapsisParakeetASR
    template_input: InputTemplate
    attributes:
        model_name: nvidia/parakeet-tdt-0.6b-v2
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
        tags=[Tags.ASR, Tags.AUDIO, Tags.PARAKEET, Tags.TRANSCRIPTION],
    )

    class AttributesBaseModel(BaseASRAttributes):
        model_name: SUPPORTED_PARAKEET_MODELS = DEFAULT_PARAKEET_MODEL

    attributes: AttributesBaseModel

    def make_inference_engine(self):
        return ParakeetASR(
            model_name=self.attributes.model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
        )
