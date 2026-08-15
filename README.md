# ml-sandbox

An explainable recommender for supervised learning methods, and the benchmark study
behind it. Master's thesis (TFM).

Given a description of your problem — and optionally your own dataset — it suggests a
method and explains *why* in terms of the tradeoffs that actually drive the choice,
rather than returning a black-box answer. You can then train alternatives on your own
data and see whether the recommendation held up.

## Status

Planning complete; implementation starting with the benchmark study.

| Artefact | Where |
|---|---|
| Thesis proposal | [`propuesta-tfm.md`](propuesta-tfm.md) |
| Requirements | [`_bmad-output/planning-artifacts/prds/`](_bmad-output/planning-artifacts/prds/) |
| UX design contract | [`_bmad-output/planning-artifacts/ux-designs/`](_bmad-output/planning-artifacts/ux-designs/) |
| Epic breakdown | [`_bmad-output/planning-artifacts/epics.md`](_bmad-output/planning-artifacts/epics.md) |
| Work tracking | GitHub issues |

## Setup

Requires [uv](https://docs.astral.sh/uv/). Python 3.12 is pinned in `.python-version`
and installed automatically.

```bash
uv sync --extra dev
uv run pytest
```

## Reproducibility

Every run is defined by [`config/benchmark.toml`](config/benchmark.toml) plus the seed
inside it. The same config must produce the same numbers — `tests/` asserts this, and
a failure there is a real bug, not a flaky test.

Nothing in `src/` should hardcode a value that belongs in the config. Config keys are
added when a task needs them, not in advance.

## Layout

```
config/     study configuration — the only place knobs live
src/        library code
tests/      including the reproducibility guarantee
```
