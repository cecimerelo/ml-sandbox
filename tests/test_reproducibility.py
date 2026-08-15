"""The scaffold's one claim: same config and seed, same numbers.

This is deliberately a single small dataset and a single method. Its job is to prove
the seeding and config plumbing works end to end, not to benchmark anything.
"""

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

from mlsandbox.config import load_config, seed_everything


def _run_once() -> list[float]:
    config = load_config()
    seed_everything(config.run.seed)

    features, target = load_iris(return_X_y=True)
    folds = StratifiedKFold(
        n_splits=config.cv.n_folds, shuffle=True, random_state=config.run.seed
    )
    model = RandomForestClassifier(random_state=config.run.seed)
    return cross_val_score(model, features, target, cv=folds).tolist()


def test_config_loads():
    config = load_config()
    assert config.cv.n_folds >= 2


def test_same_seed_gives_identical_scores():
    assert _run_once() == _run_once()
