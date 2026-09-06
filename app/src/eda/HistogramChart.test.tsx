import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { HistogramChart, histogramRows } from './HistogramChart';
import { theme } from '../theme/theme';
import type { Histogram } from './types';

function histogram(overrides: Partial<Histogram> = {}): Histogram {
  return {
    column: 'size_m2',
    kind: 'numeric',
    bins: [
      { start: 0, end: 10, count: 3 },
      { start: 10, end: 20, count: 7 },
    ],
    missing: 0,
    ...overrides,
  };
}

function show(data: Histogram) {
  return render(
    <ThemeProvider theme={theme}>
      <HistogramChart data={data} />
    </ThemeProvider>,
  );
}

describe('an ordinary histogram', () => {
  it('renders one bar per bin', () => {
    const { container } = show(histogram());
    expect(container.querySelectorAll('rect')).toHaveLength(2);
  });

  it('carries the bin ranges and counts in its accessible name', () => {
    show(histogram());
    const svg = screen.getByRole('img');
    expect(svg).toHaveAttribute('aria-label', expect.stringContaining('size_m2'));
    expect(svg.getAttribute('aria-label')).toMatch(/0\.0 to 10\.0: 3/);
  });
});

describe('an all-missing column', () => {
  it('renders no bars rather than dividing by a range that does not exist', () => {
    const { container } = show(histogram({ bins: [], missing: 5 }));
    expect(container.querySelectorAll('rect')).toHaveLength(0);
  });
});

describe('the table form', () => {
  it('is bin range times count', () => {
    const rows = histogramRows(histogram());
    expect(rows).toEqual([
      { label: '0.0–10.0', count: 3 },
      { label: '10.0–20.0', count: 7 },
    ]);
  });
});
