from __future__ import annotations

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Self

TEXT_RESPONSE_FORMAT: Final[Literal["text"]] = "text"
JSON_OBJECT_RESPONSE_FORMAT: Final[Literal["json_object"]] = "json_object"
JSON_SCHEMA_RESPONSE_FORMAT: Final[Literal["json_schema"]] = "json_schema"


class PropertyDefinition(BaseModel):
    """Structured definition for one schema property.

    Attributes:
        type_ (str): JSON schema type. Aliased to `type`.
        description (str | None): Optional field description.
        enum (list[str] | None): Optional allowed values.
        properties (dict[str, str | Self] | None): Nested object properties.
        required (list[str] | None): Required nested property names.
        items (str | Self | None): Item schema when the property is an array.
        additional_properties (bool | None): Whether extra object fields are allowed.
    """

    type_: str = Field(default="string", alias="type")
    description: str | None = None
    enum: list[str] | None = None
    properties: dict[str, str | Self] | None = None
    required: list[str] | None = None
    items: str | Self | None = None
    additional_properties: bool | None = Field(default=None, alias="additionalProperties")

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def _convert_property(prop: str | PropertyDefinition) -> dict[str, Any]:
        """Convert a property definition into JSON schema format.

        Args:
            prop (str | PropertyDefinition): Property type or nested definition.

        Returns:
            dict[str, Any]: JSON schema property definition.
        """
        if isinstance(prop, str):
            return {"type": prop}
        return prop.to_json_schema()

    def to_json_schema(self) -> dict[str, Any]:
        """Convert this property into JSON schema format.

        Returns:
            dict[str, Any]: JSON schema property definition.
        """
        result: dict[str, Any] = {"type": self.type_}
        if self.description is not None:
            result["description"] = self.description
        if self.enum is not None:
            result["enum"] = self.enum
        if self.type_ == "object" and self.properties is not None:
            result["properties"] = {k: self._convert_property(v) for k, v in self.properties.items()}
            if self.required is not None:
                result["required"] = self.required
            if self.additional_properties is not None:
                result["additionalProperties"] = self.additional_properties
        if self.type_ == "array" and self.items is not None:
            result["items"] = self._convert_property(self.items)
        return result


PropertyDefinition.model_rebuild()


class SchemaDefinition(BaseModel):
    """JSON schema definition for structured outputs.

    Attributes:
        properties (dict[str, str | PropertyDefinition]): Root schema properties.
        required (list[str]): Required root property names.
        additional_properties (bool | None): Whether extra root-level fields are allowed.
    """

    properties: dict[str, str | PropertyDefinition] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool | None = Field(default=None, alias="additionalProperties")

    @staticmethod
    def _convert_property(prop: str | PropertyDefinition) -> dict[str, Any]:
        """Convert a property definition into JSON schema format.

        Args:
            prop (str | PropertyDefinition): Property type or nested definition.

        Returns:
            dict[str, Any]: JSON schema property definition.
        """
        if isinstance(prop, str):
            return {"type": prop}
        return prop.to_json_schema()

    def to_json_schema(self) -> dict[str, Any]:
        """Convert this schema into JSON schema format.

        Returns:
            dict[str, Any]: Full JSON schema object.
        """
        json_properties = {key: self._convert_property(prop) for key, prop in self.properties.items()}
        result: dict[str, Any] = {"type": "object", "properties": json_properties, "required": self.required}
        if self.additional_properties is not None:
            result["additionalProperties"] = self.additional_properties
        return result


class LLMResponseFormat(BaseModel):
    """Provider-neutral structured output configuration.

    Attributes:
        type_ (Literal["text", "json_object"]): Output mode. Aliased to `type`.
        schema_ (SchemaDefinition): Optional schema used for structured JSON output. Aliased to `schema`.
    """

    type_: Literal["text", "json_object"] = Field(default=TEXT_RESPONSE_FORMAT, alias="type")
    schema_: SchemaDefinition = Field(default_factory=SchemaDefinition, alias="schema")

    model_config = ConfigDict(populate_by_name=True)

    def is_structured(self) -> bool:
        """Return whether the response format requires structured output.

        Returns:
            bool: True when structured JSON output is requested.
        """
        return self.type_ == JSON_OBJECT_RESPONSE_FORMAT

    def has_schema(self) -> bool:
        """Return whether a JSON schema was provided.

        Returns:
            bool: True when schema properties are defined.
        """
        return bool(self.schema_.properties)

    def to_json_schema(self) -> dict[str, Any] | None:
        """Return the configured JSON schema when structured output is enabled.

        Returns:
            dict[str, Any] | None: JSON schema object, or None for text mode.
        """
        if not self.is_structured():
            return None
        if not self.has_schema():
            return {"type": "object"}
        return self.schema_.to_json_schema()


class LLMInitArgs(BaseModel):
    """Base arguments for initializing any LLM.

    Attributes:
        llm_model_name (str): The name or path of the LLM model to use
                            (e.g., 'claude-3-7-sonnet-latest', 'TheBloke/Llama-2-7B-GGUF').
    """

    llm_model_name: str


class LLMCompletionArgs(BaseModel):
    """Base arguments for controlling LLM text generation (sampling).

    Attributes:
        temperature (float): Controls randomness. 0.0 = deterministic, >0.0 = random. Defaults to `0.2`.
        top_p (float): Nucleus sampling. Considers tokens with cumulative probability >= top_p. Defaults to `0.95`.
        top_k (int): Top-k sampling. Considers the top 'k' most probable tokens. Defaults to `40`.
        response_format (LLMResponseFormat): Provider-neutral structured output configuration.
    """

    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    response_format: LLMResponseFormat = Field(default_factory=LLMResponseFormat)
