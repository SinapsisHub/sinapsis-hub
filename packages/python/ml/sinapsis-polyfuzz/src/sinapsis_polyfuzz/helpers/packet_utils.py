from sinapsis.data_transport import DataContainer, DataFramePacket


def select_packet(container: DataContainer, source: str | None, index: int) -> DataFramePacket:
    """Select a DataFramePacket from a container by ``source`` when given, else by position.

    Args:
        container (DataContainer): Container to select from.
        source (str | None): Packet ``source`` to match. When None, ``index`` is used.
        index (int): Positional fallback within ``container.data_frames``.

    Returns:
        DataFramePacket: The selected packet.

    Raises:
        ValueError: If no packet matches the source, or the index is out of range.
    """
    if source is not None:
        for packet in container.data_frames:
            if packet.source == source:
                return packet
        available = [p.source for p in container.data_frames]
        raise ValueError(
            f"No DataFramePacket with source '{source}'. Available sources: {available}"
        )
    try:
        return container.data_frames[index]
    except IndexError as err:
        raise ValueError(
            f"Expected a DataFramePacket at index {index}, found {len(container.data_frames)} data frame(s)."
        ) from err


def column_values(
    packet: DataFramePacket, column: str, deduplicate: bool = False, dropna: bool = False
) -> list[str]:
    """Extract a column from a DataFramePacket (pandas or polars) as a list of strings.

    Args:
        packet (DataFramePacket): Packet holding the DataFrame.
        column (str): Column to extract.
        deduplicate (bool): Drop duplicate values, preserving order. Defaults to False.
        dropna (bool): Drop null/NaN cells before stringifying, so blank separator rows
            do not surface as a literal ``"nan"`` value. Defaults to False.

    Returns:
        list[str]: The column values as strings.

    Raises:
        ValueError: If the column is not present in the DataFrame.
    """
    if column not in packet.columns:
        raise ValueError(
            f"Column '{column}' not found in DataFrame. Available columns: {list(packet.columns)}"
        )
    series = packet.content[column]
    if dropna:
        series = series.drop_nulls() if packet.dataframe_type == "polars" else series.dropna()
    values = (
        series.cast(str).to_list()
        if packet.dataframe_type == "polars"
        else series.astype(str).tolist()
    )
    if deduplicate:
        return list(dict.fromkeys(values))
    return values
