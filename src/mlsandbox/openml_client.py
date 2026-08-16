"""Access to OpenML: authenticated, cached on disk, and tolerant of a flaky server.

OpenML's API has proven unreliable — repeated 504s across both v1 and v2 during
curation. Two consequences shape this module:

* Everything downloaded is cached to disk, so a re-run does not depend on the server
  being alive (D-008).
* Failures are returned as a value, not raised as a traceback. A dataset that cannot be
  fetched is a recorded exclusion with a reason, not a hole in the collection (#8).
"""

from __future__ import annotations

import logging
import time

import openml

from mlsandbox.base import StrictModel
from mlsandbox.config import Config
from mlsandbox.settings import load_settings

logger = logging.getLogger(__name__)

RETRY_DELAYS_SECONDS = (2, 8, 30)
"""Backoff between attempts. Deliberately patient: the observed failure is a gateway
timeout under load, which sometimes clears, rather than an instant hard error."""


class DatasetMetadata(StrictModel):
    dataset_id: int
    name: str
    version: int
    rows: int
    features: int
    classes: int
    missing_values: int
    categorical_features: int
    licence: str

    @property
    def is_classification(self) -> bool:
        return self.classes >= 2

    @property
    def predictors(self) -> int:
        """OpenML counts the target column in `features`; this excludes it."""
        return max(self.features - 1, 0)


class FetchFailure(StrictModel):
    dataset_id: int
    reason: str


def _quality(qualities: dict[str, float], name: str) -> int:
    """OpenML reports qualities as floats, and omits ones it could not compute."""
    return int(qualities.get(name) or 0)


def configure(config: Config) -> None:
    """Point the OpenML client at our cache directory and authenticate if a key exists.

    The key is optional: reading public datasets works without one. It is used when
    present because some endpoints rate-limit anonymous callers more aggressively.
    """
    cache_dir = config.paths.cache / "openml"
    cache_dir.mkdir(parents=True, exist_ok=True)
    openml.config.set_root_cache_directory(str(cache_dir))

    api_key = load_settings().openml_api_key
    if api_key:
        openml.config.apikey = api_key
    else:
        logger.warning("No OPENML_API_KEY set; continuing anonymously. See .env.example")


def fetch_metadata(dataset_id: int) -> DatasetMetadata | FetchFailure:
    """Fetch one dataset's metadata, retrying while the server is unwell.

    Returns a `FetchFailure` rather than raising, so a caller curating a collection can
    record why a dataset was dropped instead of losing the whole run to one bad id.
    """
    last_error = ""
    for attempt, delay in enumerate((0, *RETRY_DELAYS_SECONDS)):
        if delay:
            logger.info("Retrying dataset %s in %ss", dataset_id, delay)
            time.sleep(delay)
        try:
            dataset = openml.datasets.get_dataset(
                dataset_id,
                download_data=False,
                download_qualities=True,
                download_features_meta_data=False,
            )
        except Exception as error:  # noqa: BLE001 — any failure is a recorded exclusion
            last_error = f"{type(error).__name__}: {str(error).splitlines()[0][:120]}"
            logger.warning(
                "Attempt %s for dataset %s failed: %s", attempt + 1, dataset_id, last_error
            )
            continue

        qualities = dataset.qualities or {}
        return DatasetMetadata(
            dataset_id=dataset_id,
            name=dataset.name,
            version=dataset.version,
            rows=_quality(qualities, "NumberOfInstances"),
            features=_quality(qualities, "NumberOfFeatures"),
            classes=_quality(qualities, "NumberOfClasses"),
            missing_values=_quality(qualities, "NumberOfMissingValues"),
            categorical_features=_quality(qualities, "NumberOfSymbolicFeatures"),
            licence=dataset.licence or "unknown",
        )

    return FetchFailure(dataset_id=dataset_id, reason=last_error or "unknown failure")
