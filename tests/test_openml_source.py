"""The OpenML source.

Parsing and normalisation only — no network. The point of D-008 is that the study stops
depending on OpenML once the data is on disk, and a test suite that phones home would
contradict that.
"""

from mlsandbox.openml_source import SUITES, Unavailable


def test_ctr23_is_addressed_by_id_not_alias():
    # The OpenML-CTR23 alias returns a server error; the numeric study id works. Recorded
    # here because it looks like a typo and would be "tidied" away otherwise.
    assert SUITES["openml-ctr23"] == 353
    assert SUITES["openml-cc18"] == "OpenML-CC18"


def test_an_unavailable_dataset_is_a_value_not_an_exception():
    # One unreachable id must not cost the other hundred-odd downloads, and a gap with a
    # reason beside it is worth more than a gap.
    failure = Unavailable(dataset_id=31, reason="unreachable after retries")
    assert failure.dataset_id == 31
    assert "retries" in failure.reason


def test_the_fold_count_is_openmls_not_the_config_file():
    # OpenML's tasks define 10 folds; benchmark.toml says 5. Using OpenML's splits is what
    # makes results comparable with published work on these suites (D-003), so the config
    # governs only the datasets whose folds the study generates itself.
    from mlsandbox.openml_source import N_FOLDS

    assert N_FOLDS == 10
