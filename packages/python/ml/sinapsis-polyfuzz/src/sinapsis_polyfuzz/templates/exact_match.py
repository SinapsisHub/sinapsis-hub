import pandas as pd
from sinapsis.data_transport import DataContainer, DataFramePacket
from sinapsis.template import OutputTypes, TemplateAttributes, UIPropertiesMetadata
from sinapsis.template import Template

from sinapsis_polyfuzz.helpers.packet_utils import column_values, select_packet
from sinapsis_polyfuzz.helpers.tags import Tags


class ExactMatch(Template):
    """Splits reference values into exact matches and a non-exact residual.

    Compares a column of one DataFramePacket (references) against a column of another
    (targets) by normalized string equality. References that have an exact target are
    emitted as a matches DataFramePacket (``From``/``To``/``Similarity`` = 1.0, the
    same schema as the Polyfuzz matchers); the rest are emitted as a residual
    DataFramePacket holding only the unmatched references, ready to be fed to a
    downstream fuzzy matcher (e.g. ``TFIDFPairWrapper``).

    Packets are selected by ``from_source`` / ``to_source`` when set, otherwise by
    positional index.
    """

    UIProperties = UIPropertiesMetadata(
        category="Polyfuzz",
        output_type=OutputTypes.MULTIMODAL,
        tags=[Tags.MATCHING, Tags.RECONCILIATION, Tags.TABULAR],
    )

    class AttributesBaseModel(TemplateAttributes):
        """Attributes for :class:`ExactMatch`.

        Attributes:
            from_source (str | None): ``source`` of the reference packet. When None,
                picked by ``from_packet_index``.
            from_packet_index (int): Positional fallback for the reference packet.
            from_column (str): Column in the reference packet to match from.
            to_source (str | None): ``source`` of the target packet. When None, picked
                by ``to_packet_index``.
            to_packet_index (int): Positional fallback for the target packet.
            to_column (str): Column in the target packet to match against.
            exact_matches_source (str): ``source`` set on the appended exact-matches
                packet (``From``/``To``/``Similarity``).
            no_exact_matches_source (str): ``source`` set on the appended residual
                packet (one column named like ``from_column``).
            strip (bool): Strip surrounding whitespace before comparing. Defaults True.
            similarity_value (float): Value written to the ``Similarity`` column for
                exact matches. Defaults to 1.0.
        """

        from_source: str | None = None
        from_packet_index: int = 0
        from_column: str
        to_source: str | None = None
        to_packet_index: int = 1
        to_column: str
        exact_matches_source: str = "exact_matches"
        no_exact_matches_source: str = "no_exact_matches"
        strip: bool = True
        similarity_value: float = 1.0

    def _normalize(self, value: str) -> str:
        return value.strip() if self.attributes.strip else value

    def execute(self, container: DataContainer) -> DataContainer:
        """Split references into exact matches and residual, appending both packets.

        Args:
            container (DataContainer): Container holding the reference and target packets.

        Returns:
            DataContainer: The container with an exact-matches packet and a residual
            packet appended, plus counts written to ``generic_data``.
        """
        atts = self.attributes
        from_packet = select_packet(container, atts.from_source, atts.from_packet_index)
        to_packet = select_packet(container, atts.to_source, atts.to_packet_index)

        from_values = column_values(from_packet, atts.from_column, deduplicate=True, dropna=True)
        to_values = column_values(to_packet, atts.to_column, deduplicate=True, dropna=True)
        to_lookup = {self._normalize(t): t for t in to_values}

        exact_from: list[str] = []
        exact_to: list[str] = []
        residual: list[str] = []
        for value in from_values:
            target = to_lookup.get(self._normalize(value))
            if target is not None:
                exact_from.append(value)
                exact_to.append(target)
            else:
                residual.append(value)

        exact_df = pd.DataFrame(
            {
                "From": exact_from,
                "To": exact_to,
                "Similarity": [atts.similarity_value] * len(exact_from),
            }
        )
        residual_df = pd.DataFrame({atts.from_column: residual})

        container.data_frames.append(
            DataFramePacket(content=exact_df, source=atts.exact_matches_source)
        )
        container.data_frames.append(
            DataFramePacket(content=residual_df, source=atts.no_exact_matches_source)
        )

        summary = {"exact_matches": len(exact_from), "no_exact_matches": len(residual)}
        self._set_generic_data(container, summary)
        self.logger.info(f"ExactMatch: {summary}")
        return container
