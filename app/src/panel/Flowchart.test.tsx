import { ThemeProvider } from '@mui/material/styles';
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Flowchart } from './Flowchart';
import { theme } from '../theme/theme';
import type { Checkpoint } from './types';

function checkpoint(overrides: Partial<Checkpoint> = {}): Checkpoint {
  return {
    question: 'how many rows',
    answer: 'fewer than 500',
    fired: true,
    claim: 'With few observations, flexible methods fit noise instead of pattern.',
    ...overrides,
  };
}

function show(checkpoints: Checkpoint[]) {
  return render(
    <ThemeProvider theme={theme}>
      <Flowchart method="Lasso" checkpoints={checkpoints} />
    </ThemeProvider>,
  );
}

describe('the traversed path', () => {
  it('shows one step per fired checkpoint, in order, ending in the recommended method', () => {
    show([
      checkpoint({ question: 'how many rows', answer: 'fewer than 500', fired: true }),
      checkpoint({
        question: 'explaining individual predictions',
        answer: 'critical',
        fired: true,
      }),
    ]);
    const steps = screen.getAllByRole('listitem');
    expect(steps).toHaveLength(3); // two fired checkpoints plus the terminal node
    expect(screen.getByText('Lasso')).toBeInTheDocument();
    expect(screen.getByText('recommended')).toBeInTheDocument();
  });

  it('names the question and the answer that fired it', () => {
    show([checkpoint({ question: 'how many rows', answer: 'fewer than 500', fired: true })]);
    expect(screen.getByText('how many rows')).toBeInTheDocument();
    expect(screen.getByText('fewer than 500')).toBeInTheDocument();
  });

  it('shows the claim the answer argued for', () => {
    show([checkpoint()]);
    expect(screen.getByText(/fit noise instead of pattern/i)).toBeInTheDocument();
  });

  it('does not put a not-fired checkpoint on the path', () => {
    const { container } = show([
      checkpoint({ question: 'how many rows', answer: 'fewer than 500', fired: true }),
      checkpoint({ question: 'how much is missing', answer: 'none', fired: false }),
    ]);
    const steps = within(container.querySelector('ol')!).getAllByRole('listitem');
    expect(steps).toHaveLength(2); // one fired checkpoint plus the terminal node
  });
});

describe('checkpoints that did not fire', () => {
  it('lists them separately, with the question, answer, and stated reason', () => {
    show([
      checkpoint({
        question: 'how much is missing',
        answer: 'none',
        fired: false,
        claim: 'Nothing is missing, so this had no effect on the ranking.',
      }),
    ]);
    expect(screen.getByText(/what we discarded/i)).toBeInTheDocument();
    expect(screen.getByText('how much is missing')).toBeInTheDocument();
    expect(screen.getByText(/had no effect on the ranking/i)).toBeInTheDocument();
  });
});

describe('no checkpoints fired', () => {
  it("says plainly that the method won on general performance, not on the user's answers", () => {
    show([checkpoint({ fired: false })]);
    expect(screen.getByText(/none of your answers pushed this choice/i)).toBeInTheDocument();
    expect(screen.getByText(/Lasso is simply/i)).toBeInTheDocument();
  });
});

describe('what this does not claim to be', () => {
  it('never mentions an untaken branch, since the engine does not compute one', () => {
    // The spec's binary-tree flowchart shows both sides of every split. This renders only
    // the side that fired; asserting the panel never claims otherwise guards against a
    // future edit quietly inventing the other half.
    show([checkpoint({ question: 'how many rows', answer: 'fewer than 500', fired: true })]);
    expect(screen.queryByText(/otherwise|had you said|if you had answered/i)).toBeNull();
  });
});
