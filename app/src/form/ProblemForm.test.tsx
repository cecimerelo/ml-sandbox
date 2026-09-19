/**
 * The form's behaviours that are easy to build wrong and impossible to notice.
 */

import { ThemeProvider } from '@mui/material/styles';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ProblemForm } from './ProblemForm';
import { theme } from '../theme/theme';
import type { Detection } from '../detect/types';

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

describe('the onChange callback', () => {
  it('fires on every answer, so a stale recommendation can be flagged elsewhere', async () => {
    const onSubmit = vi.fn();
    const onChange = vi.fn();
    render(
      <ThemeProvider theme={theme}>
        <ProblemForm onSubmit={onSubmit} onChange={onChange} />
      </ThemeProvider>,
    );
    const user = userEvent.setup();
    await answer(user, /what are you trying to predict/i, 'A number');
    expect(onChange).toHaveBeenCalledTimes(1);
    await answer(user, /how many rows/i, '500 to 10,000');
    expect(onChange).toHaveBeenCalledTimes(2);
  });

  it('never recomputes the recommendation itself — only onSubmit does that', async () => {
    const onSubmit = vi.fn();
    const onChange = vi.fn();
    render(
      <ThemeProvider theme={theme}>
        <ProblemForm onSubmit={onSubmit} onChange={onChange} />
      </ThemeProvider>,
    );
    const user = userEvent.setup();
    await answer(user, /what are you trying to predict/i, 'A number');
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

const DETECTION = {
  target: 'price',
  task: 'regression' as const,
  rows: '500-10k' as const,
  features: '10-50' as const,
  feature_types: 'mixed' as const,
  missing: 'some' as const,
  class_balance: 'not applicable' as const,
  n_rows: 8412,
  n_features: 21,
  n_classes: null,
  missing_rate: 0.032,
  dropped_rows: 0,
  uncertain: [] as string[],
};

function withDetection(detection = DETECTION) {
  const onSubmit = vi.fn();
  render(
    <ThemeProvider theme={theme}>
      <ProblemForm onSubmit={onSubmit} detection={detection} />
    </ThemeProvider>,
  );
  return { onSubmit, user: userEvent.setup() };
}

describe('when a file has been read', () => {
  it('fills the questions that already exist rather than adding new ones', async () => {
    // The readings used to render as their own block, which put two controls for each
    // question on the page and left the user to work out which one counted.
    withDetection();
    const groups = screen.getAllByRole('radiogroup');
    expect(groups).toHaveLength(8);

    const kind = screen.getByRole('radiogroup', { name: /what are you trying to predict/i });
    expect(within(kind).getByRole('radio', { name: 'A number' })).toBeChecked();
  });

  it('says what the file said, beside the question it answers', async () => {
    withDetection();
    expect(screen.getByText(/8,412 rows in your file/)).toBeInTheDocument();
    expect(screen.getByText(/21 columns in your file/)).toBeInTheDocument();
    expect(screen.getByText(/3\.2% of cells are blank/)).toBeInTheDocument();
  });

  it('leaves the questions the file cannot answer alone', async () => {
    // Explainability, non-linearity and interactions are about what the user needs and
    // believes. A file has nothing to say about either.
    withDetection();
    for (const group of [/explain individual predictions/i, /straight line/i, /combination/i]) {
      const control = screen.getByRole('radiogroup', { name: group });
      for (const radio of within(control).getAllByRole('radio')) {
        expect(radio).not.toBeChecked();
      }
    }
  });

  it('is still answerable by hand — a detection is a starting point, not a verdict', async () => {
    const { user } = withDetection();
    const kind = screen.getByRole('radiogroup', { name: /what are you trying to predict/i });
    await user.click(within(kind).getByRole('radio', { name: 'One of two categories' }));
    expect(within(kind).getByRole('radio', { name: 'One of two categories' })).toBeChecked();
  });

  it('flags a reading the file did not settle', async () => {
    withDetection({ ...DETECTION, uncertain: ['task'] });
    expect(screen.getByText(/we're not sure about this one/i)).toBeInTheDocument();
  });

  it('clears the flag when the user edits the answer', async () => {
    // Editing is itself a confirmation: they have looked at it.
    const { user } = withDetection({ ...DETECTION, uncertain: ['task'] });
    const kind = screen.getByRole('radiogroup', { name: /what are you trying to predict/i });
    await user.click(within(kind).getByRole('radio', { name: 'One of two categories' }));
    expect(screen.queryByText(/we're not sure/i)).toBeNull();
  });

  it('clears the flag on an explicit Looks right', async () => {
    const { user } = withDetection({ ...DETECTION, uncertain: ['task'] });
    await user.click(screen.getByRole('button', { name: /looks right/i }));
    expect(screen.queryByText(/we're not sure/i)).toBeNull();
  });

  it('does not flag a confident reading', async () => {
    withDetection();
    expect(screen.queryByText(/we're not sure/i)).toBeNull();
  });

  it('needs only the three questions the file cannot answer', async () => {
    const { user, onSubmit } = withDetection();
    await answer(user, /explain individual predictions/i, 'Not important');
    await answer(user, /straight line/i, "I don't know");
    await answer(user, /only matter in combination/i, 'No');

    await user.click(screen.getByRole('button', { name: /get recommendation/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ rows: '500-10k', missing: 'some' });
  });
});

describe('when the file goes away', () => {
  function rerenderWith(detection: typeof DETECTION | null) {
    const onSubmit = vi.fn();
    const { rerender } = render(
      <ThemeProvider theme={theme}>
        <ProblemForm onSubmit={onSubmit} detection={DETECTION} />
      </ThemeProvider>,
    );
    return {
      onSubmit,
      user: userEvent.setup(),
      clear: () =>
        rerender(
          <ThemeProvider theme={theme}>
            <ProblemForm onSubmit={onSubmit} detection={detection} />
          </ThemeProvider>,
        ),
    };
  }

  it('takes its readings with it', async () => {
    // Left behind they are answers the user never gave, with nothing saying where they
    // came from — the caption that explained them went with the detection.
    const { clear } = rerenderWith(null);
    const kind = () => screen.getByRole('radiogroup', { name: /what are you trying to predict/i });
    expect(within(kind()).getByRole('radio', { name: 'A number' })).toBeChecked();

    clear();
    for (const radio of within(kind()).getAllByRole('radio')) {
      expect(radio).not.toBeChecked();
    }
  });

  it('resets what the user answered themselves too', async () => {
    // Whatever caused `detection` to go null — removed, replaced, or the target column
    // re-picked — the answer was given about the file as it was a moment ago, and none of
    // those leave it safe to keep presenting as still true.
    const { user, clear } = rerenderWith(null);
    await answer(user, /explain individual predictions/i, 'Critical');

    clear();
    const control = screen.getByRole('radiogroup', { name: /explain individual predictions/i });
    for (const radio of within(control).getAllByRole('radio')) {
      expect(radio).not.toBeChecked();
    }
  });

  it('leaves no detected caption behind', async () => {
    const { clear } = rerenderWith(null);
    expect(screen.getByText(/8,412 rows in your file/)).toBeInTheDocument();
    clear();
    expect(screen.queryByText(/in your file/)).toBeNull();
  });
});

describe('replacing one dataset with another', () => {
  const OTHER_DETECTION: Detection = {
    ...DETECTION,
    task: 'binary classification',
    class_balance: 'roughly equal',
    n_rows: 120,
    n_classes: 2,
  };

  /**
   * Mirrors the real sequence: the caller nulls `detection` the moment a new file is
   * accepted, before the new reading resolves. A test that skips the null step tests a
   * sequence the app never actually produces.
   */
  function setup() {
    const onSubmit = vi.fn();
    const { rerender } = render(
      <ThemeProvider theme={theme}>
        <ProblemForm onSubmit={onSubmit} detection={DETECTION} />
      </ThemeProvider>,
    );
    const show = (detection: Detection | null) =>
      rerender(
        <ThemeProvider theme={theme}>
          <ProblemForm onSubmit={onSubmit} detection={detection} />
        </ThemeProvider>,
      );
    return { user: userEvent.setup(), show };
  }

  it('re-detects rather than keeping the first file\'s readings', () => {
    const { show } = setup();
    expect(screen.getByText(/8,412 rows in your file/)).toBeInTheDocument();

    show(null);
    show(OTHER_DETECTION);
    expect(screen.queryByText(/8,412 rows in your file/)).toBeNull();
    expect(screen.getByText(/120 rows in your file/)).toBeInTheDocument();
  });

  it('resets the three questions no file answers, since they were about the old dataset', async () => {
    const { user, show } = setup();
    await answer(user, /explain individual predictions/i, 'Critical');

    show(null);
    show(OTHER_DETECTION);
    const control = screen.getByRole('radiogroup', { name: /explain individual predictions/i });
    for (const radio of within(control).getAllByRole('radio')) {
      expect(radio).not.toBeChecked();
    }
  });
});

describe('answering "what are you predicting" against what the file settles', () => {
  it('flags a contradiction and disables the button, rather than waiting for /api/train to reject it', async () => {
    // DETECTION.task is regression and "task" isn't in `uncertain` — the file settles
    // this with certainty. Overriding to a category anyway once reached scikit-learn as
    // a raw "could not convert string to float" three steps later, at training.
    const { user } = withDetection();
    await answer(user, /what are you trying to predict/i, 'One of two categories');

    expect(screen.getByText(/disagrees with your file|isn't that/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /get recommendation/i })).toHaveAttribute(
      'aria-disabled',
      'true',
    );
  });

  it('names the answer the file actually supports', async () => {
    const { user } = withDetection();
    await answer(user, /what are you trying to predict/i, 'One of two categories');
    expect(screen.getByText(/it looks like a number/i)).toBeInTheDocument();
  });

  it('says nothing when the override still agrees with an uncertain — not contradicted — detection', async () => {
    // "task" is in `uncertain` here: the file itself could not settle it, so overriding
    // it is a judgement call, not a contradiction of a known fact.
    const { user } = withDetection({ ...DETECTION, uncertain: ['task'] });
    await answer(user, /what are you trying to predict/i, 'One of two categories');

    expect(screen.queryByText(/disagrees with your file|isn't that/i)).toBeNull();
  });

  it('clears once the answer agrees with the file again', async () => {
    const { user } = withDetection();
    await answer(user, /what are you trying to predict/i, 'One of two categories');
    expect(screen.getByRole('button', { name: /get recommendation/i })).toHaveAttribute(
      'aria-disabled',
      'true',
    );

    await answer(user, /what are you trying to predict/i, 'A number');
    expect(screen.queryByText(/disagrees with your file|isn't that/i)).toBeNull();
  });

  it('says nothing without a file to contradict', async () => {
    // The no-dataset path (FR-1.3): every answer is the user's own, so there is nothing
    // here for any of them to disagree with.
    const user = userEvent.setup();
    render(
      <ThemeProvider theme={theme}>
        <ProblemForm onSubmit={vi.fn()} />
      </ThemeProvider>,
    );
    await answer(user, /what are you trying to predict/i, 'One of two categories');
    expect(screen.queryByText(/disagrees with your file|isn't that/i)).toBeNull();
  });
});
