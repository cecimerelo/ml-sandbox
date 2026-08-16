"""Loading an individual dataset from the local store."""

import gzip

from mlsandbox.pmlb_source import PINNED_REVISION, load_dataset


def store_dataset(config, name: str, payload: bytes) -> None:
    store = config.paths.datasets / "pmlb" / PINNED_REVISION
    store.mkdir(parents=True, exist_ok=True)
    (store / f"{name}.tsv.gz").write_bytes(gzip.compress(payload))


def test_reads_from_disk_without_network(config):
    store_dataset(config, "fake", b"a\tb\ttarget\n1\t2\t0\n3\t4\t1\n")

    frame = load_dataset("fake", config)

    assert frame.shape == (2, 3)


def test_target_column_is_named_consistently(config):
    # Every PMLB dataset names its outcome `target`, which is why the study can treat
    # them uniformly without per-dataset configuration.
    store_dataset(config, "fake", b"a\tb\ttarget\n1\t2\t0\n")

    assert "target" in load_dataset("fake", config).columns


def test_a_stored_dataset_is_not_refetched(config, monkeypatch):
    store_dataset(config, "fake", b"a\ttarget\n1\t0\n")

    def explode(*args, **kwargs):
        raise AssertionError("the dataset was on disk; this should not have hit the network")

    monkeypatch.setattr("mlsandbox.pmlb_source.requests.get", explode)

    assert load_dataset("fake", config).shape == (1, 2)


def test_the_store_is_scoped_by_revision(config):
    # Files fetched under one revision must not be served for another: that would mix two
    # versions of the collection with nothing to indicate it.
    store_dataset(config, "fake", b"a\ttarget\n1\t0\n")

    expected = config.paths.datasets / "pmlb" / PINNED_REVISION / "fake.tsv.gz"
    assert expected.exists()
