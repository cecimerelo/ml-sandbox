/**
 * The glossary term, and the two ways a tooltip usually fails the people it is for.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { Term } from './Term';
import { GLOSSARY } from './glossary';
import { plainText, renderCopy, termsIn } from './render';

describe('a glossed term', () => {
  it('is marked as having a definition before anyone interacts with it', () => {
    // The objection this answers: a definition behind an unmarked word only reaches a
    // reader who already suspects the word. Someone who thinks "noise" means loud sounds
    // has no reason to suspect anything, so the marking has to be visible from the start.
    render(<Term name="noise" />);
    const term = screen.getByRole('button', { name: 'noise' });
    expect(term).toBeVisible();
    expect(term).toHaveStyle({ borderBottomStyle: 'dotted' });
  });

  it('opens on keyboard focus, not only on hover', async () => {
    render(<Term name="noise" />);
    await userEvent.setup().tab();
    expect(await screen.findByRole('tooltip')).toHaveTextContent(/chance/i);
  });

  it('opens on click, so it works on a touch screen', async () => {
    render(<Term name="overfitting" />);
    await userEvent.setup().click(screen.getByRole('button', { name: 'overfitting' }));
    expect(await screen.findByRole('tooltip')).toBeInTheDocument();
  });

  it('is reachable by keyboard at all', async () => {
    render(<Term name="noise" />);
    await userEvent.setup().tab();
    expect(screen.getByRole('button', { name: 'noise' })).toHaveFocus();
  });

  it('fails loudly on a term with no definition', () => {
    // Rendering the bare word would hide the bug from everyone except whoever wrote it.
    expect(() => render(<Term name="entropy" />)).toThrow(/no glossary entry/i);
  });
});

describe('rendering catalogue copy', () => {
  it('expands a marker into a glossed term and leaves the rest as text', () => {
    render(<p>{renderCopy('methods catch {{noise}} when the data is thin')}</p>);
    expect(screen.getByRole('button', { name: 'noise' })).toBeInTheDocument();
    expect(screen.getByText(/when the data is thin/)).toBeInTheDocument();
  });

  it('reads as ordinary prose with the markers stripped', () => {
    // What a supervisor reviewing the catalogue as writing sees.
    expect(plainText('catching {{noise}} early')).toBe('catching noise early');
  });

  it('finds every marked term', () => {
    expect(termsIn('{{noise}} and {{imputation}}')).toEqual(['noise', 'imputation']);
  });

  it('leaves a string with no markers alone', () => {
    const text = 'A row is one example — one house, one patient.';
    expect(plainText(text)).toBe(text);
    expect(termsIn(text)).toEqual([]);
  });
});

describe('the definitions themselves', () => {
  it.each(Object.entries(GLOSSARY))('%s reads as a sentence, not a label', (_key, entry) => {
    expect(entry.definition.length).toBeGreaterThan(60);
    expect(entry.definition.trim()).toMatch(/\.$/);
  });
});
