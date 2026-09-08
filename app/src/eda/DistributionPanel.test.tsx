import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DistributionPanel } from './DistributionPanel';
import { CHART } from '../copy/catalogue';
import { theme } from '../theme/theme';
import type { CategoricalBars, Histogram } from './types';

function histogram(overrides: Partial<Histogram> = {}): Histogram {
  return {
    column: 'size_m2',
    kind: 'numeric',
    bins: [{ start: 0, end: 10, count: 5 }],
    missing: 0,
    boxplot: { minimum: 0, q1: 2, median: 5, q3: 8, maximum: 10, outliers: [] },
    ...overrides,
  };
}

function bars(overrides: Partial<CategoricalBars> = {}): CategoricalBars {
  return {
    column: 'city',
    kind: 'categorical',
    categories: [{ category: 'Sevilla', count: 10 }],
    other_count: 0,
    other_categories: 0,
    missing: 0,
    ...overrides,
  };
}

function show(data: Histogram | CategoricalBars) {
  return render(
    <ThemeProvider theme={theme}>
      <DistributionPanel title="size_m2" data={data} />
    </ThemeProvider>,
  );
}

describe('a numeric column', () => {
  it('gives the histogram its permanent how-to-read subtitle, from the catalogue', () => {
    show(histogram());
    expect(screen.getByText(CHART['chart.histogram.subtitle'])).toBeInTheDocument();
  });

  it('gives the boxplot its own permanent subtitle, not the histogram\'s', () => {
    show(histogram());
    expect(screen.getByText(CHART['chart.boxplot.subtitle'])).toBeInTheDocument();
  });

  it('appends the missing-value count to the histogram subtitle, never replacing it', () => {
    show(histogram({ missing: 3 }));
    const subtitle = screen.getByText(
      (_, node) => node?.textContent === `${CHART['chart.histogram.subtitle']} 3 values missing, not shown.`,
    );
    expect(subtitle).toBeInTheDocument();
  });
});

describe('a categorical column', () => {
  it('gives the bar chart its permanent how-to-read subtitle', () => {
    show(bars());
    expect(screen.getByText(CHART['chart.categorical-bars.subtitle'])).toBeInTheDocument();
  });

  it('appends the fold disclosure without dropping the how-to-read line', () => {
    show(bars({ other_count: 6, other_categories: 3 }));
    const subtitle = screen.getByText((_, node) =>
      Boolean(node?.textContent?.startsWith(CHART['chart.categorical-bars.subtitle'])),
    );
    expect(subtitle.textContent).toMatch(/Other/);
  });
});
