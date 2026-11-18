import re

COMMON_CONTROL_MARKERS_PATTERN = re.compile(
    r"(<\|[^|>]+?\|>|<\uFF5C[^\uFF5C>]+?\uFF5C>|</?s>|\[/?INST\]|<<SYS>>|<</SYS>>)"
)
EXCESSIVE_NEWLINES_PATTERN = re.compile(r"\n{3,}")


def postprocess_text(input_text: str) -> str:
    """Remove common control markers from generated text.

    Args:
        input_text (str): Raw model text to normalize.

    Returns:
        str: Cleaned response text.
    """
    cleaned_text = COMMON_CONTROL_MARKERS_PATTERN.sub("", input_text)
    cleaned_text = EXCESSIVE_NEWLINES_PATTERN.sub("\n\n", cleaned_text)
    return cleaned_text.strip()
