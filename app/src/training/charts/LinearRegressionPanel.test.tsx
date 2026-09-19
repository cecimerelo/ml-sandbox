import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { LinearRegressionPanel } from './LinearRegressionPanel';
import type { LinearRegressionCharts } from './types';

function file() {
  return new File(['a'], 'strong-signal-houses.csv', { type: 'text/csv' });
}

function charts(): LinearRegressionCharts {
  return {
    residual: { points: [{ x: 1, y: 0.1 }, { x: 2, y: -0.2 }] },
    predicted_vs_actual: { points: [{ x: 1, y: 1.1 }, { x: 2, y: 1.8 }], r2: 0.97 },
    coefficients: { bars: [{ feature: 'size_m2', value: 1200 }, { feature: 'bedrooms', value: 8000 }] },
    leverage: { points: [{ leverage: 0.02, studentized_residual: 0.3 }] },
  };
}

function stubCharts(body: LinearRegressionCharts | null) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === '/api/train/job-1/linear_regression/charts') {
        if (body === null) return { ok: false, json: async () => ({}) };
        return { ok: true, json: async () => body };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show() {
  return render(
    <ThemeProvider theme={theme}>
      <LinearRegressionPanel jobId="job-1" file={file()} target="price" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('shows a loading state before the charts arrive', () => {
  stubCharts(charts());
  show();
  expect(screen.getByLabelText(/computing charts/i)).toBeInTheDocument();
});

it('renders all four panels once the charts arrive', async () => {
  stubCharts(charts());
  show();

  expect(await screen.findByText('Residual plot')).toBeInTheDocument();
  expect(screen.getByText('Predicted vs. actual')).toBeInTheDocument();
  expect(screen.getByText('Coefficients')).toBeInTheDocument();
  expect(screen.getByText('Leverage')).toBeInTheDocument();
});

it('states R² in the predicted-vs-actual subtitle', async () => {
  stubCharts(charts());
  show();
  expect(await screen.findByText(/R² = 0.970/)).toBeInTheDocument();
});

it('shows an error state when the fetch fails, without pretending training itself failed', async () => {
  stubCharts(null);
  show();
  expect(await screen.findByText(/couldn't compute these charts/i)).toBeInTheDocument();
  expect(screen.getByText(/training itself already finished/i)).toBeInTheDocument();
});

it('re-fetches when the file changes', async () => {
  stubCharts(charts());
  const { rerender } = render(
    <ThemeProvider theme={theme}>
      <LinearRegressionPanel jobId="job-1" file={file()} target="price" />
    </ThemeProvider>,
  );
  await screen.findByText('Residual plot');

  const secondFile = new File(['b'], 'other.csv', { type: 'text/csv' });
  rerender(
    <ThemeProvider theme={theme}>
      <LinearRegressionPanel jobId="job-1" file={secondFile} target="price" />
    </ThemeProvider>,
  );

  await waitFor(() => {
    expect(vi.mocked(fetch).mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
