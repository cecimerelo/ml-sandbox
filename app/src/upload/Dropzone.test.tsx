/**
 * Uploading a dataset, and the ways a rejection can cost the user more than it should.
 */

import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

describe('an unreachable server', () => {
  it('does not blame the file', async () => {
    // This is not hypothetical: the first real use of this control ran against a stale
    // dev server whose proxy was gone, and every file — all of them valid — was reported
    // as unreadable. That sends someone to inspect data that is perfectly fine.
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/couldn't reach the server/i);
    expect(alert).not.toHaveTextContent(/that file/i);
  });

  it('says the file has not been looked at yet', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    expect(await screen.findByRole('alert')).toHaveTextContent(/haven't looked at your file/i);
  });

  it('treats a non-JSON response the same way', async () => {
    // The dev server's HTML fallback answers with 200 and a page. That is not this
    // endpoint replying, and reading it as a verdict on the file would be a fiction.
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => {
          throw new SyntaxError('Unexpected token <');
        },
      }),
    );
    const { onAccepted, user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't reach the server/i);
    expect(onAccepted).not.toHaveBeenCalled();
  });

  it('does not invent a reason when a refusal carries no message', async () => {
    respond(422, {});
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv());
    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't reach the server/i);
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

describe('a failure after a success', () => {
  it('does not leave the earlier summary on screen', async () => {
    // Two alerts at once, one saying the file was read and one saying it was refused, is
    // the interface contradicting itself. The user cannot tell which is about the file
    // they just dropped.
    respond(200, { columns: ['a', 'b'], rows: 200, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('good.csv'));
    expect(await screen.findByRole('alert')).toHaveTextContent(/200 rows/i);

    respond(422, { detail: { reason: 'no-rows', message: 'This file has a header row but no data.' } });
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('bad.csv'));

    const alerts = await screen.findAllByRole('alert');
    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toHaveTextContent(/no data/i);
    expect(alerts[0]).not.toHaveTextContent(/200 rows/i);
  });

  it('clears the error once a later file is accepted', async () => {
    respond(422, { detail: { reason: 'no-rows', message: 'no data' } });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('bad.csv'));
    await screen.findByRole('alert');

    respond(200, { columns: ['a', 'b'], rows: 7, skipped: [] });
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('good.csv'));

    const alerts = await screen.findAllByRole('alert');
    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toHaveTextContent(/7 rows/i);
  });
});

describe('the zone after a file is accepted', () => {
  it('shows the file name, not the invitation to drop one', async () => {
    // Left unchanged, a control that has just taken someone's file still reads as empty,
    // and the only confirmation is a sentence below it — easy to miss, and easy to
    // mistake for being about a previous attempt.
    respond(200, { columns: ['a', 'b'], rows: 12, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('houses.csv'));

    expect(await screen.findByText('houses.csv')).toBeInTheDocument();
    expect(screen.queryByText(/drop a csv here/i)).toBeNull();
  });

  it('says "loaded" as well as showing a tick', async () => {
    // The word carries the same meaning as the icon, so a reader who cannot see colour or
    // the glyph is not left guessing.
    respond(200, { columns: ['a'], rows: 3, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('houses.csv'));
    expect(await screen.findByText(/loaded/i)).toBeInTheDocument();
  });

  it('offers a different file rather than the same invitation', async () => {
    respond(200, { columns: ['a'], rows: 3, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('houses.csv'));
    expect(await screen.findByRole('button', { name: /choose a different file/i })).toBeInTheDocument();
  });

  it('drops the name as soon as another file is tried', async () => {
    // Leaving the previous name up while a new one is read says the wrong file was taken.
    respond(200, { columns: ['a'], rows: 3, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('first.csv'));
    await screen.findByText('first.csv');

    respond(422, { detail: { reason: 'no-rows', message: 'no data' } });
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('second.csv'));

    await screen.findByRole('alert');
    expect(screen.queryByText('first.csv')).toBeNull();
    expect(screen.getByText(/drop a csv here/i)).toBeInTheDocument();
  });
});

/**
 * Only reachable by dragging: the input has no `multiple`, so the file dialog cannot hand
 * over two. That is exactly why it is easy to miss — the path the tests exercise most is
 * the one that cannot reach it.
 */
function drop(files: File[]) {
  fireEvent.drop(screen.getByText(/drop a csv here|loaded/i).closest('div')!, {
    dataTransfer: { files },
  });
}

describe('more than one file at once', () => {
  it('refuses instead of silently taking the first', async () => {
    // The tempting version takes files[0] and drops the rest. It is silent: the user sees
    // one file accepted, cannot tell which, and never learns the others were discarded.
    const fetched = vi.fn();
    vi.stubGlobal('fetch', fetched);

    setup();
    drop([csv('a.csv'), csv('b.csv')]);

    expect(await screen.findByRole('alert')).toHaveTextContent(/one file at a time/i);
    expect(fetched).not.toHaveBeenCalled();
  });

  it('does not report either file as accepted', async () => {
    vi.stubGlobal('fetch', vi.fn());
    const { onAccepted } = setup();
    drop([csv('a.csv'), csv('b.csv')]);
    await screen.findByRole('alert');
    expect(onAccepted).not.toHaveBeenCalled();
  });

  it('clears a file that had already been accepted', async () => {
    // Otherwise the zone shows the old file as loaded beside an error about the new drop,
    // and the two cannot be told apart.
    respond(200, { columns: ['a'], rows: 3, skipped: [] });
    const { user } = setup();
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('first.csv'));
    await screen.findByText('first.csv');

    drop([csv('a.csv'), csv('b.csv')]);
    expect(await screen.findByRole('alert')).toHaveTextContent(/one file at a time/i);
    expect(screen.queryByText('first.csv')).toBeNull();
  });

  it('recovers when a single file is dropped next', async () => {
    vi.stubGlobal('fetch', vi.fn());
    const { user } = setup();
    drop([csv('a.csv'), csv('b.csv')]);
    await screen.findByRole('alert');

    respond(200, { columns: ['a', 'b'], rows: 9, skipped: [] });
    await user.upload(screen.getByLabelText(/upload a csv/i), csv('good.csv'));

    const alerts = await screen.findAllByRole('alert');
    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toHaveTextContent(/9 rows/i);
  });

  it('takes a single dropped file normally', async () => {
    respond(200, { columns: ['a', 'b'], rows: 5, skipped: [] });
    setup();
    drop([csv('one.csv')]);
    expect(await screen.findByRole('alert')).toHaveTextContent(/5 rows/i);
  });
});
