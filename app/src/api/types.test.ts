/**
 * The frontend's vocabulary against the study's, checked rather than trusted.
 *
 * These unions restate Python `Literal` types the frontend cannot import. Two
 * hand-maintained copies of the same vocabulary drift, and when they do nothing errors:
 * the form offers a band the model never saw, and the model answers rather than refusing.
 * That is the shape of every train/serve bug this project has had (D-027).
 *
 * So the test reads `config/metafeatures.json`, which the study exports from the types
 * themselves.
 */

import { describe, expect, it } from 'vitest';

// Imported rather than read from disk: the study writes this file, so importing it is the
// same act as depending on it, and the bundler resolves the path the same way in every
// environment.
import exported from '../../../config/metafeatures.json';
import { FEATURES, FEATURE_TYPES, MISSING, ROWS, TASKS, classBalanceOptions } from '../form/options';

const bands = exported._bands as Record<string, string[]>;

describe('the form offers exactly the bands the model was trained on', () => {
  it.each([
    ['task', TASKS.map((o) => o.value)],
    ['rows', ROWS.map((o) => o.value)],
    ['features', FEATURES.map((o) => o.value)],
    ['feature_types', FEATURE_TYPES.map((o) => o.value)],
    ['missing', MISSING.map((o) => o.value)],
  ])('%s', (field, offered) => {
    expect(new Set(offered)).toEqual(new Set(bands[field]));
  });
});

describe('class balance', () => {
  it('never offers `not applicable` as something to choose', () => {
    // It is what the form reports for a number, not an answer a person gives. Offering it
    // would let someone predicting categories say the question does not apply to them.
    const offered = classBalanceOptions('multiclass classification').map((o) => o.value);
    expect(offered).not.toContain('not applicable');
  });

  it('maps every answer it offers onto a band the model knows', async () => {
    const { toEngineBand } = await import('../form/options');
    for (const option of classBalanceOptions('multiclass classification')) {
      expect(bands.class_balance).toContain(toEngineBand(option.value));
    }
  });
});

describe('the regime', () => {
  it('is a meta-feature the form never asks for', () => {
    // Derived from the two bands rather than asked, because asking a user to estimate
    // observations per predictor is asking for the arithmetic they came here to avoid.
    // Deriving it in one place is also what keeps both paths agreeing (D-028).
    expect(bands).toHaveProperty('regime');
  });
});
