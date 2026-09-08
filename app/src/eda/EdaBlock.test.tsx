/**
 * Block 3 — collapsed by default, paginated, and never asking for more than the current
 * page's worth of distributions.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EdaBlock } from './EdaBlock';
import { theme } from '../theme/theme';

function histogram(column: string) {
  return {
    column,
    kind: 'numeric',
    bins: [{ start: 0, end: 10, count: 5 }],
    missing: 0,
  };
}

function inventoryOf(columns: string[]) {
  return {
    columns: columns.map((column) => ({ column, kind: 'numeric' })),
    total: columns.length,
  };
}

function stubFetch({
  total = 3,
  requestedColumns = [] as string[],
}: { total?: number; requestedColumns?: string[] } = {}) {
  const columns = Array.from({ length: total }, (_, i) => `feature-${i}`);
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      if (url === '/api/dataset/eda/columns') {
        return { ok: true, json: async () => inventoryOf(columns) };
      }
      if (url === '/api/dataset/eda/correlation') {
        return { ok: true, json: async () => ({ features: [], values: [], total_numeric: 0 }) };
      }
      const body = init?.body as FormData;
      const requested = body.getAll('columns') as string[];
      requestedColumns.push(...requested);
      return {
        ok: true,
        json: async () => ({
          target: histogram('price'),
          features: requested.map(histogram),
        }),
      };
    }),
  );
}

function file() {
  return new File(['a'], 'houses.csv', { type: 'text/csv' });
}

function setup() {
  return render(
    <ThemeProvider theme={theme}>
      <EdaBlock file={file()} target="price" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('the block itself', () => {
  it('is collapsed by default', () => {
    stubFetch();
    setup();
    expect(screen.getByRole('button', { name: /explore your data/i })).toHaveAttribute(
      'aria-expanded',
      'false',
    );
  });

  it('shows the target and the feature panels once expanded', async () => {
    stubFetch({ total: 2 });
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));

    expect(await screen.findByText(/price \(target\)/i)).toBeInTheDocument();
    expect(await screen.findByText('feature-0')).toBeInTheDocument();
    expect(await screen.findByText('feature-1')).toBeInTheDocument();
  });
});

describe('pagination', () => {
  it('asks for only the first page, not every feature', async () => {
    const requestedColumns: string[] = [];
    stubFetch({ total: 20, requestedColumns });
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));

    await waitFor(() => expect(requestedColumns.length).toBeGreaterThan(0));
    expect(requestedColumns).toHaveLength(12);
  });

  it('states the totals, never silently', async () => {
    stubFetch({ total: 500 });
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));

    expect(await screen.findByText(/showing 12 of 500 features/i)).toBeInTheDocument();
  });

  it('fetches the next page on Next, not the same twelve again', async () => {
    const requestedColumns: string[] = [];
    stubFetch({ total: 20, requestedColumns });
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));
    await screen.findByText(/showing 12 of 20/i);

    await user.click(screen.getByRole('button', { name: /^next$/i }));
    await waitFor(() => expect(requestedColumns).toHaveLength(20));

    const secondPage = requestedColumns.slice(12);
    expect(secondPage).toHaveLength(8);
    expect(secondPage[0]).toBe('feature-12');
  });

  it('disables Previous on the first page', async () => {
    stubFetch({ total: 20 });
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));
    await screen.findByText(/showing 12 of 20/i);

    expect(screen.getByRole('button', { name: /^previous$/i })).toBeDisabled();
  });

  it('disables Next on the last page', async () => {
    stubFetch({ total: 12 });
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));
    await screen.findByText(/showing 12 of 12/i);

    expect(screen.getByRole('button', { name: /^next$/i })).toBeDisabled();
  });
});

describe('when reading the data fails', () => {
  it('says so without pretending the block worked', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({}) }));
    const user = userEvent.setup();
    setup();
    await user.click(screen.getByRole('button', { name: /explore your data/i }));

    expect(await screen.findByText(/couldn't read your data/i)).toBeInTheDocument();
  });
});
