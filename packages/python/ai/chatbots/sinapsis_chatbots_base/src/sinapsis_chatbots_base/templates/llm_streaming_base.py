from abc import abstractmethod
from collections.abc import AsyncGenerator
from copy import deepcopy
from typing import Any, cast

from sinapsis.data_transport import DataContainer, LLMConversationPacket

from sinapsis_chatbots_base.templates.llm_template_base import LLMTemplateBase

SENTINEL_GENERIC_KEY = "SINAPSIS_SENTINEL"
SINAPSIS_END_OF_STREAM = "SINAPSIS_END_OF_STREAM"


class LLMStreamingTemplateBase(LLMTemplateBase):
    """Thin base for streaming LLM templates that emit partial `DataContainer` updates."""

    IS_STREAMING = True

    @abstractmethod
    def stream_backend(self, payload: Any, llm_conversation: LLMConversationPacket) -> AsyncGenerator[Any, None]:
        """Yield provider-specific stream events for one conversation packet.

        Args:
            payload (Any): Backend payload for the request.
            llm_conversation (LLMConversationPacket): Conversation packet being processed.

        Yields:
            Any: Provider-specific stream events.
        """

    @abstractmethod
    def aggregate_stream_event(self, aggregated_event: Any | None, event: Any) -> Any:
        """Merge one stream event into the aggregated stream result.

        Args:
            aggregated_event (Any | None): Aggregated stream result so far.
            event (Any): Provider-specific stream event.

        Returns:
            Any: Updated aggregated stream result.
        """

    @abstractmethod
    def extract_stream_delta(self, event: Any) -> str | None:
        """Extract the text delta from one stream event.

        Args:
            event (Any): Provider-specific stream event.

        Returns:
            str | None: Text delta, if available.
        """

    @abstractmethod
    def update_partial_packet_from_stream(
        self, partial_packet: LLMConversationPacket, event: Any, delta_text: str
    ) -> None:
        """Update a partial packet from one stream event.

        Args:
            partial_packet (LLMConversationPacket): Packet clone to mutate.
            event (Any): Provider-specific stream event.
            delta_text (str): Text delta extracted from the event.
        """

    @abstractmethod
    def finalize_stream_packet(self, llm_conversation: LLMConversationPacket, aggregated_event: Any) -> None:
        """Finalize one packet after the stream completes.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            aggregated_event (Any): Aggregated provider-specific stream result.
        """

    async def async_execute(self, container: DataContainer) -> AsyncGenerator[DataContainer, None]:
        """Execute streaming generation and emit partial containers.

        Args:
            container (DataContainer): Input container.

        Yields:
            DataContainer: Partial containers during streaming and a final EOS-marked container.
        """
        if not container.llm_conversations:
            self.logger.debug("Container has no llm conversations to process. Returning.")
            container.generic_data[SENTINEL_GENERIC_KEY] = SINAPSIS_END_OF_STREAM
            yield container
            return

        for index, llm_conversation in enumerate(container.llm_conversations):
            payload = self.build_backend_payload(llm_conversation, container=container)
            aggregated_event: Any | None = None

            async for event in self.stream_backend(payload, llm_conversation):
                aggregated_event = self.aggregate_stream_event(aggregated_event, event)
                delta_text = self.extract_stream_delta(event)
                if not delta_text:
                    continue

                partial_container = deepcopy(container)
                partial_packet = deepcopy(llm_conversation)
                self.update_partial_packet_from_stream(partial_packet, event, delta_text)
                partial_container.llm_conversations[index] = partial_packet
                yield partial_container

            if aggregated_event is not None:
                self.finalize_stream_packet(llm_conversation, aggregated_event)
                self.postprocess_llm_conversation(llm_conversation)

        container.generic_data[cast(str, SENTINEL_GENERIC_KEY)] = SINAPSIS_END_OF_STREAM
        yield container
