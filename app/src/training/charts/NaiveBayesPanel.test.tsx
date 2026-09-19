import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { NaiveBayesPanel } from './NaiveBayesPanel';
import type { NaiveBayesCharts } from './types';

function file() {
  return new File(['a'], 'sales.csv', { type: 'text/csv' });
}

function binaryCharts(): NaiveBayesCharts {
  return {
    roc: {
      points: [
        { false_positive_rate: 0, true_positive_rate: 0 },
        { false_positive_rate: 0.3, true_positive_rate: 0.75 },
        { false_positive_rate: 1, true_positive_rate: 1 },
      ],
      auc: 0.81,
      positive_class: 'yes',
    },
    confusion_matrix: { labels: ['no', 'yes'], matrix: [[38, 12], [8, 42]] },
  };
}

function multiclassCharts(): NaiveBayesCharts {
  return {
    roc: null,
    confusion_matrix: {
      labels: ['low', 'medium', 'high'],
      matrix: [
        [9, 3, 0],
        [2, 11, 1],
        [0, 4, 8],
      ],
    },
  };
}

function stubCharts(body: NaiveBayesCharts) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === '/api/train/job-1/naive_bayes/charts') {
        return { ok: true, json: async () => body };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show() {
  return render(
    <ThemeProvider theme={theme}>
      <NaiveBayesPanel jobId="job-1" file={file()} target="sold" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the ROC curve and confusion matrix for a binary target, with no coefficient panel', async () => {
  stubCharts(binaryCharts());
  show();

  expect(await screen.findByText('ROC curve')).toBeInTheDocument();
  expect(screen.getByText('Confusion matrix')).toBeInTheDocument();
  expect(screen.queryByText('Coefficients')).toBeNull();
});

it('states the AUC and the positive class in the ROC subtitle', async () => {
  stubCharts(binaryCharts());
  show();
  expect(await screen.findByText(/"yes"/)).toBeInTheDocument();
  expect(screen.getByText(/AUC = 0.810/)).toBeInTheDocument();
});

it('says why there is no ROC curve for a multiclass target, rather than an empty chart', async () => {
  stubCharts(multiclassCharts());
  show();

  expect(await screen.findByText('Confusion matrix')).toBeInTheDocument();
  expect(screen.getByText(/more than two/i)).toBeInTheDocument();
  expect(screen.queryByText('ROC curve')).toBeNull();
});
