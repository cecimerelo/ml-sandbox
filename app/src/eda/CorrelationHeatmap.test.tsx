import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { CorrelationHeatmap } from './CorrelationHeatmap';
import { CHART } from '../copy/catalogue';
import { theme } from '../theme/theme';
import type { CorrelationMatrix } from './types';

function matrix(overrides: Partial<CorrelationMatrix> = {}): CorrelationMatrix {
  return {
    features: ['size_m2', 'bedrooms'],
    values: [
      [1, 0.5],
      [0.5, 1],
    ],
    total_numeric: 2,
    ...overrides,
  };
}

function show(data: CorrelationMatrix) {
  return render(
    <ThemeProvider theme={theme}>
      <CorrelationHeatmap data={data} />
    </ThemeProvider>,
  );
}

describe('an ordinary matrix', () => {
  it('renders one cell per pair', () => {
    const { container } = show(matrix());
    // n×n cells, excluding the label text nodes.
    expect(container.querySelectorAll('svg rect')).toHaveLength(5); // 4 cells + border
  });

  it('names both features in its accessible description', () => {
    show(matrix());
    expect(screen.getByRole('img').getAttribute('aria-label')).toMatch(/2 features/);
  });

  it('offers a real matrix as its table, not a stub', async () => {
    const user = userEvent.setup();
    show(matrix());
    await user.click(screen.getByRole('button', { name: /view as table/i }));
    expect(screen.getByRole('columnheader', { name: 'bedrooms' })).toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'size_m2' })).toBeInTheDocument();
  });
});

describe('the how-to-read subtitle', () => {
  it('is always present, from the catalogue, whether or not anything was truncated', () => {
    show(matrix({ total_numeric: 2 }));
    expect(
      screen.getByText((_, node) => Boolean(node?.textContent?.startsWith(CHART['chart.correlation.subtitle']))),
    ).toBeInTheDocument();
  });
});

describe('the truncation caption', () => {
  it('states the cap against the total, never silently, alongside the how-to-read line', () => {
    show(matrix({ total_numeric: 500 }));
    const subtitle = screen.getByText((_, node) =>
      Boolean(node?.textContent?.startsWith(CHART['chart.correlation.subtitle'])),
    );
    expect(subtitle.textContent).toMatch(/showing the 30 features.*of 500/i);
  });

  it('says nothing about truncation when nothing was truncated', () => {
    show(matrix({ total_numeric: 2 }));
    expect(screen.queryByText(/showing the 30 features/i)).toBeNull();
  });
});

describe('fewer than two numeric features', () => {
  it('says there is nothing to correlate, rather than an empty grid', () => {
    show(matrix({ features: [], values: [], total_numeric: 1 }));
    expect(screen.getByText(/fewer than two numeric columns/i)).toBeInTheDocument();
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('names the all-categorical case specifically', () => {
    show(matrix({ features: [], values: [], total_numeric: 0 }));
    expect(screen.getByText(/none of your columns are numbers/i)).toBeInTheDocument();
  });

  it('offers no "View as table" for a table that cannot exist', () => {
    show(matrix({ features: [], values: [], total_numeric: 0 }));
    expect(screen.queryByRole('button', { name: /view as table/i })).toBeNull();
  });
});
