# Working conventions

Solo project, so these exist to make the history readable later — by a tutor, by a
committee, and by you in four months when you write the memoria.

## Branches

```
<type>/<issue-number>-<short-slug>
```

Examples:

```
chore/7-scaffold-research-project
research/12-run-full-benchmark
feat/23-problem-characterization-form
fix/41-fold-assignment-leak
docs/58-methodology-chapter
```

| Type | Use for |
|---|---|
| `feat` | New application capability |
| `research` | Benchmark study, analysis, experiments — work whose output is a finding |
| `fix` | Correcting broken behaviour or wrong results |
| `chore` | Tooling, scaffolding, dependencies, config |
| `docs` | Documentation and memoria material |

The issue number is mandatory. It is what links a branch back to its requirements
and its reasoning without anyone having to remember.

`research` is separate from `feat` deliberately: a research branch can legitimately
end in "this did not work," and that outcome still gets merged and written up.

Commit per unit of work rather than batching — small commits are what make a decision
traceable to its reasoning six months later. See *Commit messages* below.

## Pull requests

Even solo, open a PR. It is the natural place to record what was verified and what a
decision cost, and it survives in a form the memoria can cite. See
[`.github/pull_request_template.md`](.github/pull_request_template.md).

Link the issue with `Closes #N` so it closes on merge.

## Tests

`uv run pytest` must pass before merge.

The reproducibility test is not a formality — if the same config and seed stop
producing the same numbers, that is a real bug and the thesis's reproducibility claim
is affected.

## Commit messages

A lean template is wired up via `commit.template`, and a `prepare-commit-msg` hook
appends `Closes #N` using the issue number in the branch name — so the reference is
never typed twice.

Keep commit bodies for reasoning that is **not** already in the linked issue. The
issue holds the requirements and the acceptance criteria; the commit holds why this
particular change looks the way it does. Do not restate one in the other.

Both are enabled by repo-local config, so a fresh clone needs:

```bash
git config commit.template .gitmessage
git config core.hooksPath .githooks
```

## Decisions

Choices that shape the study or the product go in [`DECISIONS.md`](DECISIONS.md), one
entry per decision with a stable `D-NNN` id.

Record a decision there when it is one a reader could reasonably have made differently,
or when it changes something the thesis will claim. Reference the id from issues,
commits and the memoria rather than restating the reasoning.

The file is append-only. To reverse a decision, mark the old entry **superseded** and
write a new one — the history of what was considered and rejected is the part the
memoria actually needs.
