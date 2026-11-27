from polyfuzz import models
from sinapsis.template import BaseDynamicWrapperTemplate, WrapperEntryConfig
from sinapsis.template import make_dynamic_template
from sinapsis.template import Template
from sinapsis.env_vars import SINAPSIS_BUILD_DOCS

from sinapsis_polyfuzz.templates.polyfuzz_base import PolyfuzzBase, PolyfuzzBaseAttributes

EXCLUDED_ATTS: list[str] = ["BaseMatcher", "USEEmbeddings", "cosine_similarity"]


class PolyfuzzDynamic(PolyfuzzBase, BaseDynamicWrapperTemplate):
    """A dynamic wrapper class for Polyfuzz model implementations."""

    WrapperEntry = WrapperEntryConfig(
        wrapped_object=models,
        exclude_module_atts=EXCLUDED_ATTS,
        exclude_method_attributes=["scorer"],
    )
    AttributesBaseModel = PolyfuzzBaseAttributes


def __getattr__(name: str) -> Template:
    """Dynamically retrieves a template attribute from the module.

    This method checks if the requested attribute name exists within the
    predefined wrapper entry names and returns a dynamically created template
    if found.

    Args:
        name (str): The name of the attribute to retrieve.

    Returns:
        Template: A dynamically generated template object corresponding to the name.

    Raises:
        AttributeError: If the requested name is not found in the module's
            allowed attribute names.
    """
    if name in PolyfuzzDynamic.WrapperEntry.module_att_names:
        return make_dynamic_template(name, PolyfuzzDynamic)
    raise AttributeError(f"template `{name}` not found in {__name__}")


__all__ = PolyfuzzDynamic.WrapperEntry.module_att_names

if SINAPSIS_BUILD_DOCS:
    dynamic_templates = [__getattr__(template_name) for template_name in __all__]
    for template in dynamic_templates:
        globals()[template.__name__] = template
        del template
