"""The method registry.

The tests that matter here are not "the table has 21 rows". They are the ones that check
the metadata does not lie: a method claiming to handle missing values is actually fitted
on data containing them, and a method claiming to need scaling actually gets a scaler.

Three bugs in this project so far came from a field that said one thing and meant
another. Declarations are cheap; verified declarations are not.
"""

import numpy as np
import pytest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from mlsandbox.methods import ESTIMATORS, METHODS, available, build

SKLEARN_METHODS = [m for m in METHODS.values() if m.implementation == "sklearn"]


def sample(task: str, *, with_nan: bool = False, rows: int = 120):
    rng = np.random.default_rng(0)
    features = rng.normal(size=(rows, 5))
    if with_nan:
        features[rng.random(features.shape) < 0.15] = np.nan
    target = (
        (rng.random(rows) > 0.5).astype(int)
        if task == "classification"
        else rng.normal(size=rows)
    )
    return features, target


def method_task_pairs(implementation: str = "sklearn"):
    return [
        (method.name, task)
        for method in METHODS.values()
        if method.implementation == implementation
        for task in method.tasks
    ]


@pytest.mark.parametrize(("name", "task"), method_task_pairs())
def test_every_declared_pairing_builds_and_fits(name, task):
    features, target = sample(task)
    build(name, task).fit(features, target)


@pytest.mark.parametrize(("name", "task"), method_task_pairs())
def test_the_pipeline_scales_exactly_when_the_method_says_it_needs_to(name, task):
    steps = dict(build(name, task).steps)
    assert isinstance(steps.get("scale"), StandardScaler) is METHODS[name].needs_scaling


@pytest.mark.parametrize(("name", "task"), method_task_pairs())
def test_the_pipeline_imputes_exactly_when_the_method_cannot_handle_gaps(name, task):
    steps = dict(build(name, task).steps)
    imputes = isinstance(steps.get("impute"), SimpleImputer)
    assert imputes is not METHODS[name].handles_nan


@pytest.mark.parametrize(("name", "task"), method_task_pairs())
def test_missing_values_are_survivable_either_way(name, task):
    # The claim under test in D-015 and D-022. Methods that handle gaps natively see them;
    # the rest get an imputer. Either way the pipeline must fit, or the missingness
    # experiment cannot run at all.
    features, target = sample(task, with_nan=True)
    build(name, task).fit(features, target)


@pytest.mark.parametrize("name", [m.name for m in SKLEARN_METHODS if m.handles_nan])
def test_native_nan_handling_is_real_not_asserted(name):
    # Fit the bare estimator, with no imputer in front of it. If the declaration is stale
    # — scikit-learn's support has changed across versions — this is what catches it.
    method = METHODS[name]
    for task in method.tasks:
        features, target = sample(task, with_nan=True)
        ESTIMATORS[name][task]().fit(features, target)


def test_scaling_actually_changes_a_scaled_method():
    # Guards the claim behind needs_scaling. If a method declares it needs scaling but the
    # pipeline produces identical predictions without one, the flag is decorative.
    features, target = sample("classification")
    features[:, 0] *= 10_000  # one feature on a wildly different scale

    scaled = build("knn", "classification").fit(features, target).predict(features)

    from sklearn.neighbors import KNeighborsClassifier

    unscaled = KNeighborsClassifier().fit(features, target).predict(features)
    assert not np.array_equal(scaled, unscaled)


def test_a_method_refuses_a_task_it_does_not_support():
    with pytest.raises(ValueError, match="continuous"):
        build("lda", "regression")


def test_the_refusal_reads_as_an_explanation_not_an_error_code():
    # FR-8.3: incompatible methods are shown disabled with this reason, so it has to be a
    # sentence a user without ML background can act on.
    reason = METHODS["lda"].incompatibility_reason("regression")
    assert reason is not None
    assert "Linear Discriminant Analysis" in reason
    assert reason.endswith(".")


def test_a_supported_task_has_no_incompatibility_reason():
    assert METHODS["random_forest"].incompatibility_reason("classification") is None


def test_r_backed_methods_refuse_to_build_as_sklearn_pipelines():
    # GAM and BART run through a subprocess bridge (D-020). Failing loudly here stops them
    # silently becoming a scikit-learn approximation of themselves.
    with pytest.raises(ValueError, match="not scikit-learn"):
        build("gam", "regression")


def test_every_method_has_an_estimator_for_every_task_it_claims():
    for method in SKLEARN_METHODS:
        for task in method.tasks:
            assert task in ESTIMATORS[method.name], f"{method.name} claims {task}"


def test_no_estimator_exists_for_a_task_the_method_does_not_claim():
    # The reverse gap: an estimator nobody can reach, which would mean the metadata is
    # narrower than the code and a method silently unavailable.
    for name, by_task in ESTIMATORS.items():
        assert set(by_task) <= set(METHODS[name].tasks), f"{name} has an unreachable estimator"


def test_available_excludes_r_methods_by_default():
    # The study runs sklearn methods directly; R ones arrive through the bridge, so they
    # must not appear in the default list and be silently skipped later.
    names = {m.name for m in available("regression")}
    assert "gam" not in names
    assert {m.name for m in available("regression", implementation=None)} > names


def test_every_islr_family_is_represented():
    # The recommender reasons in families, so a missing family is a band of its decision
    # space the study cannot speak to.
    families = {m.family for m in METHODS.values()}
    assert families == {
        "linear",
        "regularisation",
        "neighbours",
        "discriminant",
        "dimension-reduction",
        "non-linear",
        "trees",
        "svm",
        "neural",
    }


def test_methods_without_a_sensible_default_are_tuned():
    # D-019: these have no meaningful default value, so shipping them untuned would
    # measure an arbitrary choice rather than the method.
    for name in ("ridge", "lasso", "knn", "pcr", "pls", "polynomial", "splines"):
        assert METHODS[name].tuning == "internal-cv", name


def test_metadata_survives_a_round_trip_to_json():
    # D-024: the application reads this table. A field that cannot serialise would mean
    # maintaining a second copy, which is how study and tool drift apart.
    import json

    for method in METHODS.values():
        assert json.loads(method.model_dump_json())["name"] == method.name


def test_internal_tuning_optimises_the_metric_the_study_reports():
    # D-021 scores classification with balanced accuracy. If internal cross-validation is
    # left on scikit-learn's default it maximises plain accuracy instead, so on the
    # imbalanced datasets — the reason balanced accuracy was adopted — the three tuned
    # methods would arrive optimised for the wrong objective.
    from mlsandbox.methods import SCORING

    assert SCORING["classification"] == "balanced_accuracy"
    assert SCORING["regression"] == "r2"

    knn = ESTIMATORS["knn"]["classification"]()
    assert knn.scoring == SCORING["classification"]

    ridge = ESTIMATORS["ridge"]["classification"]()
    assert ridge.scoring == SCORING["classification"]


def test_no_tuned_method_relies_on_a_removed_sklearn_parameter():
    # `penalty` on LogisticRegressionCV was deprecated in 1.8 and is removed in 1.10.
    # Relying on it would break the study on the next release, which a thesis claiming
    # reproducibility cannot afford.
    for name in ("ridge", "lasso"):
        estimator = ESTIMATORS[name]["classification"]()
        assert estimator.l1_ratios is not None, name
