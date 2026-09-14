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

The application also needs Node 22:

```bash
cd app && npm install
```

## Running the application

```bash
make dev     # both halves: API on :8000, interface on :5173
make test    # the Python suite and the frontend suite
make lint    # ruff and tsc
```

The interface proxies `/api` to the backend, so both halves are same-origin in the
browser. Nothing needs CORS, and no base URL is configured per environment — one fewer
thing to differ between development and deployment.

`make api` and `make web` run either half alone.

## Deployment

`Dockerfile` builds one image: the frontend (`npm run build`) baked in as a static
bundle, served by the same FastAPI process as the API (`api.py`'s `FRONTEND_DIST`
mount) — one service, one origin, the same "nothing needs CORS" guarantee above, now
also true in production rather than only in `vite dev`.

```bash
docker build -t ml-sandbox .
docker run -p 8000:8000 ml-sandbox
```

The packaged model (`data/model/`) is committed rather than gitignored like the rest of
`data/`, specifically so a deploy has something to load without a separate upload step —
`scripts/package_model.py` regenerates it, see [`examples/README.md`](examples/README.md)
for why every other file under `data/` stays out of git.

`render.yaml` is a [Render](https://render.com) Blueprint — connect the repo, "New >
Blueprint", and it builds this same `Dockerfile` as a single web service. Any host that
runs an arbitrary Docker image as one long-lived process works the same way; this app
specifically needs that (not a serverless/functions platform): training (`training.py`)
holds an in-memory job registry and spawns real OS subprocesses, both of which assume
one persistent process, not many stateless instances behind a load balancer.

## Reproducibility

Every run is defined by [`config/benchmark.toml`](config/benchmark.toml) plus the seed
inside it. The same config must produce the same numbers — `tests/` asserts this, and
a failure there is a real bug, not a flaky test.

Nothing in `src/` should hardcode a value that belongs in the config. Config keys are
added when a task needs them, not in advance.

## Layout

```
FINDINGS.md what the study measured — separate from DECISIONS.md, which is what
            it chose. A decision can be argued with; a finding can only be
            reproduced or refuted.
config/     study configuration — the only place knobs live
src/        library code, including the API the application calls
tests/      including the reproducibility guarantee
app/        the interface — React, MUI, TypeScript
```

The application imports `mlsandbox` rather than reimplementing any of it. That is the
whole design: the tool can only offer what the study evaluated, and the two cannot
disagree about which methods exist or when they apply.

`app/src/theme/tokens.ts` holds the design tokens, and each colour carries the
accessibility properties measured for it — not only its hex. `tokens.test.ts` recomputes
every published contrast ratio, so an accessibility claim cannot drift from the value
beside it without CI noticing.
