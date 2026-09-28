# Training pipeline

Where models are trained in this repository. There are three places, and all of them build
the model with the same function, so the study and the application train exactly the same
methods.

## The shared piece: `methods.build()`

[`methods.py`](../src/mlsandbox/methods.py) → `build(name, task, seed)` assembles the
scikit-learn pipeline for a method: data preparation (imputation and scaling) followed by
the estimator. Preparation sits inside the pipeline so it is fitted on each fold's training
part only. Fitting it outside would leak test-fold information into training, which raises
nothing and simply inflates the score. Every `random_state` is fixed to `seed`.

## 1. The benchmark study

The 38,820 evaluations behind the thesis.

1. [`scripts/run_benchmark.py`](../scripts/run_benchmark.py) loops over the datasets and
   calls `run_dataset`.
2. [`benchmark.py`](../src/mlsandbox/benchmark.py) → `run_dataset` loops over methods,
   folds and missing-value rates.
3. [`benchmark.py`](../src/mlsandbox/benchmark.py) → `evaluate_fold` is where the fit
   happens:

   ```python
   pipeline = build(method, task, seed=seed)
   fitted = clone(pipeline).fit(features.iloc[train], target[train])
   predicted = fitted.predict(features.iloc[test])
   score = score_of(task, target[test], predicted)
   ```

Each fit runs under a time budget (`timeout_for`, tiered by row count). A method that runs
over or fails is still recorded, with status `timeout` or `error`, so nothing disappears
silently.

## 2. The application: training on the user's data

[`training.py`](../src/mlsandbox/training.py) → `_fit_worker` scores the method by
cross-validation on the uploaded data, then fits it once more on every row. That final
model is the one the interface shows, not any single fold's model.

Each method runs in its own subprocess (`multiprocessing.Process`, started from
`_run_one_method`). A subprocess can be killed outright, so the per-method timeout and the
**Stop training** button use the same mechanism (D-053).

## 3. The recommender (Layer 2)

Layer 2 does not train the twenty methods. It is a random forest that learns, from the
benchmark results, which method performs best given the dataset's characteristics.

- [`layer2.py`](../src/mlsandbox/layer2.py) → `build_model` defines the forest.
- [`strategies.py`](../src/mlsandbox/strategies.py) → `learned` trains it during the
  study's evaluation, leaving one dataset out each time.
- [`artifact.py`](../src/mlsandbox/artifact.py) trains it on all the data and saves it for
  the application under `data/model/`, via
  [`scripts/package_model.py`](../scripts/package_model.py).

## Summary

| What is trained | Where | Driven by |
|---|---|---|
| The 20 methods, per dataset and fold | `benchmark.evaluate_fold` | `scripts/run_benchmark.py` |
| The chosen methods, on the user's data | `training._fit_worker` | `POST /api/train` |
| The Layer 2 recommender, leave-one-out | `strategies.learned` | the study's evaluation |
| The Layer 2 recommender, final model | `artifact.py` | `scripts/package_model.py` |
