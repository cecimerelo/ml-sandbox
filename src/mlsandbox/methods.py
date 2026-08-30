"""The method registry: what the study evaluates and what the application may offer.

One table, two consumers. The study builds pipelines from it; the application exports it
to JSON so it can explain why a method does not apply to a user's problem (FR-8.3). If a
method is not here, neither offers it — the tool must not recommend something the study
never evaluated.

Metadata is declarative and the pipeline is derived from it (D-024). Nothing assembles a
pipeline by hand, which is what makes a whole class of silent error impossible: a scaler
fitted outside the training fold does not raise, it just inflates the score. Measured on
`adult`, KNN scores 0.63 unscaled against 0.75 scaled, while a decision tree does not
move — get this wrong and the benchmark concludes trees beat everything, when what was
compared was well-configured methods against badly-configured ones.
"""

from __future__ import annotations

from collections.abc import Callable
from math import comb
from typing import Literal

import numpy as np
from sklearn.base import BaseEstimator, clone
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import (
    LinearDiscriminantAnalysis,
    QuadraticDiscriminantAnalysis,
)
from sklearn.ensemble import (
    BaggingClassifier,
    BaggingRegressor,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import (
    LassoCV,
    LinearRegression,
    LogisticRegression,
    LogisticRegressionCV,
    RidgeCV,
)
from sklearn.model_selection import GridSearchCV
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    PolynomialFeatures,
    SplineTransformer,
    StandardScaler,
)
from sklearn.svm import SVC, SVR, LinearSVC, LinearSVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from mlsandbox.base import StrictModel

Task = Literal["classification", "regression"]
Tuning = Literal["none", "internal-cv"]
Implementation = Literal["sklearn", "r"]

SCORING: dict[str, str] = {
    "classification": "balanced_accuracy",
    "regression": "r2",
}
"""The metric internal tuning optimises, deliberately identical to the one the study
scores with (D-021).

They have to match. Left at scikit-learn's default, internal cross-validation would pick
the hyperparameter that maximises plain accuracy while the study reports balanced
accuracy — so on the imbalanced datasets, exactly where the distinction was adopted for,
the tuned methods would arrive optimised for the wrong objective. And since only three
methods are tuned (D-019), the bias would fall on them alone.
"""

IMPUTATION_STRATEGY = "median"
"""Median rather than mean for numeric columns: it survives the skewed features common in
this collection, where a single extreme value drags the mean somewhere no observation
sits. Categorical columns use the most frequent value, since a median of categories is
meaningless."""

MAX_EXPANDED_FEATURES = 2_000
"""Ceiling on the columns a basis expansion may produce.

Degree 3 over 34 encoded features gives 7,770 columns — a 0.7GB matrix rebuilt on every
inner fold, and more columns than the data has information to support. Worse, that fit is a
single long numpy call, and a signal-based timeout cannot interrupt one: signals are
delivered between Python instructions, so the budget never fires and the run simply stops.

The degree is therefore chosen from the input width rather than left to a fixed grid.
Prevention, because the timeout cannot be relied on to catch it.

**Necessary and not sufficient**, which took a stalled run to notice — see
`MAX_FIT_OPERATIONS`."""

MAX_FIT_OPERATIONS = 100_000_000_000
"""Ceiling on the arithmetic one basis-expanded fit may cost — `n · p²`, since least
squares over `p` columns is quadratic in the width and linear in the rows.

**A backstop, not the main guard.** The run that stalled for sixty-nine minutes was not
let through by the width ceiling: at 115 encoded columns, degree 2 wants 6,786 columns and
the ceiling refused it correctly. What let it through was the fallback that returned the
smallest degree anyway when nothing fit. The ceiling was right; the escape hatch under it
was not.

This exists because the width ceiling is silent about rows. Two thousand columns is
affordable on eight thousand rows and much less so on a hundred thousand, and nothing else
in the pipeline notices the difference.

Calibrated against two fits that were actually measured — 2.6 billion operations in 0.8
seconds, 921 billion in 501 — which agree on roughly 4×10⁻¹⁰ seconds per operation. A
hundred billion is about forty seconds of work, comfortably inside the tightest timeout
while leaving every fit that used to complete quickly still completing.

**It does not bind in this study, and saying so is the point.** The row cap is 20,000
(D-030) and the width ceiling 2,000, so the most any fit here can cost is 8×10¹⁰ — under
this budget. It fires only if one of those two moves, which is exactly when a guard is
needed and least likely to be thought about. A backstop that currently catches nothing is
worth keeping and not worth pretending about.

A budget, not a property of the problem. A faster solver justifies a different number, and
it is named here so that is one line."""

MAX_CATEGORIES = 20
"""One-hot ceiling per categorical column. Beyond this the encoding adds more columns than
the dataset has information to support, and a high-cardinality identifier would quietly
turn a small dataset into a wide one. Rarer levels collapse into a single `infrequent`
column rather than being dropped."""


Explainability = Literal["readable", "with effort", "opaque"]
"""How a method's answers can be justified to the person they affect.

`readable` — the model *is* the explanation. A decision tree's prediction is a path of
yes/no questions; a linear model's is a weighted sum you can read off.

`with effort` — the reason is recoverable but needs work or a translation. A KNN
prediction is justified by exhibiting its neighbours, a GAM by one curve per variable,
PCR by unwinding components back into original features.

`opaque` — there is no single reason to give. A forest of three hundred trees predicts by
vote: each tree arrived down a different path, and showing all of them is not an
explanation, it is the model again. Feature importances do not close this gap — they say
which variables mattered across the data, not why *this* case came out this way.

This describes the *model*, not the recommendation. The tool explains why it suggested a
method — from theory, for every method, `opaque` ones included — and that never stops
working. What this field records is whether the user, having deployed the thing, can
justify an individual prediction to the person it affects. "An explainable recommender"
and "a recommender of explainable models" are separate properties, and only the second is
in question here.

Post-hoc attribution (SHAP, LIME) is deliberately not counted as making a method
explainable. It fits a simple surrogate near one point and explains the surrogate; where
the surrogate fits badly the explanation is plausible and wrong, with nothing to signal
which happened. For a tool whose purpose is justified recommendations, that is the wrong
side of the line to sit on (D-035).
"""


class Method(StrictModel):
    """What a method is, declared rather than implied.

    Everything here is JSON-serialisable on purpose — the application reads this same
    table, so the study and the tool cannot drift apart about which methods exist or when
    they apply.
    """

    name: str
    label: str
    family: str
    """The ISLR family. The recommender reasons in families, so the collection has to
    cover them rather than merely contain many methods."""

    tasks: list[Task]
    needs_scaling: bool
    """Whether the method's result depends on feature units. Distance-based, regularised
    and gradient-based methods do; trees do not, because a threshold split on one feature
    is unaffected by another feature's range."""

    handles_nan: bool
    """Whether the estimator accepts missing values without imputation. Verified against
    the installed scikit-learn by the test suite rather than trusted (D-022)."""

    explainability: Explainability
    """Declared per method rather than derived from `family`, because families straddle the
    line: `trees` holds both the decision tree and the random forest, `svm` both the linear
    and the RBF kernel. Stated here rather than in the recommender so there is one place to
    change it, and no way for the ranking and the filtering to disagree."""

    tuning: Tuning
    """`internal-cv` where the method has no meaningful default — Ridge and Lasso have no
    sensible λ, KNN no sensible k, and PCR, PLS, polynomial and spline bases no sensible
    complexity (D-019)."""

    implementation: Implementation
    rationale: str
    """What this method represents on the bias-variance and interpretability axes. Written
    down because the recommender's explanations are built from exactly this."""

    def supports(self, task: Task) -> bool:
        return task in self.tasks

    def incompatibility_reason(self, task: Task) -> str | None:
        """Why this method does not apply, in words a user can read (FR-8.3).

        Incompatible methods are shown disabled with this reason rather than hidden, so
        the user learns why the method does not fit instead of silently not seeing it.
        """
        if self.supports(task):
            return None
        # Leads with the consequence, then the reason. Stating only the fact leaves the
        # user to work out that it means they cannot pick this — which is the one thing
        # they need from the sentence.
        if task == "classification":
            return (
                f"{self.label} can't be used here — you're sorting things into categories, "
                "and this method only predicts numbers."
            )
        return (
            f"{self.label} can't be used here — you're predicting a number, and this "
            "method only sorts things into categories."
        )


def _basis_grid(estimator: BaseEstimator, parameter: str, degrees: list[int]) -> BaseEstimator:
    """A polynomial or spline search whose degree is bounded by the data's width.

    The grid cannot be fixed in advance: the same degree that is reasonable on eight
    features is ruinous on forty. `WidthAwareGrid` reads the width at fit time, which is
    the only point where it is known — the pipeline is built before any data is seen.
    """
    return WidthAwareGrid(estimator, parameter, degrees, scoring=SCORING["regression"])


def _grid(estimator: BaseEstimator, params: dict, task: Task) -> GridSearchCV:
    """Wrap an estimator in an internal search over `params`.

    Nested inside the outer cross-validation, so the reported score never reflects a
    hyperparameter chosen with knowledge of the test fold. Scored with the study's own
    metric, so tuning optimises what the study measures.
    """
    return GridSearchCV(estimator, params, cv=5, n_jobs=1, scoring=SCORING[task])


# Estimator factories, keyed by method name and task. Kept apart from the metadata so the
# metadata stays serialisable — the application reads it, and a Python object would not
# survive the trip.
ESTIMATORS: dict[str, dict[Task, Callable[[], BaseEstimator]]] = {
    "linear_regression": {"regression": LinearRegression},
    "logistic_regression": {
        "classification": lambda: LogisticRegression(max_iter=2000),
    },
    "ridge": {
        "regression": lambda: RidgeCV(scoring=SCORING["regression"]),
        # l1_ratios=(0,) is pure L2. `penalty` was deprecated in scikit-learn 1.8 and is
        # removed in 1.10 — using it would break the study on the next release, which a
        # thesis claiming reproducibility cannot afford.
        "classification": lambda: LogisticRegressionCV(
            l1_ratios=(0.0,),
            solver="saga",
            max_iter=2000,
            cv=5,
            scoring=SCORING["classification"],
            use_legacy_attributes=False,
        ),
    },
    "lasso": {
        "regression": LassoCV,
        # l1_ratios=(1,) is pure L1, which is what makes this Lasso rather than Ridge.
        "classification": lambda: LogisticRegressionCV(
            l1_ratios=(1.0,),
            solver="saga",
            max_iter=2000,
            cv=5,
            scoring=SCORING["classification"],
            use_legacy_attributes=False,
        ),
    },
    "knn": {
        "classification": lambda: _grid(
            KNeighborsClassifier(), {"n_neighbors": [1, 3, 5, 11, 21]}, "classification"
        ),
        "regression": lambda: _grid(
            KNeighborsRegressor(), {"n_neighbors": [1, 3, 5, 11, 21]}, "regression"
        ),
    },
    "lda": {"classification": LinearDiscriminantAnalysis},
    "qda": {"classification": QuadraticDiscriminantAnalysis},
    "naive_bayes": {"classification": GaussianNB},
    "pcr": {
        "regression": lambda: _grid(
            Pipeline([("pca", PCA()), ("model", LinearRegression())]),
            {"pca__n_components": [0.7, 0.9, 0.95]},
            "regression",
        ),
    },
    "pls": {
        "regression": lambda: _grid(
            PLSRegression(), {"n_components": [1, 2, 3, 5]}, "regression"
        ),
    },
    "polynomial": {
        "regression": lambda: _basis_grid(
            Pipeline([("poly", PolynomialFeatures()), ("model", LinearRegression())]),
            "poly__degree",
            [2, 3],
        ),
    },
    "splines": {
        "regression": lambda: _grid(
            Pipeline([("spline", SplineTransformer()), ("model", LinearRegression())]),
            {"spline__n_knots": [3, 5, 8]},
            "regression",
        ),
    },
    "decision_tree": {
        "classification": DecisionTreeClassifier,
        "regression": DecisionTreeRegressor,
    },
    "bagging": {"classification": BaggingClassifier, "regression": BaggingRegressor},
    "random_forest": {
        "classification": RandomForestClassifier,
        "regression": RandomForestRegressor,
    },
    "boosting": {
        "classification": HistGradientBoostingClassifier,
        "regression": HistGradientBoostingRegressor,
    },
    "svm_linear": {
        "classification": lambda: LinearSVC(max_iter=5000),
        "regression": lambda: LinearSVR(max_iter=5000),
    },
    "svm_rbf": {"classification": SVC, "regression": SVR},
    "mlp": {
        "classification": lambda: MLPClassifier(max_iter=1000),
        "regression": lambda: MLPRegressor(max_iter=1000),
    },
}


BOTH: list[Task] = ["classification", "regression"]

METHODS: dict[str, Method] = {
    method.name: method
    for method in [
        Method(
            name="linear_regression",
            label="Linear Regression",
            family="linear",
            tasks=["regression"],
            needs_scaling=False,
            handles_nan=False,
            explainability="readable",
            tuning="none",
            implementation="sklearn",
            rationale="The high-bias, fully interpretable baseline every other method is "
            "judged against.",
        ),
        Method(
            name="logistic_regression",
            label="Logistic Regression",
            family="linear",
            tasks=["classification"],
            needs_scaling=True,
            handles_nan=False,
            explainability="readable",
            tuning="none",
            implementation="sklearn",
            rationale="The interpretable classification baseline: coefficients read as "
            "log-odds.",
        ),
        Method(
            name="ridge",
            label="Ridge",
            family="regularisation",
            tasks=BOTH,
            needs_scaling=True,
            handles_nan=False,
            explainability="readable",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="Shrinks coefficients without eliminating them. Where correlated "
            "predictors would make plain linear regression unstable.",
        ),
        Method(
            name="lasso",
            label="Lasso",
            family="regularisation",
            tasks=BOTH,
            needs_scaling=True,
            handles_nan=False,
            explainability="readable",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="Drives coefficients to exactly zero, so it selects features as "
            "well as fits. Its appeal is interpretability under high dimensionality.",
        ),
        Method(
            name="knn",
            label="K-Nearest Neighbours",
            family="neighbours",
            tasks=BOTH,
            needs_scaling=True,
            handles_nan=False,
            explainability="with effort",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="Assumes nothing about the shape of the relationship, and pays for "
            "it in high dimensions, where every point is far from every other.",
        ),
        Method(
            name="lda",
            label="Linear Discriminant Analysis",
            family="discriminant",
            tasks=["classification"],
            needs_scaling=False,
            handles_nan=False,
            explainability="readable",
            tuning="none",
            implementation="sklearn",
            rationale="Stable where logistic regression struggles: small samples, "
            "well-separated classes.",
        ),
        Method(
            name="qda",
            label="Quadratic Discriminant Analysis",
            family="discriminant",
            tasks=["classification"],
            needs_scaling=False,
            handles_nan=False,
            explainability="with effort",
            tuning="none",
            implementation="sklearn",
            rationale="Allows each class its own covariance, buying a curved boundary at "
            "the price of many more parameters.",
        ),
        Method(
            name="naive_bayes",
            label="Naive Bayes",
            family="discriminant",
            tasks=["classification"],
            needs_scaling=False,
            handles_nan=False,
            explainability="readable",
            tuning="none",
            implementation="sklearn",
            rationale="Assumes features are independent, which is almost never true and "
            "often works anyway. Very high bias, very cheap.",
        ),
        Method(
            name="pcr",
            label="Principal Components Regression",
            family="dimension-reduction",
            tasks=["regression"],
            needs_scaling=True,
            handles_nan=False,
            explainability="with effort",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="Compresses correlated predictors before fitting. Components are "
            "chosen without reference to the target, which is its weakness against PLS.",
        ),
        Method(
            name="pls",
            label="Partial Least Squares",
            family="dimension-reduction",
            tasks=["regression"],
            needs_scaling=True,
            handles_nan=False,
            explainability="with effort",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="Like PCR, but builds components that relate to the target.",
        ),
        Method(
            name="polynomial",
            label="Polynomial Regression",
            family="non-linear",
            tasks=["regression"],
            needs_scaling=True,
            handles_nan=False,
            explainability="with effort",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="The simplest way out of linearity, and the least controlled: high "
            "degrees oscillate wildly at the edges of the data.",
        ),
        Method(
            name="splines",
            label="Regression Splines",
            family="non-linear",
            tasks=["regression"],
            needs_scaling=True,
            handles_nan=False,
            explainability="with effort",
            tuning="internal-cv",
            implementation="sklearn",
            rationale="Local flexibility without the edge behaviour of high-degree "
            "polynomials.",
        ),
        Method(
            name="decision_tree",
            label="Decision Tree",
            family="trees",
            tasks=BOTH,
            needs_scaling=False,
            handles_nan=True,
            explainability="readable",
            tuning="none",
            implementation="sklearn",
            rationale="The most interpretable non-linear method: the model is a diagram "
            "someone can read. Unstable — small data changes redraw it.",
        ),
        Method(
            name="bagging",
            label="Bagging",
            family="trees",
            tasks=BOTH,
            needs_scaling=False,
            handles_nan=True,
            explainability="opaque",
            tuning="none",
            implementation="sklearn",
            rationale="Averages many trees to cure a single tree's instability, at the "
            "cost of the diagram.",
        ),
        Method(
            name="random_forest",
            label="Random Forest",
            family="trees",
            tasks=BOTH,
            needs_scaling=False,
            handles_nan=True,
            explainability="opaque",
            tuning="none",
            implementation="sklearn",
            rationale="Bagging plus decorrelated trees. The strong default when "
            "interpretability is not required.",
        ),
        Method(
            name="boosting",
            label="Gradient Boosting",
            family="trees",
            tasks=BOTH,
            needs_scaling=False,
            handles_nan=True,
            explainability="opaque",
            tuning="none",
            implementation="sklearn",
            rationale="Fits trees sequentially to what the previous ones got wrong. Often "
            "the accuracy ceiling on tabular data (D-023: histogram implementation).",
        ),
        Method(
            name="svm_linear",
            label="Support Vector Classifier",
            family="svm",
            tasks=BOTH,
            needs_scaling=True,
            handles_nan=False,
            explainability="readable",
            tuning="none",
            implementation="sklearn",
            rationale="A linear boundary chosen to maximise the margin. Robust in high "
            "dimensions.",
        ),
        Method(
            name="svm_rbf",
            label="Support Vector Machine (RBF)",
            family="svm",
            tasks=BOTH,
            needs_scaling=True,
            handles_nan=False,
            explainability="opaque",
            tuning="none",
            implementation="sklearn",
            rationale="A curved boundary via the kernel trick. Scales badly: cost grows "
            "roughly with the square of the sample size.",
        ),
        Method(
            name="mlp",
            label="Neural Network (MLP)",
            family="neural",
            tasks=BOTH,
            needs_scaling=True,
            handles_nan=False,
            explainability="opaque",
            tuning="none",
            implementation="sklearn",
            rationale="Maximum flexibility, minimum interpretability, and hungry for data "
            "— the far end of the spectrum the recommender reasons about.",
        ),
        Method(
            name="gam",
            label="Generalised Additive Model",
            family="non-linear",
            tasks=BOTH,
            needs_scaling=False,
            handles_nan=False,
            explainability="with effort",
            tuning="internal-cv",
            implementation="r",
            rationale="Flexible per feature while staying additive, so each variable's "
            "effect remains readable. Runs through R's mgcv, whose implementation is the "
            "reference (D-020).",
        ),
        Method(
            name="bart",
            label="BART",
            family="trees",
            tasks=BOTH,
            needs_scaling=False,
            handles_nan=False,
            explainability="opaque",
            tuning="none",
            implementation="r",
            rationale="Bayesian tree ensemble, giving uncertainty intervals rather than "
            "point predictions. Runs through R's dbarts: Python has no solid "
            "implementation (D-020).",
        ),
    ]
}


def seed_everything_in(estimator, seed: int):
    """Fix every random_state the estimator exposes, however deeply nested.

    Fifteen of the method/task pairs use stochastic estimators, and scikit-learn leaves
    `random_state` at None by default — so two runs of the benchmark would produce
    different numbers for Random Forest, boosting, the MLP and the rest. That silently
    contradicts the study's reproducibility claim.

    Done by walking the parameters rather than passing the seed at each construction site,
    because the latter has to be remembered once per method and is invisible when
    forgotten. This also reaches inside pipelines and grid searches.
    """
    seeded = {
        parameter: seed
        for parameter in estimator.get_params(deep=True)
        if parameter == "random_state" or parameter.endswith("__random_state")
    }
    if seeded:
        estimator.set_params(**seeded)
    return estimator


def build(name: str, task: Task, *, seed: int = 0) -> Pipeline:
    """Assemble the pipeline for a method, derived entirely from its metadata.

    Imputation and scaling go inside the pipeline so scikit-learn fits them per training
    fold. Fitting them outside would leak test-fold information into training — which
    raises nothing and simply inflates the score.

    Every random_state is fixed to `seed`, so the same configuration produces the same
    numbers twice.
    """
    method = METHODS[name]
    reason = method.incompatibility_reason(task)
    if reason:
        raise ValueError(reason)
    if method.implementation != "sklearn":
        raise ValueError(f"{method.label} runs through {method.implementation}, not scikit-learn")

    steps: list[tuple[str, BaseEstimator]] = [("prepare", _preparation(method))]
    steps.append(("model", ESTIMATORS[name][task]()))
    return seed_everything_in(Pipeline(steps), seed)


def _preparation(method: Method) -> ColumnTransformer:
    """Impute, encode and scale, choosing the treatment per column type.

    Categorical columns need encoding before anything else can touch them: a median has no
    meaning over categories, and no estimator here accepts a string. Seventeen of the
    sixty datasets carry categorical columns, and without this every method except the
    tree ensembles fails on all of them — which would not have looked like an error in the
    results, only like those methods being unsuited to a quarter of the collection.

    Built as a `ColumnTransformer` so the choice is made per column and still fitted per
    training fold, keeping D-024's guarantee intact.
    """
    numeric_steps: list[tuple[str, BaseEstimator]] = []
    if not method.handles_nan:
        numeric_steps.append(("impute", SimpleImputer(strategy=IMPUTATION_STRATEGY)))
    if method.needs_scaling:
        numeric_steps.append(("scale", StandardScaler()))
    numeric = Pipeline(numeric_steps) if numeric_steps else "passthrough"

    categorical = Pipeline(
        [
            # Most frequent regardless of `handles_nan`: an estimator that tolerates NaN in
            # a numeric column still cannot read a gap in a string one.
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "encode",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    max_categories=MAX_CATEGORIES,
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        [
            ("numeric", numeric, make_column_selector(dtype_include=np.number)),
            ("categorical", categorical, make_column_selector(dtype_exclude=np.number)),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def available(task: Task, *, implementation: Implementation | None = "sklearn") -> list[Method]:
    """Methods that apply to this task, optionally restricted to one implementation."""
    return [
        method
        for method in METHODS.values()
        if method.supports(task)
        and (implementation is None or method.implementation == implementation)
    ]


class WidthAwareGrid(BaseEstimator):
    """A grid search that drops basis degrees too large for the data in front of it.

    A polynomial of degree `d` over `p` features produces `C(p+d, d)` columns: fine at
    eight features, ruinous at forty. The pipeline is constructed before any data is seen,
    so the decision has to be deferred to fit time.

    Prevention rather than interruption. The oversized fit is a single long numpy call, and
    the signal-based timeout cannot interrupt one — signals arrive between Python
    instructions, so the budget never fires and the run stops rather than recording a
    timeout.
    """

    def __init__(self, estimator, parameter: str, degrees: list[int], scoring: str) -> None:
        self.estimator = estimator
        self.parameter = parameter
        self.degrees = degrees
        self.scoring = scoring

    def _affordable(self, n_features: int, n_rows: int) -> list[int]:
        """Degrees this data can carry, by width *and* by what the fit will cost.

        Width alone was not enough. A degree can sit under the column ceiling and still be
        ruinous, because solving least squares over `p` columns costs about `n · p²` — so
        doubling the width quadruples the work, and the row count multiplies all of it.

        **Empty is a real answer.** This used to fall back to the smallest degree when
        nothing fit, which read as graceful degradation and was not: for a polynomial the
        smallest degree is 2, so the fallback returned the very thing the budget had just
        refused. It bypassed the guard entirely at exactly the moment the guard mattered,
        and a run spent sixty-nine minutes inside one fit proving it.

        There is nothing to degrade *to*. A degree-1 polynomial is linear regression, which
        is already in the collection under its own name — offering it here would score one
        method twice and call the second one a curve.
        """
        from math import comb

        def affordable(degree: int) -> bool:
            columns = comb(n_features + degree, degree)
            if columns > MAX_EXPANDED_FEATURES:
                return False
            return n_rows * columns**2 <= MAX_FIT_OPERATIONS

        return [d for d in self.degrees if affordable(d)]

    def fit(self, X, y=None):
        n_features = X.shape[1]
        degrees = self._affordable(n_features, X.shape[0])
        if not degrees:
            # Refused rather than run. The study's convention is that a method which
            # cannot run is absent with a reason, never scored (D-031) — and the reason is
            # a finding: this basis is not computable on data of this shape, which is
            # itself worth reporting.
            raise ValueError(
                f"Polynomial degrees {self.degrees} are all too expensive on "
                f"{X.shape[0]:,} rows and {n_features} encoded columns. The smallest "
                "would need "
                f"{X.shape[0] * comb(n_features + min(self.degrees), min(self.degrees)) ** 2:,} "
                f"operations against a budget of {MAX_FIT_OPERATIONS:,}."
            )

        self.search_ = GridSearchCV(
            clone(self.estimator),
            {self.parameter: degrees},
            cv=5,
            n_jobs=1,
            scoring=self.scoring,
        )
        self.search_.fit(X, y)
        return self

    @property
    def chosen_degree(self) -> int:
        """The degree that was actually fitted.

        Worth reading before drawing a conclusion. Where the budget leaves only degree 1,
        `polynomial` **is** linear regression — same basis, same fit — and its score is
        evidence about a line, not about a curve. Reported rather than inferred, so the
        analysis does not read "the polynomial did no better than the linear model" off a
        row where the two were the same model.
        """
        return int(self.search_.best_params_[self.parameter])

    def predict(self, X):
        return self.search_.predict(X)
