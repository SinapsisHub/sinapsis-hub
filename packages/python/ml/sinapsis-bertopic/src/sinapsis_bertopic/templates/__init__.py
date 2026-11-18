import importlib

from sinapsis.template import Template

_root_lib_path: str = "sinapsis_bertopic.templates"  # noqa: RUF067

_template_lookup: dict = {  # noqa: RUF067
    "BERTopicFitModel": f"{_root_lib_path}.bertopic_fit_model",
    "BERTopicFitModelFromDataFrame": f"{_root_lib_path}.bertopic_fit_model_from_dataframe",
    "BERTopicPredict": f"{_root_lib_path}.bertopic_predict",
}


def __getattr__(name: str) -> Template:
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"template `{name}` not found in {_root_lib_path}")


__all__ = list(_template_lookup.keys())
