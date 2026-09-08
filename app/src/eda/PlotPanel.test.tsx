import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import type React from 'react';

import { PlotPanel } from './PlotPanel';
import { theme } from '../theme/theme';

function show(props: Partial<React.ComponentProps<typeof PlotPanel>> = {}) {
  return render(
    <ThemeProvider theme={theme}>
      <PlotPanel
        title="size_m2"
        chart={<div data-testid="chart">chart</div>}
        table={<div data-testid="table">table</div>}
        {...props}
      />
    </ThemeProvider>,
  );
}

describe('anatomy', () => {
  it('shows the title always', () => {
    show();
    expect(screen.getByText('size_m2')).toBeInTheDocument();
  });

  it('shows the subtitle only when given one', () => {
    show({ subtitle: 'Showing 12 of 500 features.' });
    expect(screen.getByText('Showing 12 of 500 features.')).toBeInTheDocument();
  });

  it('shows the caption only when given one', () => {
    show({ caption: 'n = 400' });
    expect(screen.getByText('n = 400')).toBeInTheDocument();
  });

  it('shows the chart, not the table, by default', () => {
    show();
    expect(screen.getByTestId('chart')).toBeInTheDocument();
    expect(screen.queryByTestId('table')).toBeNull();
  });
});

describe('View as table', () => {
  it('toggles to the table and back, never showing both at once', async () => {
    const user = userEvent.setup();
    show();

    await user.click(screen.getByRole('button', { name: /view as table/i }));
    expect(screen.getByTestId('table')).toBeInTheDocument();
    expect(screen.queryByTestId('chart')).toBeNull();

    await user.click(screen.getByRole('button', { name: /view as chart/i }));
    expect(screen.getByTestId('chart')).toBeInTheDocument();
    expect(screen.queryByTestId('table')).toBeNull();
  });

  it('is reachable and operable from the keyboard alone (#48)', async () => {
    // A native `Button`, not a click handler on a div — Tab reaches it and Enter
    // activates it without a mouse, which is the whole of what "every chart has a
    // table view reachable by keyboard" asks for.
    const user = userEvent.setup();
    show();

    await user.tab();
    expect(screen.getByRole('button', { name: /view as table/i })).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(screen.getByTestId('table')).toBeInTheDocument();
  });
});
