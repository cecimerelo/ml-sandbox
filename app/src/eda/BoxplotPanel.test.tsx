import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { BoxplotPanel } from './BoxplotPanel';
import { theme } from '../theme/theme';
import type { BoxplotSummary } from './types';

function boxplot(overrides: Partial<BoxplotSummary> = {}): BoxplotSummary {
  return { minimum: 0, q1: 2, median: 5, q3: 8, maximum: 10, outliers: [], ...overrides };
}

function show(data: BoxplotSummary) {
  return render(
    <ThemeProvider theme={theme}>
      <BoxplotPanel title="size_m2" data={data} />
    </ThemeProvider>,
  );
}

describe('a single feature\'s boxplot', () => {
  it('renders one chart, in its own panel', () => {
    const { container } = show(boxplot());
    expect(screen.getByText('size_m2')).toBeInTheDocument();
    expect(container.querySelectorAll('svg')).toHaveLength(1);
    expect(screen.getAllByRole('button', { name: /view as table/i })).toHaveLength(1);
  });

  it('carries no subtitle — the how-to-read line lives in the section header', () => {
    show(boxplot());
    expect(screen.queryByText(/middle half/i)).toBeNull();
  });

  it('offers the five-number summary as a table', async () => {
    const user = userEvent.setup();
    show(boxplot({ median: 5 }));
    await user.click(screen.getByRole('button', { name: /view as table/i }));
    expect(screen.getByRole('cell', { name: '5' })).toBeInTheDocument();
  });
});
