from polyfuzz import models
from sinapsis.template import BaseDynamicWrapperTemplate, WrapperEntryConfig
from sinapsis.template import make_dynamic_template
from sinapsis.template import Template
from sinapsis.env_vars import SINAPSIS_BUILD_DOCS

from sinapsis_polyfuzz.templates.polyfuzz_pair_base import PolyfuzzPairAttributes, PolyfuzzPairBase

EXCLUDED_ATTS: list[str] = ["BaseMatcher", "USEEmbeddings", "cosine_similarity"]


class PolyfuzzPairDynamic(PolyfuzzPairBase, BaseDynamicWrapperTemplate):
    """A dynamic wrapper for Polyfuzz models that match two DataFramePacket columns."""

    WrapperEntry = WrapperEntryConfig(
        wrapped_object=models,
        template_name_suffix="PairWrapper",
        exclude_module_atts=EXCLUDED_ATTS,
        exclude_method_attributes=["scorer"],
    )
    AttributesBaseModel = PolyfuzzPairAttributes


def __getattr__(name: str) -> Template:
    """Dynamically retrieves a paired-matching template attribute from the module.

    Args:
        name (str): The name of the attribute to retrieve.

    Returns:
        Template: A dynamically generated template object corresponding to the name.

    Raises:
        AttributeError: If the requested name is not found in the module's
            allowed attribute names.
    """
    if name in PolyfuzzPairDynamic.WrapperEntry.module_att_names:
        return make_dynamic_template(name, PolyfuzzPairDynamic)
    raise AttributeError(f"template `{name}` not found in {__name__}")


__all__ = PolyfuzzPairDynamic.WrapperEntry.module_att_names

if SINAPSIS_BUILD_DOCS:
    dynamic_templates = [__getattr__(template_name) for template_name in __all__]
    for template in dynamic_templates:
        globals()[template.__name__] = template
        del template
