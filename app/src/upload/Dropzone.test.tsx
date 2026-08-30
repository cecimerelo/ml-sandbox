/**
 * Uploading a dataset, and the ways a rejection can cost the user more than it should.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Dropzone } from './Dropzone';
import { MAX_BYTES } from './limits';
import { theme } from '../theme/theme';

function setup() {
  const onAccepted = vi.fn();
  render(
    <ThemeProvider theme={theme}>
      <Dropzone onAccepted={onAccepted} />
    </ThemeProvider>,
  );
  return { onAccepted, user: userEvent.setup() };
}

function csv(name = 'data.csv', size?: number): File {
  const file = new File(['a,b\n1,2\n'], name, { type: 'text/csv' });
  if (size !== undefined) Object.defineProperty(file, 'size', { value: size });
  return file;
}

function respond(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: status < 400, json: async () => body }),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('an oversized file', () => {
  it('is refused without being uploaded', async () => {
    // The whole point of a client-side check: a check that happens after the upload has
    // happened is not this check.
    const fetched = vi.fn();
    vi.stubGlobal('fetch', fetched);

    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('big.csv', MAX_BYTES + 1));

    expect(fetched).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent(/the limit is 50 mb/i);
  });

  it('names the actual size, not only the limit', async () => {
    vi.stubGlobal('fetch', vi.fn());
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('big.csv', 84 * 1024 * 1024));
    expect(await screen.findByRole('alert')).toHaveTextContent(/84 mb/i);
  });
});

describe('a file the server refuses', () => {
  it('shows the server’s message rather than a generic one', async () => {
    respond(422, { detail: { reason: 'not-a-csv', message: "This file isn't a CSV we can read." } });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('photo.png'));
    expect(await screen.findByRole('alert')).toHaveTextContent(/isn't a csv/i);
  });

  it('leaves the dropzone open', async () => {
    // Someone who dropped the wrong file has not withdrawn anything. Closing the control
    // they need to use next would make a mis-click expensive.
    respond(422, { detail: { reason: 'no-rows', message: 'This file has a header row but no data.' } });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    await screen.findByRole('alert');
    expect(screen.getByLabelText(/upload a csv/i)).toBeInTheDocument();
  });

  it('does not report the file as accepted', async () => {
    respond(422, { detail: { reason: 'not-a-csv', message: 'no' } });
    const { onAccepted, user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    await screen.findByRole('alert');
    expect(onAccepted).not.toHaveBeenCalled();
  });
});

describe('a file the server accepts', () => {
  it('reports it upward with the file itself', async () => {
    // The browser keeps the only copy: the server drops it when the request ends, so the
    // next call that needs the data sends it again.
    const summary = { columns: ['a', 'b'], rows: 2, skipped: [] };
    respond(200, summary);
    const { onAccepted, user } = setup();
    const file = csv();
    await user.upload(screen.getByLabelText(/upload a csv/i), file);
    await waitFor(() => expect(onAccepted).toHaveBeenCalledWith(file, summary));
  });

  it('says how much of the file can be used', async () => {
    respond(200, { columns: ['a', 'b'], rows: 1234, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    expect(await screen.findByRole('alert')).toHaveTextContent(/1,234 rows, 2 usable columns/i);
  });

  it('says how many columns were skipped, and can name them', async () => {
    // A user with forty skipped columns needs to know it happened, not to read forty
    // names — but they must be able to.
    respond(200, { columns: ['a'], rows: 5, skipped: ['when', 'notes'] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/2 columns skipped/i);
    expect(screen.getByText(/2 columns skipped/i)).toBeInTheDocument();
  });

  it('says nothing about skipping when nothing was skipped', async () => {
    respond(200, { columns: ['a', 'b'], rows: 2, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    expect(await screen.findByRole('alert')).not.toHaveTextContent(/skipped/i);
  });
});

describe('a network failure', () => {
  it('is a message, not a blank screen', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't read that file/i);
  });
});

describe('the control', () => {
  it('is reachable without a mouse', async () => {
    setup();
    expect(screen.getByLabelText(/upload a csv/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose a file/i })).toBeInTheDocument();
  });

  it('says the dataset is optional', () => {
    // Advice-only is the product, not a fallback. The control must not imply otherwise.
    setup();
    expect(screen.getByText(/without one/i)).toBeInTheDocument();
  });
});
