/**
 * The shell's accessibility criteria, checked by rendering rather than by reading.
 *
 * #32 requires a specific focus order and a specific ARIA state. Both are properties of
 * the rendered output, and both survive a plausible refactor that breaks them — reordering
 * JSX, or wrapping the title in a layout element. Reading the source to confirm them is
 * the kind of verification that passes right up until it matters.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, within } from '@testing-library/react';
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

  it('keeps the answers the user gave themselves', async () => {
    // Explainability, non-linearity and interactions were never the file's to fill in, and
    // removing a CSV is no reason to make someone say again what they need.
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

    await user.upload(screen.getByLabelText(/upload a csv/i), file('good.csv'));
    await screen.findByText('good.csv');
    await user.click(screen.getByRole('button', { name: /^remove$/i }));

    expect(screen.queryByText('Suggested method')).toBeNull();
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
