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
    flexibility: { label: 'flexible', detail: 'splits the data repeatedly.' },
    interpretability: { label: 'opaque', detail: 'no single reason to give for one answer.' },
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

  it('marks the tie on the method it applies to', () => {
    // Not in a banner above the list. A banner naming the same methods the list repeats
    // underneath gives a reader two places to look, and makes the more important half —
    // that these are equivalent — read as a footnote to the less important half.
    show(
      result({
        alternatives: [
          suggestion({ method: 'boosting', label: 'Gradient Boosting', expected_shortfall: 0.022 }),
        ],
      }),
    );
    expect(screen.getByText(/too close to call apart from Random Forest/i)).toBeInTheDocument();
  });

  it('marks only the methods that are actually tied', () => {
    show(
      result({
        alternatives: [
          suggestion({ method: 'boosting', label: 'Gradient Boosting', expected_shortfall: 0.022 }),
          suggestion({ method: 'knn', label: 'K-Nearest Neighbours', expected_shortfall: 0.4 }),
        ],
      }),
    );
    expect(screen.getAllByText(/too close to call/i)).toHaveLength(1);
  });

  it('names each method once', () => {
    // The redundancy this replaced: a banner listing three methods, and a list repeating
    // the same three underneath it.
    show(
      result({
        alternatives: [
          suggestion({ method: 'boosting', label: 'Gradient Boosting', expected_shortfall: 0.022 }),
        ],
      }),
    );
    expect(screen.getAllByText('Gradient Boosting')).toHaveLength(1);
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

  it('names the field the way the form asked it, not the engine\'s internal name', () => {
    // 'feature_types' is the field name in the API response; a reader never saw a
    // question called that.
    show(result({ support: { field: 'feature_types', answer: 'mixed', datasets: 24, total: 106 } }));
    expect(screen.getByText(/of which 24 resembled yours on what kind of columns/i)).toBeInTheDocument();
    expect(screen.queryByText(/feature_types/i)).toBeNull();
  });

  it('says the recommendation rests on the form alone', () => {
    // Until Epic 4 trains the recommended method on an uploaded dataset, every number
    // here comes from the benchmark, not from the user's own file — a reader could
    // otherwise take "based on 106 datasets" to mean their file was among them.
    show();
    expect(screen.getByText(/based only on your answers to the form/i)).toBeInTheDocument();
  });

  it('says plainly when none did', () => {
    show(result({ support: { field: 'missing', answer: 'a lot', datasets: 0, total: 106 } }));
    // Named the way the form asked the question, not the engine's field name.
    expect(screen.getByText(/no dataset in the study had an answer like yours for how much is missing/i)).toBeInTheDocument();
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

describe('the position sections', () => {
  it("name the recommended method, not the concept in the abstract", () => {
    // What this replaced: the same paragraph explaining bias-variance to every user,
    // regardless of what was recommended — informative about the axis, silent about the
    // answer.
    show();
    expect(screen.getByText('Random Forest is flexible')).toBeInTheDocument();
    expect(screen.getByText('Random Forest is opaque')).toBeInTheDocument();
  });

  it("say what that means for this method", () => {
    show();
    expect(screen.getByText(/splits the data repeatedly/i)).toBeInTheDocument();
    expect(screen.getByText(/no single reason to give/i)).toBeInTheDocument();
  });
});
