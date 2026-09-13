/**
 * Block 4 — the explicit "Train" click, the honest progress estimate, per-method status,
 * and Stop training (#82, FR-8.4, NFR-1).
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { theme } from '../theme/theme';
import { TrainingPanel } from './TrainingPanel';
import type { TrainingStatus } from './types';

function file() {
  return new File(['a'], 'houses.csv', { type: 'text/csv' });
}

function status(overrides: Partial<TrainingStatus> = {}): TrainingStatus {
  return {
    id: 'job-1',
    methods: ['random_forest', 'logistic_regression'],
    budget_seconds: 60,
    current: null,
    halted_early: false,
    aborted: false,
    abort_detail: null,
    done: false,
    results: {},
    ...overrides,
  };
}

/**
 * A `fetch` stub driven by a queue of `GET /api/train/{id}` responses, consumed one per
 * poll — the shape a real training run actually produces, not a single fixed snapshot.
 */
function stubTraining(statuses: TrainingStatus[]) {
  const queue = [...statuses];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === '/api/train' && init?.method === 'POST') {
        return { ok: true, json: async () => ({ job_id: 'job-1' }) };
      }
      if (url === '/api/train/job-1/stop') {
        return { ok: true, json: async () => ({}) };
      }
      if (url === '/api/train/job-1') {
        const next = queue.length > 1 ? queue.shift()! : queue[0]!;
        return { ok: true, json: async () => next };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show(overrides: Partial<Parameters<typeof TrainingPanel>[0]> = {}) {
  return render(
    <ThemeProvider theme={theme}>
      <TrainingPanel
        file={file()}
        target="price"
        task="regression"
        methods={['random_forest', 'logistic_regression']}
        {...overrides}
      />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('without what training needs', () => {
  it('disables the button and says why when there is no dataset', () => {
    show({ file: null, target: null, task: null });
    expect(screen.getByRole('button', { name: /train these methods/i })).toBeDisabled();
    expect(screen.getByText(/upload a file/i)).toBeInTheDocument();
  });

  it('disables the button and says why when nothing is left to train', () => {
    show({ methods: [] });
    expect(screen.getByRole('button', { name: /train these methods/i })).toBeDisabled();
    expect(screen.getByText(/ruled out by what you told us/i)).toBeInTheDocument();
  });
});

describe('a successful run', () => {
  it('starts the job on click and shows every method, from pending to done', async () => {
    stubTraining([
      status({ current: 'random_forest' }),
      status({
        current: 'logistic_regression',
        results: {
          random_forest: {
            method: 'random_forest',
            status: 'ok',
            mean_score: 0.87,
            std_score: 0.02,
            fold_scores: [0.85, 0.89],
            fit_seconds: 1.2,
            detail: null,
          },
        },
      }),
      status({
        done: true,
        current: null,
        results: {
          random_forest: {
            method: 'random_forest',
            status: 'ok',
            mean_score: 0.87,
            std_score: 0.02,
            fold_scores: [0.85, 0.89],
            fit_seconds: 1.2,
            detail: null,
          },
          logistic_regression: {
            method: 'logistic_regression',
            status: 'ok',
            mean_score: 0.81,
            std_score: 0.03,
            fold_scores: [0.79, 0.83],
            fit_seconds: 0.9,
            detail: null,
          },
        },
      }),
    ]);
    const user = userEvent.setup();
    show();

    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    expect(await screen.findByText(/training random_forest/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/score: 0\.87/i)).toBeInTheDocument(), {
      timeout: 3000,
    });
    await waitFor(() => expect(screen.getByText(/score: 0\.81/i)).toBeInTheDocument(), {
      timeout: 3000,
    });
  });

  it('explains what Score means once a real score has landed, not before', async () => {
    stubTraining([
      status({ current: 'random_forest' }),
      status({
        done: true,
        results: {
          random_forest: {
            method: 'random_forest',
            status: 'ok',
            mean_score: 0.5,
            std_score: 0.01,
            fold_scores: [],
            fit_seconds: 1,
            detail: null,
          },
        },
      }),
    ]);
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    expect(screen.queryByText(/simply guessing the average/i)).toBeNull();
    await waitFor(
      () => expect(screen.getByText(/simply guessing the average/i)).toBeInTheDocument(),
      { timeout: 3000 },
    );
  });

  it('shows the honest ceiling estimate while a job is active, not a smooth bar', async () => {
    stubTraining([status({ current: 'random_forest' })]);
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    // Two methods left (neither finished yet), 60s tier each — a ceiling stated as a
    // number, never a determinate bar implying a percentage nothing here actually knows.
    expect(await screen.findByText(/up to 120s left/i)).toBeInTheDocument();
    expect(document.querySelector('[role="progressbar"][aria-valuenow]')).toBeNull();
  });
});

describe('stopping', () => {
  it('offers Stop only while a job is active', async () => {
    stubTraining([status({ current: 'random_forest' }), status({ done: true })]);
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    expect(await screen.findByRole('button', { name: /stop training/i })).toBeInTheDocument();

    await waitFor(() => expect(screen.queryByRole('button', { name: /stop training/i })).toBeNull(), {
      timeout: 3000,
    });
  });
});

describe('what the run says about itself', () => {
  it('explains an early halt rather than letting a short list look incomplete', async () => {
    stubTraining([
      status({
        done: true,
        halted_early: true,
        results: {
          random_forest: {
            method: 'random_forest',
            status: 'ok',
            mean_score: 0.87,
            std_score: 0.02,
            fold_scores: [],
            fit_seconds: 1,
            detail: null,
          },
        },
      }),
    ]);
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    expect(await screen.findByText(/too close to call apart/i)).toBeInTheDocument();
  });

  it('names a timed-out method without hiding the rest of the run', async () => {
    stubTraining([
      status({
        done: true,
        results: {
          random_forest: {
            method: 'random_forest',
            status: 'timeout',
            mean_score: null,
            std_score: null,
            fold_scores: [],
            fit_seconds: 60,
            detail: 'exceeded 60s',
          },
        },
      }),
    ]);
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    expect(await screen.findByText(/took longer than/i)).toBeInTheDocument();
  });

  it('surfaces an aborted job\'s reason', async () => {
    stubTraining([
      status({ done: true, aborted: true, abort_detail: 'random_forest: something broke' }),
    ]);
    const user = userEvent.setup();
    show();
    await user.click(screen.getByRole('button', { name: /train these methods/i }));

    expect(await screen.findByText(/something broke/i)).toBeInTheDocument();
  });
});

describe('a new recommendation while training is in flight', () => {
  it('stops the previous job and returns to the idle button', async () => {
    stubTraining([status({ current: 'random_forest' })]);
    const user = userEvent.setup();
    const { rerender } = show({ resetSignal: 0 });
    await user.click(screen.getByRole('button', { name: /train these methods/i }));
    await screen.findByText(/training random_forest/i);

    rerender(
      <ThemeProvider theme={theme}>
        <TrainingPanel
          file={file()}
          target="price"
          task="regression"
          methods={['decision_tree']}
          resetSignal={1}
        />
      </ThemeProvider>,
    );

    expect(await screen.findByRole('button', { name: /train these methods/i })).toBeInTheDocument();
  });
});
