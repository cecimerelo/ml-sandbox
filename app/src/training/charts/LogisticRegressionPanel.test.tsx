import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { LogisticRegressionPanel } from './LogisticRegressionPanel';
import type { LogisticRegressionCharts } from './types';

function file() {
  return new File(['a'], 'sales.csv', { type: 'text/csv' });
}

function binaryCharts(): LogisticRegressionCharts {
  return {
    roc: {
      points: [
        { false_positive_rate: 0, true_positive_rate: 0 },
        { false_positive_rate: 0.2, true_positive_rate: 0.8 },
        { false_positive_rate: 1, true_positive_rate: 1 },
      ],
      auc: 0.87,
      positive_class: 'yes',
    },
    confusion_matrix: { labels: ['no', 'yes'], matrix: [[40, 10], [5, 45]] },
    coefficients: { bars: [{ feature: 'size_m2', value: 1.2 }, { feature: 'bedrooms', value: -0.4 }] },
  };
}

function multiclassCharts(): LogisticRegressionCharts {
  return {
    roc: null,
    confusion_matrix: {
      labels: ['low', 'medium', 'high'],
      matrix: [
        [10, 2, 0],
        [1, 12, 1],
        [0, 3, 9],
      ],
    },
    coefficients: { bars: [] },
  };
}

function stubCharts(body: LogisticRegressionCharts) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === '/api/train/job-1/logistic_regression/charts') {
        return { ok: true, json: async () => body };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show() {
  return render(
    <ThemeProvider theme={theme}>
      <LogisticRegressionPanel jobId="job-1" file={file()} target="sold" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the ROC curve, confusion matrix, and coefficients for a binary target', async () => {
  stubCharts(binaryCharts());
  show();

  expect(await screen.findByText('ROC curve')).toBeInTheDocument();
  expect(screen.getByText('Confusion matrix')).toBeInTheDocument();
  expect(screen.getByText('Coefficients')).toBeInTheDocument();
});

it('states the AUC and the positive class in the ROC subtitle', async () => {
  stubCharts(binaryCharts());
  show();
  expect(await screen.findByText(/"yes"/)).toBeInTheDocument();
  expect(screen.getByText(/AUC = 0.870/)).toBeInTheDocument();
});

it('says why there is no ROC curve or coefficients for a multiclass target, rather than an empty chart', async () => {
  stubCharts(multiclassCharts());
  show();

  expect(await screen.findByText('Confusion matrix')).toBeInTheDocument();
  expect(screen.getByText(/more than two/i)).toBeInTheDocument();
  expect(screen.queryByText('ROC curve')).toBeNull();
  expect(screen.queryByText('Coefficients')).toBeNull();
});
