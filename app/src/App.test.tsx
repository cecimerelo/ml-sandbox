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
  it('is marked as the current page on its own surface', () => {
    renderAt('/benchmark');
    expect(screen.getByRole('link', { name: 'Benchmark' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  it('is not marked current from the dashboard', () => {
    // Announcing it as current elsewhere would tell a screen-reader user they are already
    // where the link goes.
    renderAt('/');
    expect(screen.getByRole('link', { name: 'Benchmark' })).not.toHaveAttribute('aria-current');
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

  it.each(['/', '/benchmark'])('the privacy link is reachable from %s', (path) => {
    // Persistent on both surfaces per the spine. Added late, this is the kind of element
    // that lands on one surface and not the other.
    renderAt(path);
    expect(screen.getByRole('link', { name: /privacy notice/i })).toBeInTheDocument();
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
