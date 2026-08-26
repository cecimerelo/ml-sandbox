"""Fold assignments.

Every score in the study is computed on these. A partition that quietly loses rows, or
that differs between two methods on the same dataset, produces numbers that look fine and
compare nothing.
"""

import numpy as np
import pytest

from mlsandbox.folds import FoldSet, from_openml, generate


@pytest.fixture
def binary_target() -> np.ndarray:
    return np.array([0] * 80 + [1] * 20)


def test_every_row_is_tested_exactly_once(binary_target):
    folds = generate("d", target=binary_target, n_folds=5, seed=1, stratified=True)
    assert folds.covers(len(binary_target))


def test_train_and_test_never_overlap(binary_target):
    folds = generate("d", target=binary_target, n_folds=5, seed=1, stratified=True)
    for train, test in folds.folds:
        assert not set(train) & set(test)


def test_stratified_folds_keep_a_rare_class_present(binary_target):
    # Without stratification a rare class can be missing from a training fold entirely,
    # and the method is then blamed for a split it never had a chance at.
    folds = generate("d", target=binary_target, n_folds=5, seed=1, stratified=True)
    for train, _test in folds.folds:
        assert set(binary_target[train]) == {0, 1}


def test_the_same_seed_produces_the_same_folds(binary_target):
    first = generate("d", target=binary_target, n_folds=5, seed=7, stratified=True)
    second = generate("d", target=binary_target, n_folds=5, seed=7, stratified=True)
    assert first.folds == second.folds


def test_different_seeds_produce_different_folds(binary_target):
    first = generate("d", target=binary_target, n_folds=5, seed=1, stratified=True)
    second = generate("d", target=binary_target, n_folds=5, seed=2, stratified=True)
    assert first.folds != second.folds


def test_regression_folds_are_not_stratified():
    continuous = np.linspace(0, 1, 100)
    folds = generate("d", target=continuous, n_folds=5, seed=1, stratified=False)
    assert folds.covers(100)


def test_the_origin_of_the_folds_is_recorded(binary_target):
    # The collection mixes sources: OpenML datasets use published splits, PMLB ones use
    # generated. A reader comparing two datasets deserves to know which is which.
    assert generate("d", target=binary_target, n_folds=5, seed=1, stratified=True).origin == (
        "generated"
    )
    assert from_openml("d", [([0, 1], [2])]).origin == "openml"


def test_coverage_catches_a_partition_that_loses_rows():
    # The failure this guards against: folds that look plausible but evaluate on less data
    # than the dataset contains.
    incomplete = FoldSet(dataset="d", origin="openml", folds=[([0, 1], [2]), ([2], [0])])
    assert not incomplete.covers(3)
