from enum import Enum


class Tags(str, Enum):
    """Enumeration for tags used in optical character recognition."""

    EASYOCR = "easyocr"
    DOCUMENT = "document"
    IMAGE = "image"
    OCR = "optical_character_recognition"
    TEXT = "text"
    TEXT_RECOGNITION = "text_recognition"
