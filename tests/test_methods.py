"""The method registry.

The tests that matter here are not "the table has 21 rows". They are the ones that check
the metadata does not lie: a method claiming to handle missing values is actually fitted
on data containing them, and a method claiming to need scaling actually gets a scaler.

Three bugs in this project so far came from a field that said one thing and meant
another. Declarations are cheap; verified declarations are not.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from mlsandbox.methods import ESTIMATORS, METHODS, available, build

SKLEARN_METHODS = [m for m in METHODS.values() if m.implementation == "sklearn"]


def sample(task: str, *, with_nan: bool = False, rows: int = 120):
    """A DataFrame, not an array: the pipeline chooses its treatment per column type, so it
    needs the dtypes a bare array does not carry."""
    rng = np.random.default_rng(0)
    values = rng.normal(size=(rows, 5))
    if with_nan:
        values[rng.random(values.shape) < 0.15] = np.nan
    features = pd.DataFrame(values, columns=[f"n{i}" for i in range(5)])
    target = (
        (rng.random(rows) > 0.5).astype(int)
        if task == "classification"
        else rng.normal(size=rows)
    )
    return features, target


def numeric_steps(pipeline) -> dict:
    """The steps applied to numeric columns, now nested inside the ColumnTransformer."""
    prepare = pipeline.named_steps["prepare"]
    numeric = next(t for name, t, _ in prepare.transformers if name == "numeric")
    return dict(numeric.steps) if hasattr(numeric, "steps") else {}


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
    steps = numeric_steps(build(name, task))
    assert isinstance(steps.get("scale"), StandardScaler) is METHODS[name].needs_scaling


@pytest.mark.parametrize(("name", "task"), method_task_pairs())
def test_the_pipeline_imputes_exactly_when_the_method_cannot_handle_gaps(name, task):
    # Numeric columns only. Categorical ones are always imputed, because an estimator that
    # tolerates NaN in a number still cannot read a gap in a string.
    steps = numeric_steps(build(name, task))
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
    features["n0"] *= 10_000  # one feature on a wildly different scale

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


@pytest.mark.parametrize(("name", "task"), method_task_pairs())
def test_no_random_state_is_left_unset(name, task):
    # Fifteen method/task pairs use stochastic estimators, and scikit-learn leaves
    # random_state at None. Unfixed, two runs of the benchmark produce different numbers
    # and the study's reproducibility claim is false — quietly, since nothing errors.
    pipeline = build(name, task, seed=42)
    unset = [
        parameter
        for parameter, value in pipeline.get_params(deep=True).items()
        if parameter.endswith("random_state") and value is None
    ]
    assert not unset, f"{name}/{task} leaves {unset} unset"


def test_the_same_seed_reproduces_a_stochastic_method():
    features, target = sample("regression")
    first = build("random_forest", "regression", seed=7).fit(features, target)
    second = build("random_forest", "regression", seed=7).fit(features, target)
    assert np.array_equal(first.predict(features), second.predict(features))


def test_a_different_seed_changes_a_stochastic_method():
    # Guards against the fix being vacuous: if the seed were ignored rather than applied,
    # the previous test would still pass.
    features, target = sample("regression")
    first = build("random_forest", "regression", seed=7).fit(features, target)
    second = build("random_forest", "regression", seed=8).fit(features, target)
    assert not np.array_equal(first.predict(features), second.predict(features))


def mixed_sample(rows: int = 200, *, with_nan: bool = False):
    """A frame with both numeric and categorical columns, as 17 of the 60 datasets have."""
    rng = np.random.default_rng(0)
    frame = pd.DataFrame(
        {
            "n1": rng.normal(size=rows),
            "n2": rng.normal(size=rows),
            "c1": rng.choice(["a", "b", "c"], size=rows),
            "c2": rng.choice(["yes", "no"], size=rows),
        }
    )
    if with_nan:
        frame.loc[:20, "n1"] = np.nan
        frame.loc[:15, "c1"] = None
    return frame, (rng.random(rows) > 0.5).astype(int)


@pytest.mark.parametrize(
    ("name", "task"),
    [(n, t) for n, t in method_task_pairs() if n != "qda"],
)
def test_categorical_columns_do_not_break_any_method(name, task):
    # The bug this guards against cost a benchmark run. Without encoding, the median
    # imputer rejects strings and no estimator can read them, so every method except the
    # tree ensembles failed on 17 of the 60 datasets — and in the results that would not
    # have looked like an error, only like those methods being unsuited to a quarter of
    # the collection.
    features, target = mixed_sample()
    if task == "regression":
        target = target.astype(float)
    build(name, task, seed=1).fit(features, target)


@pytest.mark.parametrize(
    ("name", "task"),
    [(n, t) for n, t in method_task_pairs() if n != "qda"],
)
def test_categorical_and_missing_together_are_survivable(name, task):
    # Both at once, because a gap in a string column is a different problem from a gap in
    # a numeric one — and `handles_nan` only ever meant the numeric case.
    features, target = mixed_sample(with_nan=True)
    if task == "regression":
        target = target.astype(float)
    build(name, task, seed=1).fit(features, target)


def test_high_cardinality_columns_do_not_explode_the_feature_space():
    # An identifier-like column would otherwise turn a small dataset into a wide one, which
    # is a different problem than the one being studied.
    from mlsandbox.methods import MAX_CATEGORIES

    rng = np.random.default_rng(0)
    frame = pd.DataFrame({"id": [f"v{i}" for i in range(300)], "n": rng.normal(size=300)})
    target = (rng.random(300) > 0.5).astype(int)

    fitted = build("logistic_regression", "classification", seed=1).fit(frame, target)
    produced = fitted.named_steps["prepare"].transform(frame).shape[1]
    assert produced <= MAX_CATEGORIES + 2


def test_a_basis_expansion_drops_degrees_the_data_cannot_carry():
    # Degree 3 over 34 encoded features gives 7,770 columns: more than the data supports,
    # and a single long numpy call that the signal-based timeout cannot interrupt. The run
    # stops rather than recording a timeout, so this has to be prevented, not caught.
    from mlsandbox.methods import WidthAwareGrid

    grid = WidthAwareGrid(None, "poly__degree", [2, 3], scoring="r2")
    assert grid._affordable(5) == [2, 3]
    assert grid._affordable(40) == [2]


def test_the_smallest_degree_always_survives():
    # A grid with nothing in it would fail rather than degrade, and a basis expansion that
    # expands nothing is not one.
    from mlsandbox.methods import WidthAwareGrid

    grid = WidthAwareGrid(None, "poly__degree", [2, 3], scoring="r2")
    assert grid._affordable(5_000) == [2]


def test_polynomial_stays_fast_on_a_wide_dataset():
    # The regression this guards: an unbounded degree stalled a benchmark run indefinitely.
    import time

    rng = np.random.default_rng(0)
    features = pd.DataFrame(rng.normal(size=(1_000, 34)))
    target = rng.normal(size=1_000)

    started = time.perf_counter()
    build("polynomial", "regression", seed=1).fit(features, target)
    assert time.perf_counter() - started < 30
