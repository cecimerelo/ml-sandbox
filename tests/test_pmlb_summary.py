"""Parsing PMLB's summary table — the index the whole collection is selected from.

Pure parsing: no disk, no network. Caching is a separate concern and is tested where it
lives.
"""

from mlsandbox.pmlb_source import parse_summary

HEADER = "dataset\tn_instances\tn_features\tn_classes\ttask\tn_categorical_features\timbalance"


def parse(*rows: str):
    return parse_summary("\n".join([HEADER, *rows]))


def test_reads_every_row():
    datasets = parse(
        "tiny_clf\t120\t4\t2\tclassification\t1\t0.05",
        "big_reg\t50000\t12\t0\tregression\t0\t0.0",
    )
    assert [d.name for d in datasets] == ["tiny_clf", "big_reg"]


def test_distinguishes_task_types():
    clf, reg = parse(
        "tiny_clf\t120\t4\t2\tclassification\t1\t0.05",
        "big_reg\t50000\t12\t0\tregression\t0\t0.0",
    )
    assert clf.is_classification
    assert not reg.is_classification


def test_reads_the_fields_the_selection_rules_depend_on():
    (dataset,) = parse("tiny_clf\t120\t4\t2\tclassification\t1\t0.05")
    assert dataset.rows == 120
    assert dataset.predictors == 4
    assert dataset.classes == 2
    assert dataset.categorical_predictors == 1


def test_blank_numbers_do_not_take_down_the_index():
    # PMLB leaves some fields empty rather than zero. One blank must not cost the whole
    # collection.
    (dataset,) = parse("odd\t100\t\t2\tclassification\t\t")
    assert dataset.predictors == 0


def test_non_numeric_values_are_treated_as_missing():
    (dataset,) = parse("odd\t100\tNA\t2\tclassification\t0\t0.0")
    assert dataset.predictors == 0
