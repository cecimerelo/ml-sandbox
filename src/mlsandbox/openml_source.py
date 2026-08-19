"""The benchmark collection's primary source: OpenML's curated suites.

CC18 for classification, CTR23 for regression (D-025). Chosen over PMLB for citation
strength and, more concretely, for provenance: PMLB leaves most origin fields unfilled,
where OpenML records a source and a licence per dataset — which is what a thesis needs to
say where its evidence came from.

The trade is reliability. OpenML's API has gone down for days at a time, with an upstream
issue open since July, so everything here retries patiently and caches to disk. Once
fetched, the study never needs the service again (D-008).
"""

from __future__ import annotations

import json
import logging
import time

import openml

from mlsandbox.base import StrictModel
from mlsandbox.config import Config
from mlsandbox.dataset import Dataset
from mlsandbox.settings import load_settings

logger = logging.getLogger(__name__)

SUITES: dict[str, str | int] = {
    "openml-cc18": "OpenML-CC18",
    "openml-ctr23": 353,
}
"""CTR23's alias fails against the API; its numeric study id works. CC18's alias is fine."""

RETRY_DELAYS_SECONDS = (2, 8, 30)
"""Backoff between attempts. Patient on purpose: the observed failure is a gateway
timeout under load, which sometimes clears, rather than an instant hard error."""


class Unavailable(StrictModel):
    """A dataset that could not be fetched, kept as a value rather than an exception.

    One bad id must not cost the rest of the collection, and a gap nobody can explain is
    worse than a gap with a reason next to it.
    """

    dataset_id: int
    reason: str


def metadata_path(config: Config):
    """Where the fetched suite index lives.

    Belongs with the source rather than with the script that writes it: several callers
    need to know, and a path defined in a script is a path nobody else can import.
    """
    return config.paths.datasets / "openml" / "suite-metadata.json"


def load_metadata(config: Config) -> list[Dataset]:
    """Read the fetched suite index from disk.

    Raises rather than fetching: a silent download here would hide that the study is
    reaching for the network at a point where D-008 says it should not need to.
    """
    path = metadata_path(config)
    if not path.exists():
        raise FileNotFoundError(
            f"{path.name} is missing — run scripts/fetch_openml.py --metadata"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Dataset.model_validate(d) for suite in raw.values() for d in suite]


def configure(config: Config) -> None:
    """Point the client at our store and authenticate when a key is present.

    The key is optional — public datasets read fine without one — but anonymous callers
    are rate-limited harder, which matters when fetching a hundred datasets in a row.
    """
    store = config.paths.datasets / "openml"
    store.mkdir(parents=True, exist_ok=True)
    openml.config.set_root_cache_directory(str(store))

    api_key = load_settings().openml_api_key
    if api_key:
        openml.config.apikey = api_key
    else:
        logger.warning("No OPENML_API_KEY set; continuing anonymously. See .env.example")


def _with_retries(call, describe: str):
    """Run `call`, retrying while the server is unwell. Returns None once out of patience."""
    last_error = ""
    for attempt, delay in enumerate((0, *RETRY_DELAYS_SECONDS)):
        if delay:
            logger.info("Retrying %s in %ss", describe, delay)
            time.sleep(delay)
        try:
            return call()
        except Exception as error:  # noqa: BLE001 — every failure is recorded, not raised
            last_error = f"{type(error).__name__}: {str(error).splitlines()[0][:120]}"
            logger.warning("Attempt %s for %s failed: %s", attempt + 1, describe, last_error)
    logger.error("Giving up on %s: %s", describe, last_error)
    return None


def suite_dataset_ids(suite: str) -> list[int]:
    study = _with_retries(lambda: openml.study.get_suite(SUITES[suite]), f"suite {suite}")
    return sorted(study.data) if study else []


def _quality(qualities: dict[str, float], name: str) -> int:
    """OpenML reports qualities as floats and omits ones it could not compute."""
    return int(qualities.get(name) or 0)


def fetch_dataset(dataset_id: int, suite: str) -> Dataset | Unavailable:
    """Fetch one dataset's metadata, normalised into the study's vocabulary."""
    record = _with_retries(
        lambda: openml.datasets.get_dataset(
            dataset_id,
            download_data=False,
            download_qualities=True,
            download_features_meta_data=False,
        ),
        f"dataset {dataset_id}",
    )
    if record is None:
        return Unavailable(dataset_id=dataset_id, reason="unreachable after retries")

    qualities = record.qualities or {}
    classes = _quality(qualities, "NumberOfClasses")
    return Dataset(
        name=record.name,
        source=suite,
        # OpenML versions a dataset independently of its id, and the pair is what
        # identifies the exact bytes. A bare id would not be reproducible.
        revision=str(record.version),
        rows=_quality(qualities, "NumberOfInstances"),
        # OpenML counts the target among its features, unlike PMLB. Normalised here so
        # the selection rules never branch on which source a dataset came from.
        predictors=max(_quality(qualities, "NumberOfFeatures") - 1, 0),
        # CC18 is classification-only and CTR23 regression-only, so the suite settles the
        # task. Safer than inferring from the class count, which is how the PMLB import
        # silently filed every regression dataset as classification.
        task="classification" if suite == "openml-cc18" else "regression",
        classes=classes,
        categorical_predictors=_quality(qualities, "NumberOfSymbolicFeatures"),
        # Genuinely reported here, unlike PMLB where it is absent. Nine CC18 datasets
        # carry real gaps, which complements D-015's injected MCAR missingness.
        missing_values=_quality(qualities, "NumberOfMissingValues"),
        imbalance=None,
        licence=record.licence or "unknown",
        origin=f"https://www.openml.org/d/{dataset_id}",
    )


def fetch_suite(suite: str, config: Config) -> tuple[list[Dataset], list[Unavailable]]:
    """Fetch every dataset in a suite, recording the ones that fail."""
    configure(config)
    found: list[Dataset] = []
    missing: list[Unavailable] = []
    for dataset_id in suite_dataset_ids(suite):
        result = fetch_dataset(dataset_id, suite)
        (missing if isinstance(result, Unavailable) else found).append(result)  # type: ignore[arg-type]
    logger.info("%s: %s fetched, %s unavailable", suite, len(found), len(missing))
    return found, missing


N_FOLDS = 10
"""The fold count OpenML's tasks define — verified as (1 repeat, 10 folds) across all 40
tasks in the collection.

Not the 5 in `benchmark.toml`, which governs only the datasets whose folds we generate.
Using OpenML's splits is what makes results comparable with published work on these suites
(D-003), and the price is that the classification half costs twice what a 5-fold run would.
"""


def task_id_for(dataset_name: str, suite: str) -> int | None:
    """Find the task whose dataset has this name.

    Splits live on the *task*, not the dataset — a distinction easy to miss, since the two
    are fetched through different endpoints and only the dataset carries the name.
    """
    study = _with_retries(lambda: openml.study.get_suite(SUITES[suite]), f"suite {suite}")
    if study is None:
        return None
    for task_id in study.tasks:
        task = _with_retries(
            lambda tid=task_id: openml.tasks.get_task(tid, download_data=False),
            f"task {task_id}",
        )
        if task is not None and task.get_dataset().name == dataset_name:
            return task_id
    return None


def load_splits(task_id: int) -> list[tuple[list[int], list[int]]] | None:
    """Read a task's predefined folds as (train, test) index pairs.

    Returns None when unavailable rather than raising: a dataset whose splits cannot be
    read is one the harness generates folds for instead, which is a recorded fallback and
    not a reason to lose the run.
    """
    task = _with_retries(
        lambda: openml.tasks.get_task(task_id, download_splits=True, download_data=False),
        f"splits for task {task_id}",
    )
    if task is None:
        return None
    split = task.download_split()
    # OpenML nests as repeat -> fold -> sample. Every task in this collection is a single
    # repeat, so the outer level is flattened away rather than carried around unused.
    repeat = split.split[0]
    return [
        (list(repeat[fold][0].train), list(repeat[fold][0].test)) for fold in sorted(repeat)
    ]
