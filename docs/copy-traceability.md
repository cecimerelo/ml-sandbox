# Copy traceability

Every explanation the product shows, and where its claim comes from.

**This table is a thesis appendix. It is never rendered in the interface** — FR-2.3 keeps
the UI citation-free, and the point of the appendix is that grounding can be demonstrated
without the product ever naming a source.

It exists to answer one question, which is the likeliest one at a defence: *how do you know
these explanations are correct?* Without the table that is an awkward moment. With it, it
is an exhibit.

## How to read a row

**Claim** is what the string asserts, stripped to its content. **Source** is where that
claim comes from in the reference text. **Engine** is the rule that consumes the same
belief, so it can be checked that the copy does not promise more than the code delivers —
constraint 3 in `app/src/copy/catalogue.ts`.

A row with no engine rule is not a defect: some copy explains what a question *is* rather
than what the answer does.

## Reference

James, Witten, Hastie & Tibshirani, *An Introduction to Statistical Learning*, 2nd edition
(corrected printing, June 2023) — the copy in this repository.

> **Pending before submission.** The rows below cite chapters and named sections. Page
> numbers against this exact printing still have to be filled in, and each claim re-read
> against its section rather than against memory of it. Left explicit rather than quietly
> approximate: an appendix whose references were never opened is worse than no appendix,
> because it looks checked.

## Form questions

| String | Claim | Source | Engine rule |
|---|---|---|---|
| `form.prediction-type` | Methods are built for numbers or for categories, and the target decides which apply | Ch. 2, *Statistical Learning* — regression vs classification problems | `Method.tasks`, `incompatibility_reason` |
| `form.rows` | With few observations, flexible methods describe coincidence rather than pattern | Ch. 2, *Assessing Model Accuracy* — the bias-variance trade-off | `small-sample-favours-simple`, `small-sample-penalises-flexible` |
| `form.features` | As predictors grow relative to observations, apparent patterns multiply | Ch. 6, *Considerations in High Dimensions* | `high-dimensional-favours-regularisation` |
| `form.feature-types` | Some methods split on labels directly; others need them encoded first, which can produce more columns than rows | Ch. 3, *Other Considerations in the Regression Model* (qualitative predictors); Ch. 8, *Tree-Based Methods* | `categorical-features-favour-trees` |
| `form.missing` | Most methods cannot read a blank, so gaps are filled in before training and the filling shapes the result | Ch. 8, *Tree-Based Methods* (missing values); Ch. 3 | `missing-values-favour-trees` |
| `form.class-balance` | A dominant class lets a method score well by always predicting it | Ch. 4, *Classification* — the null classifier and error rates | `imbalance-penalises-naive-methods` |
| `form.explainability` | Some methods yield the reason for a prediction; others yield only the prediction | Ch. 2, *Prediction Accuracy vs. Model Interpretability* | `Method.explainability`, `excluded_by_constraints` (D-035) |
| `form.non-linearity` | Linear methods cannot follow a relationship that curves; others can | Ch. 7, *Moving Beyond Linearity* | `non-linearity-penalises-linear-methods`, `non-linearity-favours-flexible` |
| `form.interactions` | Some methods find joint effects unaided; additive methods need the term written in by hand | Ch. 3, *Extensions of the Linear Model* (interaction terms); Ch. 8 | `interactions-favour-methods-that-find-them`, `interactions-penalise-additive-methods` (D-039) |

## Recommendation panel

| String | Claim | Source | Engine rule |
|---|---|---|---|
| `panel.bias-variance.explanation` | Methods trade steadiness against the ability to follow detail, and neither end is right in general | Ch. 2, *Assessing Model Accuracy* — the bias-variance trade-off | the flexibility rules as a set |
| `panel.interpretability.explanation` | Whether a prediction can be explained is separate from whether it is accurate | Ch. 2, *Prediction Accuracy vs. Model Interpretability* | `Method.explainability` |

## Disabled reasons

Generated from the method registry rather than written here, so the study and the interface
cannot disagree about when a method applies (D-024). Their claim is the method's task
support, which is verified against the installed scikit-learn by the test suite rather than
asserted (D-022).

## What is not yet covered

Chart subtitles — roughly twenty-nine, one per distinct chart form — belong to the epics
that build the charts. Shape A's form questions differ from Shape B's, because the question
there is *"is this right?"* rather than *"what is it?"*, and arrive with the upload path.
