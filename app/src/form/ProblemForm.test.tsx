/**
 * The form's behaviours that are easy to build wrong and impossible to notice.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ProblemForm } from './ProblemForm';
import { theme } from '../theme/theme';

function setup() {
  const onSubmit = vi.fn();
  render(
    <ThemeProvider theme={theme}>
      <ProblemForm onSubmit={onSubmit} />
    </ThemeProvider>,
  );
  return { onSubmit, user: userEvent.setup() };
}

/** Answer a question by its visible label. */
async function answer(user: ReturnType<typeof userEvent.setup>, group: RegExp, option: string) {
  const fieldset = screen.getByRole('radiogroup', { name: group });
  await user.click(within(fieldset).getByRole('radio', { name: option }));
}

async function fillEverything(user: ReturnType<typeof userEvent.setup>) {
  await answer(user, /what are you trying to predict/i, 'A number');
  await answer(user, /how many rows/i, '500 to 10,000');
  await answer(user, /how many columns/i, '10 to 50');
  await answer(user, /what kind of columns/i, 'Numbers');
  await answer(user, /how much of your data is missing/i, 'None');
  await answer(user, /explain individual predictions/i, 'Not important');
  await answer(user, /straight line/i, "I don't know");
  await answer(user, /only matter in combination/i, 'No');
}

describe('the submit button', () => {
  it('is inert until every visible question is answered', async () => {
    const { user, onSubmit } = setup();
    const button = screen.getByRole('button', { name: /get recommendation/i });
    expect(button).toHaveAttribute('aria-disabled', 'true');

    await user.click(button);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('is aria-disabled rather than disabled, so it stays focusable', async () => {
    // A `disabled` button cannot be focused, so the tooltip explaining why it is inert is
    // unreachable by exactly the people who most need it.
    setup();
    const button = screen.getByRole('button', { name: /get recommendation/i });
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute('aria-disabled', 'true');
  });

  it('becomes active once nothing is left', async () => {
    const { user } = setup();
    await fillEverything(user);
    expect(screen.getByRole('button', { name: /get recommendation/i })).toHaveAttribute(
      'aria-disabled',
      'false',
    );
  });
});

describe('the class balance question', () => {
  it('is not asked when predicting a number', async () => {
    const { user } = setup();
    await answer(user, /what are you trying to predict/i, 'A number');
    expect(screen.queryByRole('radiogroup', { name: /categories about the same size/i })).toBeNull();
  });

  it('is asked when predicting categories', async () => {
    const { user } = setup();
    await answer(user, /what are you trying to predict/i, 'One of two categories');
    expect(
      screen.getByRole('radiogroup', { name: /categories about the same size/i }),
    ).toBeInTheDocument();
  });

  it('offers a long-tail answer only for several categories', async () => {
    const { user } = setup();
    await answer(user, /what are you trying to predict/i, 'One of two categories');
    expect(screen.queryByRole('radio', { name: /several categories are rare/i })).toBeNull();

    await answer(user, /what are you trying to predict/i, 'One of several categories');
    expect(screen.getByRole('radio', { name: /several categories are rare/i })).toBeInTheDocument();
  });

  it('retains the answer across a trip through regression', async () => {
    // Hiding a question must not punish the user for exploring. Clearing it would mean a
    // person who changed their mind twice has to answer it again.
    const { user } = setup();
    await answer(user, /what are you trying to predict/i, 'One of two categories');
    await answer(user, /categories about the same size/i, 'One category dominates');

    await answer(user, /what are you trying to predict/i, 'A number');
    await answer(user, /what are you trying to predict/i, 'One of two categories');

    const group = screen.getByRole('radiogroup', { name: /categories about the same size/i });
    expect(within(group).getByRole('radio', { name: 'One category dominates' })).toBeChecked();
  });

  it('does not block submission when it is not being asked', async () => {
    const { user, onSubmit } = setup();
    await fillEverything(user);
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});

describe('what gets sent', () => {
  it('reports class balance as not applicable for a number', async () => {
    // Rather than a default standing in for an answer nobody gave.
    const { user, onSubmit } = setup();
    await fillEverything(user);
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({
      task: 'regression',
      class_balance: 'not applicable',
    });
  });

  it('sends no regime — the engine derives it from the two bands', async () => {
    const { user, onSubmit } = setup();
    await fillEverything(user);
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    expect(onSubmit.mock.calls[0]?.[0]).not.toHaveProperty('regime');
  });

  it('collapses the long-tail answer onto the engine band it maps to', async () => {
    const { user, onSubmit } = setup();
    await fillEverything(user);
    await answer(user, /what are you trying to predict/i, 'One of several categories');
    await answer(user, /categories about the same size/i, 'Several categories are rare');
    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ class_balance: 'one class dominates' });
  });
});

describe('nothing happens until asked', () => {
  it('does not submit while questions are being answered', async () => {
    // FR-1.7. A page that rearranges itself mid-decision makes the answer someone was
    // about to give feel like it was already wrong.
    const { user, onSubmit } = setup();
    await fillEverything(user);
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe('the explanations', () => {
  it('are visible without being asked for', () => {
    setup();
    expect(screen.getByText(/a row is one example/i)).toBeVisible();
  });

  it('are outside the tab order', async () => {
    // A keyboard user moves field to field. Traversing prose between every control is a
    // tax on the people who can least afford one.
    const { user } = setup();
    await user.tab();
    expect(screen.getAllByRole('radio')[0]).toHaveFocus();
  });
});
