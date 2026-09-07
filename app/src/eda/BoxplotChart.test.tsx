import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { BoxplotChart, boxplotRows } from './BoxplotChart';
import { theme } from '../theme/theme';
import type { BoxplotSummary } from './types';

function summary(overrides: Partial<BoxplotSummary> = {}): BoxplotSummary {
  return {
    minimum: 1,
    q1: 2,
    median: 3,
    q3: 4,
    maximum: 5,
    outliers: [],
    ...overrides,
  };
}

function show(data: BoxplotSummary) {
  return render(
    <ThemeProvider theme={theme}>
      <BoxplotChart data={data} />
    </ThemeProvider>,
  );
}

describe('an ordinary boxplot', () => {
  it('renders the box', () => {
    const { container } = show(summary());
    expect(container.querySelector('rect')).toBeInTheDocument();
  });

  it('carries the five-number summary in its accessible description', () => {
    show(summary());
    const label = screen.getByRole('img').getAttribute('aria-label');
    expect(label).toMatch(/min 1\.0/);
    expect(label).toMatch(/median 3\.0/);
    expect(label).toMatch(/max 5\.0/);
  });
});

describe('outliers', () => {
  it('renders one point per outlier', () => {
    const { container } = show(summary({ outliers: [20, -5] }));
    expect(container.querySelectorAll('circle')).toHaveLength(2);
  });

  it('names the count in its accessible description', () => {
    show(summary({ outliers: [20, -5] }));
    expect(screen.getByRole('img').getAttribute('aria-label')).toMatch(/2 outlier/);
  });

  it('says nothing about outliers when there are none', () => {
    show(summary());
    expect(screen.getByRole('img').getAttribute('aria-label')).not.toMatch(/outlier/);
  });
});

describe('the table form', () => {
  it('is the five-number summary, plus a row per outlier', () => {
    const rows = boxplotRows(summary({ outliers: [20] }));
    expect(rows).toEqual([
      { label: 'Minimum', count: 1 },
      { label: 'Q1', count: 2 },
      { label: 'Median', count: 3 },
      { label: 'Q3', count: 4 },
      { label: 'Maximum', count: 5 },
      { label: 'Outlier 1', count: 20 },
    ]);
  });
});
