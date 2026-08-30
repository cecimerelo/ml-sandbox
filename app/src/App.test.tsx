/**
 * The shell's accessibility criteria, checked by rendering rather than by reading.
 *
 * #32 requires a specific focus order and a specific ARIA state. Both are properties of
 * the rendered output, and both survive a plausible refactor that breaks them — reordering
 * JSX, or wrapping the title in a layout element. Reading the source to confirm them is
 * the kind of verification that passes right up until it matters.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { App } from './App';
import { theme } from './theme/theme';

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
  it.each(['/', '/benchmark'])('is not offered on %s yet', (path) => {
    // Built and tested, and deliberately not shown: accepting a file does not yet change
    // anything a user would see. A control that takes someone's data and gives nothing
    // back is worse than one that is missing — it implies the file is being used.
    //
    // The same judgement as the Benchmark link and the privacy notice. This test is what
    // makes the omission deliberate rather than something that quietly stayed missing.
    renderAt(path);
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
