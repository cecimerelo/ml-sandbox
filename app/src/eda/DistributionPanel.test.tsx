import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DistributionPanel } from './DistributionPanel';
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
  it('renders the histogram only, not a boxplot — that lives in its own section now', () => {
    const { container } = show(histogram());
    // One "View as table" per panel; two would mean a second chart snuck in. Scoped to
    // `role="img"` rather than every `svg`: the panel's own Expand icon is an svg too.
    expect(screen.getAllByRole('button', { name: /view as table/i })).toHaveLength(1);
    expect(container.querySelectorAll('svg[role="img"]')).toHaveLength(1);
  });

  it('carries no subtitle — the how-to-read line lives in the section header', () => {
    show(histogram());
    expect(screen.queryByText(/range of values/i)).toBeNull();
  });

  it('states the missing-value count as a caption when there is one', () => {
    show(histogram({ missing: 3 }));
    expect(screen.getByText('3 values missing, not shown.')).toBeInTheDocument();
  });

  it('says nothing when there is nothing missing', () => {
    show(histogram({ missing: 0 }));
    expect(screen.queryByText(/missing/i)).toBeNull();
  });
});

describe('a categorical column', () => {
  it('carries no subtitle either', () => {
    show(bars());
    expect(screen.queryByText(/how many rows have it/i)).toBeNull();
  });

  it('states the fold as a caption, never silently', () => {
    show(bars({ other_count: 6, other_categories: 3 }));
    expect(screen.getByText(/folded into "Other"/i)).toBeInTheDocument();
  });
});
