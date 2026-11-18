from unsloth import FastLanguageModel

from sinapsis_unsloth.helpers.schemas.base import RoleDelimiters
from sinapsis_unsloth.helpers.schemas.inference import UnslothGenerateArgs
from sinapsis_unsloth.templates.unsloth_base import UnslothBase, UnslothBaseAttributes

from abc import abstractmethod

import torch
from sinapsis.data_transport import DataContainer, TextPacket
from sinapsis.template import TemplateAttributeType
from transformers import PreTrainedTokenizer, TextStreamer


class UnslothInferenceBaseAttributes(UnslothBaseAttributes):
    """Configuration attributes for Unsloth inference templates.

    Attributes:
        rag_context_key (str | None): Metadata key to retrieve RAG context from the text packet. Defaults to None.
        generate_args (UnslothGenerateArgs): Configuration for model generation parameters (temperature, max_new_tokens,
            sampling settings, etc.).
        stream (bool): Whether to enable token-by-token output streaming to the console. Defaults to False.
    """

    rag_context_key: str | None = None
    generate_args: UnslothGenerateArgs
    stream: bool = False


class UnslothInferenceBase(UnslothBase):
    """Base template for optimized LLM inference using Unsloth.

    Subclasses must implement model-type-specific behavior through the abstract methods.
    """

    AttributesBaseModel = UnslothInferenceBaseAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.model = self._set_inference_mode()
        self.pattern = self._setup_patterns()
        self.tokenizer = self._prepare_tokenizer()
        self.text_streamer = TextStreamer(self.tokenizer, skip_prompt=True) if self.attributes.stream else None

    def _set_inference_mode(self) -> FastLanguageModel:
        """Configures the model for optimized inference.

        Returns:
            FastLanguageModel: The optimized inference-ready model.
        """
        model = FastLanguageModel.for_inference(self.model)
        return model

    def cancel_execution(self) -> None:
        """Safely cancels the current execution and releases GPU memory.

        Deletes the current instance of the loaded language model and resets the corresponding
        attribute to `None`.
        """
        del self.model
        self.model = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    @abstractmethod
    def _setup_patterns(self) -> RoleDelimiters | None:
        """Set up and return the role delimiters.

        Subclasses must implement this method defining the patterns to use for extraction.

        Returns:
            RoleDelimiters or None: The role delimiters if they are set, otherwise None.
        """

    @abstractmethod
    def _prepare_tokenizer(self) -> PreTrainedTokenizer:
        """Prepares and returns the tokenizer for the model.

        Subclasses must implement this method to modify the tokenizer as needed.

        Returns:
            PreTrainedTokenizer: The tokenizer used by the model.
        """

    def get_extra_context(self, text_packet: TextPacket) -> str | None:
        """Retrieves RAG context data from packet metadata using the configured rag_context_key.

        Args:
            text_packet (TextPacket): The incoming TextPacket containing potential context data in its generic_data.

        Returns:
            str | None:  Newline-joined context strings when RAG data exists, or None when
                rag_context_key is unset, missing, or points to empty data
        """
        if self.attributes.rag_context_key is None:
            return None

        context_data = text_packet.generic_data.get(self.attributes.rag_context_key)
        if not context_data:
            return None

        return "\n".join(context_data)

    @abstractmethod
    def _format_inputs(self, text_packet: TextPacket) -> str | list[str]:
        """Model-specific input formatting (e.g., chat templates, instruction wrapping).

        Subclasses must implement this method to define the inputs for the models.

        Returns:
            A string or chat-structured input ready for tokenization.
        """

    def _tokenize(self, formatted_inputs: str | list[str]) -> dict[str, torch.Tensor]:
        """Formats and tokenizes the input instruction.

        Returns:
            dict[str, torch.Tensor]: Tokenized inputs ready for generation.
        """
        return self.tokenizer(formatted_inputs, return_tensors="pt").to("cuda")

    @staticmethod
    def extract_between_markers(text: str, start_marker: str | None, end_marker: str | None) -> str:
        """Extracts text between markers (if available).

        Args:
            text (str): Input text to process
            start_marker (str | None, optional): Beginning delimiter.
            end_marker (str | None, optional): Ending delimiter.

        Returns:
            str: Extracted text
        """
        extracted = text

        if start_marker and start_marker in extracted:
            extracted = extracted.split(start_marker, 1)[1]

        if end_marker and end_marker in extracted:
            extracted = extracted.split(end_marker, 1)[0]

        return extracted.strip()

    @abstractmethod
    def _extract_response(self, output: str) -> str | tuple[str, str]:
        """Processes raw model output into final response format.

        Subclasses must implement this method to define the extraction logic.

        Args:
            output (str): Complete generated text including any special tokens

        Returns:
            str | tuple[str, str]: For simple responses (non-reasoning models) a plan string
                is returned, otherwise a tuple of (reasoning_steps, final_answer)
        """

    def get_response(self, text_packet: TextPacket) -> str | tuple[str, str]:
        """Generates and processes a response for a single input.

        Args:
            text_packet: Input text with optional metadata

        Returns:
            str | tuple[str, str]: For simple responses (non-reasoning models) a plan string
                is returned, otherwise a tuple of (reasoning_steps, final_answer)
        """
        inputs = self._format_inputs(text_packet)
        tokenized_inputs = self._tokenize(inputs)
        outputs = self.model.generate(
            **tokenized_inputs,
            streamer=self.text_streamer,
            **self.attributes.generate_args.model_dump(exclude_none=True),
        )
        decoded_output = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        self.logger.debug(decoded_output)
        return self._extract_response(decoded_output)

    def execute(self, container: DataContainer) -> DataContainer:
        """Executes text generation with streaming output.

        Args:
            container (DataContainer): Input data container (passed through unchanged).

        Returns:
            The input container with generation results logged.
        """
        if not container.texts:
            self.logger.debug("No need to process response.")
            return container

        new_packets = []

        for text_packet in container.texts:
            response = self.get_response(text_packet)
            if isinstance(response, str):
                new_packets.append(TextPacket(content=response))
            else:
                cot, answer = response
                new_packets.append(TextPacket(content=answer, generic_data={self.instance_name: cot}))

        container.texts.extend(new_packets)
        return container
