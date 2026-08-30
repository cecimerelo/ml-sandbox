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

const UNUSABLE = [
  { column: 'listed_on', reason: 'date' as const, message: "Dates aren't supported yet." },
  {
    column: 'agent_note',
    reason: 'free-text' as const,
    message: 'Almost every row here is different.',
  },
];

function setup(columns = ['size_m2', 'city', 'price'], unusable = UNUSABLE) {
  const onDetected = vi.fn();
  render(
    <ThemeProvider theme={theme}>
      <DatasetPanel
        file={new File(['a,b\n1,2\n'], 'houses.csv', { type: 'text/csv' })}
        columns={columns}
        unusable={unusable}
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

  it('offers every usable column', async () => {
    const { user } = setup(['a', 'b', 'c'], []);
    await user.click(screen.getByRole('combobox', { name: /predict/i }));
    expect(await screen.findAllByRole('option')).toHaveLength(3);
  });

  it('reads nothing until one is chosen', () => {
    const fetched = vi.fn();
    vi.stubGlobal('fetch', fetched);
    setup();
    expect(fetched).not.toHaveBeenCalled();
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

  it('reports nothing readable upward', async () => {
    // `null` rather than nothing: the previous reading has to be cleared, or the form
    // keeps showing properties of a target the user has moved on from.
    respond(422, { detail: { reason: 'single-value', message: 'nothing to predict' } });
    const { onDetected, user } = setup();
    await pick(user, 'city');
    await screen.findByRole('alert');
    expect(onDetected).toHaveBeenCalledWith(null);
    expect(onDetected).not.toHaveBeenCalledWith(expect.objectContaining({ n_rows: 388 }));
  });

  it('lets the user pick another column', async () => {
    respond(422, { detail: { reason: 'identifier', message: 'looks like an identifier' } });
    const { user } = setup();
    await pick(user, 'city');
    await screen.findByRole('alert');

    respond(200, DETECTION);
    await pick(user, 'price');
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
  });
});

describe('what it reports', () => {
  it('hands the reading to the form rather than showing it itself', async () => {
    // A second block showing the same six answers put two controls for each on the page,
    // and left the user to work out which one counted.
    respond(200, DETECTION);
    const { onDetected, user } = setup();
    await pick(user, 'price');
    await waitFor(() =>
      expect(onDetected).toHaveBeenCalledWith(expect.objectContaining({ task: 'regression' })),
    );
    expect(screen.queryByText(/388 rows/)).toBeNull();
  });
});

describe('columns that cannot be predicted', () => {
  it('are shown disabled rather than hidden', async () => {
    // The same rule FR-8.3 sets for methods that do not apply. A column that is simply
    // absent leaves someone scrolling for it and wondering whether they uploaded the right
    // file.
    const { user } = setup();
    await user.click(screen.getByRole('combobox', { name: /predict/i }));

    const listed = await screen.findByRole('option', { name: /listed_on/ });
    expect(listed).toHaveAttribute('aria-disabled', 'true');
  });

  it('say why, beside the column', async () => {
    // The reason is the point. Greying it out without one teaches nothing and invites the
    // user to assume the file was read wrongly.
    const { user } = setup();
    await user.click(screen.getByRole('combobox', { name: /predict/i }));
    expect(await screen.findByText(/dates aren't supported yet/i)).toBeInTheDocument();
    expect(screen.getByText(/almost every row here is different/i)).toBeInTheDocument();
  });

  it('cannot be chosen', async () => {
    const fetched = vi.fn();
    vi.stubGlobal('fetch', fetched);
    const { user } = setup();
    await user.click(screen.getByRole('combobox', { name: /predict/i }));

    // The click is refused rather than ignored: a disabled option takes no pointer events
    // at all, so there is no path from here to a request.
    await expect(
      user.click(await screen.findByRole('option', { name: /agent_note/ })),
    ).rejects.toThrow(/pointer-events/);
    expect(fetched).not.toHaveBeenCalled();
  });

  it('sit after the usable ones', async () => {
    // A list that opens on greyed-out entries reads as broken.
    const { user } = setup();
    await user.click(screen.getByRole('combobox', { name: /predict/i }));
    const options = await screen.findAllByRole('option');
    expect(options[0]).toHaveTextContent('size_m2');
    expect(options.at(-1)).toHaveTextContent('agent_note');
  });
});
