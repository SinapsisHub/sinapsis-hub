<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Data-Analysis
<br>
</h1>

<h3 align="center">Classification, regression, clustering and feature processing with scikit-learn and XGBoost.</h3>

## Overview

**`sinapsis-data-analysis`** — Templates to work with models for classification, regression and clustering with xgboost and sklearn.

Tabular ML workflows need training and inference plus consistent preprocessing. These Templates allow analysis steps to compose with existing readers, metrics and export operations.

### Where it fits

Model selection and evaluation depend on the dataset. Choose a classification, regression or manifold/feature transform Template according to the target and validate preprocessing consistency at inference.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-data-analysis
# or
pip install sinapsis-data-analysis
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

**Sinapsis Data Analysis** provides a variety of templates for machine learning workflows:

<details>
<summary><strong><span style="font-size: 1.25em;">Scikit-Learn Models</span></strong></summary>

The following model types are supported:

- **Linear Models**: LinearRegression, Ridge, Lasso, ElasticNet, LogisticRegression, etc.
- **Neighbors Models**: KNeighborsClassifier, KNeighborsRegressor, RadiusNeighborsClassifier, etc.
- **Neural Network Models**: MLPClassifier, MLPRegressor, BernoulliRBM
- **SVM Models**: SVC, SVR, LinearSVC, LinearSVR, NuSVC, NuSVR, OneClassSVM, etc.
- **Tree Models**: DecisionTreeClassifier, DecisionTreeRegressor, ExtraTreeClassifier, etc.

Each template uses the same base attributes:
- **`generic_field_key` (str, required)**: Key of the generic field where datasets are stored
- **`model_save_path` (str, required)**: Path where the trained model will be saved
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">XGBoost Models</span></strong></summary>

XGBoost model templates include:
- XGBClassifier
- XGBRegressor
- XGBRanker
- XGBRFClassifier
- XGBRFRegressor
- Booster

Attributes are the same as those for Scikit-learn templates.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">Manifold Learning</span></strong></summary>

Templates for dimensionality reduction using scikit-learn's manifold learning techniques:

- **SKLearnManifold**: Base class for all manifold learning algorithms
  - **`generic_field_key` (str, required)**: Key of the generic field where the input data is stored

Specific algorithms include t-SNE, MDS, Isomap, LocallyLinearEmbedding, and more.
</details>

<details>
<summary><strong><span style="font-size: 1.25em;">Inference Templates</span></strong></summary>

Templates for using trained models to make predictions on new data:

- **SKLearnInference**: For inference with scikit-learn models
- **XGBoostInference**: For inference with XGBoost models

To use these templates, you should replace the **`model_path`** to point to the path of the trained model.
</details>


For example, for ***LinearRegression*** use ```sinx templates example-config LinearRegression``` to produce an example config.

## Example Agent

The following is adapted directly from the package’s shipped [`sklearn_inference.yml`](src/sinapsis_data_analysis/configs/sklearn_inference.yml) configuration. Save it as `my_data_analysis_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_data_analysis_agent

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: load_iris
  class_name: load_irisWrapper
  template_input: InputTemplate
  attributes:
    split_dataset: false
    load_iris:
      return_X_y: false
      as_frame: true
- template_name: SKLearnInference
  class_name: SKLearnInference
  template_input: load_iris
  attributes:
    model_path: 'artifacts/knn_classifier.joblib'
    generic_field_key: 'load_iris'
```

```bash
sinx jobs run my_data_analysis_agent.yaml
```

More configurations: [`australian_credit_infer.yml`](src/sinapsis_data_analysis/configs/australian_credit_infer.yml), [`credit_approval_infer.yml`](src/sinapsis_data_analysis/configs/credit_approval_infer.yml), [`sklearn_inference.yml`](src/sinapsis_data_analysis/configs/sklearn_inference.yml), [`xgb_inference.yml`](src/sinapsis_data_analysis/configs/xgb_inference.yml), [`sktime_sklearn.yml`](src/sinapsis_data_analysis/configs/sktime_sklearn.yml), [`xgboost_sklearn.yml`](src/sinapsis_data_analysis/configs/xgboost_sklearn.yml), [`sklearn_sklearn.yml`](src/sinapsis_data_analysis/configs/sklearn_sklearn.yml), [`sklearn_manifold.yml`](src/sinapsis_data_analysis/configs/sklearn_manifold.yml), [`sklearn_xgboost.yml`](src/sinapsis_data_analysis/configs/sklearn_xgboost.yml), [`decision_sklearn.yml`](src/sinapsis_data_analysis/configs/decision_sklearn.yml), [`manifold_sklearn.yml`](src/sinapsis_data_analysis/configs/manifold_sklearn.yml), [`sklearn_svm.yml`](src/sinapsis_data_analysis/configs/sklearn_svm.yml), [`australian_credit_data_visualization.yml`](src/sinapsis_data_analysis/configs/australian_credit_data_visualization.yml), [`data_visualization.yml`](src/sinapsis_data_analysis/configs/data_visualization.yml) (and 8 more).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
