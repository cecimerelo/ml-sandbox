/**
 * The shell's accessibility criteria, checked by rendering rather than by reading.
 *
 * #32 requires a specific focus order and a specific ARIA state. Both are properties of
 * the rendered output, and both survive a plausible refactor that breaks them — reordering
 * JSX, or wrapping the title in a layout element. Reading the source to confirm them is
 * the kind of verification that passes right up until it matters.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { App } from './App';
import { theme } from './theme/theme';

function file(name: string): File {
  return new File(['a,b\n1,2\n'], name, { type: 'text/csv' });
}

function renderAt(path: string) {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('focus order', () => {
  it('reaches the skip link first, then the title', async () => {
    renderAt('/');
    const user = userEvent.setup();

    await user.tab();
    expect(screen.getByRole('link', { name: /skip to main content/i })).toHaveFocus();

    await user.tab();
    expect(screen.getByRole('link', { name: 'ML Sandbox' })).toHaveFocus();
  });

  it('keeps the skip link focusable rather than hiding it from the focus order', async () => {
    // `display: none` and `visibility: hidden` would both remove it from the one thing it
    // exists to be in. The clip-rect idiom is what keeps it reachable.
    renderAt('/');
    await userEvent.setup().tab();
    expect(screen.getByRole('link', { name: /skip to main content/i })).toBeVisible();
  });

  it('points the skip link at a target that exists', () => {
    // A skip link to a missing anchor fails silently: focus stays put and the user has no
    // way to tell the control did nothing.
    const { container } = renderAt('/');
    const href = screen.getByRole('link', { name: /skip to main content/i }).getAttribute('href');
    expect(href).toBe('#main');
    expect(container.querySelector('#main')).not.toBeNull();
  });
});

describe('the Benchmark link', () => {
  it.each(['/', '/benchmark'])('is absent from %s while the surface is empty', (path) => {
    // The spine specifies it, and it returns with Epic 6. A link to a blank page spends
    // the user's attention and returns nothing, which is worse than not offering it.
    renderAt(path);
    expect(screen.queryByRole('link', { name: 'Benchmark' })).toBeNull();
  });
});

describe('the surfaces', () => {
  it('renders the dashboard at /', () => {
    renderAt('/');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Describe your problem');
  });

  it('renders the benchmark at /benchmark', () => {
    renderAt('/benchmark');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Benchmark');
  });

  it('has exactly one h1 per surface', () => {
    // Two would leave a screen-reader user without a single answer to "what is this page".
    renderAt('/');
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
  });
});

describe('chrome present on both surfaces', () => {
  it.each(['/', '/benchmark'])('the top bar and footer render at %s', (path) => {
    renderAt(path);
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
  });

  it.each(['/', '/benchmark'])('the privacy link is absent from %s for now', (path) => {
    // It returns with 2.8, once 3.1 and 2.7 give it something true to describe. A notice
    // that promises what the code does not do is worse than no notice at all.
    renderAt(path);
    expect(screen.queryByRole('link', { name: /privacy notice/i })).toBeNull();
  });

  it('the product title returns to the dashboard', () => {
    renderAt('/benchmark');
    expect(screen.getByRole('link', { name: 'ML Sandbox' })).toHaveAttribute('href', '/');
  });
});

describe('the reading column', () => {
  it('holds the dashboard to a readable width rather than the full page', () => {
    // The 1440px content column is sized for the plot grid — panels two to four abreast.
    // Prose and controls have no such requirement, and a line of text that wide is
    // scanned rather than read.
    renderAt('/');
    const heading = screen.getByRole('heading', { level: 1 });
    const column = heading.parentElement;
    expect(column).toHaveStyle({ marginLeft: 'auto', marginRight: 'auto' });
  });
});

describe('the dataset upload', () => {
  it('sits above the questions, since it is what decides their shape', () => {
    renderAt('/');
    const dropzone = screen.getByLabelText(/upload a csv/i);
    const firstQuestion = screen.getAllByRole('radiogroup')[0];
    expect(dropzone.compareDocumentPosition(firstQuestion!)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });

  it('does not imply the form needs one', () => {
    // Advice-only is the product, not a fallback for people without data.
    renderAt('/');
    expect(screen.getByText(/without one/i)).toBeInTheDocument();
  });

  it('is not offered on the benchmark surface', () => {
    renderAt('/benchmark');
    expect(screen.queryByLabelText(/upload a csv/i)).toBeNull();
  });
});

describe('what the interface says', () => {
  it('never shows our issue numbers', () => {
    // This shipped once: an upload reported "filling them in from the file is 3.2".
    // Scaffolding copy gets written for whoever is building the thing and then stays,
    // and a reader has no way to know 3.2 is not something about their data.
    renderAt('/');
    const text = document.body.textContent ?? '';
    expect(text).not.toMatch(/\b[1-6]\.\d{1,2}\b/);
  });

  it('does not name the epics or the tickets', () => {
    renderAt('/');
    const text = document.body.textContent ?? '';
    for (const word of [/\bepic\b/i, /\bissue #/i, /\bFR-\d/, /\bTODO\b/]) {
      expect(text).not.toMatch(word);
    }
  });
});

describe('replacing a dataset that fails', () => {
  it('does not leave the previous file driving the form', async () => {
    // The page holds the readings, so a failure in the control has to reach it. Otherwise
    // the zone says nothing is loaded while the questions still hold the last file's
    // properties, and a recommendation could be asked for about a dataset the user
    // replaced.
    const user = userEvent.setup();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ columns: ['a', 'b'], rows: 5, skipped: [] }),
      }),
    );
    renderAt('/');
    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');
    expect(screen.getByRole('combobox', { name: /predict/i })).toBeInTheDocument();

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: { reason: 'no-rows', message: 'no data' } }),
      }),
    );
    await user.upload(screen.getByLabelText(/upload a csv/i), file('bad.csv'));
    await screen.findByRole('alert');

    expect(screen.queryByRole('combobox', { name: /predict/i })).toBeNull();
    vi.unstubAllGlobals();
  });
});

describe('removing a dataset', () => {
  it('takes the target picker and the detected answers with it', async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ columns: ['a', 'b'], rows: 5, skipped: [] }),
      }),
    );
    renderAt('/');
    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');
    expect(screen.getByRole('combobox', { name: /predict/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^remove$/i }));

    expect(screen.queryByRole('combobox', { name: /predict/i })).toBeNull();
    expect(screen.queryByText(/in your file/)).toBeNull();
    vi.unstubAllGlobals();
  });

  it('leaves manual answers alone when no target was ever confirmed', async () => {
    // No detection ever completed here — the file was removed before a target column was
    // picked — so there is nothing this reset the way `ProblemForm.test.tsx` covers
    // explicitly for a detection that did land.
    const user = userEvent.setup();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ columns: ['a', 'b'], rows: 5, skipped: [] }),
      }),
    );
    renderAt('/');
    const explain = screen.getByRole('radiogroup', { name: /explain individual predictions/i });
    await user.click(within(explain).getByRole('radio', { name: 'Critical' }));

    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');
    await user.click(screen.getByRole('button', { name: /^remove$/i }));

    const after = screen.getByRole('radiogroup', { name: /explain individual predictions/i });
    expect(within(after).getByRole('radio', { name: 'Critical' })).toBeChecked();
    vi.unstubAllGlobals();
  });

  it('clears an existing recommendation rather than leaving it stale', async () => {
    // Removing the file took the premise the recommendation was worked out from, not just
    // made an answer old — dimming it and offering "press Get Recommendation again" would
    // point at a question the form can no longer even ask.
    const user = userEvent.setup();
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (url === '/api/dataset') {
          return { ok: true, json: async () => ({ columns: ['a', 'b'], rows: 5, skipped: [] }) };
        }
        return { ok: true, json: async () => recommendation() };
      }),
    );
    renderAt('/');

    await answer(user, /what are you trying to predict/i, 'A number');
    await answer(user, /how many rows/i, '500 to 10,000');
    await answer(user, /how many columns/i, '10 to 50');
    await answer(user, /what kind of columns/i, 'Numbers');
    await answer(user, /how much of your data is missing/i, 'None');
    await answer(user, /explain individual predictions/i, 'Not important');
    await answer(user, /straight line/i, "I don't know");
    await answer(user, /only matter in combination/i, 'No');
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    await screen.findByText('Suggested method');

    // The form collapses to its one-line summary once a recommendation exists.
    await user.click(screen.getByRole('button', { name: /^edit$/i }));

    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');
    await user.click(screen.getByRole('button', { name: /^remove$/i }));

    expect(screen.queryByText('Suggested method')).toBeNull();
    vi.unstubAllGlobals();
  });
});

describe('changing the target after a recommendation exists', () => {
  it('clears the stale recommendation rather than pairing its method list with a new task', async () => {
    // A recommendation's method list (what the Training panel offers) is worked out for
    // one specific task/target. Re-detecting a different target updates the task/target
    // shown immediately, but the old method list is only replaced on the next "Get
    // Recommendation" — leaving the old `result` in place let a regression-only method
    // reach `/api/train` alongside a freshly re-detected classification task.
    const user = userEvent.setup();
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (url === '/api/dataset') {
          return { ok: true, json: async () => ({ columns: ['a', 'b'], rows: 5, skipped: [] }) };
        }
        if (url === '/api/dataset/detect') {
          return {
            ok: true,
            json: async () => ({
              task: 'regression',
              rows: '500-10k',
              features: '10-50',
              feature_types: 'numeric',
              missing: 'none',
              class_balance: 'not applicable',
              n_rows: 5,
              n_features: 1,
              n_classes: null,
              missing_rate: 0,
              dropped_rows: 0,
              uncertain: [],
            }),
          };
        }
        if (url === '/api/recommend') {
          return { ok: true, json: async () => recommendation() };
        }
        // The EDA block's own endpoints (columns, correlation, distributions) — not
        // under test here, so a harmless "couldn't read your data" rather than a
        // crash from being handed a shape they don't expect.
        return { ok: false, json: async () => ({}) };
      }),
    );
    renderAt('/');

    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');

    await answer(user, /what are you trying to predict/i, 'A number');
    await answer(user, /how many rows/i, '500 to 10,000');
    await answer(user, /how many columns/i, '10 to 50');
    await answer(user, /what kind of columns/i, 'Numbers');
    await answer(user, /how much of your data is missing/i, 'None');
    await answer(user, /explain individual predictions/i, 'Not important');
    await answer(user, /straight line/i, "I don't know");
    await answer(user, /only matter in combination/i, 'No');
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    await screen.findByText('Suggested method');

    await user.click(screen.getByRole('button', { name: /^edit$/i }));
    await user.click(screen.getByRole('combobox', { name: /predict/i }));
    await user.click(screen.getByRole('option', { name: 'b' }));

    expect(screen.queryByText('Suggested method')).toBeNull();
    vi.unstubAllGlobals();
  });

  it('trains against the task the recommendation actually used, not detection\'s auto-filled one', async () => {
    // "What are you trying to predict?" is auto-filled from `detection.task` but stays
    // user-editable — the auto-detected type can be wrong. Here detection says binary
    // classification, but the answer submitted (and so the recommendation computed for)
    // is regression. Training must follow what was actually asked, not `detection.task`.
    const user = userEvent.setup();
    let trainedTask: string | null = null;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url === '/api/dataset') {
          return { ok: true, json: async () => ({ columns: ['a', 'b'], rows: 5, skipped: [] }) };
        }
        if (url === '/api/dataset/detect') {
          return {
            ok: true,
            json: async () => ({
              task: 'binary classification',
              rows: '500-10k',
              features: '10-50',
              feature_types: 'numeric',
              missing: 'none',
              class_balance: 'roughly equal',
              n_rows: 5,
              n_features: 1,
              n_classes: 2,
              missing_rate: 0,
              dropped_rows: 0,
              uncertain: [],
            }),
          };
        }
        if (url === '/api/recommend') {
          return { ok: true, json: async () => recommendation() };
        }
        if (url === '/api/train' && init?.method === 'POST') {
          trainedTask = (init.body as FormData).get('task') as string;
          return { ok: true, json: async () => ({ job_id: 'job-1' }) };
        }
        if (url.startsWith('/api/train/')) {
          return {
            ok: true,
            json: async () => ({
              id: 'job-1',
              methods: ['random_forest'],
              budget_seconds: 60,
              current: null,
              halted_early: false,
              aborted: false,
              abort_detail: null,
              done: true,
              results: {},
            }),
          };
        }
        return { ok: false, json: async () => ({}) };
      }),
    );
    renderAt('/');

    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');

    // Training needs a target column, not just an answered form — picking one is what
    // fires `onDetected` and fills `detection` (task: binary classification here).
    await user.click(screen.getByRole('combobox', { name: /predict/i }));
    await user.click(screen.getByRole('option', { name: 'a' }));

    // Overrides the auto-filled "One of two categories" away to "A number".
    await answer(user, /what are you trying to predict/i, 'A number');
    await answer(user, /how many rows/i, '500 to 10,000');
    await answer(user, /how many columns/i, '10 to 50');
    await answer(user, /what kind of columns/i, 'Numbers');
    await answer(user, /how much of your data is missing/i, 'None');
    await answer(user, /explain individual predictions/i, 'Not important');
    await answer(user, /straight line/i, "I don't know");
    await answer(user, /only matter in combination/i, 'No');
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    await screen.findByText('Suggested method');

    await user.click(screen.getByRole('button', { name: /train these methods/i }));
    await waitFor(() => expect(trainedTask).toBe('regression'));

    vi.unstubAllGlobals();
  });
});

describe('the form summary bar', () => {
  function stubFetch() {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => recommendation() }),
    );
  }

  async function getRecommendation(user: ReturnType<typeof userEvent.setup>) {
    await answer(user, /what are you trying to predict/i, 'A number');
    await answer(user, /how many rows/i, '500 to 10,000');
    await answer(user, /how many columns/i, '10 to 50');
    await answer(user, /what kind of columns/i, 'Numbers');
    await answer(user, /how much of your data is missing/i, 'None');
    await answer(user, /explain individual predictions/i, 'Not important');
    await answer(user, /straight line/i, "I don't know");
    await answer(user, /only matter in combination/i, 'No');
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    await screen.findByText('Suggested method');
  }

  it('replaces the expanded form with a one-line summary once a recommendation exists', async () => {
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    expect(screen.getByLabelText(/upload a csv/i)).toBeInTheDocument();

    await getRecommendation(user);

    expect(screen.queryByRole('radiogroup')).toBeNull();
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('says the form is collapsed, not a dump of the raw answers', async () => {
    // Nine bare values with no question beside them read as noise, not as a summary —
    // confirmed against the actual thing once it was on screen.
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    await getRecommendation(user);

    expect(screen.getByText('Your answers')).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('re-expands the form on Edit, with the results still showing below', async () => {
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    await getRecommendation(user);

    await user.click(screen.getByRole('button', { name: /^edit$/i }));

    expect(screen.getByLabelText(/upload a csv/i)).toBeInTheDocument();
    expect(screen.getByText('Suggested method')).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('moves focus to the first field on Edit', async () => {
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    await getRecommendation(user);

    await user.click(screen.getByRole('button', { name: /^edit$/i }));

    expect(screen.getAllByRole('radio')[0]).toHaveFocus();
    vi.unstubAllGlobals();
  });

  it('collapses again on Done, without submitting', async () => {
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    await getRecommendation(user);
    await user.click(screen.getByRole('button', { name: /^edit$/i }));

    await user.click(screen.getByRole('button', { name: /^done$/i }));

    expect(screen.queryByRole('radiogroup')).toBeNull();
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('collapses automatically on the next Get Recommendation, without a separate Done click', async () => {
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    await getRecommendation(user);
    await user.click(screen.getByRole('button', { name: /^edit$/i }));

    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    await screen.findByRole('button', { name: /^edit$/i });

    expect(screen.queryByRole('radiogroup')).toBeNull();
    vi.unstubAllGlobals();
  });

  it('moves focus to the recommendation heading on a successful run', async () => {
    stubFetch();
    const user = userEvent.setup();
    renderAt('/');
    await getRecommendation(user);

    expect(screen.getByRole('heading', { level: 2, name: 'Random Forest' })).toHaveFocus();
    vi.unstubAllGlobals();
  });
});

/** Answer a question by its visible label — mirrors `ProblemForm.test.tsx`'s own helper. */
async function answer(user: ReturnType<typeof userEvent.setup>, group: RegExp, option: string) {
  const fieldset = screen.getByRole('radiogroup', { name: group });
  await user.click(within(fieldset).getByRole('radio', { name: option }));
}

/** A minimal but shape-complete `/api/recommend` response. */
function recommendation() {
  const suggestion = (overrides: Record<string, unknown> = {}) => ({
    method: 'random_forest',
    label: 'Random Forest',
    flexibility: { label: 'flexible', detail: 'splits the data repeatedly' },
    interpretability: { label: 'opaque', detail: 'no single reason to give for one answer' },
    expected_shortfall: 0.02,
    uncertainty: 0.005,
    reasons: [],
    factors: [],
    characteristics: null,
    excluded_by_constraint: false,
    ...overrides,
  });
  return {
    recommended: suggestion(),
    alternatives: [],
    excluded: [],
    checkpoints: [],
    support: { field: 'rows', answer: '500-10k', datasets: 30, total: 106 },
    provisional: false,
  };
}
