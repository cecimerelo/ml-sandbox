import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CategoricalBarChart, categoricalRows } from './CategoricalBarChart';
import { theme } from '../theme/theme';
import type { CategoricalBars } from './types';

function bars(overrides: Partial<CategoricalBars> = {}): CategoricalBars {
  return {
    column: 'city',
    kind: 'categorical',
    categories: [
      { category: 'Sevilla', count: 10 },
      { category: 'Bilbao', count: 4 },
    ],
    other_count: 0,
    other_categories: 0,
    missing: 0,
    ...overrides,
  };
}

function show(data: CategoricalBars) {
  return render(
    <ThemeProvider theme={theme}>
      <CategoricalBarChart data={data} />
    </ThemeProvider>,
  );
}

describe('no fold', () => {
  it('renders one bar per category and nothing else', () => {
    const { container } = show(bars());
    expect(container.querySelectorAll('rect')).toHaveLength(2);
  });
});

describe('a folded tail', () => {
  it('adds exactly one more bar for the fold', () => {
    const { container } = show(bars({ other_count: 6, other_categories: 3 }));
    expect(container.querySelectorAll('rect')).toHaveLength(3);
  });

  it('names how many categories it stands for, never silently', () => {
    show(bars({ other_count: 6, other_categories: 3 }));
    const svg = screen.getByRole('img');
    expect(svg.getAttribute('aria-label')).toMatch(/Other \(3 categories\): 6/);
  });
});

describe('the table form', () => {
  it('is category times count, fold included when present', () => {
    const rows = categoricalRows(bars({ other_count: 6, other_categories: 3 }));
    expect(rows).toEqual([
      { label: 'Sevilla', count: 10 },
      { label: 'Bilbao', count: 4 },
      { label: 'Other (3 categories)', count: 6 },
    ]);
  });
});
