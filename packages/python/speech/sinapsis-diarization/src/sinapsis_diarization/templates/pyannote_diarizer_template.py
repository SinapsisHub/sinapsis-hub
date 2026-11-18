# -*- coding: utf-8 -*-
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_diarization.base_models.supported_models import DEFAULT_PYANNOTE_MODEL, SUPPORTED_PYANNOTE_MODELS
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.pyannote_diarizer import PyannoteEngine
from sinapsis_diarization.templates.base_diarizer_template import BaseDiarizerAttributes, SinapsisBaseDiarizer


class PyannoteDiarizerAttributes(BaseDiarizerAttributes):
    """
    model_name (str): name of the model to run
    num_speakers (str): number of speakers to predict
    """

    model_name: SUPPORTED_PYANNOTE_MODELS = DEFAULT_PYANNOTE_MODEL
    num_speakers: int = 2


class SinapsisPyannoteDiarizer(SinapsisBaseDiarizer):
    """PyannoteDiarizer Template. Runs a diarization pipeline with pyannote models.
    This pipeline ingests mono audio sampled at 16kHz and outputs speaker diarization.
    Stereo or multi-channel audio files are automatically downmixed to mono by averaging the channels.
    Audio files sampled at a different rate are resampled to 16kHz automatically upon loading.

    Supported models:
    'pyannote/speaker-diarization-community-1'

    Attributes:
    model_name (str): name of model to run
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    root_dir(str): Path to root directory. Optional
    audio_file_path (str): Path to audio file. Optional
    num_speakers (str): number of speakers to predict

    Example agent:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: SinapsisPyannoteDiarizer
    class_name: SinapsisPyannoteDiarizer
    template_input: InputTemplate
    attributes:
        model_name: pyannote/speaker-diarization-community-1
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0
        root_dir: /root/.cache/sinapsis
        audio_file_path: null
        num_speakers: 2

    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[Tags.AUDIO, Tags.DIARIZATION, Tags.PYANNOTE, Tags.SPEAKER_DIARIZATION],
    )
    AttributesBaseModel = PyannoteDiarizerAttributes
    attributes: PyannoteDiarizerAttributes

    def make_inference_engine(self):
        return PyannoteEngine(
            model_name=self.attributes.model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
            num_speakers=self.attributes.num_speakers,
        )
