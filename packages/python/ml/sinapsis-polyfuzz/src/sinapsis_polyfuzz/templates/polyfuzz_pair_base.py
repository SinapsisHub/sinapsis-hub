from collections.abc import Sequence

from sinapsis.data_transport import DataContainer, DataFramePacket
from sinapsis.template import OutputTypes, TemplateAttributes, UIPropertiesMetadata

from sinapsis_polyfuzz.helpers.packet_utils import column_values, select_packet
from sinapsis_polyfuzz.helpers.tags import Tags
from sinapsis_polyfuzz.templates.polyfuzz_base import PolyfuzzBase


class PolyfuzzPairAttributes(TemplateAttributes):
    """Attributes for paired (two-packet) Polyfuzz matching.

    Instead of matching a column against a static ``to_list``, the references and the
    targets are taken from columns of two DataFramePackets already in the container.

    Attributes:
        from_source (str | None): ``source`` of the packet holding the reference
            values. When None, the packet is picked by ``from_packet_index``.
        from_packet_index (int): Positional fallback for the reference packet.
        from_column (str): Column in the reference packet to match from.
        to_source (str | None): ``source`` of the packet holding the target values.
            When None, the packet is picked by ``to_packet_index``.
        to_packet_index (int): Positional fallback for the target packet.
        to_column (str): Column in the target packet to match against.
        overwrite (bool): If True, replace the reference packet's content with the
            matches table; otherwise append a new matches packet. Defaults to False.
        matches_source (str | None): ``source`` set on the appended matches packet
            (only used when ``overwrite`` is False).
        deduplicate (bool): Match over the unique values of each column (preserving
            order) instead of every row. Defaults to True.
        min_similarity (float): Backend-independent post-filter. Matches whose
            ``similarity_column`` is below this value are dropped (treated as
            no-match). Defaults to 0.0 (no filtering). Use this rather than relying on
            the matcher's own threshold, which is only honored by some backends.
        similarity_column (str): Name of the similarity column produced by the matcher.
            Defaults to "Similarity".
    """

    from_source: str | None = None
    from_packet_index: int = 0
    from_column: str
    to_source: str | None = None
    to_packet_index: int = 1
    to_column: str
    overwrite: bool = False
    matches_source: str | None = None
    deduplicate: bool = True
    min_similarity: float = 0.0
    similarity_column: str = "Similarity"


class PolyfuzzPairBase(PolyfuzzBase):
    """Polyfuzz matching between columns of two DataFramePackets.

    Reads a reference list and a target list from columns of two packets in the
    container, runs a single ``match(from_list, to_list)`` with the wrapped matcher,
    and writes the resulting matches DataFrame (columns ``From``/``To``/``Similarity``)
    back to the container. Unlike :class:`PolyfuzzBase`, it does not iterate over every
    DataFramePacket, so unrelated tables (e.g. with different columns) are untouched.
    """

    UIProperties = UIPropertiesMetadata(
        category="Polyfuzz",
        output_type=OutputTypes.MULTIMODAL,
        tags=[Tags.POLYFUZZ, Tags.MATCHING, Tags.TABULAR],
    )

    AttributesBaseModel = PolyfuzzPairAttributes

    def _save_matches(
        self, container: DataContainer, from_packet: DataFramePacket, matches: Sequence
    ) -> None:
        """Overwrite the reference packet with the matches table, or append a new packet."""
        if self.attributes.overwrite:
            from_packet.content = matches
        else:
            container.data_frames.append(
                DataFramePacket(content=matches, source=self.attributes.matches_source)
            )

    def execute(self, container: DataContainer) -> DataContainer:
        """Match ``from_column`` against ``to_column`` across two packets and store the result.

        Args:
            container (DataContainer): Container holding the reference and target packets.

        Returns:
            DataContainer: The container with the matches DataFrame appended (or the
            reference packet overwritten when ``overwrite`` is True).
        """
        from_packet = select_packet(
            container, self.attributes.from_source, self.attributes.from_packet_index
        )
        from_list = column_values(
            from_packet, self.attributes.from_column, self.attributes.deduplicate
        )
        if not from_list:
            self.logger.info("No reference values to match; returning container unchanged.")
            return container

        to_packet = select_packet(
            container, self.attributes.to_source, self.attributes.to_packet_index
        )
        to_list = column_values(to_packet, self.attributes.to_column, self.attributes.deduplicate)

        matches = self.wrapped_callable.match(from_list, to_list)
        matches = self._apply_min_similarity(matches)
        self._save_matches(container, from_packet, matches)
        return container

    def _apply_min_similarity(self, matches: Sequence) -> Sequence:
        """Drop matches whose similarity is below ``min_similarity`` (backend-independent)."""
        atts = self.attributes
        if atts.min_similarity <= 0.0 or atts.similarity_column not in matches.columns:
            return matches
        keep = matches[atts.similarity_column].fillna(0.0) >= atts.min_similarity
        return matches[keep].reset_index(drop=True)
