import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Flowchart } from './Flowchart';
import { theme } from '../theme/theme';
import type { DecisionFactor } from './types';

function factor(overrides: Partial<DecisionFactor> = {}): DecisionFactor {
  return {
    question: 'how many rows',
    answer: 'fewer than 500',
    claim: 'With few observations, flexible methods fit noise instead of pattern.',
    over: null,
    ...overrides,
  };
}

function show(factors: DecisionFactor[]) {
  render(
    <ThemeProvider theme={theme}>
      <Flowchart method="Lasso" factors={factors} />
    </ThemeProvider>,
  );
}

describe('the traversed path', () => {
  it('shows one step per factor, in order, ending in the recommended method', () => {
    show([
      factor({ question: 'how many rows', answer: 'fewer than 500' }),
      factor({ question: 'explaining individual predictions', answer: 'critical' }),
    ]);
    const steps = screen.getAllByText(/^[0-9]$/);
    expect(steps).toHaveLength(3); // two factors plus the terminal node
    expect(screen.getByText('Lasso')).toBeInTheDocument();
    expect(screen.getByText('recommended')).toBeInTheDocument();
  });

  it('names the question and the answer that fired it', () => {
    show([factor({ question: 'how many rows', answer: 'fewer than 500' })]);
    expect(screen.getByText('how many rows')).toBeInTheDocument();
    expect(screen.getByText('fewer than 500')).toBeInTheDocument();
  });

  it('shows the claim the answer argued for', () => {
    show([factor()]);
    expect(screen.getByText(/fit noise instead of pattern/i)).toBeInTheDocument();
  });

  it('names the method a step displaced, when there was one', () => {
    show([factor({ over: 'Random Forest' })]);
    expect(screen.getByText(/ruled out Random Forest here/i)).toBeInTheDocument();
  });

  it('says nothing about displacement when nothing was displaced', () => {
    show([factor({ over: null })]);
    expect(screen.queryByText(/ruled out/i)).toBeNull();
  });
});

describe('no factors fired', () => {
  it('says plainly that the method won on general performance, not on the user\'s answers', () => {
    show([]);
    expect(screen.getByText(/nothing about your answers pushed/i)).toBeInTheDocument();
    expect(screen.getByText(/Lasso is simply/i)).toBeInTheDocument();
  });
});

describe('what this does not claim to be', () => {
  it('never mentions an untaken branch, since the engine does not compute one', () => {
    // The spec's binary-tree flowchart shows both sides of every split. This renders only
    // the side that fired; asserting the panel never claims otherwise guards against a
    // future edit quietly inventing the other half.
    show([factor({ question: 'how many rows', answer: 'fewer than 500' })]);
    expect(screen.queryByText(/otherwise|had you said|if you had answered/i)).toBeNull();
  });
});
