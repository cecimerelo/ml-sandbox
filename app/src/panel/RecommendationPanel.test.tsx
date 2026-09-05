/**
 * The recommendation panel — and the two ways it could mislead.
 *
 * It can imply the methods are further apart than the study found them, or it can present
 * an ordering that is a coin toss as though it were a ranking. Both look like ordinary
 * interface polish from the inside.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { RecommendationPanel } from './RecommendationPanel';
import { fitScore, indistinguishable } from './types';
import type { Recommendation, Suggestion } from './types';
import { theme } from '../theme/theme';

function suggestion(overrides: Partial<Suggestion> = {}): Suggestion {
  return {
    method: 'random_forest',
    label: 'Random Forest',
    expected_shortfall: 0.02,
    uncertainty: 0.005,
    reasons: [],
    excluded_by_constraint: false,
    ...overrides,
  };
}

function result(overrides: Partial<Recommendation> = {}): Recommendation {
  return {
    recommended: suggestion(),
    alternatives: [
      suggestion({ method: 'boosting', label: 'Gradient Boosting', expected_shortfall: 0.09 }),
      suggestion({ method: 'knn', label: 'K-Nearest Neighbours', expected_shortfall: 0.15 }),
    ],
    excluded: [],
    support: { field: 'rows', answer: '500-10k', datasets: 30, total: 106 },
    provisional: false,
    ...overrides,
  };
}

function show(r: Recommendation = result()) {
  render(
    <ThemeProvider theme={theme}>
      <RecommendationPanel result={r} />
    </ThemeProvider>,
  );
}

describe('the fit score', () => {
  it('is the shortfall subtracted from one, not rescaled across the methods shown', () => {
    // Rescaling is the tempting version: make the best fill the bar and the worst fall
    // short, and the panel looks decisive. It would manufacture separation the data does
    // not have — the study's own headline is that these methods sit close together, and
    // an interface that stretched them would contradict the thesis it is built on.
    expect(fitScore(0.02)).toBeCloseTo(0.98);
    expect(fitScore(0.09)).toBeCloseTo(0.91);
  });

  it('stays inside 0 and 1 whatever the shortfall', () => {
    expect(fitScore(2)).toBe(0);
    expect(fitScore(-1)).toBe(1);
  });

  it('is shown as a number, never as a bar alone', () => {
    show();
    expect(screen.getByText('0.98')).toBeInTheDocument();
    expect(screen.getByText(/fit score · 0–1/)).toBeInTheDocument();
  });

  it('exposes the score to a screen reader as a value, not a decoration', () => {
    show();
    const [meter] = screen.getAllByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '0.98');
  });
});

describe('when an ordering is not evidence', () => {
  it('two methods within their combined spread are indistinguishable', () => {
    const a = suggestion({ expected_shortfall: 0.02, uncertainty: 0.01 });
    const b = suggestion({ expected_shortfall: 0.025, uncertainty: 0.01 });
    expect(indistinguishable(a, b)).toBe(true);
  });

  it('two methods further apart than their spread are not', () => {
    const a = suggestion({ expected_shortfall: 0.02, uncertainty: 0.001 });
    const b = suggestion({ expected_shortfall: 0.2, uncertainty: 0.001 });
    expect(indistinguishable(a, b)).toBe(false);
  });

  it('says so before the ranking is read', () => {
    // The model is trained on about a hundred datasets. Where the intervals overlap the
    // order is a coin toss, and presenting it as a ranking is the confident wrong answer
    // this layer exists to avoid.
    show(
      result({
        alternatives: [
          suggestion({ method: 'boosting', label: 'Gradient Boosting', expected_shortfall: 0.022 }),
        ],
      }),
    );
    expect(screen.getByText(/too close to call apart/i)).toHaveTextContent(
      /gradient boosting/i,
    );
  });

  it('says nothing when the methods are clearly apart', () => {
    show();
    expect(screen.queryByText(/too close to call/i)).toBeNull();
  });
});

describe('the reasons', () => {
  it('are the user’s own answers given back to them', () => {
    show(
      result({
        recommended: suggestion({
          reasons: ['With few observations, flexible methods fit noise instead of pattern.'],
        }),
      }),
    );
    expect(screen.getByText(/fit noise instead of pattern/i)).toBeInTheDocument();
  });

  it('say plainly when nothing about the problem pushed either way', () => {
    // Better than an empty section, which reads as a bug, and better than inventing a
    // reason the engine did not have.
    show();
    expect(screen.getByText(/does best on data in general/i)).toBeInTheDocument();
  });
});

describe('what a constraint cost', () => {
  it('shows the methods it ruled out', () => {
    // Withholding the best method leaves the user unable to see what their own constraint
    // cost them (D-035).
    show(
      result({
        excluded: [
          suggestion({ method: 'mlp', label: 'Neural Network', excluded_by_constraint: true }),
        ],
      }),
    );
    expect(screen.getByText(/ruled out by what you told us/i)).toBeInTheDocument();
    expect(screen.getByText('Neural Network')).toBeInTheDocument();
  });

  it('says nothing about exclusions when there are none', () => {
    show();
    expect(screen.queryByText(/ruled out/i)).toBeNull();
  });
});

describe('how much the study knows', () => {
  it('says how many datasets resembled the problem', () => {
    show();
    expect(screen.getByText(/106 datasets, of which 30/i)).toBeInTheDocument();
  });

  it('says plainly when none did', () => {
    show(result({ support: { field: 'missing', answer: 'a lot', datasets: 0, total: 106 } }));
    expect(screen.getByText(/no dataset in the study had missing/i)).toBeInTheDocument();
  });

  it('says when the model behind it is unfinished', () => {
    show(result({ provisional: true }));
    expect(screen.getByText(/treat it as provisional/i)).toBeInTheDocument();
  });

  it('says nothing about provisional when the benchmark is done', () => {
    show();
    expect(screen.queryByText(/provisional/i)).toBeNull();
  });
});
