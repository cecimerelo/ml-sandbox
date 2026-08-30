/**
 * The answers each question offers, and the one rule that is not a UI choice.
 *
 * **Band thresholds are engine semantics.** Where an exact value maps to a band —
 * 8,412 rows to `500-10k` — that mapping changes the recommendation, so it belongs to the
 * engine and is cited here rather than redefined. This file holds only which options exist
 * and what they are called.
 */

import type {
  ClassBalance,
  Explainability,
  FeatureBand,
  FeatureTypes,
  MissingLevel,
  RowBand,
  Suspicion,
  Task,
} from '../api/types';

export interface Option<T> {
  value: T;
  label: string;
}

export const TASKS: Option<Task>[] = [
  { value: 'regression', label: 'A number' },
  { value: 'binary classification', label: 'One of two categories' },
  { value: 'multiclass classification', label: 'One of several categories' },
];

export const ROWS: Option<RowBand>[] = [
  { value: '<500', label: 'Fewer than 500' },
  { value: '500-10k', label: '500 to 10,000' },
  { value: '>10k', label: 'More than 10,000' },
];

export const FEATURES: Option<FeatureBand>[] = [
  { value: '<10', label: 'Fewer than 10' },
  { value: '10-50', label: '10 to 50' },
  { value: '>50', label: 'More than 50' },
];

export const FEATURE_TYPES: Option<FeatureTypes>[] = [
  { value: 'numeric', label: 'Numbers' },
  { value: 'categorical', label: 'Labels' },
  { value: 'mixed', label: 'Both' },
];

export const MISSING: Option<MissingLevel>[] = [
  { value: 'none', label: 'None' },
  { value: 'some', label: 'Some' },
  { value: 'a lot', label: 'A lot' },
];

export const EXPLAINABILITY: Option<Explainability>[] = [
  { value: 'not important', label: 'Not important' },
  { value: 'somewhat', label: 'Somewhat' },
  { value: 'critical', label: 'Critical' },
];

/** Shared by both belief questions, so the three always-asked ones read as one rhythm. */
export const SUSPICION: Option<Suspicion>[] = [
  { value: 'no', label: 'No' },
  { value: 'unsure', label: "I don't know" },
  { value: 'yes', label: 'Yes' },
];

/**
 * The option set depends on the prediction type, because the two the PRD lists are
 * binary-shaped and do not describe a twelve-class long tail.
 *
 * `several classes are rare` maps to the same engine band as `one class dominates`. It
 * exists so a user with a long tail is not forced into a description that is false about
 * their data — a wrong answer given because the right one was not offered is worse than a
 * coarser question.
 */
export type ClassBalanceAnswer =
  | 'roughly equal'
  | 'one class dominates'
  | 'several classes are rare';

export function classBalanceOptions(task: Task): Option<ClassBalanceAnswer>[] {
  const shared: Option<ClassBalanceAnswer>[] = [
    { value: 'roughly equal', label: 'Roughly equal' },
    { value: 'one class dominates', label: 'One category dominates' },
  ];
  if (task !== 'multiclass classification') return shared;
  return [...shared, { value: 'several classes are rare', label: 'Several categories are rare' }];
}

/**
 * Three answers, two engine bands.
 *
 * `several classes are rare` is its own answer because a long tail is not "one category
 * dominates" and a user should not have to say something false about their data. It maps
 * to the same band **until the engine has a third**, which would be an engine change and
 * not a UI one — so the collapse happens here, once, and visibly.
 *
 * Kept distinct in the UI rather than sharing a value: two radio options with the same
 * value select together, which is a bug the type system will not catch.
 */
export function toEngineBand(answer: ClassBalanceAnswer): ClassBalance {
  return answer === 'roughly equal' ? 'roughly equal' : 'one class dominates';
}

export function isClassification(task: Task): boolean {
  return task !== 'regression';
}
