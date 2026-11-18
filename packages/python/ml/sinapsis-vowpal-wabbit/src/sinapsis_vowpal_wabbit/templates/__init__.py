import importlib

from sinapsis.template import Template

_root_lib_path: str = "sinapsis_vowpal_wabbit.templates"  # noqa: RUF067

_template_lookup: dict = {  # noqa: RUF067
    "CBExploreADFLearn": f"{_root_lib_path}.cb_explore_adf_learn",
    "CBExploreADFLearnEmbeddings": f"{_root_lib_path}.cb_explore_adf_learn_embeddings",
    "CBExploreADFPredict": f"{_root_lib_path}.cb_explore_adf_predict",
    "CBExploreADFPredictEmbeddings": f"{_root_lib_path}.cb_explore_adf_predict_embeddings",
}


def __getattr__(name: str) -> Template:
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"template `{name}` not found in {_root_lib_path}")


__all__ = list(_template_lookup.keys())
