/**
 * Choosing an outcome and confirming what the file said.
 *
 * The failure this guards is not visible: a detector that reports confidently about a
 * column nobody should be predicting produces a model, a score, and no sign anything went
 * wrong.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { DatasetPanel } from './DatasetPanel';
import { theme } from '../theme/theme';

const DETECTION = {
  task: 'regression',
  rows: '<500',
  features: '<10',
  feature_types: 'mixed',
  missing: 'none',
  class_balance: 'not applicable',
  n_rows: 388,
  n_features: 4,
  n_classes: null,
  missing_rate: 0,
  dropped_rows: 12,
  uncertain: [],
};

function setup(columns = ['size_m2', 'city', 'price']) {
  const onDetected = vi.fn();
  render(
    <ThemeProvider theme={theme}>
      <DatasetPanel
        file={new File(['a,b\n1,2\n'], 'houses.csv', { type: 'text/csv' })}
        columns={columns}
        onDetected={onDetected}
      />
    </ThemeProvider>,
  );
  return { onDetected, user: userEvent.setup() };
}

function respond(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: status < 400, json: async () => body }),
  );
}

async function pick(user: ReturnType<typeof userEvent.setup>, column: string) {
  await user.click(screen.getByRole('combobox', { name: /what are you trying to predict/i }));
  await user.click(await screen.findByRole('option', { name: column }));
}

afterEach(() => vi.unstubAllGlobals());

describe('the target', () => {
  it('has no default', async () => {
    // The study itself guessed at this — it took the last column — and was wrong on five
    // of forty datasets, training models to predict the day of the month from a house's
    // price. It did not error; every method just scored near zero, which reads as a hard
    // dataset (D-041). A suggested default here is that same guess with an alibi.
    setup(['size_m2', 'city', 'price']);
    const control = screen.getByRole('combobox', { name: /predict/i });
    // Checked against the column names rather than for emptiness: MUI renders a
    // zero-width placeholder, and what matters is that no column is standing in for an
    // answer nobody gave.
    for (const column of ['size_m2', 'city', 'price']) {
      expect(control).not.toHaveTextContent(column);
    }
  });

  it('offers every column', async () => {
    const { user } = setup(['a', 'b', 'c']);
    await user.click(screen.getByRole('combobox', { name: /predict/i }));
    expect(await screen.findAllByRole('option')).toHaveLength(3);
  });

  it('shows nothing below it until one is chosen', () => {
    setup();
    expect(screen.queryByText(/how many rows/i)).toBeNull();
  });
});

describe('a target that cannot be predicted', () => {
  it('says so, naming the column', async () => {
    respond(422, {
      detail: {
        reason: 'identifier',
        message: '`invoice` has a different value in almost every row.',
      },
    });
    const { user } = setup(['invoice', 'price']);
    await pick(user, 'invoice');
    expect(await screen.findByRole('alert')).toHaveTextContent(/invoice/);
  });

  it('reads nothing from the file', async () => {
    respond(422, { detail: { reason: 'single-value', message: 'nothing to predict' } });
    const { onDetected, user } = setup();
    await pick(user, 'city');
    await screen.findByRole('alert');
    expect(onDetected).not.toHaveBeenCalled();
    expect(screen.queryByText(/how many rows/i)).toBeNull();
  });

  it('lets the user pick another column', async () => {
    respond(422, { detail: { reason: 'identifier', message: 'looks like an identifier' } });
    const { user } = setup();
    await pick(user, 'city');
    await screen.findByRole('alert');

    respond(200, DETECTION);
    await pick(user, 'price');
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
    expect(screen.getByText(/388 rows/)).toBeInTheDocument();
  });
});

describe('what the file said', () => {
  it('shows the exact count beside its band', async () => {
    // Both, because they answer different questions: the count lets a user check the
    // reading against their file, the band is what the engine consumes.
    respond(200, DETECTION);
    const { user } = setup();
    await pick(user, 'price');
    expect(await screen.findByText(/388 rows · <500/)).toBeInTheDocument();
  });

  it('explains rows that were left out rather than hiding them', async () => {
    // A row count that still included them would describe a dataset that will not be used.
    respond(200, DETECTION);
    const { user } = setup();
    await pick(user, 'price');
    expect(await screen.findByText(/12 rows left out/i)).toBeInTheDocument();
  });

  it('says nothing about dropped rows when none were', async () => {
    respond(200, { ...DETECTION, dropped_rows: 0 });
    const { user } = setup();
    await pick(user, 'price');
    await screen.findByText(/388 rows/);
    expect(screen.queryByText(/left out/i)).toBeNull();
  });

  it('reports what was read upward', async () => {
    respond(200, DETECTION);
    const { onDetected, user } = setup();
    await pick(user, 'price');
    await waitFor(() => expect(onDetected).toHaveBeenCalled());
    expect(onDetected.mock.calls[0]?.[1]).toMatchObject({ task: 'regression' });
  });
});

describe('a reading the file does not settle', () => {
  it('flags the field, not the page', async () => {
    // "Some of this might be wrong" tells a reader to re-check everything, which gets
    // re-checked by nobody. Naming the field turns a warning into a task with an end.
    respond(200, { ...DETECTION, uncertain: ['task'] });
    const { user } = setup();
    await pick(user, 'price');
    expect(await screen.findByText(/we're not sure about this one/i)).toBeInTheDocument();
  });

  it('does not rely on colour alone', async () => {
    respond(200, { ...DETECTION, uncertain: ['task'] });
    const { user } = setup();
    await pick(user, 'price');
    // The words carry the same meaning as the amber, so the flag survives being unable to
    // see the difference.
    expect(await screen.findByText(/please check it/i)).toBeInTheDocument();
  });

  it('clears only when the user says so', async () => {
    // A warning that clears itself has been accepted on the user's behalf, which is the
    // outcome FR-8.2 exists to prevent.
    respond(200, { ...DETECTION, uncertain: ['task'] });
    const { user } = setup();
    await pick(user, 'price');
    await screen.findByText(/we're not sure/i);

    await user.click(screen.getByRole('button', { name: /looks right/i }));
    expect(screen.queryByText(/we're not sure/i)).toBeNull();
  });

  it('leaves confident readings unflagged', async () => {
    respond(200, DETECTION);
    const { user } = setup();
    await pick(user, 'price');
    await screen.findByText(/388 rows/);
    expect(screen.queryByText(/we're not sure/i)).toBeNull();
  });
});

describe('the counts', () => {
  it('are not offered as something to disagree with', async () => {
    // A person cannot meaningfully disagree that their file has 388 rows, and offering
    // them the chance implies the reading is a matter of taste.
    respond(200, DETECTION);
    const { user } = setup();
    await pick(user, 'price');
    await screen.findByText(/388 rows/);
    const groups = screen.queryAllByRole('radiogroup');
    expect(groups.length).toBeGreaterThan(0);
    for (const group of groups) {
      expect(group).not.toHaveAccessibleName(/how many rows/i);
    }
  });
});

describe('where a value came from', () => {
  it('marks a detected reading with words as well as colour', async () => {
    // Colour alone says nothing to a reader who cannot see the difference. The caption
    // carries the meaning; the colour only makes it quicker to find.
    respond(200, DETECTION);
    const { user } = setup();
    await pick(user, 'price');
    expect(await screen.findAllByText(/detected from your file/i)).not.toHaveLength(0);
  });

  it('does not mark a fact about the file as a detection', async () => {
    // A row count is not a reading that could have gone another way, so it is not
    // presented as one.
    respond(200, DETECTION);
    const { user } = setup();
    await pick(user, 'price');
    const rows = await screen.findByText(/388 rows · <500/);
    expect(rows).not.toHaveTextContent(/detected/i);
  });
});
